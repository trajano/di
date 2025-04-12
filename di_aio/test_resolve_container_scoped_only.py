from typing import Protocol, runtime_checkable

import pytest

from ._convert_to_factory import convert_to_factory
from ._extractors import extract_dependencies_from_callable
from ._types import ComponentDefinition, ResolvedComponent
from ._util import (
    extract_dependencies_from_signature,
    extract_satisfied_types_from_type,
)
from .enums import ComponentScope
from .resolver import resolve_container_scoped_only


class Config:
    def __init__(self):
        self.config_value = "abc123"


class Service:
    def __init__(self, *, xyz: Config):
        self.config = xyz


@runtime_checkable
class Source(Protocol):
    def provide(self) -> str: ...


class NameSource:
    def provide(self) -> str:
        return "Archie"


class NumberSource:
    def provide(self) -> str:
        return "42"


class ServiceWithConfigAndSources:
    def __init__(self, *, config: Config, sources: list[Source]):
        self.config = config
        self.sources = sources

    def get(self) -> str:
        joined_sources = ",".join(source.provide() for source in self.sources)
        return f"{self.config.config_value} {joined_sources}"


@pytest.mark.asyncio
async def test_resolve_container_scoped_only_simple_graph():
    config_factory = convert_to_factory(Config)
    service_factory = convert_to_factory(Service)

    config_def = ComponentDefinition(
        type=Config,
        satisfied_types=extract_satisfied_types_from_type(Config),
        dependencies=extract_dependencies_from_signature(Config.__init__),
        collection_dependencies=set(),
        factory=config_factory,
        scope=ComponentScope.CONTAINER,
    )

    service_def = ComponentDefinition(
        type=Service,
        satisfied_types=extract_satisfied_types_from_type(Service),
        dependencies=extract_dependencies_from_signature(Service.__init__),
        collection_dependencies=set(),
        factory=service_factory,
        scope=ComponentScope.CONTAINER,
    )

    components = await resolve_container_scoped_only([service_def, config_def])

    # Should return two components, in dependency order
    assert len(components) == 2
    assert components[0].instance.__class__ is Config
    assert components[1].instance.__class__ is Service
    assert components[1].instance.config is components[0].instance
    assert all(isinstance(comp, ResolvedComponent) for comp in components)


@pytest.mark.asyncio
async def test_resolve_container_with_multiple_sources():
    config_def = ComponentDefinition(
        type=Config,
        satisfied_types=extract_satisfied_types_from_type(Config),
        dependencies=extract_dependencies_from_signature(Config.__init__),
        collection_dependencies=set(),
        factory=convert_to_factory(Config),
        scope=ComponentScope.CONTAINER,
    )

    name_source_def = ComponentDefinition(
        type=NameSource,
        satisfied_types=extract_satisfied_types_from_type(NameSource),
        dependencies=extract_dependencies_from_signature(NameSource.__init__),
        collection_dependencies=set(),
        factory=convert_to_factory(NameSource),
        scope=ComponentScope.CONTAINER,
    )

    number_source_def = ComponentDefinition(
        type=NumberSource,
        satisfied_types=extract_satisfied_types_from_type(NumberSource),
        dependencies=extract_dependencies_from_signature(NumberSource.__init__),
        collection_dependencies=set(),
        factory=convert_to_factory(NumberSource),
        scope=ComponentScope.CONTAINER,
    )

    deps, collection_deps = extract_dependencies_from_callable(
        ServiceWithConfigAndSources.__init__
    )

    service_with_sources_def = ComponentDefinition(
        type=ServiceWithConfigAndSources,
        satisfied_types=extract_satisfied_types_from_type(ServiceWithConfigAndSources),
        dependencies=deps,
        collection_dependencies=collection_deps,
        factory=convert_to_factory(ServiceWithConfigAndSources),
        scope=ComponentScope.CONTAINER,
    )

    components = await resolve_container_scoped_only(
        [
            config_def,
            name_source_def,
            service_with_sources_def,
            number_source_def,
        ]
    )

    svc = next(
        c.instance
        for c in components
        if isinstance(c.instance, ServiceWithConfigAndSources)
    )
    assert svc.get() == "abc123 Archie,42"
