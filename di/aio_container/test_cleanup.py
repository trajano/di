from typing import TypeVar

import pytest

from di.aio_container.resolver import resolve_callable_dependencies
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
        from ._convert_to_factory import convert_to_factory
        from ._types import ComponentDefinition
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
