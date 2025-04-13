import functools
import inspect
from collections.abc import Awaitable, Callable
from typing import ParamSpec, TypeVar, overload

from di_aio.default_aio_container_future import default_context_holder
from di_aio.exceptions import ContainerError
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
    future_context: set[Context] | None,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[..., Awaitable[R]]]: ...


def autowired(
    func: Callable[P, Awaitable[R]] | None = None,
    *,
    future_context: set[Context] | None = None,
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
            if len(the_context) == 0:
                w_msg = "Invocation attempted before context was present"
                raise ContainerError(w_msg)
            context = next(iter(the_context))
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
