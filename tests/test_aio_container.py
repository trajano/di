import pytest

from di_aio import AioContainer, ConfigurableAioContainer, autowired_with_container


class Config:
    def __init__(self):
        self.value = "abc"


class Service:
    def __init__(self, *, config: Config):
        self.config = config


class Consumer:
    def __init__(self, *, service: Service):
        self.service = service


@pytest.mark.asyncio
async def test_aio_container():
    configurable_container = ConfigurableAioContainer()
    configurable_container += Config
    configurable_container += Service
    configurable_container += Consumer

    async with AioContainer(
        definitions=configurable_container.get_definitions()
    ) as container:

        @autowired_with_container(container=container)
        async def consume(*, consumer: Consumer):
            return consumer.service.config.value

        result = await consume()
        assert result == "abc"
