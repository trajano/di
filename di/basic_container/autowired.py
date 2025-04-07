import functools
import inspect
from collections.abc import Callable
from typing import ParamSpec, TypeVar, overload

from .container import Container
from .default_container import default_container

P = ParamSpec("P")
R = TypeVar("R")


@overload
def autowired(func: Callable[P, R]) -> Callable[..., R]: ...  # pragma: no cover


@overload
def autowired(
    *, container: Container
) -> Callable[[Callable[P, R]], Callable[..., R]]: ...  # pragma: no cover


def autowired(
    func: Callable[P, R] | None = None,
    *,
    container: Container = default_container,
) -> Callable[P, R] | Callable[[Callable[P, R]], Callable[..., R]]:
    """Function decorator for dependency injection.

    Automatically injects keyword-only parameters from the container
    if they are not supplied at call-time.

    Supports usage with or without parentheses:

    Usage::

        @autowired
        def my_func(*, service: MyService): ...

        @autowired(container=my_container)
        def my_func(*, service: MyService): ...

    :param func: The function to decorate (only used in direct decorator form).
    :param container: Optional; a container to resolve dependencies from.
    :return: The decorated function or a decorator.
    """

    def wrapper(f: Callable[P, R]) -> Callable[..., R]:
        sig = inspect.signature(f)

        @functools.wraps(f)
        def inner(*args: P.args, **kwargs: P.kwargs) -> R:
            bound_args = sig.bind_partial(*args, **kwargs)
            bound_args.apply_defaults()

            for name, param in sig.parameters.items():
                if (
                    param.kind == inspect.Parameter.KEYWORD_ONLY
                    and name not in bound_args.arguments
                ) and param.annotation != inspect.Parameter.empty:
                    dep = container.get_optional_component(param.annotation)
                    if dep is not None:
                        bound_args.arguments[name] = dep

            return f(*bound_args.args, **bound_args.kwargs)

        return inner

    if func is None:
        return wrapper
    return wrapper(func)
