"""Test for using the `@component` decorator with a non-default container.

This validates that component types registered with an alternate container
are properly resolved with dependencies injected.
"""

import typing
from collections.abc import Callable
from typing import TypeVar

from di import BasicContainer, autowired, component

T = TypeVar("T")


@typing.runtime_checkable
class Proto(typing.Protocol):
    def meth(self) -> str:
        """Protocol that must be implemented by dependency classes."""
        raise NotImplementedError


# Define a custom container for this test
alternate_container = BasicContainer()


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
def autowired_sample(in_: str, *, my_service: MainService) -> str:
    return f"{in_} - {my_service.foo()}"


def aliased_autowired(func: Callable[..., T]) -> Callable[..., T]:
    """An example of a decorator alias"""
    return autowired(container=alternate_container)(func)


@aliased_autowired
def aliased_autowired_sample(in_: str, *, my_service: MainService) -> str:
    return f"aliased {in_} - {my_service.foo()}"


def test_autowired():
    assert autowired_sample("abc") == "abc - foo"


def test_aliased_autowired():
    """Show how to do aliasing of the autowired decorator to preset the container."""
    assert aliased_autowired_sample("abc") == "aliased abc - foo"


def test_decorator_with_alternate_container():
    """Ensures that classes registered via @component(container=...) are added
    to the correct container and resolved with proper dependency injection.
    """
    impl: MainService = alternate_container[MainService]
    assert impl.foo() == "foo"
    assert isinstance(impl, MainService)
    assert isinstance(alternate_container[FirstDependency], FirstDependency)
    assert isinstance(alternate_container[SecondDependency], SecondDependency)
