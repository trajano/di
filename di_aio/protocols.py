import types
from collections.abc import Awaitable, Callable
from typing import Any, ParamSpec, Protocol, TypeVar

from ._types import ComponentDefinition
from .enums import ComponentScope

P = ParamSpec("P")
T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)


class Container(Protocol[T_co]):
    async def resolve_callable(
        self, fn: Callable[..., Awaitable[T]]
    ) -> Callable[..., Awaitable[T]]: ...
    async def __aenter__(self) -> T_co: ...
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> bool | None: ...


class ConfigurableContainer(Protocol):
    def add_component_type(self, component_type: type) -> None: ...

    def add_component_factory(
        self,
        factory: Callable[P, T] | Callable[P, Awaitable[T]],
        *,
        scope: ComponentScope = ComponentScope.CONTAINER,
    ) -> None: ...
    def add_component_implementation(self, implementation: object) -> None: ...
    def get_definitions(self) -> tuple[ComponentDefinition[Any], ...]:
        """
        Return the collected component definitions.
        """
        ...

    def context(self, *, is_default: bool = True) -> Container: ...
