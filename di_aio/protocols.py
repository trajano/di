import types
from collections.abc import Awaitable, Callable
from typing import Any, ParamSpec, Protocol, TypeVar

from ._types import ComponentDefinition
from .enums import ComponentScope

P = ParamSpec("P")
T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)


class Context(Protocol[T_co]):
    async def resolve_callable(
        self, fn: Callable[..., Awaitable[T]]
    ) -> Callable[..., Awaitable[T]]: ...  # pragma: no cover
    async def __aenter__(self) -> T_co: ...  # pragma: no cover
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> bool | None: ...  # pragma: no cover
    async def get_instances(self, typ: type[T]) -> list[T]: ...  # pragma: no cover
    async def get_instance(self, typ: type[T]) -> T: ...  # pragma: no cover
    async def get_optional_instance(
        self, typ: type[T]
    ) -> T | None: ...  # pragma: no cover


class ConfigurableContainer(Protocol):
    def add_component_type(self, component_type: type) -> None: ...  # pragma: no cover

    def add_component_factory(
        self,
        factory: Callable[P, T] | Callable[P, Awaitable[T]],
        *,
        scope: ComponentScope = ComponentScope.CONTAINER,
    ) -> None: ...  # pragma: no cover
    def add_component_implementation(
        self, implementation: object
    ) -> None: ...  # pragma: no cover
    def get_definitions(self) -> tuple[ComponentDefinition[Any], ...]:
        """
        Return the collected component definitions.
        """
        ...  # pragma: no cover

    def context(self) -> Context: ...  # pragma: no cover
