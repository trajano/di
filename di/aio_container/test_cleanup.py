import contextlib
from typing import TypeVar

import pytest

from di.aio_container.resolver import resolve_callable_dependencies
from ._convert_to_factory import convert_to_factory
from ._types import ComponentDefinition
from di.enums import ComponentScope

T = TypeVar("T")


@pytest.mark.asyncio
async def test_function_scope_cleanup():
    tracker = {"entered": False, "exited": False}

    class TrackedDisposable:
        def __init__(self):
            pass

        async def __aenter__(self):
            tracker["entered"] = True
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            tracker["exited"] = True

    def make_definition_for_type(typ):
        return ComponentDefinition(
            type=typ,
            satisfied_types={typ},
            dependencies=set(),
            collection_dependencies=set(),
            factory=convert_to_factory(typ),
            scope=ComponentScope.FUNCTION,
        )

    defs = [make_definition_for_type(TrackedDisposable)]

    async def run(*, x: TrackedDisposable) -> bool:
        return isinstance(x, TrackedDisposable)

    wrapped = await resolve_callable_dependencies(run, container_scope_components=[], definitions=defs)
    result = await wrapped()
    assert result is True
    assert tracker["entered"] is True
    assert tracker["exited"] is True


@pytest.mark.asyncio
async def test_converted():
    tracker = {"entered": False, "exited": False}

    class TrackedDisposable:
        def __init__(self):
            pass

        async def __aenter__(self):
            tracker["entered"] = True
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            tracker["exited"] = True

    factory = convert_to_factory(TrackedDisposable)
    x = factory()
    assert isinstance(x,contextlib.AbstractAsyncContextManager)
    assert isinstance(x,TrackedDisposable)
    async with x:
        assert tracker["entered"] is True
    assert tracker["exited"] is True


@pytest.mark.asyncio
async def test_not_converted():
    tracker = {"entered": False, "exited": False}

    class TrackedDisposable:
        def __init__(self):
            pass

        async def __aenter__(self):
            tracker["entered"] = True
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            tracker["exited"] = True

    disposable_type = TrackedDisposable
    assert not isinstance(disposable_type, contextlib.AbstractAsyncContextManager)
    assert not isinstance(disposable_type, TrackedDisposable)
    assert isinstance(disposable_type, type)

    async with disposable_type() as result:
        assert isinstance(result, TrackedDisposable)
        assert tracker["entered"] is True
    assert tracker["exited"] is True

@pytest.mark.asyncio
async def test_disposable():
    tracker = {"entered": False, "exited": False}

    class TrackedDisposable:
        def __init__(self):
            pass

        async def __aenter__(self):
            tracker["entered"] = True
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            tracker["exited"] = True

    x = TrackedDisposable()
    assert isinstance(x,contextlib.AbstractAsyncContextManager)
    assert isinstance(x,TrackedDisposable)
    async with x:
        assert tracker["entered"] is True
    assert tracker["exited"] is True

@pytest.mark.asyncio
async def test_dependency_injection_of_tracked_disposable():
    tracker = {"entered": False, "exited": False}

    class TrackedDisposable:
        async def __aenter__(self):
            tracker["entered"] = True
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            tracker["exited"] = True

    # Register it as a function-scoped component
    disposable_def = ComponentDefinition(
        type=TrackedDisposable,
        satisfied_types={TrackedDisposable},
        dependencies=set(),
        collection_dependencies=set(),
        factory=convert_to_factory(TrackedDisposable),
        scope=ComponentScope.FUNCTION,
    )

    async def handler(*, dep: TrackedDisposable) -> str:
        assert isinstance(dep, TrackedDisposable)
        return "ok"

    # Resolve dependencies and execute
    wrapped = await resolve_callable_dependencies(
        handler,
        container_scope_components=[],
        definitions=[disposable_def],
    )
    result = await wrapped()

    assert result == "ok"
    assert tracker["entered"] is True
    assert tracker["exited"] is True
