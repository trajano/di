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


class MyDepWithDeps:
    def __init__(self, *, proto: Proto):
        self._proto = proto

    def blah(self):
        return f"blah-{self._proto.meth()}"

    async def ablah(self):
        await asyncio.sleep(0.001)
        return f"blah-{await self._proto.ablah()}"


async def my_dep_builder() -> MyDep:
    await asyncio.sleep(0.001)
    return MyDep()


async def my_dep_with_deps_builder(my_dep: Proto) -> MyDepWithDeps:
    await asyncio.sleep(0.001)
    return MyDepWithDeps(proto=my_dep)


def bad_builder():
    """Does nothing."""
    pass


class MyClass:
    def __init__(self, *, my_dep: MyDep):
        self._my_dep = my_dep

    def foo(self):
        return self._my_dep.meth()


async def test_resolver():
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
    (resolved, instances) = await resolve(definitions=definitions)
    assert len(resolved) == 2
    assert isinstance(resolved[Proto][0], MyDep)
    assert resolved[Proto][0].meth() == "foo"
    assert (await resolved[MyDep][0].ablah()) == "ablah"


async def test_resolver_with_class():
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
            type=MyClass,
            satisfied_types={MyClass},
            implementation=None,
            dependencies={MyDep},
            factory=None,
            factory_is_async=False,
        ),
    ]
    (resolved, instances) = await resolve(definitions=definitions)
    assert isinstance(resolved[MyClass][0], MyClass)
    assert resolved[MyClass][0].foo() == "foo"


async def test_resolver_with_deps():
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
            type=MyDepWithDeps,
            satisfied_types={MyDepWithDeps},
            implementation=None,
            dependencies={Proto},
            factory=my_dep_with_deps_builder,
            factory_is_async=True,
        ),
    ]
    (resolved, instances) = await resolve(definitions=definitions)
    assert len(resolved) == 3
    assert isinstance(resolved[Proto][0], MyDep)
    assert resolved[Proto][0].meth() == "foo"
    assert (await resolved[MyDep][0].ablah()) == "ablah"
    assert isinstance(resolved[MyDepWithDeps][0], MyDepWithDeps)
    assert (await resolved[MyDepWithDeps][0].ablah()) == "blah-ablah"
