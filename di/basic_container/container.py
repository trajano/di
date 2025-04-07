from typing import (
    ParamSpec,
    TypeVar,
    Type,
    List,
    Self,
    Protocol,
    Callable,
    Union,
)


T = TypeVar("T")
P = ParamSpec("P")


class Container(Protocol):
    def add_component_type(self, component_type: Type[T]) -> Self:
        """
        Adds a component type into the container. This will throw a ContainerError if an attempt
        to add was done after the first get operation.

        :param component_type: A class type to be added as a component.
        :return: self (for chaining)
        """
        raise NotImplementedError()  # pragma: no cover

    def add_component_factory(self, factory: Callable[P, T]) -> Self:
        """
        Adds a component factory into the container. This will throw a ContainerError if an attempt
        to add was done after the first get operation.  The component registered will be the
        return type of the callable.

        :param factory: The factory that would construct the object.  The function can take additional kwargs which represent dependencies in the container
        :return: self (for chaining)
        """
        raise NotImplementedError()  # pragma: no cover

    def __iadd__(self, other: Union[Type[T], Callable[..., T]]) -> Self:
        raise NotImplementedError()  # pragma: no cover

    def get_component(self, component_type: Type[T]) -> T:
        """
        Gets a single component from the container that satisfies the given type.
        This resolves all constructor dependencies for the component.

        Raises:
            ContainerError: If no components or more than one satisfy the type.
        """
        raise NotImplementedError()  # pragma: no cover

    def get_optional_component(self, component_type: Type[T]) -> T | None:
        """
        Gets a single component from the container that satisfies the given type.

        Returns:
            A single component or None if not found.

        Raises:
            ContainerError: If more than one component satisfies the type.
        """
        raise NotImplementedError()  # pragma: no cover

    def get_components(self, component_type: Type[T]) -> List[T]:
        """
        Gets all components from the container that satisfy the given type.

        Returns:
            A list of components that match the given type.
        """
        raise NotImplementedError()  # pragma: no cover

    def __len__(self) -> int:
        """
        Returns the number of registered component types in the container.
        """
        raise NotImplementedError()  # pragma: no cover

    def __getitem__(self, component_type: Type[T]) -> T:
        """
        Alias for get_component(component_type).
        """
        raise NotImplementedError()  # pragma: no cover

    def __contains__(self, component_type: Type[T]) -> bool:
        """
        Check if the type is registered in the container.
        """
        raise NotImplementedError()  # pragma: no cover
