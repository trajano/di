"""
Autowire using factory method
"""

import asyncio

from di.aio import autowired, factory


class AsyncService:
    def __init__(self, data: list[int]):
        self._sum = sum(data)

    async def fetch(self):
        await asyncio.sleep(0.1)
        return self._sum


@factory
def make_async_service(*, data: list[int]) -> AsyncService:
    print(data)
    return AsyncService(data)


@factory
async def answer_to_life_the_universe_and_everything() -> int:
    await asyncio.sleep(0.1)
    return 42


@factory
async def favorite_number() -> int:
    await asyncio.sleep(0.1)
    return 69


@autowired
async def work(*, async_service: AsyncService):
    return await async_service.fetch()


def test_example():
    assert asyncio.run(work()) == (42 + 69)
