from typing import Any, get_args, get_origin

from ._toposort import _toposort_components
from ._types import ComponentDefinition
from .enums import ComponentScope
from .exceptions import (
    ComponentNotFoundError,
    ConfigurationError,
)


def validate_container_definitions(definitions: list[ComponentDefinition[Any]]) -> None:
    """Validates all component definitions for:

    - Scope rule: container-scoped components may only depend on container-scoped ones.
    - Dependency rule: all dependencies must be satisfied unless they are list[T] or
      set[T].
    - No cycles are allowed among container-scoped components.

    :param definitions: List of all registered component definitions.
    :raises ContainerInitializationError: If a scope rule is violated.
    :raises ComponentNotFoundError: If a dependency is not registered.
    :raises CycleDetectedError: If container-scoped components form a cycle.
    """
    type_to_scope: dict[type, ComponentScope] = {}
    type_to_definition: dict[type, ComponentDefinition[Any]] = {}

    for definition in definitions:
        for t in definition.satisfied_types:
            if t not in type_to_scope or definition.scope == ComponentScope.CONTAINER:
                type_to_scope[t] = definition.scope
                type_to_definition[t] = definition

    _detect_unresolved_dependencies(definitions, type_to_scope)
    _detect_scope_violations(definitions, type_to_scope)
    _detect_cycles(definitions)


def _detect_unresolved_dependencies(
    definitions: list[ComponentDefinition[Any]],
    type_to_scope: dict[type, ComponentScope],
) -> None:
    for definition in definitions:
        for dep in definition.dependencies:
            origin = get_origin(dep)
            args = get_args(dep)

            if origin in (list, set) and args:
                continue

            if dep not in type_to_scope:
                raise ComponentNotFoundError(component_type=dep)


def _detect_scope_violations(
    definitions: list[ComponentDefinition[Any]],
    type_to_scope: dict[type, ComponentScope],
) -> None:
    for definition in definitions:
        if definition.scope != ComponentScope.CONTAINER:
            continue

        for dep in definition.dependencies:
            origin = get_origin(dep)
            args = get_args(dep)

            if origin in (list, set) and args:
                for arg in args:
                    if type_to_scope.get(arg) != ComponentScope.CONTAINER:
                        msg = (
                            f"Multi-injection dependency {origin}[{arg}] is "
                            f"satisfied by a non-container-scoped component"
                        )
                        raise ConfigurationError(msg)
                continue

            dep_scope = type_to_scope.get(dep)
            if dep_scope != ComponentScope.CONTAINER:
                msg = (
                    f"Container-scoped component cannot depend on function-scoped "
                    f"dependency: {dep}"
                )
                raise ConfigurationError(msg)


def _detect_cycles(definitions: list[ComponentDefinition[Any]]) -> None:
    _toposort_components(definitions)
