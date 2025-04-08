import pytest
from typing import Any

from di.enums import ComponentScope
from ._types import ComponentDefinition, ResolvedComponent
from .resolver import resolve_satisfying_components
from ._convert_to_factory import convert_to_factory


class C:
    pass


class B:
    def __init__(self, *, c: C):
        self.c = c


class A:
    def __init__(self, *, b: B):
        self.b = b


def make_definition(cls, deps: set[type]):
    return ComponentDefinition(
        type=cls,
        satisfied_types={cls},
        dependencies=deps,
        collection_dependencies=set(),
        factory=convert_to_factory(cls),
        scope=ComponentScope.FUNCTION
    )


@pytest.mark.asyncio
async def test_resolve_linear_chain():
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
