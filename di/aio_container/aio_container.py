import contextlib
from collections.abc import Awaitable, Callable, Iterable
from typing import (
    Any,
    ParamSpec,
    Self,
    TypeVar,
    overload,
)

from di.enums import ContainerState
from di.exceptions import ComponentNotFoundError

from ._types import ComponentDefinition, ResolvedComponent
from .configurable_container import ConfigurableAioContainer
from .default_aio_container_future import default_aio_container_future
from .default_container import default_container
from .resolver import (
    resolve_callable_dependencies,
    resolve_container_scoped_only,
    resolve_satisfying_components,
)
from .validator import validate_container_definitions

P = ParamSpec("P")
T = TypeVar("T")


class AioContainer(contextlib.AbstractAsyncContextManager):
    """
    Runtime container that resolves and manages container-scoped components.
    """

    @overload
    def __init__(self, definitions: Iterable[ComponentDefinition[Any]]) -> None: ...
    @overload
    def __init__(
        self,
        definitions: None = None,
        container: ConfigurableAioContainer | None = None,
    ) -> None: ...

    def __init__(
        self,
        definitions: Iterable[ComponentDefinition[Any]] | None = None,
        *,
        container: ConfigurableAioContainer | None = None,
    ) -> None:
        if not definitions and not container:
            # this is the default container
            self._definitions = list(default_container.get_definitions())
            default_aio_container_future.set_result(self)
        elif container and not definitions:
            self._definitions = list(container.get_definitions())
        elif definitions and not container:
            self._definitions = list(definitions)
        else:
            raise ValueError("Cannot specify both definitions and container")
        self._state = ContainerState.INITIALIZING
        self._container_scope_components: list[ResolvedComponent[Any]] = []

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

    async def resolve_callable(
        self, fn: Callable[..., Awaitable[T]]
    ) -> Callable[..., Awaitable[T]]:
        return await resolve_callable_dependencies(
            fn,
            container_scope_components=self._container_scope_components,
            definitions=self._definitions,
        )

    async def get_instances(self, typ: type[T]) -> list[T]:
        return await resolve_satisfying_components(
            typ,
            resolved_components=self._container_scope_components,
            definitions=self._definitions,
        )

    async def get_instance(self, typ: type[T]) -> T:
        maybe_instance = await self.get_optional_instance(typ)
        if not maybe_instance:
            raise ComponentNotFoundError(component_type=typ)
        return maybe_instance

    async def get_optional_instance(self, typ: type[T]) -> T | None:
        return (await self.get_instances(typ))[0]

    def get_satisfied_types(self) -> set[type]:
        return {
            satisfied_type
            for definition in self._definitions
            for satisfied_type in definition.satisfied_types
        }
