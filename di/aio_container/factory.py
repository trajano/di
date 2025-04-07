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

from .container import Container
from .default_aio_container import default_aio_container

T = TypeVar("T")
R = TypeVar("R")


@overload
def factory(fn: Callable[..., R]) -> Callable[..., R]: ...  # pragma: no cover
@overload
def factory(
    *, container: Container = default_aio_container
) -> Callable[[Callable[..., R]], Callable[..., R]]: ...  # pragma: no cover


def factory(
    fn: Callable[..., R] | None = None, *, container: Container = default_aio_container
) -> Callable[..., R] | Callable[[Callable[..., R]], Callable[..., R]]:
    """Function decorator to register a factory with a container.

    Supports usage with or without parentheses, and both sync/async functions.

    :param fn: The factory function (sync or async) to register.
    :param container: Optional; the container instance to register the factory in.
    :return: The original function, or a decorator function.
    """

    def wrap(target_fn: Callable[..., R]) -> Callable[..., R]:
        container.add_component_factory(target_fn)
        return target_fn

    if fn is None:
        return wrap
    return wrap(fn)
