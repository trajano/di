from typing import Callable, Awaitable, TypeVar, Any, ParamSpec, Self, Tuple

from di._util import (
    extract_dependencies_from_signature,
    extract_satisfied_types_from_type,
    extract_satisfied_types_from_return_of_callable,
)
from ._extractors import extract_dependencies_from_callable
from di.enums import ComponentScope, ContainerState
from di.exceptions import DuplicateRegistrationError
from ._convert_to_factory import convert_to_factory
from ._types import ComponentDefinition
from .resolver import resolve_container_scoped_only
from .validator import validate_container_definitions

P = ParamSpec("P")
T = TypeVar("T")


class ConfigurableAioContainer:
    """
    Configurable container that accepts component registrations and builds
    a finalized AioContainer.
    """

    def __init__(self) -> None:
        self._definitions: list[ComponentDefinition[Any]] = []
        self._registered_sources: set = set()

    def _ensure_not_registered(self, component_source: Any):
        if component_source in self._registered_sources:
            raise DuplicateRegistrationError(type_or_factory=component_source)
        self._registered_sources.add(component_source)

    def add_component_type(self, component_type: type) -> None:
        self._ensure_not_registered(component_type)
        factory = convert_to_factory(component_type)
        deps, collection_deps = extract_dependencies_from_callable(component_type.__init__)
        self._definitions.append(
            ComponentDefinition(
                type=component_type,
                satisfied_types=extract_satisfied_types_from_type(component_type),
                dependencies=deps,
                collection_dependencies=collection_deps,
                factory=factory,
                scope=ComponentScope.CONTAINER,
            )
        )

    def add_component_implementation(self, implementation: object) -> None:
        self._ensure_not_registered(implementation)
        factory = convert_to_factory(implementation)
        self._definitions.append(
            ComponentDefinition(
                type=type(implementation),
                satisfied_types=extract_satisfied_types_from_type(type(implementation)),
                dependencies=set(),
                collection_dependencies=set(),
                factory=factory,
                scope=ComponentScope.CONTAINER,
            )
        )

    def add_component_factory(
            self,
            factory: Callable[P, T] | Callable[P, Awaitable[T]],
            *,
            scope: ComponentScope = ComponentScope.CONTAINER,
    ) -> None:
        self._ensure_not_registered(factory)
        async_factory = convert_to_factory(factory)
        deps, collection_deps = extract_dependencies_from_callable(factory)
        _return_type, satisfied_types = extract_satisfied_types_from_return_of_callable(
            factory
        )
        self._definitions.append(
            ComponentDefinition(
                type=factory,
                satisfied_types=satisfied_types,
                dependencies=deps,
                collection_dependencies=collection_deps,
                factory=async_factory,
                scope=scope,
            )
        )

    def add_context_managed_component(
            self,
            component_type: type,
            *,
            scope: ComponentScope = ComponentScope.CONTAINER,
    ) -> None:
        """
        Register a component type that implements sync or async context management.

        This ensures that the component's lifecycle is handled via `async with`
        and cleanup is invoked on container exit.

        :param component_type: A class that implements either `__enter__/__exit__`
                               or `__aenter__/__aexit__`.
        :param scope: The lifecycle scope for the component (default: CONTAINER).
        :raises DuplicateRegistrationError: If the type has already been registered.
        """
        self._ensure_not_registered(component_type)
        factory = convert_to_factory(component_type)
        deps, collection_deps = extract_dependencies_from_callable(component_type.__init__)
        self._definitions.append(
            ComponentDefinition(
                type=component_type,
                satisfied_types=extract_satisfied_types_from_type(component_type),
                dependencies=deps,
                collection_dependencies=collection_deps,
                factory=factory,
                scope=scope,
            )
        )

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
        self._container_scope_components: list = []

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