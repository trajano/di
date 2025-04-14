import asyncio
from contextlib import AbstractAsyncContextManager
from typing import Self

import pytest

from di_aio import (
    autowired,
    component,
    DEFAULT_CONFIGURABLE_CONTAINER,
    factory,
)
from di_aio.testing import reset_default_aio_context, reset_default_container

_tracking = {"started": False, "stopped": False}


@pytest.fixture(autouse=True)
def _reset():
    reset_default_aio_context()


reset_default_container()


class Config:
    def __init__(self, value) -> None:
        self.value = value


@factory
def build_config() -> Config:
    return Config("abc")


@component
class Service:
    def __init__(self, *, config: Config) -> None:
        self.config = config

    async def start(self) -> None:
        _tracking["started"] = True

    async def stop(self) -> None:
        _tracking["stopped"] = True


@component
class Consumer:
    def __init__(self, *, service: Service) -> None:
        self.service = service

    async def start(self) -> None:
        await self.service.start()

    async def stop(self) -> None:
        await self.service.stop()


class Resource:
    def __init__(self, value) -> None:
        self.value = value


@component
class ResourceProducer(AbstractAsyncContextManager):
    def __init__(self, *, consumer: Consumer) -> None:
        self._consumer = consumer

    async def __aenter__(self) -> Self:
        await self._consumer.start()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback, /) -> None:
        await self._consumer.stop()

    async def get_resource(self) -> Resource:
        return Resource(self._consumer.service.config.value)


@autowired
async def consume(*, producer: ResourceProducer):
    return await producer.get_resource()


async def server():
    async with DEFAULT_CONFIGURABLE_CONTAINER.context():
        resource = await consume()
        result = resource.value
        assert result == "abc"


def test_container_contains():
    assert len(DEFAULT_CONFIGURABLE_CONTAINER.get_definitions()) == 4

def test_typical_usage_scenario():
    asyncio.run(server())
