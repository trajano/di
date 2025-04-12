from collections.abc import Awaitable, Callable
from typing import ParamSpec, Protocol, TypeVar

from .enums import ComponentScope

P = ParamSpec("P")
T = TypeVar("T")
R = TypeVar("R")


class ConfigurableContainer(Protocol):
    def add_component_type(self, component_type: type) -> None: ...

    def add_component_factory(
        self,
        factory: Callable[P, T] | Callable[P, Awaitable[T]],
        *,
        scope: ComponentScope = ComponentScope.CONTAINER,
    ) -> None: ...
    def add_component_implementation(self, implementation: object) -> None: ...


class Container(Protocol):
    async def resolve_callable(
        self, fn: Callable[..., Awaitable[T]]
    ) -> Callable[..., Awaitable[T]]: ...
