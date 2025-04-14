"""Autowired."""

import functools
import inspect
from collections.abc import Awaitable, Callable
from typing import ParamSpec, TypeVar, overload

from di_aio.default_aio_container_future import DEFAULT_CONTEXT_HOLDER
from di_aio.future_context import FutureContext
from di_aio.protocols import Context

P = ParamSpec("P")
R = TypeVar("R")


@overload
def autowired(
    func: Callable[P, Awaitable[R]],
) -> Callable[..., Awaitable[R]]: ...  # pragma: no cover
@overload
def autowired(
    *,
    future_context: FutureContext | None,
) -> Callable[
    [Callable[P, Awaitable[R]]], Callable[..., Awaitable[R]]
]: ...  # pragma: no cover


def autowired(
    func: Callable[P, Awaitable[R]] | None = None,
    *,
    future_context: FutureContext | None = None,
) -> (
    Callable[..., Awaitable[R]]
    | Callable[[Callable[P, Awaitable[R]]], Callable[..., Awaitable[R]]]
):
    """Decorate auto-injecting dependencies from a future container.

    Automatically resolves a callable's dependencies at invocation time using
    the default or provided future context.

    :param func: An async function to decorate (when used without parentheses).
    :param future_context: Optional future context instance to use.
    :returns: A wrapped coroutine with dependencies injected.
    :raises TypeError: If applied to a non-async function.
    """

    def decorator(fn: Callable[P, Awaitable[R]]) -> Callable[..., Awaitable[R]]:
        if not inspect.iscoroutinefunction(fn):
            msg = "@autowire can only be applied to async def functions"
            raise TypeError(msg)

        @functools.wraps(fn)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            the_context = future_context or DEFAULT_CONTEXT_HOLDER
            context = the_context.result()
            resolved_fn = await context.resolve_callable(fn)
            return await resolved_fn(*args, **kwargs)

        return wrapper

    if func:
        return decorator(func)
    return decorator


def autowired_with_context(
    context: Context,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[..., Awaitable[R]]]:
    """Decorate injecting dependencies using a specific container.

    Primarily used in tests to inject dependencies from an explicit container
    instead of a future-resolved default.

    :param context: A container instance for dependency resolution.
    :returns: A wrapped coroutine with injected arguments.
    :raises TypeError: If applied to a non-async function.
    """

    def decorator(fn: Callable[P, Awaitable[R]]) -> Callable[..., Awaitable[R]]:
        if not inspect.iscoroutinefunction(fn):
            msg = "@autowire can only be applied to async def functions"
            raise TypeError(msg)

        @functools.wraps(fn)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            resolved_fn = await context.resolve_callable(fn)
            return await resolved_fn(*args, **kwargs)

        return wrapper

    return decorator
