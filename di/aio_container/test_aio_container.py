import pytest
from di.enums import ComponentScope
from ._types import ComponentDefinition
from ._convert_to_factory import convert_to_factory
from di._util import (
    extract_satisfied_types_from_type,
    extract_dependencies_from_signature,
)
from di.aio_container import AioContainer


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
async def test_container_definitions_and_resolution_methods():
    # --- Definitions ---
    config_def = ComponentDefinition(
        type=Config,
        satisfied_types=extract_satisfied_types_from_type(Config),
        dependencies=set(),
        collection_dependencies=set(),
        factory=convert_to_factory(Config),
        scope=ComponentScope.CONTAINER,
    )

    async def create_service(*, config: Config) -> Service:
        return Service(config=config)

    service_def = ComponentDefinition(
        type=Service,
        satisfied_types=extract_satisfied_types_from_type(Service),
        dependencies=extract_dependencies_from_signature(create_service),
        collection_dependencies=set(),
        factory=convert_to_factory(create_service),
        scope=ComponentScope.CONTAINER,
    )

    consumer_def = ComponentDefinition(
        type=Consumer,
        satisfied_types=extract_satisfied_types_from_type(Consumer),
        dependencies=extract_dependencies_from_signature(Consumer),
        collection_dependencies=set(),
        factory=convert_to_factory(Consumer),
        scope=ComponentScope.CONTAINER,
    )

    # --- Container Setup ---
    container = AioContainer([config_def, service_def, consumer_def])

    async with container:
        # --- get_definition ---
        assert container.get_definition(Config) == config_def
        assert container.get_definition(Service) == service_def
        assert container.get_definition(Consumer) == consumer_def

        # --- get_instance ---
        config = container.get_instance(Config)
        service = container.get_instance(Service)
        consumer = container.get_instance(Consumer)

        assert isinstance(config, Config)
        assert isinstance(service, Service)
        assert isinstance(consumer, Consumer)
        assert service.config is config
        assert consumer.service is service

        # --- satisfied_types ---
        all_types = container.satisfied_types()
        assert Config in all_types
        assert Service in all_types
        assert Consumer in all_types
