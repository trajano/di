import pytest

from ._context import AioContext
from ._convert_to_factory import convert_to_factory
from ._util import (
    extract_dependencies_from_signature,
    extract_satisfied_types_from_type,
)
from .decorators import autowired_with_context
from .enums import ComponentScope
from .types import ComponentDefinition


class A:
    def __init__(self) -> None:
        self.value = "A"


class B:
    def __init__(self, *, a: A) -> None:
        self.a = a


@pytest.mark.asyncio
async def test_autowire_injects_dependencies():
    a_def = ComponentDefinition(
        type=A,
        satisfied_types=extract_satisfied_types_from_type(A),
        dependencies=set(),
        collection_dependencies=set(),
        factory=convert_to_factory(A),
        scope=ComponentScope.CONTAINER,
    )

    b_def = ComponentDefinition(
        type=B,
        satisfied_types=extract_satisfied_types_from_type(B),
        dependencies=extract_dependencies_from_signature(B),
        collection_dependencies=set(),
        factory=convert_to_factory(B),
        scope=ComponentScope.CONTAINER,
    )

    container = AioContext(definitions=[a_def, b_def])

    async with container:

        @autowired_with_context(context=container)
        async def handler(x: int, *, b: B):
            return x, b

        result = await handler(42)

        assert isinstance(result, tuple)
        assert result[0] == 42
        assert isinstance(result[1], B)
        assert isinstance(result[1].a, A)
        assert result[1].a.value == "A"
