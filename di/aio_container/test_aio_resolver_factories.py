import asyncio
import typing

from .implementation_definition import ImplementationDefinition
from .aio_resolver import resolve


@typing.runtime_checkable
class Proto(typing.Protocol):
    def meth(self) -> str: ...
    async def ablah(self) -> str: ...


class MyDep(Proto):
    def meth(self):
        return "foo"

    async def ablah(self):
        await asyncio.sleep(0.001)
        return "ablah"


class MyDep2(Proto):
    def meth(self):
        return "foo2"

    async def ablah(self):
        await asyncio.sleep(0.001)
        return "ablah2"


async def my_dep_builder() -> MyDep:
    await asyncio.sleep(0.001)
    return MyDep()


def my_sync_dep_builder() -> MyDep:
    return MyDep()


async def my_other_async_dep_builder() -> MyDep:
    await asyncio.sleep(0.001)
    return MyDep()


async def test_resolver_get_one():
    definitions = [
        ImplementationDefinition(
            type=MyDep,
            satisfied_types={MyDep, Proto},
            implementation=None,
            dependencies=set(),
            factory=my_dep_builder,
            factory_is_async=True,
        )
    ]
    resolved = await resolve(definitions=definitions)
    assert len(resolved[Proto]) == 1


async def test_resolver_get_sync():
    definitions = [
        ImplementationDefinition(
            type=MyDep,
            satisfied_types={MyDep, Proto},
            implementation=None,
            dependencies=set(),
            factory=my_sync_dep_builder,
            factory_is_async=False,
        )
    ]
    resolved = await resolve(definitions=definitions)
    assert len(resolved[Proto]) == 1


async def test_resolver_get_list():
    definitions = [
        ImplementationDefinition(
            type=MyDep,
            satisfied_types={MyDep, Proto},
            implementation=None,
            dependencies=set(),
            factory=my_dep_builder,
            factory_is_async=True,
        ),
        ImplementationDefinition(
            type=MyDep,
            satisfied_types={MyDep, Proto},
            implementation=None,
            dependencies=set(),
            factory=my_other_async_dep_builder,
            factory_is_async=True,
        ),
        ImplementationDefinition(
            type=MyDep,
            satisfied_types={MyDep, Proto},
            implementation=None,
            dependencies=set(),
            factory=my_sync_dep_builder,
            factory_is_async=False,
        ),
    ]
    resolved = await resolve(definitions=definitions)
    assert len(resolved[Proto]) == 3


async def test_resolver_get_list_with_classes():
    definitions = [
        ImplementationDefinition(
            type=MyDep,
            satisfied_types={MyDep, Proto},
            implementation=None,
            dependencies=set(),
            factory=my_dep_builder,
            factory_is_async=True,
        ),
        ImplementationDefinition(
            type=MyDep,
            satisfied_types={MyDep, Proto},
            implementation=None,
            dependencies=set(),
            factory=my_other_async_dep_builder,
            factory_is_async=True,
        ),
        ImplementationDefinition(
            type=MyDep,
            satisfied_types={MyDep, Proto},
            implementation=None,
            dependencies=set(),
            factory=my_sync_dep_builder,
            factory_is_async=False,
        ),
        ImplementationDefinition(
            type=MyDep,
            satisfied_types={MyDep, Proto},
            implementation=None,
            dependencies=set(),
            factory=my_sync_dep_builder,
            factory_is_async=False,
        ),
    ]
    resolved = await resolve(definitions=definitions)
    assert len(resolved[Proto]) == 3
