"""
Tests for `convert_to_factory` dispatch logic.

These tests validate the correct transformation of different component
sources into async context-managed factories.

Each test uses `async with` to confirm that the returned object is
context-managed and produces the correct instance type.
"""

import asyncio

from ._convert_to_factory import convert_to_factory


class SyncClass:
    def __init__(self, *, value: str):
        self.value = value


class DummyContextManager:
    def __enter__(self):
        return self  # Yield self for isinstance check

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def sync_cm_factory() -> DummyContextManager:
    return DummyContextManager()


async def async_factory_fn(value: str) -> str:
    return f"async-{value}"


def sync_factory_fn(value: str) -> str:
    return f"sync-{value}"


def test_convert_type_factory():
    factory = convert_to_factory(SyncClass)
    instance = None

    async def run():
        nonlocal instance
        async with factory(value="test") as result:
            instance = result

    asyncio.run(run())
    assert isinstance(instance, SyncClass)
    assert instance.value == "test"


def test_convert_sync_factory():
    factory = convert_to_factory(sync_factory_fn)
    value = None

    async def run():
        nonlocal value
        async with factory(value="ok") as result:
            value = result

    asyncio.run(run())
    assert value == "sync-ok"


def test_convert_async_factory():
    factory = convert_to_factory(async_factory_fn)
    value = None

    async def run():
        nonlocal value
        async with factory(value="ok") as result:
            value = result

    asyncio.run(run())
    assert value == "async-ok"


def test_convert_sync_context_manager_factory():
    factory = convert_to_factory(sync_cm_factory)
    result = None

    async def run():
        nonlocal result
        async with factory() as value:
            result = value

    asyncio.run(run())
    assert isinstance(result, DummyContextManager)


def test_convert_instance_literal():
    obj = {"foo": "bar"}
    factory = convert_to_factory(obj)
    resolved = None

    async def run():
        nonlocal resolved
        async with factory() as instance:
            resolved = instance

    asyncio.run(run())
    assert resolved is obj
