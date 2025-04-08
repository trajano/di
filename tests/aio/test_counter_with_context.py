"""
Autowire using factory method
"""

import asyncio
import contextlib

from di.aio import autowired, component, factory

counts = [0, 0, 0]
another_count = [0, 0, 0]


class AnotherService(contextlib.AbstractAsyncContextManager):
    async def __aenter__(self):
        another_count[1] = another_count[1] + 1
        self._enter_id = another_count[1]
        return self

    async def __aexit__(self, exc_type, exc_value, traceback, /):
        another_count[2] = another_count[2] + 1
        self._exit_id = another_count[2]

    def __init__(self):
        another_count[0] = another_count[0] + 1
        self._instance_id = another_count[0]

    async def fetch(self):
        await asyncio.sleep(0.1)
        return self._instance_id, self._enter_id, self._exit_id


class AsyncService(contextlib.AbstractAsyncContextManager):
    async def __aenter__(self):
        counts[1] = counts[1] + 1
        self._enter_id = counts[1]
        return self

    async def __aexit__(self, exc_type, exc_value, traceback, /):
        counts[2] = counts[2] + 1
        self._exit_id = counts[2]

    def __init__(self):
        counts[0] = counts[0] + 1
        self._instance_id = counts[0]

    async def fetch(self):
        await asyncio.sleep(0.1)
        return self._instance_id, self._enter_id, self._exit_id


@factory(singleton=False)
def make_async_service() -> AsyncService:
    return AsyncService()


@factory(singleton=True)
def make_async_service_2() -> AnotherService:
    return AnotherService()


@autowired
async def work(*, async_service: AsyncService, _another: AnotherService):
    return await async_service.fetch()


async def test_example():
    counts[0] = 0
    counts[1] = 0
    counts[2] = 0
    assert (await work()) == (1, 1, 1)
    assert (await work()) == (2, 2, 2)
    assert (await work()) == (3, 3, 3)
    assert (await work()) == (4, 4, 4)
    assert another_count == [1, 1, 1]
