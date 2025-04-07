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

    implementation: T | None
    """The resolved instance of the implementation, if already constructed."""

    factory: Callable[..., T] | None
    """Factory to build the implementation if applicable.

    Must use keyword-only arguments."""
