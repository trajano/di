from collections.abc import Callable
from typing import (
    ParamSpec,
    Self,
    TypeVar,
)

from di.protocols import ComponentAddable

T = TypeVar("T")
P = ParamSpec("P")


class Container(ComponentAddable):
    """Dependency injection container."""

    def add_component_type(self, component_type: type[T]) -> None:
        """Add a component type into the container.

        This will throw a ContainerError if an attempt to add was done after the first
        get operation.

        :param component_type: A class type to be added as a component.
        :return: self (for chaining)
        """
        raise NotImplementedError  # pragma: no cover

    def add_component_factory(
        self, factory: Callable[P, T], *, singleton: bool = True
    ) -> None:
        """Add a component factory into the container.

        This will throw a ContainerError if an attempt to add was done after the first
        get operation.  The component registered will be the return type of the
        callable.

        :param *:
        :param factory: The factory that would construct the object.  The function can
        take additional kwargs which represent dependencies in the container
        :param singleton: Create singleton
        :return: self (for chaining)
        """
        raise NotImplementedError  # pragma: no cover

    def __iadd__(self, other: type[T] | Callable[..., T]) -> Self:
        """Add factory or component types to the container."""
        return NotImplemented  # pragma: no cover

    def get_component(self, component_type: type[T]) -> T:
        """Get a single component from the container that satisfies the given type.

        Raises:
            ContainerError: If no components or more than one satisfy the type.

        """
        raise NotImplementedError  # pragma: no cover

    def get_optional_component(self, component_type: type[T]) -> T | None:
        """Get a single component from the container that satisfies the given type.

        Returns:
            A single component or None if not found.

        Raises:
            ContainerError: If more than one component satisfies the type.

        """
        raise NotImplementedError  # pragma: no cover

    def get_components(self, component_type: type[T]) -> list[T]:
        """Get all components from the container that satisfy the given type.

        Returns:
            A list of components that match the given type.

        """
        raise NotImplementedError  # pragma: no cover

    def __len__(self) -> int:
        """Return the number of registered component types in the container."""
        raise NotImplementedError  # pragma: no cover

    def __getitem__(self, component_type: type[T]) -> T:
        """Alias for get_component(component_type)."""
        raise NotImplementedError  # pragma: no cover

    def __contains__(self, component_type: type[T]) -> bool:
        """Check if the type is registered in the container."""
        raise NotImplementedError  # pragma: no cover
