import dataclasses
from typing import Generic, Type, Set, Any, TypeVar


T = TypeVar("T")


@dataclasses.dataclass
class ImplementationDefinition(Generic[T]):
    type: Type[T]
    """The primary type (class) of the implementation."""

    satisfied_types: Set[Type[Any]]
    """A set of types satisfied by the implementation (excluding 'object')."""

    dependencies: Set[Type[Any]]
    """A set of types that are constructor dependencies of the implementation."""

    implementation: T | None
    """The resolved instance of the implementation, if already constructed."""
