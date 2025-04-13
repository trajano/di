import asyncio
import functools
import inspect
from collections.abc import Awaitable, Callable
from typing import ParamSpec, TypeVar, overload

from .aio_container import AioContext
from .default_aio_container_future import default_aio_context_future

P = ParamSpec("P")
R = TypeVar("R")


@overload
def autowired(
    func: Callable[P, Awaitable[R]],
) -> Callable[..., Awaitable[R]]: ...
@overload
def autowired(
    *,
    future_context: asyncio.Future[AioContext],
) -> Callable[[Callable[P, Awaitable[R]]], Callable[..., Awaitable[R]]]: ...


def autowired(
    func: Callable[P, Awaitable[R]] | None = None,
    *,
    future_context: asyncio.Future[AioContext] = default_aio_context_future,
) -> (
    Callable[..., Awaitable[R]]
    | Callable[[Callable[P, Awaitable[R]]], Callable[..., Awaitable[R]]]
):
    """This will autowire to a future container upon invocation."""

    def decorator(fn: Callable[P, Awaitable[R]]) -> Callable[..., Awaitable[R]]:
        if not inspect.iscoroutinefunction(fn):
            msg = "@autowire can only be applied to async def functions"
            raise TypeError(msg)

        @functools.wraps(fn)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            container = await future_context
            resolved_fn = await container.resolve_callable(fn)
            return await resolved_fn(*args, **kwargs)

        return wrapper

    if func:
        return decorator(func)
    return decorator


def autowired_with_container(
    container: AioContext,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[..., Awaitable[R]]]:
    def decorator(fn: Callable[P, Awaitable[R]]) -> Callable[..., Awaitable[R]]:
        if not inspect.iscoroutinefunction(fn):
            msg = "@autowire can only be applied to async def functions"
            raise TypeError(msg)

        @functools.wraps(fn)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            resolved_fn = await container.resolve_callable(fn)
            return await resolved_fn(*args, **kwargs)

        return wrapper

    return decorator
