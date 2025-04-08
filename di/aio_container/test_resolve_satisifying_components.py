import pytest
from typing import Any

from di.enums import ComponentScope
from ._types import ComponentDefinition, ResolvedComponent
from .resolver import resolve_satisfying_components, resolve_container_scoped_only
from ._convert_to_factory import convert_to_factory


class C:
    pass


class B:
    def __init__(self, *, stuff: C):
        self.c = stuff


class A:
    def __init__(self, *, b: B):
        self.b = b


def make_definition(cls, deps: set[type], scope: ComponentScope = ComponentScope.FUNCTION):
    return ComponentDefinition(
        type=cls,
        satisfied_types={cls},
        dependencies=deps,
        collection_dependencies=set(),
        factory=convert_to_factory(cls),
        scope=scope
    )


@pytest.mark.asyncio
async def test_resolve_linear_chain_with_function_scope_only():
    defs = [
        make_definition(C, deps=set()),
        make_definition(B, deps={C}),
        make_definition(A, deps={B}),
    ]

    result = await resolve_satisfying_components(A, resolved_components=[], definitions=defs)
    assert len(result) == 1
    a = result[0]
    assert isinstance(a, A)
    assert isinstance(a.b, B)
    assert isinstance(a.b.c, C)


@pytest.mark.asyncio
async def test_resolve_with_container_scoped_component():
    defs = [
        make_definition(C, deps=set(), scope=ComponentScope.CONTAINER),
        make_definition(B, deps={C}),
        make_definition(A, deps={B}),
    ]

    resolved = await resolve_container_scoped_only(defs)

    result = await resolve_satisfying_components(A, resolved_components=resolved, definitions=defs)
    assert len(result) == 1
    a = result[0]
    assert isinstance(a, A)
    assert isinstance(a.b, B)
    assert isinstance(a.b.c, C)


@pytest.mark.asyncio
async def test_resolve_empty_inputs():
    result = await resolve_satisfying_components(object, resolved_components=[], definitions=[])
    assert result == []
