from collections.abc import Awaitable, Callable
from typing import Self

import pytest

from di_aio.exceptions import ContainerError
from di_aio.future_context import FutureContext
from di_aio.protocols import Context


class DummyContext(Context):
    async def resolve_callable(self, fn) -> Callable[..., Awaitable]: ...
    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None: ...
    async def get_instances(self, typ) -> list: ...
    async def get_instance(self, typ): ...
    async def get_optional_instance(self, typ): ...


def test_set_and_get_result():
    ctx = FutureContext()
    dummy = DummyContext()
    ctx.set_result(dummy)
    assert ctx.result() is dummy


def test_set_result_twice_raises():
    ctx = FutureContext()
    dummy1 = DummyContext()
    dummy2 = DummyContext()
    ctx.set_result(dummy1)
    with pytest.raises(ContainerError, match="resolved already"):
        ctx.set_result(dummy2)


def test_get_result_without_set_raises():
    ctx = FutureContext()
    with pytest.raises(ContainerError, match="not yet resolved"):
        ctx.result()


def test_reset_allows_reuse():
    ctx = FutureContext()
    dummy1 = DummyContext()
    ctx.set_result(dummy1)
    ctx.reset()

    dummy2 = DummyContext()
    ctx.set_result(dummy2)
    assert ctx.result() is dummy2
