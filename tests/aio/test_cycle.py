import pytest

from di import ComponentNotFoundError
from di.aio import AioContainer


class A:
    def __init__(self, *, b: "B"):
        self._b = b


class B:
    def __init__(self, *, a: A):
        self._a = a


async def test_cycle_detection():
    """Check to ensure the container errors out when a circular dependency is present.

    The cycle itself cannot be detected because in order to create a cycle you need
    to use forward reference or __future__.annotations.  As such the only viable
    result is ComponentNotFoundError
    """
    container = AioContainer()
    container += A
    container += B

    with pytest.raises(ComponentNotFoundError):
        await container.get_component(A)
