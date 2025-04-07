from collections.abc import Awaitable, Callable
from typing import (
    Any,
    List,
    ParamSpec,
    Protocol,
    Self,
    Type,
    TypeVar,
)

T = TypeVar("T")
P = ParamSpec("P")


class Container(Protocol):
    def add_component_type(self, component_type: type) -> None:
        """Adds a component type into the container. This will throw a ContainerError if an attempt
        to add was done after the first get operation.

        :param component_type: A class type to be added as a component.
        """
        raise NotImplementedError  # pragma: no cover

    def add_component_factory(
        self, factory: Callable[P, T] | Callable[P, Awaitable[T]]
    ) -> None:
        """Adds a component factory into the container. This will throw a ContainerError if an attempt
        to add was done after the first get operation.  The component registered will be the
        return type of the callable.

        :param factory: The factory that would construct the object.  The function can take additional kwargs which represent dependencies in the container
        """
        raise NotImplementedError  # pragma: no cover

    def add_component_implementation(self, implementation: Any) -> None:
        """Adds a fully constructed object instance into the container. This is typically used for
        singletons or externally managed instances.

        The type of the implementation, along with all types it satisfies (via MRO), will be
        registered to allow for dependency resolution.

        :param implementation: The preconstructed object instance to add.
        """
        raise NotImplementedError  # pragma: no cover

    def __iadd__(self, other: Any) -> Self:
        return NotImplemented  # pragma: no cover

    async def get_component(self, component_type: Type[T]) -> T:
        """Gets a single component from the container that satisfies the given type.
        This resolves all constructor dependencies for the component.

        Raises:
            ContainerError: If no components or more than one satisfy the type.

        """
        raise NotImplementedError  # pragma: no cover

    async def get_optional_component(self, component_type: Type[T]) -> T | None:
        """Gets a single component from the container that satisfies the given type.

        Returns:
            A single component or None if not found.

        Raises:
            ContainerError: If more than one component satisfies the type.

        """
        raise NotImplementedError  # pragma: no cover

    async def get_components(self, component_type: Type[T]) -> List[T]:
        """Gets all components from the container that satisfy the given type.

        Returns:
            A list of components that match the given type.

        """
        raise NotImplementedError  # pragma: no cover
