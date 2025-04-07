import asyncio

from di.aio import autowired, component


@component
class AsyncService:
    async def fetch(self):
        await asyncio.sleep(0.1)
        return "Fetched async result"


class AsyncWorker:
    @autowired
    async def work(self, *, async_service: AsyncService):
        result = await async_service.fetch()
        print("Result:", result)


def test_example():
    worker = AsyncWorker()
    asyncio.run(worker.work())
