"""Component source transformers.

These will take a component source—such as a factory function, class, or
instance—and normalize it into an async factory. Each factory will produce
context-managed component instances.

This abstraction allows the dependency injection container to treat all
component sources uniformly, ensuring that:

- Synchronous functions are wrapped into async factories.
- Plain instances are wrapped in no-op context managers.
- Type-based components generate constructor-based factories.
- All resulting objects are returned via async context management.

This promotes a consistent lifecycle management approach across all component
scenarios, as defined in the container design.

See the high-level design documentation in `__init__.py` for full details.
"""

import asyncio
import types
from collections.abc import Awaitable, Callable
from contextlib import AbstractAsyncContextManager, AbstractContextManager
from types import TracebackType
from typing import TypeVar

from typing_extensions import ParamSpec

from ._types import ContainerAsyncFactory

P = ParamSpec("P")
T = TypeVar("T")


class AsyncContextWrapper(AbstractAsyncContextManager[T]):
    """Wrap a synchronous context manager to make it usable in `async with`.

    This is useful for integrating traditional blocking resources (e.g., file handles,
    database sessions) into an asyncio-compatible system without blocking the event
    loop.

    :param sync_cm: An instance of a synchronous context manager.
    """

    def __init__(self, sync_cm: AbstractContextManager[T]):
        self._sync_cm = sync_cm
        self._entered: T | None = None

    async def __aenter__(self) -> T:
        self._entered = await asyncio.to_thread(self._sync_cm.__enter__)
        return self._entered

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ):
        await asyncio.to_thread(self._sync_cm.__exit__, exc_type, exc_val, exc_tb)


def convert_async_def_to_factory(
    fn: Callable[..., Awaitable[T]],
) -> ContainerAsyncFactory[T, P]:
    """Convert `async def` to factory.

    Converts an `async def` function returning `T` into a container-compliant
    async factory returning a context-managed instance.

    The returned factory wraps the result in a `NoOpAsyncContextManager` to
    ensure that the container always deals with context-managed components.

    :param fn: An async function producing the component.
    :return: A factory returning the result in an async context manager.
    """

    def factory(*args: P.args, **kwargs: P.kwargs) -> AbstractAsyncContextManager:
        class AsyncContext(AbstractAsyncContextManager):
            async def __aenter__(self) -> T:
                return await fn(*args, **kwargs)

            async def __aexit__(
                self,
                exc_type: type[BaseException] | None,
                exc_val: BaseException | None,
                exc_tb: types.TracebackType | None,
            ):
                # no-op
                pass

        return AsyncContext()

    return factory


def convert_sync_def_to_factory(
    fn: Callable[..., T], *, on_thread: bool = False
) -> ContainerAsyncFactory[T, P]:
    """Convert a sync def to factory.

    Converts a synchronous factory function into an async factory wrapped
    in a context manager.

    This wraps the sync function into an `async def` function and then delegates
    to `convert_async_def_to_factory` for consistent behavior.

    If `on_thread` is True, the synchronous function will be executed via
    `asyncio.to_thread` to avoid blocking the event loop.

    :param fn: A `def` function that returns an instance of `T`.
    :param on_thread: Whether to run the function in a thread executor.
    :return: An async factory producing `I` via `async with`.
    """

    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        if on_thread:
            return await asyncio.to_thread(fn, *args, **kwargs)
        return fn(*args, **kwargs)

    return convert_async_def_to_factory(wrapper)


def convert_component_type_to_factory(
    component_type: type[T], *, on_thread: bool = False
) -> ContainerAsyncFactory[T, P]:
    """Convert component type to factory.

    Converts a component type (typically a class) into an async factory that
    constructs the type using dependency-injected keyword arguments.

    The constructor is expected to define keyword-only parameters as
    dependencies.

    If `on_thread` is True, instantiation will occur in a background thread
    using `asyncio.to_thread`.

    :param component_type: The class/type to instantiate.
    :param on_thread: Whether to instantiate the component on a thread.
    :return: An async factory producing instances of the component type.
    """
    if issubclass(component_type, AbstractAsyncContextManager):

        def async_context_manager_factory(
            *args: P.args, **kwargs: P.kwargs
        ) -> AbstractAsyncContextManager[T]:
            return component_type(*args, **kwargs)

        return async_context_manager_factory

    if issubclass(component_type, AbstractContextManager):

        def async_context_manager_factory_with_wrapper(
            *args: P.args, **kwargs: P.kwargs
        ) -> AbstractAsyncContextManager[T]:
            return AsyncContextWrapper(component_type(*args, **kwargs))

        return async_context_manager_factory_with_wrapper

    def sync_factory(*_args: P.args, **kwargs: P.kwargs) -> T:
        return component_type(**kwargs)

    return convert_sync_def_to_factory(sync_factory, on_thread=on_thread)


def convert_sync_context_manager_to_factory(
    sync_cm_fn: Callable[..., AbstractContextManager[T]],
) -> ContainerAsyncFactory[T, P]:
    """Convert sync context manager to factory.

    Converts a function that returns a synchronous context manager into an async
    factory that supports `async with` via a thread-based wrapper.

    This allows synchronous context-managed resources (e.g., file handles,
    DB sessions) to be integrated safely into an async DI container.

    :param sync_cm_fn: A callable that returns a sync context manager.
    :return: An async factory yielding the context-managed instance.
    """
    U = TypeVar("U")

    class AsyncContextWrapper(AbstractAsyncContextManager[U]):
        def __init__(self, sync_cm: AbstractContextManager[U]):
            self._sync_cm = sync_cm

        async def __aenter__(self) -> U:
            self._entered = await asyncio.to_thread(self._sync_cm.__enter__)
            return self._entered

        async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: TracebackType | None,
        ):
            await asyncio.to_thread(self._sync_cm.__exit__, exc_type, exc_val, exc_tb)

    def factory(*args: P.args, **kwargs: P.kwargs) -> AbstractAsyncContextManager[T]:
        sync_cm = sync_cm_fn(*args, **kwargs)
        return AsyncContextWrapper(sync_cm)

    return factory


def convert_implementation_to_factory(implementation: T) -> ContainerAsyncFactory[T, P]:
    """Convert implementation to factory.

    Wraps a provided instance (literal implementation) in a no-op async
    context manager, making it compatible with the container's factory model.

    This wrapping occurs even if the instance is an `AbstractAsyncContextManager`.
    The DI container does not take ownership of external context managers and will
    never call their `__aexit__()` method.

    :param implementation: A literal instance to wrap.
    :return: An async factory that yields the given instance.
    """

    def factory() -> T:
        return implementation

    return convert_sync_def_to_factory(factory)


def convert_async_context_manager_to_factory(
    cm: Callable[..., AbstractAsyncContextManager[T]],
) -> ContainerAsyncFactory[T, P]:
    """Adapt an async context manager function into a ContainerAsyncFactory.

    Since async context managers already conform to the ContainerAsyncFactory interface,
    this is effectively an identity conversion.
    """
    return cm
