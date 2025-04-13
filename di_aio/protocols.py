import types
from collections.abc import Awaitable, Callable
from typing import Any, ParamSpec, Protocol, TypeVar

from ._types import ComponentDefinition
from .enums import ComponentScope

P = ParamSpec("P")
T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)


class Context(Protocol[T_co]):
    """Async context for resolving DI-managed callable dependencies."""

    async def resolve_callable(
        self, fn: Callable[..., Awaitable[T]]
    ) -> Callable[..., Awaitable[T]]:
        """Inject dependencies into a coroutine-compatible callable."""
        ...  # pragma: no cover

    async def __aenter__(self) -> T_co:
        """Enter the context and return the bound container instance."""
        ...  # pragma: no cover

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> bool | None:
        """Exit the context and clean up managed components."""
        ...  # pragma: no cover

    async def get_instances(self, typ: type[T]) -> list[T]:
        """Return all instances matching the given type."""
        ...  # pragma: no cover

    async def get_instance(self, typ: type[T]) -> T:
        """Return a single instance matching the given type."""
        ...  # pragma: no cover

    async def get_optional_instance(self, typ: type[T]) -> T | None:
        """Return a matching instance or None if not found."""
        ...  # pragma: no cover


class ConfigurableContainer(Protocol):
    """A container that supports registration of component providers."""

    def add_component_type(self, component_type: type) -> None:
        """Register a type to be resolved as a component."""
        ...  # pragma: no cover

    def add_component_factory(
        self,
        factory: Callable[P, T] | Callable[P, Awaitable[T]],
        *,
        scope: ComponentScope = ComponentScope.CONTAINER,
    ) -> None:
        """Register a factory function that produces a component."""
        ...  # pragma: no cover

    def add_component_implementation(self, implementation: object) -> None:
        """Register an existing object as a component."""
        ...  # pragma: no cover

    def get_definitions(self) -> tuple[ComponentDefinition[Any], ...]:
        """Return the collected component definitions."""
        ...  # pragma: no cover

    def context(self) -> Context:
        """Return an async context manager for dependency resolution."""
        ...  # pragma: no cover
