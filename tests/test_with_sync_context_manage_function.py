import asyncio
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

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


@contextmanager
def some_context_manager() -> Generator[str, Any, Any]:
    yield "a string"


my_own_container.add_sync_context_managed_function(some_context_manager)


async def service():
    async with my_own_container.context() as context:
        resource = await context.get_instance(str)
        assert resource == "a string"
        worker = await context.get_instance(AsyncWorker)
        await worker.work()


def test_with_sync_cm(capsys):
    """This is executed in a sync test to allow triggering of the exit method"""
    asyncio.run(service())
    captured = capsys.readouterr()
    assert "Result: Fetched async result a string" in captured.out
