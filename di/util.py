import inspect
import typing
from collections.abc import Awaitable, Callable, Coroutine
from inspect import isclass
from typing import Any


def extract_dependencies_from_signature(fn: Callable[..., Any]) -> set[type]:
    """Extract the types of each kwarg from the callable."""
    return {
        param.annotation
        for param in inspect.signature(fn).parameters.values()
        if param.kind == param.KEYWORD_ONLY
        and param.annotation is not inspect.Parameter.empty
    }


def extract_satisfied_types_from_return_of_callable(
    fn: Callable[..., Any],
) -> tuple[type, set[type]]:
    """Extracts the return type of callable and gets the satisfied types and the primary type."""
    sig = inspect.signature(fn)
    return_annotation = sig.return_annotation

    if return_annotation is inspect.Signature.empty:
        raise TypeError("Return type must be known")

    return return_annotation, extract_satisfied_types_from_type(return_annotation)


def extract_satisfied_types_from_type(component_type: type) -> set[type]:
    """Recursively extract satisfied types from a type.

    - Unwraps Awaitable[T] or Coroutine[..., T]
    - Returns MRO for the actual type being satisfied
    - Always includes the original component_type
    - Excludes `object`
    """
    origin = typing.get_origin(component_type)
    args = typing.get_args(component_type)

    if (
        isclass(origin)
        and (issubclass(origin, Awaitable) or issubclass(origin, Coroutine))
        and args
    ):
        # Recursively unwrap the awaited type
        return extract_satisfied_types_from_type(args[-1])

    return {cls for cls in component_type.mro() if cls is not object}
