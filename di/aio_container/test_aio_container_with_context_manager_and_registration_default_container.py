from contextlib import AbstractAsyncContextManager
from typing import Self

import pytest

from di.aio_container import (
    AioContainer,
    ConfigurableAioContainer,
    autowired_with_container,
)

from .component import component
from .default_container import default_container

_tracking = {"started": False, "stopped": False}


class Resource:
    def __init__(self, value):
        self.value = value


@pytest.mark.asyncio
async def test_aio_container():
    configurable_container = ConfigurableAioContainer()

    @component
    class Config:
        def __init__(self):
            self.value = "abc"

    @component
    class Service:
        def __init__(self, *, config: Config):
            self.config = config

        async def start(self):
            _tracking["started"] = True

        async def stop(self):
            _tracking["stopped"] = True

    @component
    class Consumer:
        def __init__(self, *, service: Service):
            self.service = service

        async def start(self):
            await self.service.start()

        async def stop(self):
            await self.service.stop()

    @component
    class ResourceProducer(AbstractAsyncContextManager):
        def __init__(self, *, consumer: Consumer):
            self._consumer = consumer

        async def __aenter__(self) -> Self:
            await self._consumer.start()
            return self

        async def get_resource(self):
            return Resource(self._consumer.service.config.value)

        async def __aexit__(self, exc_type, exc_value, traceback, /):
            await self._consumer.stop()

    async with AioContainer(
        definitions=default_container.get_definitions()
    ) as container:
        assert ResourceProducer in container.get_satisfied_types()
        prods = await container.get_instances(ResourceProducer)
        print(prods)
        assert len(prods) == 1
        prod = await container.get_instance(ResourceProducer)
        optional_prod = await container.get_optional_instance(ResourceProducer)
        assert prod is not None
        assert prod == optional_prod
        assert prod in prods

        @autowired_with_container(container=container)
        async def consume(*, producer: ResourceProducer):
            return await producer.get_resource()

        resource = await consume()
        result = resource.value
        assert result == "abc"
