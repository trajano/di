import asyncio
from collections.abc import Awaitable, Callable
from contextlib import AbstractContextManager
from typing import Any, ParamSpec, TypeVar, overload

from ._transformers import (
    convert_async_def_to_factory,
    convert_component_type_to_factory,
    convert_implementation_to_factory,
    convert_sync_def_to_factory,
)
from ._types import ContainerAsyncFactory

T = TypeVar("T")
P = ParamSpec("P")


@overload
def convert_to_factory(
    source: Callable[..., AbstractContextManager[T]],
) -> ContainerAsyncFactory[T, P]: ... # pragma: no cover


@overload
def convert_to_factory(
    source: Callable[..., Awaitable[T]],
) -> ContainerAsyncFactory[T, P]: ... # pragma: no cover


@overload
def convert_to_factory(source: type[T]) -> ContainerAsyncFactory[T, P]:
    ... # pragma: no cover


@overload
def convert_to_factory(source: T) -> ContainerAsyncFactory[T, P]: ... # pragma: no cover


def convert_to_factory(source: Any) -> ContainerAsyncFactory:
    """Convert any source to factory.

    Dispatch to the correct transformer based on the type and structure
    of the input. Accepts functions, types, or literal instances.

    :param source: Any supported component source.
    :return: A normalized async context-managed factory.
    """
    if isinstance(source, type):
        return convert_component_type_to_factory(source)

    if callable(source):
        if asyncio.iscoroutinefunction(source):
            return convert_async_def_to_factory(source)

        return convert_sync_def_to_factory(source)

    return convert_implementation_to_factory(source)
