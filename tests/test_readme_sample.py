import asyncio

import pytest

from di_aio import (
    autowired,
    component,
    default_container,
    reset_default_aio_context_future,
)

reset_default_aio_context_future()


@component
class AsyncService:
    async def fetch(self):
        await asyncio.sleep(0.1)
        return "Fetched async result"


@component
class AsyncWorker:
    @autowired
    async def work(self, *, async_service: AsyncService):
        result = await async_service.fetch()
        print("Result:", result)


async def service():
    async with default_container.context() as context:
        worker = await context.get_instance(AsyncWorker)
        await worker.work()


@pytest.mark.asyncio(loop_scope="function")
async def test_run(capsys):
    reset_default_aio_context_future()
    await service()
    captured = capsys.readouterr()
    assert "Result: Fetched async result" in captured.out
