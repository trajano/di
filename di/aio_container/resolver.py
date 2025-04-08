from typing import Any, get_origin, get_args
from ._types import ComponentDefinition, ContainerScopeComponent
from di.enums import ComponentScope
from ._toposort import _toposort_components
import inspect


async def resolve_container_scoped_only(
        definitions: list[ComponentDefinition[Any]],
) -> list[ContainerScopeComponent]:
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

    # Index container-scoped definitions by satisfied type
    type_to_definition = {
        t: definition
        for definition in definitions
        if definition.scope == ComponentScope.CONTAINER
        for t in definition.satisfied_types
    }

    # Create instances in resolved order
    instances: list[ContainerScopeComponent] = []
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

            if origin in (list, set) and args and args[0] in definition.collection_dependencies:
                expected_type = args[0]
                kwargs[name] = [
                    instance for typ, instance in constructed.items()
                    if isinstance(instance, expected_type)
                ]
                continue

            kwargs[name] = constructed[dep_type]

        context_manager = definition.factory(**kwargs)
        instance = await context_manager.__aenter__()

        instances.append(
            ContainerScopeComponent(
                satisfied_types=definition.satisfied_types,
                context_manager=context_manager,
                instance=instance,
            )
        )

        for typ in definition.satisfied_types:
            constructed[typ] = instance

    return instances