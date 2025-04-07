import functools
import inspect
from collections.abc import Awaitable, Callable, Coroutine
from typing import (
    Any,
    ParamSpec,
    TypeVar,
    overload,
)

from .container import Container
from .default_aio_container import default_aio_container

P = ParamSpec("P")
R = TypeVar("R")


@overload
def autowired(
    func: Callable[P, Awaitable[R]],
) -> Callable[..., Coroutine[Any, Any, R]]: ...  # pragma: no cover


@overload
def autowired(
    *, container: Container
) -> Callable[
    [Callable[P, Awaitable[R]]], Callable[..., Awaitable[R]]
]: ...  # pragma: no cover


def autowired(
    func: Callable[P, Awaitable[R]] | None = None,
    *,
    container: Container = default_aio_container,
) -> (
    Callable[P, Awaitable[R]]
    | Callable[P, Coroutine[Any, Any, R]]
    | Callable[[Callable[P, Awaitable[R]]], Callable[..., Awaitable[R]]]
):
    """Async-only autowired decorator.

    Injects keyword-only parameters from the container if not provided.
    Raises TypeError if used on a non-async function.
    """

    def wrapper(f: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        if not inspect.iscoroutinefunction(f):
            msg = "The @autowired decorator only supports async functions."
            raise TypeError(msg)

        sig = inspect.signature(f)

        @functools.wraps(f)
        async def inner(*args: P.args, **kwargs: P.kwargs) -> R:
            bound_args = sig.bind_partial(*args, **kwargs)
            bound_args.apply_defaults()

            for name, param in sig.parameters.items():
                if (
                    param.kind == inspect.Parameter.KEYWORD_ONLY
                    and name not in bound_args.arguments
                    and param.annotation != inspect.Parameter.empty
                ):
                    dep = await container.get_optional_component(param.annotation)
                    if dep is not None:
                        bound_args.arguments[name] = dep

            return await f(*bound_args.args, **bound_args.kwargs)

        return inner

    if func is None:
        return wrapper
    return wrapper(func)
