import contextlib
import inspect
from collections.abc import Awaitable, Callable
from contextlib import AbstractAsyncContextManager
from typing import Any, ParamSpec, Self, TypeVar, overload

from di._util import (
    extract_dependencies_from_signature,
    extract_satisfied_types_from_return_of_callable,
    extract_satisfied_types_from_type,
)
from di.enums import ComponentScope, ContainerState
from di.exceptions import (
    ContainerLockedError,
    DuplicateRegistrationError,
)
from ._convert_to_factory import convert_to_factory
from ._types import ComponentDefinition, ContainerScopeComponent
from .validator import validate_container_definitions

P = ParamSpec("P")
T = TypeVar("T")


class AioContainer(contextlib.AbstractAsyncContextManager):
    def __init__(self):
        self._definitions: list[ComponentDefinition[Any]] = []
        self._container_scope_components: list[ContainerScopeComponent[Any]] = []
        self._component_sources_registered: set = set()
        self._state = ContainerState.INITIALIZING

    def _ensure_not_locked(self):
        if self._state != ContainerState.INITIALIZING:
            raise ContainerLockedError

    def _ensure_not_registered(self, component_source: Any):
        if component_source in self._component_sources_registered:
            raise DuplicateRegistrationError(type_or_factory=component_source)
        self._component_sources_registered.add(component_source)

    def add_component_type(self, component_type: type) -> None:
        self._ensure_not_locked()
        self._ensure_not_registered(component_type)

        factory = convert_to_factory(component_type)
        deps = extract_dependencies_from_signature(factory)
        satisfied_types = extract_satisfied_types_from_type(component_type)

        self._definitions.append(
            ComponentDefinition(
                satisfied_types=satisfied_types,
                dependencies=deps,
                factory=factory,
                scope=ComponentScope.CONTAINER,
            )
        )

    def add_component_implementation(self, implementation: object) -> None:
        self._ensure_not_locked()
        self._ensure_not_registered(implementation)

        factory = convert_to_factory(implementation)
        satisfied_types = extract_satisfied_types_from_type(type(implementation))

        self._definitions.append(
            ComponentDefinition(
                satisfied_types=satisfied_types,
                dependencies=set(),
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
        self._ensure_not_locked()
        self._ensure_not_registered(factory)

        normalized_factory = convert_to_factory(factory)
        deps = extract_dependencies_from_signature(factory)
        _primary_type, satisfied_types = (
            extract_satisfied_types_from_return_of_callable(factory)
        )

        self._definitions.append(
            ComponentDefinition(
                satisfied_types=satisfied_types,
                dependencies=deps,
                factory=normalized_factory,
                scope=scope,
            )
        )

    async def __aenter__(self):
        """switches the state to validating and start validation of the container"""
        self._state = ContainerState.VALIDATING
        validate_container_definitions(self._definitions)
        await self._initialize_container_scoped()
        self._state = ContainerState.SERVICING
        return self

    async def _initialize_container_scoped(self):
        self._container_scope_components = await resolve_container_scoped_only(
            self._definitions
        )

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._state = ContainerState.CLOSING

        # Reverse teardown of all container-scoped components
        for component in reversed(self._container_scope_components):
            await component.context_manager.__aexit__(exc_type, exc_val, exc_tb)

        self._container_scope_components.clear()

    @overload
    def __iadd__(self, other: type) -> Self: ...

    @overload
    def __iadd__(self, other: Callable[..., Any]) -> Self: ...

    @overload
    def __iadd__(self, other: object) -> Self: ...

    def __iadd__(self, other: object) -> Self:
        if inspect.isclass(other):
            self.add_component_type(other)
        elif callable(other):
            self.add_component_factory(other)
        else:
            self.add_component_implementation(other)
        return self
