import asyncio
import inspect
from contextlib import AbstractContextManager, AbstractAsyncContextManager
from typing import Any, Callable, Awaitable, overload, Type, TypeVar

from ._transformers import (
    convert_async_def_to_factory,
    convert_sync_def_to_factory,
    convert_component_type_to_factory,
    convert_sync_context_manager_to_factory,
    convert_implementation_to_factory,
)
from ._types import ContainerAsyncFactory

T = TypeVar("T")


@overload
def convert_to_factory(
    source: Callable[..., AbstractContextManager[T]],
) -> ContainerAsyncFactory[T]: ...


@overload
def convert_to_factory(
    source: Callable[..., Awaitable[T]],
) -> ContainerAsyncFactory[T]: ...


@overload
def convert_to_factory(source: type[T]) -> ContainerAsyncFactory[T]: ...


@overload
def convert_to_factory(source: T) -> ContainerAsyncFactory[T]: ...


def convert_to_factory(source: Any) -> ContainerAsyncFactory:
    """
    Dispatches to the correct transformer based on the type and structure
    of the input. Accepts functions, types, or literal instances.

    :param source: Any supported component source.
    :return: A normalized async context-managed factory.
    """
    if isinstance(source, type):
        return convert_component_type_to_factory(source)

    if callable(source):

        if asyncio.iscoroutinefunction(source):
            return convert_async_def_to_factory(source)

        try:
            sig = inspect.signature(source)
            if sig.return_annotation is not inspect.Signature.empty and issubclass(
                sig.return_annotation, AbstractContextManager
            ):
                return convert_sync_context_manager_to_factory(source)  # type: ignore
        except (ValueError, TypeError):
            pass  # If we can’t analyze it, fallback to sync def

        return convert_sync_def_to_factory(source)

    return convert_implementation_to_factory(source)
