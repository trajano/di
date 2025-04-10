import asyncio
import functools
import inspect
from collections.abc import Awaitable, Callable
from typing import ParamSpec, TypeVar, overload

from di.aio_container import AioContainer
from di.aio_container.default_aio_container_future import default_aio_container_future

P = ParamSpec("P")
R = TypeVar("R")


@overload
def autowired(
    func: Callable[P, Awaitable[R]],
) -> Callable[..., Awaitable[R]]: ...
@overload
def autowired(
    *,
    future_container: asyncio.Future[AioContainer],
) -> Callable[[Callable[P, Awaitable[R]]], Callable[..., Awaitable[R]]]: ...


def autowired(
    func: Callable[P, Awaitable[R]] | None = None,
    *,
    future_container: asyncio.Future[AioContainer] = default_aio_container_future,
) -> (
    Callable[..., Awaitable[R]]
    | Callable[[Callable[P, Awaitable[R]]], Callable[..., Awaitable[R]]]
):
    """This will autowire to a future container upon invocation."""

    def decorator(fn: Callable[P, Awaitable[R]]) -> Callable[..., Awaitable[R]]:
        if not inspect.iscoroutinefunction(fn):
            raise TypeError("@autowire can only be applied to async def functions")

        @functools.wraps(fn)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            container = await future_container
            resolved_fn = await container.resolve_callable(fn)
            return await resolved_fn(*args, **kwargs)

        return wrapper

    if func:
        return decorator(func)
    return decorator


def autowired_with_container(
    container: AioContainer,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[..., Awaitable[R]]]:
    def decorator(fn: Callable[P, Awaitable[R]]) -> Callable[..., Awaitable[R]]:
        if not inspect.iscoroutinefunction(fn):
            raise TypeError("@autowire can only be applied to async def functions")

        @functools.wraps(fn)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            resolved_fn = await container.resolve_callable(fn)
            return await resolved_fn(*args, **kwargs)

        return wrapper

    return decorator
