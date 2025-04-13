import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import pytest

from di_aio.alt import ConfigurableAioContainer, autowired, component

my_own_container = ConfigurableAioContainer()


@component(container=my_own_container)
class AsyncService:
    async def fetch(self):
        await asyncio.sleep(0.1)
        return "Fetched async result"


@component(container=my_own_container)
class AsyncWorker:
    @autowired(future_context=my_own_container.future_context())
    async def work(self, *, async_service: AsyncService, foo: str):
        result = await async_service.fetch()
        print("Result:", result, foo)


@asynccontextmanager
async def some_acm() -> AsyncGenerator[str, Any]:
    yield "a string"


my_own_container.add_context_managed_function(some_acm)


async def service():
    async with my_own_container.context() as context:
        worker = await context.get_instance(AsyncWorker)
        await worker.work()


@pytest.mark.asyncio
async def test_run(capsys):
    await service()
    captured = capsys.readouterr()
    assert "Result: Fetched async result a string" in captured.out
