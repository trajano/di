from collections.abc import Awaitable, Coroutine

import pytest

from di_aio._util import (
    extract_satisfied_types_from_return_of_callable,
    extract_satisfied_types_from_type,
)


def test_extract_satisfied_types_from_type_awaitable():
    assert int in extract_satisfied_types_from_type(Awaitable[int])
    assert int in extract_satisfied_types_from_type(Coroutine[None, None, int])


def test_extract_satisfied_types_from_type():
    assert int in extract_satisfied_types_from_type(int)
    assert str in extract_satisfied_types_from_type(str)


def test_extract_satisfied_types_from_return_of_callable_fail():
    async def no_type_function():
        return 1

    with pytest.raises(TypeError):
        extract_satisfied_types_from_return_of_callable(no_type_function)
