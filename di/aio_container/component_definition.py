import dataclasses
from collections.abc import Callable
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclasses.dataclass
class ComponentDefinition(Generic[T]):
    """Component definition."""

    type: type[T]
    """The primary type (class) of the implementation."""

    satisfied_types: set
    """A set of types satisfied by the implementation (excluding 'object')."""

    dependencies: set
    """A set of types that are constructor dependencies of the implementation."""

    implementation: T | None = None
    """The resolved instance of the implementation, if already constructed."""

    factory: Callable[..., T] | None = None
    """Factory to build the implementation if applicable.

    Must use keyword-only arguments."""

    factory_is_async: bool = False
    """Factory is an async def."""

    factory_builds_singleton: bool = True
    """Factory builds a singleton.

    If true, then the factory only generates once, otherwise it will always be
    called when needed."""
