import pytest
import asyncio
from types import SimpleNamespace
from contextlib import asynccontextmanager

from di.enums import ComponentScope
from ._types import ComponentDefinition
from ._convert_to_factory import convert_to_factory
from di._util import (
    extract_satisfied_types_from_type,
    extract_dependencies_from_signature,
)
from di.aio_container import AioContainer
from .autowired import autowired_with_container


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
        dependencies=extract_dependencies_from_signature(make_request_scoped),
        collection_dependencies=set(),
        factory=convert_to_factory(make_request_scoped),
        scope=ComponentScope.FUNCTION,
    )

    container = AioContainer([request_def, request_scoped_def])

    @autowired_with_container(container=container)
    async def handler(*, arg: str, scoped: RequestScoped):
        return scoped.source, arg

    async with container:
        result = await handler(arg="hello")
        assert result == ("Resolved for Phoenix", "hello")
