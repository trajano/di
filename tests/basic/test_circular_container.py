"""Test for registering a circular dependency."""

import pytest

from di import BasicContainer, CycleDetectedError


class A:
    def __init__(self, *, b: "B"):
        self._b = b


class B:
    def __init__(self, *, a: A):
        self._a = a


def test_cycle_detection():
    """Check to ensure the container errors out when a circular dependency is present."""
    container = BasicContainer()
    container += A
    container += B

    with pytest.raises(CycleDetectedError) as exc_info:
        container.get_component(A)

    assert exc_info.value.component_type in (A, B)
