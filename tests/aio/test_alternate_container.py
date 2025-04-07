"""Test for using the `@component` decorator with a non-default container.

This validates that component types registered with an alternate container
are properly resolved with dependencies injected.
"""

import typing
from collections.abc import Awaitable, Callable
from typing import TypeVar

from di.aio import AioContainer, autowired, component

T = TypeVar("T")


@typing.runtime_checkable
class Proto(typing.Protocol):
    def meth(self) -> str:
        """Protocol that must be implemented by dependency classes."""
        raise NotImplementedError


# Define a custom container for this test
alternate_container = AioContainer()


@component(container=alternate_container)
class FirstDependency(Proto):
    def meth(self) -> str:
        return "foo"


@component(container=alternate_container)
class SecondDependency(Proto):
    def meth(self) -> str:
        return "mydep2"


@component(container=alternate_container)
class MainService:
    def __init__(self, *, my_dep: FirstDependency):
        self._my_dep = my_dep

    def foo(self) -> str:
        """Returns result from the injected dependency."""
        return self._my_dep.meth()


@autowired(container=alternate_container)
async def autowired_sample(in_: str, *, my_service: MainService) -> str:
    return f"{in_} - {my_service.foo()}"


def aliased_autowired(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
    """An example of a decorator alias"""
    return autowired(container=alternate_container)(func)


@aliased_autowired
async def aliased_autowired_sample(in_: str, *, my_service: MainService) -> str:
    return f"aliased {in_} - {my_service.foo()}"


async def test_autowired():
    assert (await autowired_sample("abc")) == "abc - foo"


async def test_aliased_autowired():
    """Show how to do aliasing of the autowired decorator to preset the container."""
    assert (await aliased_autowired_sample("abc")) == "aliased abc - foo"
