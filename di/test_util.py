# test_util.py

import pytest
from contextlib import AbstractAsyncContextManager, AbstractContextManager
from typing import Awaitable, Coroutine, Any, Protocol

from ._util import extract_satisfied_types_from_type


class Resource:
    pass


class CustomAsyncContext(AbstractAsyncContextManager):
    async def __aenter__(self) -> Resource:
        return Resource()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # no-op
        pass


class CustomSyncContext(AbstractContextManager):
    def __enter__(self) -> Resource:
        return Resource()

    def __exit__(self, exc_type, exc_val, exc_tb):
        # no-op
        pass


class Parent:
    pass


class Child(Parent):
    pass


class ProtoA(Protocol):
    def a(self) -> str: ...


class ProtoB(Protocol):
    def b(self) -> int: ...


class Impl(ProtoA, ProtoB):
    def a(self) -> str:
        return "a"

    def b(self) -> int:
        return 42


def test_extract_from_direct_class_type():
    assert Resource in extract_satisfied_types_from_type(Resource)


def test_extract_from_awaitable():
    assert Resource in extract_satisfied_types_from_type(Awaitable[Resource])


def test_extract_from_coroutine():
    assert Resource in extract_satisfied_types_from_type(Coroutine[Any, Any, Resource])


def test_extract_from_custom_async_context_class():
    assert CustomAsyncContext in extract_satisfied_types_from_type(CustomAsyncContext)


def test_extract_from_custom_sync_context_class():
    assert CustomSyncContext in extract_satisfied_types_from_type(CustomSyncContext)


def test_extract_inheritance():
    satisfied = extract_satisfied_types_from_type(Child)
    assert Child in satisfied
    assert Parent in satisfied


def test_extract_multiple_protocols():
    satisfied = extract_satisfied_types_from_type(Impl)
    assert Impl in satisfied
    assert ProtoA in satisfied
    assert ProtoB in satisfied
