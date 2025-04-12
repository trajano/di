from contextlib import asynccontextmanager

import pytest
import pytest_asyncio

from ._transformers import (
    convert_async_context_manager_to_factory,
    convert_async_def_to_factory,
    convert_component_type_to_factory,
    convert_implementation_to_factory,
    convert_sync_context_manager_to_factory,
    convert_sync_def_to_factory,
)


class Sample:
    def __init__(self, *, name: str):
        self.name = name


class SyncContextManager:
    def __init__(self):
        self.state = "initial"

    def __enter__(self):
        self.state = "entered"
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.state = "exited"


@pytest_asyncio.fixture
async def resolved(factory):
    async with factory() as result:
        yield result


@pytest.mark.asyncio
async def test_convert_async_def_to_factory():
    async def async_fn():
        return "async result"

    factory = convert_async_def_to_factory(async_fn)
    async with factory() as result:
        assert result == "async result"


@pytest.mark.asyncio
async def test_convert_sync_def_to_factory():
    def sync_fn():
        return "sync result"

    factory = convert_sync_def_to_factory(sync_fn)
    async with factory() as result:
        assert result == "sync result"


@pytest.mark.asyncio
async def test_convert_sync_def_to_factory_on_thread():
    def sync_fn():
        return "threaded result"

    factory = convert_sync_def_to_factory(sync_fn, on_thread=True)
    async with factory() as result:
        assert result == "threaded result"


@pytest.mark.asyncio
async def test_convert_component_type_to_factory():
    factory = convert_component_type_to_factory(Sample)
    async with factory(name="Alice") as obj:
        assert isinstance(obj, Sample)
        assert obj.name == "Alice"


@pytest.mark.asyncio
async def test_convert_sync_context_manager_to_factory():
    def factory():
        return SyncContextManager()

    async_factory = convert_sync_context_manager_to_factory(factory)
    async with async_factory() as obj:
        assert isinstance(obj, SyncContextManager)
        assert obj.state == "entered"


@pytest.mark.asyncio
async def test_convert_implementation_to_factory():
    instance = Sample(name="impl")
    factory = convert_implementation_to_factory(instance)
    async with factory() as result:
        assert result is instance


@pytest.mark.asyncio
async def test_convert_asynccontextmanager():
    """An asynccontextmanager cannot be detected at runtime without running it.

    Therefore it must be converted explicitly.
    """
    tracking = {
        "before_yield": False,
        "after_yield": False,
    }

    class MyDep:
        def __init__(self):
            self.value = 42

    @asynccontextmanager
    async def get_connection():
        tracking["before_yield"] = True
        yield MyDep()
        tracking["after_yield"] = True

    factory = convert_async_context_manager_to_factory(get_connection)

    async with factory() as result:
        assert result.value == 42
