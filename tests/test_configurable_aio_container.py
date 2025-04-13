import asyncio
from contextlib import AbstractAsyncContextManager

import pytest

from di_aio.alt import ConfigurableAioContainer
from di_aio.enums import ComponentScope
from di_aio.exceptions import DuplicateRegistrationError


# Component as a type (class)
class A:
    def __init__(self):
        self.name = "A"


# Component as a sync factory
def make_b(*, a: A) -> str:
    return f"B:{a.name}"


# Component as an async factory
async def make_c(*, a: A) -> int:
    await asyncio.sleep(0)
    return len(a.name)


# Async context-managed component
class AsyncCM(AbstractAsyncContextManager):
    async def __aenter__(self):
        return "async_cm"

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # no-op
        pass


def test_configurable_aio_container_definition_registration():
    container = ConfigurableAioContainer()

    container.add_component_type(A)
    container.add_component_factory(make_b)
    container.add_component_factory(make_c)
    container.add_context_managed_type(AsyncCM)

    definitions = container.get_definitions()

    assert len(definitions) == 4

    types = {t for defn in definitions for t in defn.satisfied_types}
    assert A in types
    assert str in types
    assert int in types

    scopes = [defn.scope for defn in definitions]
    assert all(scope == ComponentScope.CONTAINER for scope in scopes)


def test_duplicate_registration_raises():
    container = ConfigurableAioContainer()
    container.add_component_type(A)

    with pytest.raises(DuplicateRegistrationError):
        container.add_component_type(A)
