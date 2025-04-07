"""
Autowire using factory method
"""

import asyncio

from di.aio import autowired, factory
import contextlib

counts = [0, 0, 0]


class AsyncService(contextlib.AbstractAsyncContextManager):
    async def __aenter__(self):
        counts[1] = counts[1] + 1
        self._enter_id = counts[1]
        return self

    async def __aexit__(self, exc_type, exc_value, traceback, /):
        counts[2] = counts[2] + 1
        self._exit_id = counts[2]
        return self

    def __init__(self):
        counts[0] = counts[0] + 1
        self._instance_id = counts[0]

    async def fetch(self):
        await asyncio.sleep(0.1)
        return self._instance_id, self._enter_id, self._exit_id


@factory(singleton=False)
def make_async_service() -> AsyncService:
    return AsyncService()


@autowired
async def work(*, async_service: AsyncService):
    return await async_service.fetch()


def test_example():
    counts[0] = 0
    counts[1] = 0
    counts[2] = 0
    assert asyncio.run(work()) == (1, 1, 1)
    assert asyncio.run(work()) == (2, 2, 2)
    assert asyncio.run(work()) == (3, 3, 3)
    assert asyncio.run(work()) == (4, 4, 4)
