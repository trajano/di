import asyncio
import uuid

import pytest

from di_aio.alt import (
    ComponentScope,
    ConfigurableAioContainer,
    autowired,
    component,
    factory,
)

my_own_container = ConfigurableAioContainer()


@component(container=my_own_container)
class AsyncService:
    async def fetch(self):
        await asyncio.sleep(0.1)
        return "Fetched async result"


class AsyncWorker:
    def __init__(self, name: str) -> None:
        self._name = name

    @autowired(future_context=my_own_container.future_context())
    async def work(self, *, async_service: AsyncService):
        result = await async_service.fetch()
        print(f"name:{self._name}", result)


@factory(container=my_own_container, scope=ComponentScope.FUNCTION)
async def build_worker() -> AsyncWorker:
    return AsyncWorker(str(uuid.uuid4()))


async def service():
    async with my_own_container.context() as context:
        worker1 = await context.get_instance(AsyncWorker)
        await worker1.work()
        worker2 = await context.get_instance(AsyncWorker)
        await worker2.work()
        assert worker1 != worker2


@pytest.mark.asyncio
async def test_run(capsys):
    await service()
    captured = capsys.readouterr()
    assert captured.out.count("Fetched async result") == 2
