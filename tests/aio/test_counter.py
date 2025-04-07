"""
Autowire using factory method
"""

import asyncio

from di.aio import autowired, factory

instance_count = [0]


class AsyncService:
    def __init__(self):
        instance_count[0] = instance_count[0] + 1
        self._instance_id = instance_count[0]

    async def fetch(self):
        await asyncio.sleep(0.1)
        return self._instance_id


@factory(singleton=False)
def make_async_service() -> AsyncService:
    return AsyncService()


@autowired
async def work(*, async_service: AsyncService):
    return await async_service.fetch()


def test_example():
    instance_count[0] = 0
    assert asyncio.run(work()) == 1
    assert asyncio.run(work()) == 2
    assert asyncio.run(work()) == 3
    assert asyncio.run(work()) == 4
