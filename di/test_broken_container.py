"""
Test for using the `@component` decorator with a non-default container.

This validates that component types registered with an alternate container
are properly resolved with dependencies injected.
"""

import typing
from logging import Logger

import pytest

from di import BasicContainer, component, ContainerError


@typing.runtime_checkable
class Proto(typing.Protocol):
    def meth(self) -> str:
        """Protocol that must be implemented by dependency classes."""
        raise NotImplementedError()


# Define a custom container for this test
alternate_container = BasicContainer()


@component(container=alternate_container)
class MainService:
    def __init__(self, *, my_dep: Logger):
        self._my_dep = my_dep

    def foo(self) -> None:
        """Returns result from the injected dependency."""
        return self._my_dep.error("foo")


def test_broken_container():
    """
    Check to ensure the container errors out
    """
    with pytest.raises(ContainerError):
        alternate_container.get_component(MainService)
