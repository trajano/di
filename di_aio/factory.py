"""factory decorator for automatic container registration.

This module defines a `factory` decorator which adds the decorated class to
a DI container. By default, the factory is registered in the `default_aio_container`.

Usage:

    @factory
    class MyClass: ...

    @factory(container=some_container)
    class AnotherClass: ...
"""

from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar, overload

from .configurable_container import ConfigurableContainer
from .default_container import default_container
from .enums import ComponentScope

P = ParamSpec("P")

T = TypeVar("T")


@overload
def factory(fn: Callable[..., T]) -> Callable[..., T]: ...
@overload
def factory(
    *,
    container: ConfigurableContainer,
    scope: ComponentScope = ComponentScope.CONTAINER,
) -> Callable[[Callable[P, T]], Callable[..., T]]: ...


def factory(
    fn: Callable[P, T] | None = None,
    *,
    container: ConfigurableContainer = default_container,
    scope: ComponentScope = ComponentScope.CONTAINER,
) -> Callable[..., T] | Callable[[Callable[P, T]], Callable[..., T]]:
    """Class decorator to register a factory type with a container.

    Supports usage with or without parentheses.

    :param fn: The class to be registered, only used in no-parentheses form.
    :param container: Optional; a container instance to register the factory in.
    :param scope: Optional; a container instance to register the factory in.
    :return: Either the original class (if used directly), or a decorator function.
    """
    if fn is None:
        return factory_with_container(container=container, scope=scope)
    return factory_with_container(container=container, scope=scope)(fn)


def factory_with_container(
    *,
    container: ConfigurableContainer,
    scope: ComponentScope = ComponentScope.CONTAINER,
) -> Callable[..., Any]:
    def wrap(fn: type[T]) -> type[T]:
        container.add_component_factory(fn, scope=scope)
        return fn

    return wrap
