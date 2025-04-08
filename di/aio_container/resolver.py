from typing import Any, get_origin, get_args, Union, TypeVar, Awaitable, Callable
from ._types import ComponentDefinition, ResolvedComponent
from di.enums import ComponentScope
from ._toposort import _toposort_components
import inspect

from di.exceptions import ComponentNotFoundError

T = TypeVar("T")


async def resolve_container_scoped_only(
        definitions: list[ComponentDefinition[Any]],
) -> list[ResolvedComponent]:
    """
    Resolves all container-scoped components in topological order and enters
    their async context managers. Returns the ordered list of live container
    components wrapped in ContainerScopeComponent entries.

    The result order ensures that calling __aexit__() in reverse safely
    tears down dependencies after their dependents.

    :param definitions: All registered component definitions.
    :return: Ordered list of initialized ContainerScopeComponent instances.
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
            if param.kind != param.KEYWORD_ONLY:
                continue
            if param.annotation is inspect.Parameter.empty:
                continue
            if param.default is not inspect.Parameter.empty:
                continue

            dep_type = param.annotation
            origin = get_origin(dep_type)
            args = get_args(dep_type)

            if (
                    origin in (list, set)
                    and args
                    and args[0] in definition.collection_dependencies
            ):
                expected_type = args[0]
                kwargs[name] = [
                    instance
                    for typ, instance in constructed.items()
                    if isinstance(instance, expected_type)
                ]
                continue

            kwargs[name] = constructed[dep_type]

        context_manager = definition.factory(**kwargs)
        instance = await context_manager.__aenter__()

        instances.append(
            ResolvedComponent(
                satisfied_types=definition.satisfied_types,
                context_manager=context_manager,
                instance=instance,
            )
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
    """
    Resolve all component instances satisfying a given type, including those
    that need to be lazily constructed from function-scoped definitions.

    This method handles:
    - Direct type lookups (must be satisfied or raise ComponentNotFoundError).
    - Optional dependencies (injected as `None` if not found).
    - Collection dependencies (injected as empty list/set if not found).

    Assumes `definitions` are already topologically sorted.

    :param typ: The type to resolve.
    :param resolved_components: Components already resolved (e.g., container-scoped).
    :param definitions: All component definitions, already topologically sorted.
    :return: List of instances satisfying the type (usually length 1 unless multi-binding).
    :raises ComponentNotFoundError: If a required dependency cannot be resolved.
    """
    results: list[T] = []

    # Cache to avoid duplicate instantiation
    constructed: dict[type, Any] = {
        t: c.instance for c in resolved_components for t in c.satisfied_types
    }

    # Step 1: Reuse already-resolved components
    for component in resolved_components:
        if typ in component.satisfied_types:
            results.append(component.instance)

    # Step 2: Resolve function-scoped components if needed
    for definition in definitions:
        if definition.scope != ComponentScope.FUNCTION:
            continue
        if typ not in definition.satisfied_types:
            continue

        sig = inspect.signature(definition.type.__init__)
        kwargs = {}

        for name, param in sig.parameters.items():
            if param.kind != param.KEYWORD_ONLY:
                continue
            if param.annotation is inspect.Parameter.empty:
                continue
            if param.default is not inspect.Parameter.empty:
                continue

            dep = param.annotation
            origin = get_origin(dep)
            args = get_args(dep)

            # Optional[X] or Union[X, NoneType]
            if origin is Union and type(None) in args and len(args) == 2:
                inner_type = next(a for a in args if a is not type(None))
                matches = await resolve_satisfying_components(
                    inner_type,
                    resolved_components=resolved_components,
                    definitions=definitions,
                )
                kwargs[name] = matches[0] if matches else None

            # list[X] or set[X]
            elif origin in (list, set) and args:
                item_type = args[0]
                matches = await resolve_satisfying_components(
                    item_type,
                    resolved_components=resolved_components,
                    definitions=definitions,
                )
                kwargs[name] = origin(matches)

            # Direct required dependency
            else:
                matches = await resolve_satisfying_components(
                    dep,
                    resolved_components=resolved_components,
                    definitions=definitions,
                )
                if not matches:
                    raise ComponentNotFoundError(component_type=dep)
                kwargs[name] = matches[0]

        context_manager = definition.factory(**kwargs)
        instance = await context_manager.__aenter__()

        resolved_components.append(
            ResolvedComponent(
                satisfied_types=definition.satisfied_types,
                context_manager=context_manager,
                instance=instance,
            )
        )

        for t in definition.satisfied_types:
            constructed[t] = instance

        if typ in definition.satisfied_types:
            results.append(instance)

    return results

async def resolve_callable(
        fn: Callable[..., Awaitable[T]],
        container_scope_components: list[ResolvedComponent[Any]],
        definitions: list[ComponentDefinition[Any]]
) ->  Callable[..., Awaitable[T]]:
    """
    Resolves the required dependencies of the callable and returns a new coroutine function
    with those arguments already applied. The result can be awaited directly.

    This is intended to support `@autowired`-style use cases.

    :param fn: A function whose dependencies are declared via keyword-only parameters.
    :param container_scope_components: Already resolved container-scoped components.
    :param definitions: All component definitions.
    :return: A coroutine function that requires no arguments.
    """
    sig = inspect.signature(fn)
    kwargs = {}

    for name, param in sig.parameters.items():
        if param.kind != param.KEYWORD_ONLY:
            continue
        if param.annotation is inspect.Parameter.empty:
            continue
        if param.default is not inspect.Parameter.empty:
            continue

        dep_type = param.annotation
        origin = get_origin(dep_type)
        args = get_args(dep_type)

        # Optional[X] or Union[X, None]
        if origin is Union and type(None) in args and len(args) == 2:
            inner_type = next(a for a in args if a is not type(None))
            matches = await resolve_satisfying_components(
                inner_type,
                resolved_components=container_scope_components,
                definitions=definitions,
            )
            kwargs[name] = matches[0] if matches else None

        # list[X] or set[X]
        elif origin in (list, set) and args:
            item_type = args[0]
            matches = await resolve_satisfying_components(
                item_type,
                resolved_components=container_scope_components,
                definitions=definitions,
            )
            kwargs[name] = origin(matches)

        # Direct required dependency
        else:
            matches = await resolve_satisfying_components(
                dep_type,
                resolved_components=container_scope_components,
                definitions=definitions,
            )
            if not matches:
                raise ComponentNotFoundError(component_type=dep_type)
            kwargs[name] = matches[0]

    async def wrapped() -> T:
        return await fn(**kwargs)

    return wrapped
