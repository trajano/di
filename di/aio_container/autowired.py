import functools
import inspect
from collections.abc import Awaitable, Callable
from typing import ParamSpec, TypeVar

from di.aio_container import AioContainer

P = ParamSpec("P")
R = TypeVar("R")


def autowire_with_container(
    container: AioContainer,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    def decorator(fn: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        if not inspect.iscoroutinefunction(fn):
            raise TypeError("@autowire can only be applied to async def functions")

        @functools.wraps(fn)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            resolved_fn = await container.resolve_callable(fn)
            return await resolved_fn(*args, **kwargs)

        return wrapper

    return decorator
