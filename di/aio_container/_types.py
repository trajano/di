from contextlib import AbstractAsyncContextManager
from typing import Protocol, TypeVar

I_co = TypeVar("I_co", covariant=True)
I = TypeVar("I")


class ContainerAsyncFactory(Protocol[I_co]):
    """
    Represents a factory that returns an asynchronous context-managed instance
    of type `I`.

    This factory, when called, returns an `AbstractAsyncContextManager[I]`
    to support `async with` usage.
    """

    def __call__(self, *args, **kwargs) -> AbstractAsyncContextManager[I_co]: ...
