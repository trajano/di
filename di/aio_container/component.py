"""
Component decorator for automatic container registration.

This module defines a `component` decorator which adds the decorated class to
a DI container. By default, the component is registered in the `default_aio_container`.

Usage:

    @component
    class MyClass: ...

    @component(container=some_container)
    class AnotherClass: ...
"""

from typing import Type, TypeVar, Callable, Optional, Union, overload

from .container import Container
from .default_aio_container import default_aio_container

T = TypeVar("T")


@overload
def component(cls: Type[T]) -> Type[T]: ...  # pragma: no cover
@overload
def component(
    *, container: Container = default_aio_container
) -> Callable[[Type[T]], Type[T]]: ...  # pragma: no cover


def component(
    cls: Optional[Type[T]] = None, *, container: Container = default_aio_container
) -> Union[Type[T], Callable[[Type[T]], Type[T]]]:
    """
    Class decorator to register a component type with a dependency injection container.

    Supports usage with or without parentheses.

    :param cls: The class to be registered, only used in no-parentheses form.
    :param container: Optional; a container instance to register the component in.
    :return: Either the original class (if used directly), or a decorator function.
    """

    def wrap(target_cls: Type[T]) -> Type[T]:
        container.add_component_type(target_cls)
        return target_cls

    if cls is None:
        return wrap
    else:
        return wrap(cls)
