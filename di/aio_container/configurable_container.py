import contextlib
from contextlib import AbstractContextManager, AbstractAsyncContextManager
from typing import Callable, Awaitable, TypeVar, Any, ParamSpec, Self
from typing import Tuple

from di import DuplicateRegistrationError
from di._util import (
    extract_satisfied_types_from_type,
    extract_satisfied_types_from_return_of_callable,
)
from di.aio_container._convert_to_factory import convert_to_factory
from di.aio_container._extractors import extract_dependencies_from_callable
from di.aio_container._types import ComponentDefinition
from di.configurable_container import ConfigurableContainer
from di.enums import ComponentScope

P = ParamSpec("P")
T = TypeVar("T")


class ConfigurableAioContainer(ConfigurableContainer):
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
        deps, collection_deps = extract_dependencies_from_callable(
            component_type.__init__
        )
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
        return_type, satisfied_types = extract_satisfied_types_from_return_of_callable(
            factory
        )
        self._definitions.append(
            ComponentDefinition(
                type=return_type,
                satisfied_types=satisfied_types,
                dependencies=deps,
                collection_dependencies=collection_deps,
                factory=async_factory,
                scope=scope,
            )
        )

    def add_context_managed_function(
        self,
        fn: Callable[..., contextlib.AbstractAsyncContextManager],
        *,
        scope: ComponentScope = ComponentScope.CONTAINER,
    ) -> None:
        """
        Register a component type that implements sync or async context management.

        This ensures that the component's lifecycle is handled via `async with`
        and cleanup is invoked on container exit.

        :param fn: A callable annotated with @asynccontextmanager
        :param scope: The lifecycle scope for the component (default: CONTAINER).
        :raises DuplicateRegistrationError: If the type has already been registered.
        """
        self._ensure_not_registered(fn)
        deps, collection_deps = extract_dependencies_from_callable(fn)
        return_type, satisfied_types = extract_satisfied_types_from_return_of_callable(
            fn
        )
        self._definitions.append(
            ComponentDefinition(
                type=return_type,
                satisfied_types=satisfied_types,
                dependencies=deps,
                collection_dependencies=collection_deps,
                factory=fn,
                scope=scope,
            )
        )

    def add_context_managed_type(
        self,
        cm_type: type[contextlib.AbstractAsyncContextManager]
                 | type[contextlib.AbstractContextManager],
        *,
        scope: ComponentScope = ComponentScope.CONTAINER,
    ) -> None:
        """
        Register a component type that implements sync or async context management.

        This ensures that the component's lifecycle is handled via `async with`
        and cleanup is invoked on container exit.

        :param cm_type: A context manager
        :param scope: The lifecycle scope for the component (default: CONTAINER).
        :raises DuplicateRegistrationError: If the type has already been registered.
        """
        self._ensure_not_registered(cm_type)
        factory = convert_to_factory(cm_type)
        deps, collection_deps = extract_dependencies_from_callable(cm_type.__init__)
        self._definitions.append(
            ComponentDefinition(
                type=cm_type,
                satisfied_types=extract_satisfied_types_from_type(cm_type),
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

    def __iadd__(self, other: Any) -> Self:
        """Routes to the proper add method"""
        if isinstance(other, type):
            if issubclass(other, (AbstractContextManager, AbstractAsyncContextManager)):
                self.add_context_managed_type(other)
            else:
                self.add_component_type(other)
        elif callable(other):
            self.add_component_factory(other)
        else:
            self.add_component_implementation(other)

        return self
