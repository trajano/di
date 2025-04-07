from typing import Awaitable, Coroutine


from di.util import extract_satisfied_types_from_type


def test_extract_satisfied_types_from_type_awaitable():
    assert int in extract_satisfied_types_from_type(Awaitable[int])
    assert int in extract_satisfied_types_from_type(Coroutine[None, None, int])
