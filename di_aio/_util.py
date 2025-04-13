"""Utility functions used by both asyncio and basic containers."""

import inspect
import typing
from collections.abc import AsyncGenerator, Awaitable, Callable, Coroutine, Generator
from contextlib import AbstractAsyncContextManager, AbstractContextManager
from inspect import Parameter, isclass
from typing import Any


def extract_dependencies_from_signature(fn: Callable[..., Any]) -> set[type]:
    """Extract the types of each keyword-only argument from a callable's signature.

    :param fn: The function or callable to inspect.
    :return: A set of types representing the annotated keyword-only dependencies.
    """
    return {
        param.annotation
        for param in inspect.signature(fn).parameters.values()
        if param.kind == param.KEYWORD_ONLY
        and param.annotation is not inspect.Parameter.empty
    }


def extract_satisfied_types_from_return_of_callable(
    fn: Callable[..., Any],
) -> tuple[type, set[type]]:
    """Extract the return type of a callable and derive its satisfied types.

    :param fn: The callable to inspect.
    :return: A tuple of (return_type, satisfied_types)
    :raises TypeError: If the return type is not annotated.
    """
    sig = inspect.signature(fn)
    return_annotation = sig.return_annotation

    if return_annotation is inspect.Signature.empty:
        msg = "Return type must be known"
        raise TypeError(msg)

    return unwrap_type(return_annotation), extract_satisfied_types_from_type(
        return_annotation,
    )


def unwrap_type(typ: type) -> type:
    """Recursively unwraps wrapper types to extract the innermost concrete type.

    This function strips away generic asynchronous or context manager wrappers,
    such as:

    - :class:`typing.Awaitable`
    - :class:`typing.Coroutine`
    - :class:`contextlib.AbstractAsyncContextManager`
    - :class:`contextlib.AbstractContextManager`
    - :class:`typing.AsyncGenerator`

    The innermost type is returned, which is useful for introspection or resolving
    base types during dependency injection analysis.

    :param typ: The possibly wrapped type to unwrap.
    :type typ: type
    :return: The innermost unwrapped type.
    :rtype: type

    :example:

    .. code-block:: python

        _unwrap_type(Awaitable[int])                       # returns int
        _unwrap_type(AbstractAsyncContextManager[str])     # returns str
        _unwrap_type(AsyncGenerator[str, None])            # returns str
    """
    origin = typing.get_origin(typ)
    unwrap_targets = {
        Awaitable,
        Coroutine,
        AbstractAsyncContextManager,
        AbstractContextManager,
        Generator,
    }
    args = typing.get_args(typ)

    if isinstance(origin, type) and issubclass(origin, AsyncGenerator):
        return unwrap_type(args[0])
    if isinstance(origin, type) and issubclass(origin, Generator):
        return unwrap_type(args[0])
    if origin in unwrap_targets and args:
        return unwrap_type(args[-1])
    return typ


def extract_satisfied_types_from_type(typ: type) -> set[type]:
    """Extract all types satisfied by a component type.

    - Unwraps Awaitable[T], Coroutine[..., T], AbstractAsyncContextManager[T],
      AbstractContextManager[T].
    - Includes all classes in the MRO (method resolution order) of the unwrapped type.
    - Always includes the original type if class-based.
    - Excludes `object`.

    :param typ: The type annotation to analyze.
    :return: A set of types that the component satisfies.
    """
    unwrapped_type = unwrap_type(typ)
    if isclass(unwrapped_type):
        return {cls for cls in unwrapped_type.mro() if cls is not object}

    return {unwrapped_type}


def maybe_dependency(param: Parameter) -> bool:
    """Check if the parameter may be a dependency.

    A parameter is maybe a dependency if it is keyword only, has an
    annotation and has no default.
    :param param: parameter
    :return:  parameter may be a dependency.
    """
    return (
        param.kind == param.KEYWORD_ONLY
        and param.annotation is not inspect.Parameter.empty
        and param.default is inspect.Parameter.empty
    )
