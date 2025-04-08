from typing import get_origin, get_args, Any

from di.enums import ComponentScope
from di.exceptions import CycleDetectedError
from ._types import ComponentDefinition


def _toposort_components(
    definitions: list[ComponentDefinition[Any]],
) -> list[type]:
    type_to_definition = {t: d for d in definitions for t in d.satisfied_types}

    resolved: list[type] = []
    visiting = set()
    visited = set()

    def dfs(current: type):
        if current in visited:
            return
        if current in visiting:
            raise CycleDetectedError(component_type=current)
        visiting.add(current)

        definition = type_to_definition.get(current)
        if definition:
            for dep in definition.dependencies:
                origin = get_origin(dep)
                args = get_args(dep)
                if origin in (list, set) and args:
                    for arg in args:
                        if arg in type_to_definition:
                            dfs(arg)
                elif dep in type_to_definition:
                    dfs(dep)

        visiting.remove(current)
        visited.add(current)
        resolved.append(current)

    for t in type_to_definition:
        dfs(t)

    return resolved
