"""Factory decorator for automatic container registration.

This module defines a `factory` decorator which adds a factory function
(synchronous or asynchronous) to a DI container. By default, the factory
is registered in the `default_aio_container`.

Usage:

    @factory
    def make_service():
        return MyService()

    @factory(container=some_container)
    async def make_async_service():
        return await create_service()

The decorator supports use with or without parentheses.
"""

from collections.abc import Callable
from typing import TypeVar, overload

from di.register_to_container import register_factory_to_container

from .container import Container
from .default_aio_container import default_aio_container

T = TypeVar("T")
R = TypeVar("R")


@overload
def factory(fn: Callable[..., R]) -> Callable[..., R]: ...  # pragma: no cover
@overload
def factory(
    *, container: Container = default_aio_container, singleton: bool = True
) -> Callable[[Callable[..., R]], Callable[..., R]]: ...  # pragma: no cover


def factory(
    fn: Callable[..., R] | None = None,
    *,
    container: Container = default_aio_container,
    singleton: bool = True,
) -> Callable[..., R] | Callable[[Callable[..., R]], Callable[..., R]]:
    """Function decorator to register a factory with a container.

    Supports usage with or without parentheses, and both sync/async functions.

    :param fn: The factory function (sync or async) to register.
    :param container: Optional; the container instance to register the factory in.
    :param singleton: Create singleton
    :return: The original function, or a decorator function.
    """
    return register_factory_to_container(fn, container, singleton=singleton)
