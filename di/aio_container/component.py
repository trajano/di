"""Component decorator for automatic container registration.

This module defines a `component` decorator which adds the decorated class to
a DI container. By default, the component is registered in the `default_aio_container`.

Usage:

    @component
    class MyClass: ...

    @component(container=some_container)
    class AnotherClass: ...
"""

from collections.abc import Callable
from typing import TypeVar, overload, Optional, Union

from .default_container import default_container
from ..configurable_container import ConfigurableContainer

T = TypeVar("T")


@overload
def component(cls: type[T]) -> type[T]: ...
@overload
def component(*, container: ConfigurableContainer) -> Callable[[type[T]], type[T]]: ...


def component(
    cls: Optional[type[T]] = None,
    *,
    container: ConfigurableContainer = default_container,
) -> Union[type[T], Callable[[type[T]], type[T]]]:
    """Class decorator to register a component type with a container.

    Supports usage with or without parentheses.

    :param cls: The class to be registered, only used in no-parentheses form.
    :param container: Optional; a container instance to register the component in.
    :return: Either the original class (if used directly), or a decorator function.
    """
    if cls is None:
        return component_with_container(container=container)
    else:
        return component_with_container(container=container)(cls)


def component_with_container(
    *,
    container: ConfigurableContainer,
) -> Union[type[T], Callable[[type[T]], type[T]]]:
    def wrap(target_cls: type[T]) -> type[T]:
        container.add_component_type(target_cls)
        return target_cls

    return wrap
