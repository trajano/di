import pytest

from di_aio.alt import AioContext, ConfigurableAioContainer
from di_aio.testing import autowired_with_context


class Config:
    def __init__(self) -> None:
        self.value = "abc"


class Service:
    def __init__(self, *, config: Config) -> None:
        self.config = config


class Consumer:
    def __init__(self, *, service: Service) -> None:
        self.service = service


@pytest.mark.asyncio
async def test_alt_container():
    """Use an alt container and explicit context to autowire."""
    configurable_container = ConfigurableAioContainer()
    configurable_container += Config
    configurable_container += Service
    configurable_container += Consumer

    async with AioContext(
        definitions=configurable_container.get_definitions(),
    ) as container:

        @autowired_with_context(context=container)
        async def consume(*, consumer: Consumer):
            return consumer.service.config.value

        result = await consume()
        assert result == "abc"
