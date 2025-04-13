"""Resolver."""

import functools
import inspect
from collections.abc import Awaitable, Callable
from inspect import Parameter
from typing import Any, ParamSpec, TypeVar, Union, get_args, get_origin

from ._toposort import _toposort_components
from ._types import ComponentDefinition, ResolvedComponent
from ._util import maybe_dependency
from .enums import ComponentScope
from .exceptions import ComponentNotFoundError

UNION_NONE_ARGS_LENGTH = 2

P = ParamSpec("P")
T = TypeVar("T")


def _maybe_collection_dependency(
    param: Parameter,
    definition: ComponentDefinition,
) -> bool:
    dep_type = param.annotation
    origin = get_origin(dep_type)
    args = get_args(dep_type)

    is_collection = origin in (list, set)
    if len(args) == 0:
        return False
    is_arg_in_collection_dependencies = args[0] in definition.collection_dependencies
    return is_collection and is_arg_in_collection_dependencies


def _is_dep_optional(origin: type, args: tuple[Any]) -> bool:
    return (
        origin is Union and type(None) in args and len(args) == UNION_NONE_ARGS_LENGTH
    )


def _is_dep_collection(origin: type, args: tuple[Any]) -> bool:
    return origin in (list, set) and len(args) == 1


async def resolve_container_scoped_only(
    definitions: list[ComponentDefinition[Any]],
) -> list[ResolvedComponent]:
    """Resolve container-scoped components in topological order.

    Enters each component's async context and returns the ordered list of
    initialized `ContainerScopeComponent` entries.

    The result order ensures that calling ``__aexit__()`` in reverse safely
    tears down dependencies after their dependents.

    :param definitions: All registered component definitions.
    :returns: Ordered list of initialized ContainerScopeComponent instances.
    """
    sorted_types = _toposort_components(definitions)

    # Only keep container-scoped types for resolution
    container_types = {
        t
        for d in definitions
        if d.scope == ComponentScope.CONTAINER
        for t in d.satisfied_types
    }
    sorted_types = [t for t in sorted_types if t in container_types]

    # Index container-scoped definitions by satisfied type
    type_to_definition = {
        t: definition
        for definition in definitions
        if definition.scope == ComponentScope.CONTAINER
        for t in definition.satisfied_types
    }

    # Create instances in resolved order
    instances: list[ResolvedComponent] = []
    constructed: dict[type, Any] = {}

    for t in sorted_types:
        definition = type_to_definition[t]
        sig = inspect.signature(definition.type.__init__)
        kwargs = {}
        for name, param in sig.parameters.items():
            # Only consider typed keyword-only parameters without defaults
            if not maybe_dependency(param):
                continue

            dep_type = param.annotation
            args = get_args(dep_type)

            if _maybe_collection_dependency(param, definition):
                expected_type = args[0]
                kwargs[name] = [
                    instance
                    for typ, instance in constructed.items()
                    if isinstance(instance, expected_type)
                ]
                continue

            kwargs[name] = constructed[dep_type]

        context_manager = definition.build_context_manager(**kwargs)
        instance = await context_manager.__aenter__()

        instances.append(
            ResolvedComponent(
                satisfied_types=definition.satisfied_types,
                context_manager=context_manager,
                instance=instance,
            ),
        )

        for typ in definition.satisfied_types:
            constructed[typ] = instance

    return instances


