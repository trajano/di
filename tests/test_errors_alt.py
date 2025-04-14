import asyncio
import inspect
import typing
from typing import Protocol

import pytest

from di_aio._resolver.resolver import _maybe_optional_dependency
from di_aio.alt import (
    ConfigurableAioContainer,
)
from di_aio.exceptions import ComponentNotFoundError


@typing.runtime_checkable
class Worker(Protocol):
    pass


class AsyncService:
    async def fetch(self):
        await asyncio.sleep(0.1)
        return "Fetched async result"


class AsyncWorker(Worker):
    # @autowired(future_context=my_container.future_context())
    async def work(self, *, async_service: AsyncService):
        result = await async_service.fetch()
        print("Result:", result)


class SecondAsyncWorker(Worker):
    # @autowired
    async def work(self, *, async_service: AsyncService):
        result = await async_service.fetch()
        print("Result:", result)


async def bad_func(*, _foo: Worker | None) -> int:
    return 123


@pytest.mark.asyncio
async def test_component_not_found():
    my_container = ConfigurableAioContainer()
    my_container.add_component_type(AsyncService)
    my_container.add_component_type(AsyncWorker)
    my_container.add_component_type(SecondAsyncWorker)
    async with my_container.context() as context:
        with pytest.raises(ComponentNotFoundError):
            await context.get_instance(str)


@pytest.mark.asyncio
async def test_more_than_one_optional():
    my_container = ConfigurableAioContainer()
    my_container.add_component_type(AsyncService)
    my_container.add_component_type(AsyncWorker)
    my_container.add_component_type(SecondAsyncWorker)
    my_container.future_context().reset()
    async with my_container.context() as context:
        with pytest.raises(LookupError):
            await context.get_instance(Worker)


def test_maybe_optional_dependency():
    p = inspect.signature(bad_func).parameters.get("_foo")
    assert isinstance(p, inspect.Parameter)
    assert _maybe_optional_dependency(p)


@pytest.mark.asyncio
async def test_more_than_one_optional_func():
    my_container = ConfigurableAioContainer()
    my_container.add_component_type(AsyncService)
    my_container.add_component_type(AsyncWorker)
    my_container.add_component_type(SecondAsyncWorker)
    my_container.add_component_factory(bad_func)
    with pytest.raises(LookupError):
        async with my_container.context() as context:
            await context.get_instance(int)
