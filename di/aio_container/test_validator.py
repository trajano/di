from typing import Any

import pytest

from ._types import ComponentDefinition, ContainerAsyncFactory
from di.enums import ComponentScope
from di.exceptions import (
    ContainerInitializationError,
    ComponentNotFoundError,
    CycleDetectedError,
)
from .validator import validate_container_definitions


class DummyAsyncCM:
    def __init__(self, value):
        self._value = value

    async def __aenter__(self):
        return self._value

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


def make_factory(t: type) -> ContainerAsyncFactory:
    def factory(**kwargs):
        return DummyAsyncCM(t())

    return factory


class A:
    pass


class B:
    pass


class C:
    pass


class D:
    pass


class E:
    pass


def make_def(satisfies, deps, scope, factory=None):
    return ComponentDefinition[Any](
        satisfied_types=satisfies,
        dependencies=deps,
        factory=factory or make_factory(next(iter(satisfies))),
        scope=scope,
    )


def test_valid_container_only():
    defs = [
        make_def({A}, set(), ComponentScope.CONTAINER),
        make_def({B}, {A}, ComponentScope.CONTAINER),
    ]
    validate_container_definitions(defs)


def test_valid_function_mixed_scope():
    defs = [
        make_def({A}, set(), ComponentScope.CONTAINER),
        make_def({B}, {A}, ComponentScope.FUNCTION),
        make_def({C}, {A, B}, ComponentScope.FUNCTION),
    ]
    validate_container_definitions(defs)


def test_invalid_scope_violation():
    defs = [
        make_def({A}, set(), ComponentScope.FUNCTION),
        make_def({B}, {A}, ComponentScope.CONTAINER),
    ]
    with pytest.raises(ContainerInitializationError):
        validate_container_definitions(defs)


def test_missing_dependency_error():
    defs = [
        make_def({A}, {B}, ComponentScope.CONTAINER),
    ]
    with pytest.raises(ComponentNotFoundError):
        validate_container_definitions(defs)


def test_list_dependency_allowed():
    defs = [
        make_def({B}, set(), ComponentScope.CONTAINER),  # satisfies B
        make_def({A}, {list[B]}, ComponentScope.CONTAINER),
    ]
    validate_container_definitions(defs)


def test_set_dependency_allowed():
    defs = [
        make_def({B}, set(), ComponentScope.CONTAINER),  # satisfies B
        make_def({A}, {set[B]}, ComponentScope.CONTAINER),
    ]
    validate_container_definitions(defs)


def test_mixed_dependency_some_missing():
    defs = [
        make_def({A}, {list[B], C}, ComponentScope.CONTAINER),
    ]
    with pytest.raises(ComponentNotFoundError):
        validate_container_definitions(defs)


def test_cycle_detected():
    defs = [
        make_def({A}, {B}, ComponentScope.CONTAINER),
        make_def({B}, {A}, ComponentScope.CONTAINER),
    ]
    with pytest.raises(CycleDetectedError):
        validate_container_definitions(defs)
