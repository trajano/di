"""Resolver."""

import functools
import inspect
from collections.abc import Awaitable, Callable
from inspect import Parameter
from typing import Any, ParamSpec, TypeVar, Union, get_args, get_origin

from ._util import maybe_dependency
from .resolver2 import resolve_scope
from .resolver2.scope_filters import is_container_scope, is_function_scope
from .types import ComponentDefinition, ResolvedComponent

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
    return await resolve_scope(definitions, scope_filter=is_container_scope)


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
    resolved = await resolve_scope(
        definitions, scope_filter=is_function_scope, parent=resolved_components
    )
    return [t.instance for t in resolved if typ in t.satisfied_types]


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
