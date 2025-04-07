"""
Autowire using factory method
"""

import asyncio

from di.aio import autowired, factory


class AsyncService:
    async def fetch(self):
        await asyncio.sleep(0.1)
        return "Fetched async result"


@factory
def make_async_service() -> AsyncService:
    return AsyncService()


@autowired
async def work(*, async_service: AsyncService):
    result = await async_service.fetch()
    print("Result:", result)


def test_example():
    asyncio.run(work())
