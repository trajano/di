import pytest
from typing import Any
import contextlib
from di.enums import ComponentScope
from ._types import ComponentDefinition, ResolvedComponent
from .resolver import (
    resolve_satisfying_components,
    resolve_container_scoped_only,
    resolve_callable_dependencies,
)
from ._convert_to_factory import convert_to_factory


class C:
    def __init__(self):
        self.label = "injected-c"


class B:
    def __init__(self, *, stuff: C):
        self.c = stuff


class A:
    def __init__(self, *, b: B):
        self.b = b


def make_definition(
    cls, deps: set[type], scope: ComponentScope = ComponentScope.FUNCTION
):
    return ComponentDefinition(
        type=cls,
        satisfied_types={cls},
        dependencies=deps,
        collection_dependencies=set(),
        factory=convert_to_factory(cls),
        scope=scope,
    )


@pytest.mark.asyncio
async def test_resolve_linear_chain_with_function_scope_only():
    defs = [
        make_definition(C, deps=set()),
        make_definition(B, deps={C}),
        make_definition(A, deps={B}),
    ]

    result = await resolve_satisfying_components(
        A, resolved_components=[], definitions=defs
    )
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

    result = await resolve_satisfying_components(
        A, resolved_components=resolved, definitions=defs
    )
    assert len(result) == 1
    a = result[0]
    assert isinstance(a, A)
    assert isinstance(a.b, B)
    assert isinstance(a.b.c, C)


@pytest.mark.asyncio
async def test_resolve_empty_inputs():
    result = await resolve_satisfying_components(
        object, resolved_components=[], definitions=[]
    )
    assert result == []


@pytest.mark.asyncio
async def test_resolve_callable_basic():
    defs = [
        make_definition(C, deps=set()),
        make_definition(B, deps={C}),
    ]

    async def run(*, stuff: C, b: B) -> str:
        assert isinstance(stuff, C)
        assert isinstance(b, B)
        assert isinstance(b.c, C)
        return "success"

    wrapped = await resolve_callable_dependencies(
        run, container_scope_components=[], definitions=defs
    )
    result = await wrapped()
    assert result == "success"


@pytest.mark.asyncio
async def test_resolve_callable_with_user_args():
    defs = [
        make_definition(C, deps=set()),
        make_definition(B, deps={C}),
    ]

    async def run(x: int, *, b: B, y: str = "default") -> str:
        assert isinstance(b, B)
        assert isinstance(b.c, C)
        assert x == 99
        assert y == "extra"
        return f"{x}-{y}-{b.c.label}"

    wrapped = await resolve_callable_dependencies(
        run, container_scope_components=[], definitions=defs
    )
    result = await wrapped(99, y="extra")
    assert result == "99-extra-injected-c"
