import asyncio
import uuid
from types import FunctionType

import pytest

from di_aio._convert_to_factory import (
    convert_async_def_to_factory,
    convert_component_type_to_factory,
)
from di_aio.enums import ComponentScope
from di_aio.resolver2.resolver import (
    resolve_scope,
    extract_kwargs_from_type_constructor,
)
from di_aio.resolver2.scope_filters import is_container_scope, is_function_scope
from di_aio.types import ComponentDefinition


class AsyncService:
    async def fetch(self):
        await asyncio.sleep(0.1)
        return "Fetched async result"


class AsyncWorker:
    def __init__(self, name: str) -> None:
        self._name = name

    async def work(self, *, async_service: AsyncService):
        result = await async_service.fetch()
        print(f"name:{self._name}", result)


async def random_uuid() -> str:
    return str(uuid.uuid4())


async def build_worker(*, name: str) -> AsyncWorker:
    return AsyncWorker(name)


@pytest.mark.asyncio
async def test_single():
    resolved = await resolve_scope(
        [
            ComponentDefinition(
                type=AsyncService,
                satisfied_types={AsyncService},
                scope=ComponentScope.CONTAINER,
                collection_dependencies=set(),
                dependencies=set(),
                factory=convert_component_type_to_factory(AsyncService),
            )
        ]
    )
    assert len(resolved) == 1


@pytest.mark.asyncio
async def test_one_func():
    definitions = [
        ComponentDefinition(
            type=AsyncService,
            satisfied_types={AsyncService},
            scope=ComponentScope.CONTAINER,
            collection_dependencies=set(),
            dependencies=set(),
            factory=convert_component_type_to_factory(AsyncService),
        ),
        ComponentDefinition(
            type=str,
            constructor=random_uuid,
            satisfied_types={str},
            scope=ComponentScope.FUNCTION,
            collection_dependencies=set(),
            dependencies=set(),
            factory=convert_async_def_to_factory(random_uuid),
        ),
    ]
    resolved_container = await resolve_scope(
        definitions, scope_filter=is_container_scope
    )
    resolved_function = await resolve_scope(
        definitions, scope_filter=is_function_scope, parent=resolved_container
    )
    assert len(resolved_container) == 1
    assert len(resolved_function) == 2


@pytest.mark.asyncio
async def test_func_with_dep():
    definitions = [
        ComponentDefinition(
            type=AsyncService,
            satisfied_types={AsyncService},
            scope=ComponentScope.CONTAINER,
            collection_dependencies=set(),
            dependencies=set(),
            factory=convert_component_type_to_factory(AsyncService),
        ),
        ComponentDefinition(
            type=str,
            constructor=random_uuid,
            satisfied_types={str},
            scope=ComponentScope.FUNCTION,
            collection_dependencies=set(),
            dependencies=set(),
            factory=convert_async_def_to_factory(random_uuid),
        ),
        ComponentDefinition(
            type=AsyncWorker,
            constructor=build_worker,
            satisfied_types={AsyncWorker},
            scope=ComponentScope.FUNCTION,
            collection_dependencies=set(),
            dependencies={str},
            factory=convert_async_def_to_factory(build_worker),
        ),
    ]
    resolved_container = await resolve_scope(
        definitions, scope_filter=is_container_scope
    )
    resolved_function = await resolve_scope(
        definitions, scope_filter=is_function_scope, parent=resolved_container
    )
    assert len(resolved_container) == 1
    assert len(resolved_function) == 3


@pytest.mark.asyncio
async def test_func_with_dep_def(capsys):
    assert isinstance(build_worker, FunctionType)
    func_def = ComponentDefinition(
        type=AsyncWorker,
        satisfied_types={AsyncWorker},
        scope=ComponentScope.FUNCTION,
        collection_dependencies=set(),
        dependencies={str, AsyncService},
        constructor=build_worker,
        factory=convert_async_def_to_factory(build_worker),
    )
    c = extract_kwargs_from_type_constructor(func_def, {str: "abc"})
    assert c == {"name": "abc"}
    async with func_def.build_context_manager(name="foo") as worker:
        await worker.work(async_service=AsyncService())
    cap = capsys.readouterr()
    assert "Fetched async result" in cap.out


@pytest.mark.asyncio
async def test_convert_to_factory(capsys):
    factory = convert_async_def_to_factory(build_worker)
    async with factory(name="foo") as worker:
        await worker.work(async_service=AsyncService())

    cap = capsys.readouterr()
    assert "Fetched async result" in cap.out
