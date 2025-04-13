import asyncio
from typing import Protocol

import pytest

from di_aio import (
    autowired,
    component,
    default_container,
)
from di_aio.decorators import autowired_with_context
from di_aio.exceptions import ComponentNotFoundError
from di_aio.testing import reset_default_aio_context


@pytest.fixture(autouse=True)
def reset():
    """
    This is needed to allow the default to be reset across tests.
    """
    reset_default_aio_context()


class Worker(Protocol):
    pass


@component
class AsyncService:
    async def fetch(self):
        await asyncio.sleep(0.1)
        return "Fetched async result"


@component
class AsyncWorker(Worker):
    @autowired
    async def work(self, *, async_service: AsyncService):
        result = await async_service.fetch()
        print("Result:", result)


@component
class SecondAsyncWorker(Worker):
    @autowired
    async def work(self, *, async_service: AsyncService):
        result = await async_service.fetch()
        print("Result:", result)


@pytest.mark.asyncio
async def test_component_not_found():
    async with default_container.context() as context:
        with pytest.raises(ComponentNotFoundError):
            await context.get_instance(str)


@pytest.mark.asyncio
async def test_more_than_one_optional():
    async with default_container.context() as context:
        with pytest.raises(LookupError):
            await context.get_instance(Worker)


@pytest.mark.asyncio
async def test_autowire_no_async():
    with pytest.raises(TypeError):

        @autowired  # pyright: ignore[reportArgumentType]
        def not_async():
            # no-op
            pass


@pytest.mark.asyncio
async def test_autowire_with_context_no_async():
    async with default_container.context() as context:
        with pytest.raises(TypeError):

            @autowired_with_context(context=context)  # pyright: ignore[reportArgumentType]
            def not_async():
                # no-op
                pass
