import inspect
from collections import defaultdict, deque
from typing import Any, get_args, get_origin

from di.enums import ComponentScope
from di.exceptions import CycleDetectedError

from ._types import ComponentDefinition, ResolvedComponent


def _toposort_components(
    definitions: list[ComponentDefinition[Any]],
) -> list[type]:
    """
    Sort components in dependency order using topological sort.

    Includes both regular and collection dependencies.

    :param definitions: Component definitions to sort.
    :return: List of types in instantiation order.
    """
    graph = defaultdict(set)
    all_nodes = {definition.type for definition in definitions}

    # Build graph only between actual component types
    for definition in definitions:
        component_type = definition.type
        deps = definition.dependencies | definition.collection_dependencies
        for dep in deps:
            if dep in all_nodes:
                graph[dep].add(component_type)

    in_degree = dict.fromkeys(all_nodes, 0)
    for deps in graph.values():
        for dep in deps:
            in_degree[dep] += 1

    # Use deterministic ordering for queue based on registration order
    type_order = {definition.type: idx for idx, definition in enumerate(definitions)}
    queue = deque(
        sorted(
            (node for node in all_nodes if in_degree[node] == 0),
            key=lambda t: type_order[t],
        )
    )
    sorted_nodes = []

    while queue:
        node = queue.popleft()
        sorted_nodes.append(node)
        for dependent in sorted(graph[node], key=lambda t: type_order[t]):
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)

    if len(sorted_nodes) != len(all_nodes):
        raise CycleDetectedError

    return sorted_nodes


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

    # Index container-scoped definitions by satisfied type
    type_to_definition = {
        definition.type: definition
        for definition in definitions
        if definition.scope == ComponentScope.CONTAINER
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
