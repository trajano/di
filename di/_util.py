"""Utility functions used by both asyncio and basic containers."""

import inspect
import typing
from collections.abc import Awaitable, Callable, Coroutine
from contextlib import AbstractAsyncContextManager, AbstractContextManager
from inspect import isclass
from typing import Any


def extract_dependencies_from_signature(fn: Callable[..., Any]) -> set[type]:
    """
    Extract the types of each keyword-only argument from a callable's signature.

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
    """
    Extract the return type of a callable and derive its satisfied types.

    :param fn: The callable to inspect.
    :return: A tuple of (return_type, satisfied_types)
    :raises TypeError: If the return type is not annotated.
    """
    sig = inspect.signature(fn)
    return_annotation = sig.return_annotation

    if return_annotation is inspect.Signature.empty:
        raise TypeError("Return type must be known")

    return return_annotation, extract_satisfied_types_from_type(return_annotation)


def extract_satisfied_types_from_type(component_type: type) -> set[type]:
    """
    Recursively extract all types satisfied by a component type.

    - Unwraps Awaitable[T], Coroutine[..., T], AbstractAsyncContextManager[T], AbstractContextManager[T].
    - Includes all classes in the MRO (method resolution order) of the unwrapped type.
    - Always includes the original type if class-based.
    - Excludes `object`.

    :param component_type: The type annotation to analyze.
    :return: A set of types that the component satisfies.
    """
    origin = typing.get_origin(component_type)
    args = typing.get_args(component_type)

    unwrap_targets = {
        Awaitable,
        Coroutine,
        AbstractAsyncContextManager,
        AbstractContextManager,
    }

    if origin in unwrap_targets and args:
        return extract_satisfied_types_from_type(args[-1])

    if isclass(component_type):
        return {cls for cls in component_type.mro() if cls is not object}

    return {component_type}
