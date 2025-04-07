from collections.abc import Callable
from typing import ParamSpec, Protocol, TypeVar

P = ParamSpec("P")
T = TypeVar("T")
R = TypeVar("R")


class ComponentAddable(Protocol):
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

        :param factory: The factory that would construct the object.  The function can
        take additional kwargs which represent dependencies in the container
        :param singleton: factory will generate a singleton
        :return: self (for chaining)
        """
        raise NotImplementedError  # pragma: no cover
