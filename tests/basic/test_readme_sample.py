import asyncio

import pytest

from di_aio import (
    autowired,
    component,
    get_default_context,
)


@pytest.mark.asyncio
async def test_readme_sample(capsys):
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
        async with get_default_context() as context:
            worker = await context.get_instance(AsyncWorker)
            await worker.work()

    await service()
    captured = capsys.readouterr()
    assert "Result: Fetched async result" in captured.out
