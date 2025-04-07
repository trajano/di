"""Component decorator for automatic container registration.

This module defines a `component` decorator which adds the decorated class to
a DI container. By default, the component is registered in the `default_container`.

Usage:

    @component
    class MyClass: ...

    @component(container=some_container)
    class AnotherClass: ...
"""

from collections.abc import Callable
from typing import TypeVar, overload

from .container import Container
from .default_container import default_container

T = TypeVar("T")


@overload
def component(cls: type[T]) -> type[T]: ...  # pragma: no cover
@overload
def component(
    *, container: Container = default_container
) -> Callable[[type[T]], type[T]]: ...  # pragma: no cover


def component(
    cls: type[T] | None = None, *, container: Container = default_container
) -> type[T] | Callable[[type[T]], type[T]]:
    """Class decorator to register a component into a container.

    Supports usage with or without parentheses.

    :param cls: The class to be registered, only used in no-parentheses form.
    :param container: Optional; a container instance to register the component in.
    :return: Either the original class (if used directly), or a decorator function.
    """

    def wrap(target_cls: type[T]) -> type[T]:
        container.add_component_type(target_cls)
        return target_cls

    if cls is None:
        return wrap
    return wrap(cls)
