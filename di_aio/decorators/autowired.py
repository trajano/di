import functools
import inspect
from collections.abc import Awaitable, Callable
from typing import ParamSpec, TypeVar, overload

from di_aio.default_aio_container_future import default_context_holder
from di_aio.future_context import FutureContext
from di_aio.protocols import Context

P = ParamSpec("P")
R = TypeVar("R")


@overload
def autowired(
    func: Callable[P, Awaitable[R]],
) -> Callable[..., Awaitable[R]]: ...
@overload
def autowired(
    *,
    future_context: FutureContext | None,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[..., Awaitable[R]]]: ...


def autowired(
    func: Callable[P, Awaitable[R]] | None = None,
    *,
    future_context: FutureContext| None = None,
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
            if future_context is None:
                the_context = default_context_holder
            else:
                the_context = future_context
            context = the_context.result()
            resolved_fn = await context.resolve_callable(fn)
            return await resolved_fn(*args, **kwargs)

        return wrapper

    if func:
        return decorator(func)
    return decorator


def autowired_with_container(
    container: Context,
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
