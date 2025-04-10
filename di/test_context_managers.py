from contextlib import (
    asynccontextmanager,
    contextmanager,
    AbstractContextManager,
    AbstractAsyncContextManager,
)
from typing import AsyncGenerator, Any, get_origin, get_args, Generator
import inspect


class Resource:
    pass


@asynccontextmanager
async def get_resource_acm() -> AsyncGenerator[Resource, Any]:
    yield Resource()


@contextmanager
def get_resource_cm() -> Generator[Resource, Any, Any]:
    yield Resource()


def test_inspection_async():
    """Checks what can be retrieved from inspecting a context manager"""
    assert callable(get_resource_acm)
    assert not inspect.iscoroutinefunction(get_resource_acm)
    assert not inspect.isasyncgenfunction(get_resource_acm)

    sig = inspect.signature(get_resource_acm, follow_wrapped=False)
    return_annotation = sig.return_annotation
    ret_origin = get_origin(return_annotation)
    ret_args = get_args(return_annotation)
    assert issubclass(ret_origin, AsyncGenerator)
    assert ret_args[0] == Resource


def test_inspection_sync():
    """Checks what can be retrieved from inspecting a context manager"""
    assert callable(get_resource_cm)
    assert not inspect.iscoroutinefunction(get_resource_cm)
    assert not inspect.isgenerator(get_resource_cm)

    sig = inspect.signature(get_resource_cm, follow_wrapped=False)
    return_annotation = sig.return_annotation
    ret_origin = get_origin(return_annotation)
    ret_args = get_args(return_annotation)
    assert issubclass(ret_origin, Generator)
    assert ret_args[0] == Resource
