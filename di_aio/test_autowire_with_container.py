from contextlib import asynccontextmanager

import pytest

from ._convert_to_factory import convert_to_factory
from ._types import ComponentDefinition
from ._util import (
    extract_dependencies_from_signature,
    extract_satisfied_types_from_type,
)
from .aio_container import AioContainer
from .autowired import autowired_with_container
from .enums import ComponentScope
from .resolver import resolve_callable_dependencies


class Request:
    def __init__(self, name: str):
        self.name = name


class RequestScoped:
    def __init__(self, *, request: Request):
        self.source = f"Resolved for {request.name}"


@asynccontextmanager
async def make_request_scoped(*, request: Request):
    yield RequestScoped(request=request)


@pytest.mark.asyncio
async def test_autowired_with_asynccontextmanager():
    request_instance = Request("Phoenix")

    request_def = ComponentDefinition(
        type=Request,
        satisfied_types=extract_satisfied_types_from_type(Request),
        dependencies=set(),
        collection_dependencies=set(),
        factory=convert_to_factory(request_instance),
        scope=ComponentScope.CONTAINER,
    )

    request_scoped_def = ComponentDefinition(
        type=RequestScoped,
        satisfied_types=extract_satisfied_types_from_type(RequestScoped),
        dependencies=extract_dependencies_from_signature(RequestScoped),
        collection_dependencies=set(),
        factory=make_request_scoped,
        scope=ComponentScope.FUNCTION,
    )

    container = AioContainer([request_def, request_scoped_def])

    @autowired_with_container(container=container)
    async def handler(*, arg: str, scoped: RequestScoped):
        return scoped.source, arg

    async with container:
        result = await handler(arg="hello")
        assert result == ("Resolved for Phoenix", "hello")


@pytest.mark.asyncio
async def test_autowired_with_container_and_function_scope():
    request_instance = Request("Phoenix")

    request_def = ComponentDefinition(
        type=Request,
        satisfied_types=extract_satisfied_types_from_type(Request),
        dependencies=set(),
        collection_dependencies=set(),
        factory=convert_to_factory(request_instance),
        scope=ComponentScope.CONTAINER,
    )

    request_scoped_def = ComponentDefinition(
        type=RequestScoped,
        satisfied_types=extract_satisfied_types_from_type(RequestScoped),
        dependencies=extract_dependencies_from_signature(RequestScoped),
        collection_dependencies=set(),
        factory=convert_to_factory(RequestScoped),
        scope=ComponentScope.FUNCTION,
    )

    container = AioContainer([request_def, request_scoped_def])

    @autowired_with_container(container=container)
    async def handler(*, arg: str, scoped: RequestScoped):
        return scoped.source, arg

    async with container:
        result = await handler(arg="hello")
        assert result == ("Resolved for Phoenix", "hello")


@pytest.mark.asyncio
async def test_autowired_with_container_and_function_scope_no_decorator():
    request_instance = Request("Phoenix")

    request_def = ComponentDefinition(
        type=Request,
        satisfied_types=extract_satisfied_types_from_type(Request),
        dependencies=set(),
        collection_dependencies=set(),
        factory=convert_to_factory(request_instance),
        scope=ComponentScope.CONTAINER,
    )

    request_scoped_def = ComponentDefinition(
        type=RequestScoped,
        satisfied_types=extract_satisfied_types_from_type(RequestScoped),
        dependencies=extract_dependencies_from_signature(RequestScoped),
        collection_dependencies=set(),
        factory=convert_to_factory(RequestScoped),
        scope=ComponentScope.FUNCTION,
    )

    container = AioContainer([request_def, request_scoped_def])

    async def handler(*, arg: str, scoped: RequestScoped):
        return scoped.source, arg

    async with container:
        handler2 = await resolve_callable_dependencies(
            handler,
            container_scope_components=container._container_scope_components,
            definitions=container._definitions,
        )
        result = await handler2(arg="hello")
        assert result == ("Resolved for Phoenix", "hello")
