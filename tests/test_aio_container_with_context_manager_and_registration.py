from contextlib import AbstractAsyncContextManager
from typing import Self

import pytest

from di_aio.alt import AioContext, ConfigurableAioContainer, component
from di_aio.testing import autowired_with_container

_tracking = {"started": False, "stopped": False}


class Resource:
    def __init__(self, value) -> None:
        self.value = value


@pytest.mark.asyncio
async def test_aio_container():
    configurable_container = ConfigurableAioContainer()

    @component(container=configurable_container)
    class Config:
        def __init__(self) -> None:
            self.value = "abc"

    @component(container=configurable_container)
    class Service:
        def __init__(self, *, config: Config) -> None:
            self.config = config

        async def start(self):
            _tracking["started"] = True

        async def stop(self):
            _tracking["stopped"] = True

    @component(container=configurable_container)
    class Consumer:
        def __init__(self, *, service: Service) -> None:
            self.service = service

        async def start(self):
            await self.service.start()

        async def stop(self):
            await self.service.stop()

    @component(container=configurable_container)
    class ResourceProducer(AbstractAsyncContextManager):
        def __init__(self, *, consumer: Consumer) -> None:
            self._consumer = consumer

        async def __aenter__(self) -> Self:
            await self._consumer.start()
            return self

        async def get_resource(self):
            return Resource(self._consumer.service.config.value)

        async def __aexit__(self, exc_type, exc_value, traceback, /)->None:
            await self._consumer.stop()

    async with AioContext(
        definitions=configurable_container.get_definitions(),
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
