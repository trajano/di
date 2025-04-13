from collections.abc import Awaitable, Callable, Iterable
from contextlib import AbstractAsyncContextManager
from types import TracebackType
from typing import Any, ParamSpec, Self, TypeVar, overload

from ._types import ComponentDefinition, ResolvedComponent
from ._validator import validate_container_definitions
from .enums import ContainerState
from .exceptions import ComponentNotFoundError
from .protocols import ConfigurableContainer, Context
from .resolver import (
    resolve_callable_dependencies,
    resolve_container_scoped_only,
    resolve_satisfying_components,
)

P = ParamSpec("P")
T = TypeVar("T")


class AioContext(AbstractAsyncContextManager, Context):
    """Async DI container that manages container-scoped components."""

    @overload
    def __init__(self, *, definitions: Iterable[ComponentDefinition[Any]]) -> None: ...
    @overload
    def __init__(self, *, container: ConfigurableContainer) -> None: ...

    def __init__(
        self,
        *,
        definitions: Iterable[ComponentDefinition[Any]] | None = None,
        container: ConfigurableContainer | None = None,
    ) -> None:
        """Initialize the AioContext.

        :param definitions: Component definitions to register.
        :param container: Container whose definitions will be used.
        :raises ValueError: If neither nor both arguments are passed.
        """
        if container and not definitions:
            self._definitions = list(container.get_definitions())
        elif definitions and not container:
            self._definitions = list(definitions)
        else:
            msg = "Must be either definitions or container"
            raise ValueError(msg)

        self._state = ContainerState.INITIALIZING
        self._container_scope_components: list[ResolvedComponent[Any]] = []

    async def __aenter__(self) -> Self:
        """Validate and initialize all container-scoped components.

        :returns: Self after initialization.
        """
        self._state = ContainerState.VALIDATING
        validate_container_definitions(self._definitions)

        self._state = ContainerState.SERVICING
        self._container_scope_components = await resolve_container_scoped_only(
            self._definitions,
        )
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Clean up all container-scoped component contexts."""
        self._state = ContainerState.CLOSING
        for component in reversed(self._container_scope_components):
            await component.context_manager.__aexit__(exc_type, exc_val, exc_tb)
        self._container_scope_components.clear()

    async def resolve_callable(
        self, fn: Callable[..., Awaitable[T]],
    ) -> Callable[..., Awaitable[T]]:
        """Resolve a coroutine function's dependencies for invocation.

        :param fn: The async function to resolve.
        :returns: A wrapped coroutine with injected dependencies.
        """
        return await resolve_callable_dependencies(
            fn,
            container_scope_components=self._container_scope_components,
            definitions=self._definitions,
        )

    async def get_instances(self, typ: type[T]) -> list[T]:
        """Get all instances satisfying a given type.

        :param typ: The type to resolve.
        :returns: A list of instances matching the type.
        """
        return await resolve_satisfying_components(
            typ,
            resolved_components=self._container_scope_components,
            definitions=self._definitions,
        )

    async def get_instance(self, typ: type[T]) -> T:
        """Get a single instance satisfying a given type.

        :param typ: The type to resolve.
        :returns: The first instance matching the type.
        :raises ComponentNotFoundError: If the component is not found.
        """
        maybe_instance = await self.get_optional_instance(typ)
        if not maybe_instance:
            raise ComponentNotFoundError(component_type=typ)
        return maybe_instance

    async def get_optional_instance(self, typ: type[T]) -> T | None:
        """Return a matching instance or None if not found.

        :param typ: The type to resolve.
        :returns: The first matching instance or None.
        """
        return (await self.get_instances(typ))[0]

    def get_satisfied_types(self) -> set[type]:
        """Return all types satisfied by this container.

        :returns: A set of all satisfied types from registered definitions.
        """
        return {
            satisfied_type
            for definition in self._definitions
            for satisfied_type in definition.satisfied_types
        }
