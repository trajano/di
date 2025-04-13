from collections import defaultdict, deque
from typing import Any, ParamSpec

from ._types import ComponentDefinition
from .exceptions import CycleDetectedError

P = ParamSpec("P")


def _toposort_components(
    definitions: list[ComponentDefinition[Any]],
) -> list[type]:
    """Sort components in dependency order using topological sort.

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