async def resolve_satisfying_components(
    typ: type[T],
    /,
    *,
    resolved_components: list[ResolvedComponent[Any]],
    definitions: list[ComponentDefinition[Any]],
) -> list[T]:
    """Resolve components matching a type from resolved and scoped sources.

    This includes components that must be lazily created from function-scoped
    definitions.

    This method handles:
    - Direct type lookups (raises if unsatisfied).
    - Optional dependencies (`None` if not found).
    - Collection dependencies (empty list/set if not found).

    Assumes `definitions` are already topologically sorted.

    :param typ: The type to resolve.
    :param resolved_components: Components already resolved (e.g.,
        container-scoped). This is immutable.
    :param definitions: All component definitions, already topologically
        sorted.
    :returns: List of instances satisfying the type.
    :raises ComponentNotFoundError: If a required dependency cannot be
        resolved.
    """
    # Cache to avoid duplicate instantiation
    constructed: dict[type, Any] = {
        t: c.instance for c in resolved_components for t in c.satisfied_types
    }

    # Step 1: Reuse already-resolved components
    results = [
        component.instance
        for component in resolved_components
        if typ in component.satisfied_types
    ]

    # Step 2: Resolve function-scoped components if needed
    for definition in definitions:
        if definition.scope != ComponentScope.FUNCTION:
            continue
        if typ not in definition.satisfied_types:
            continue

        sig = inspect.signature(definition.type.__init__)
        kwargs = {}
        args = ()
        copy_of_resolved_components = resolved_components.copy()

        for name, param in sig.parameters.items():
            if not maybe_dependency(param):
                continue

            dep = param.annotation
            origin = get_origin(dep)
            param_args = get_args(dep)

            if _is_dep_optional(origin, param_args):
                inner_type = next(a for a in param_args if a is not type(None))
                matches = await resolve_satisfying_components(
                    inner_type,
                    resolved_components=copy_of_resolved_components,
                    definitions=definitions,
                )
                kwargs[name] = matches[0] if matches else None

            elif _is_dep_collection(origin, param_args):
                item_type = param_args[0]
                matches = await resolve_satisfying_components(
                    item_type,
                    resolved_components=copy_of_resolved_components,
                    definitions=definitions,
                )
                kwargs[name] = origin(matches)

            # Direct required dependency
            else:
                matches = await resolve_satisfying_components(
                    dep,
                    resolved_components=copy_of_resolved_components,
                    definitions=definitions,
                )
                if not matches:
                    raise ComponentNotFoundError(component_type=dep)
                kwargs[name] = matches[0]

        context_manager = definition.build_context_manager(*args, **kwargs)
        instance = await context_manager.__aenter__()

        copy_of_resolved_components.append(
            ResolvedComponent(
                satisfied_types=definition.satisfied_types,
                context_manager=context_manager,
                instance=instance,
            ),
        )

        for t in definition.satisfied_types:
            constructed[t] = instance

        if typ in definition.satisfied_types:
            results.append(instance)

    return results


async def resolve_callable_dependencies(
    fn: Callable[..., Awaitable[T]],
    container_scope_components: list[ResolvedComponent[Any]],
    definitions: list[ComponentDefinition[Any]],
) -> Callable[..., Awaitable[T]]:
    """Bind dependencies to a coroutine function using async context.

    The returned function still accepts any positional and keyword arguments
    provided by the caller.

    This ensures all function-scoped components are managed with an async
    context manager stack.

    :param fn: A function whose dependencies are declared via keyword-only
        parameters.
    :param container_scope_components: Already resolved container-scoped
        components.
    :param definitions: All component definitions.
    :returns: A coroutine function that may still take user-supplied arguments.
    """

    @functools.wraps(fn)
    async def wrapped(*wrapped_args: P.args, **user_kwargs: P.kwargs) -> T:
        sig = inspect.signature(fn)
        injected_kwargs = {}
        for name, param in sig.parameters.items():
            if not maybe_dependency(param):
                continue

            dep_type = param.annotation
            origin = get_origin(dep_type)
            args = get_args(dep_type)

            # is Optional[X] or Union[X, None]
            if _is_dep_optional(origin, args):
                inner_type = next(a for a in args if a is not type(None))
                matches = await resolve_satisfying_components(
                    inner_type,
                    resolved_components=container_scope_components,
                    definitions=definitions,
                )
                injected_kwargs[name] = matches[0] if matches else None

            # is list[X] or set[X]
            elif _is_dep_collection(origin, args):
                item_type = args[0]
                matches = await resolve_satisfying_components(
                    item_type,
                    resolved_components=container_scope_components,
                    definitions=definitions,
                )
                injected_kwargs[name] = origin(matches)

            # Direct required dependency
            else:
                matches = await resolve_satisfying_components(
                    dep_type,
                    resolved_components=container_scope_components,
                    definitions=definitions,
                )
                if matches:
                    injected_kwargs[name] = matches[0]

        return await fn(*wrapped_args, **user_kwargs, **injected_kwargs)

    return wrapped
