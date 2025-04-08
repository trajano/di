from typing import Callable, Awaitable, TypeVar, Any, ParamSpec, Self, Tuple

from di.configurable_container import ConfigurableContainer
from di.enums import ComponentScope, ContainerState
from ._convert_to_factory import convert_to_factory
from ._types import ComponentDefinition, ContainerScopeComponent
from .resolver import resolve_container_scoped_only
from .validator import validate_container_definitions
from di._util import (
    extract_dependencies_from_signature,
    extract_satisfied_types_from_return_of_callable,
    extract_satisfied_types_from_type,
)

P = ParamSpec("P")
T = TypeVar("T")


class ConfigurableAioContainer(ConfigurableContainer):
    """
    Configurable container that accepts component registrations and builds
    a finalized AioContainer.
    """

    def __init__(self) -> None:
        self._definitions: list[ComponentDefinition[Any]] = []

    def add_component_type(self, component_type: type) -> None:
        factory = convert_to_factory(component_type)
        self._definitions.append(ComponentDefinition(
            satisfied_types=extract_satisfied_types_from_type(component_type),
            dependencies=extract_dependencies_from_signature(factory),
            factory=factory,
            scope=ComponentScope.CONTAINER
        ))

    def add_component_implementation(self, implementation: object) -> None:
        factory = convert_to_factory(implementation)
        self._definitions.append(ComponentDefinition(
            satisfied_types=extract_satisfied_types_from_type(type(implementation)),
            dependencies=set(),
            factory=factory,
            scope=ComponentScope.CONTAINER
        ))

    def add_component_factory(
            self,
            factory: Callable[P, T] | Callable[P, Awaitable[T]],
            *,
            scope: ComponentScope = ComponentScope.CONTAINER,
    ) -> None:
        async_factory = convert_to_factory(factory)
        _return_type, satisfied_types =extract_satisfied_types_from_return_of_callable(factory)
        self._definitions.append(ComponentDefinition(
            satisfied_types=satisfied_types ,
            dependencies=extract_dependencies_from_signature(factory),
            factory=async_factory,
            scope=scope
        ))

    def get_definitions(self) -> Tuple[ComponentDefinition[Any], ...]:
        """
        Return the collected component definitions for use in AioContainer.
        """
        return tuple(self._definitions)


class AioContainer:
    """
    Runtime container that resolves and manages container-scoped components.
    """

    def __init__(self, definitions: list[ComponentDefinition[Any]]) -> None:
        self._definitions = list(definitions)
        self._state = ContainerState.INITIALIZING
        self._container_scope_components: list[ContainerScopeComponent] = []

    async def __aenter__(self) -> Self:
        self._state = ContainerState.VALIDATING
        validate_container_definitions(self._definitions)

        self._state = ContainerState.SERVICING
        self._container_scope_components = await resolve_container_scoped_only(
            self._definitions
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._state = ContainerState.CLOSING
        for component in reversed(self._container_scope_components):
            await component.context_manager.__aexit__(exc_type, exc_val, exc_tb)
        self._container_scope_components.clear()
