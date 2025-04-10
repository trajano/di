import pytest

from di._util import (
    extract_dependencies_from_signature,
    extract_satisfied_types_from_type,
)
from di.enums import ComponentScope

from ._convert_to_factory import convert_to_factory
from ._types import ComponentDefinition
from .aio_container import AioContainer
from .autowired import autowired_with_container


class A:
    def __init__(self):
        self.value = "A"


class B:
    def __init__(self, *, a: A):
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

    container = AioContainer([a_def, b_def])

    async with container:

        @autowired_with_container(container=container)
        async def handler(x: int, *, b: B):
            return x, b

        result = await handler(42)

        assert isinstance(result, tuple)
        assert result[0] == 42
        assert isinstance(result[1], B)
        assert isinstance(result[1].a, A)
        assert result[1].a.value == "A"
