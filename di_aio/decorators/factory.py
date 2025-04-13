"""Decorator for registering factory classes with a DI container.

This module defines a ``factory`` decorator that registers the decorated
class with a dependency injection container. By default, registration is
done in the ``default_aio_container``.

Usage::

    @factory
    class MyClass: ...

    @factory(container=some_container)
    class AnotherClass: ...
"""

from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar, overload

from di_aio.default_container import default_container
from di_aio.enums import ComponentScope
from di_aio.protocols import ConfigurableContainer

P = ParamSpec("P")
T = TypeVar("T")


@overload
def factory(fn: Callable[..., T]) -> Callable[..., T]: ...  # pragma: no cover
@overload
def factory(
    *,
    container: ConfigurableContainer,
    scope: ComponentScope = ComponentScope.CONTAINER,
) -> Callable[[Callable[P, T]], Callable[..., T]]: ...  # pragma: no cover


def factory(
    fn: Callable[P, T] | None = None,
    *,
    container: ConfigurableContainer = default_container,
    scope: ComponentScope = ComponentScope.CONTAINER,
) -> Callable[..., T] | Callable[[Callable[P, T]], Callable[..., T]]:
    """Class decorator to register a factory with a DI container.

    Can be used with or without parentheses.

    :param fn: The class to register, if used without parentheses.
    :param container: The container to register the factory with.
    :param scope: The component scope for the registered factory.
    :returns: The original class or a decorator function.
    """
    if fn is None:
        return _factory_with_container(container=container, scope=scope)
    return _factory_with_container(container=container, scope=scope)(fn)


def _factory_with_container(
    *,
    container: ConfigurableContainer,
    scope: ComponentScope = ComponentScope.CONTAINER,
) -> Callable[..., Any]:
    """Create a decorator that registers a factory with the given container.

    :param container: The target container for registration.
    :param scope: The scope to use for the registered component.
    :returns: A decorator that registers the factory.
    """

    def wrap(fn: type[T]) -> type[T]:
        container.add_component_factory(fn, scope=scope)
        return fn

    return wrap
