import asyncio
import typing

import pytest

from .. import ComponentNotFoundError
from .aio_resolver import resolve
from .implementation_definition import ImplementationDefinition


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


class MyClass:
    def __init__(self, *, my_dep: MyDep):
        self._my_dep = my_dep

    def foo(self):
        return self._my_dep.meth()


class MyClassWithList:
    def __init__(self, *, my_deps: list[Proto]):
        self._my_deps = my_deps

    def dep_count(self):
        return len(self._my_deps)


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
    resolved = await resolve(definitions=definitions)
    print(resolved)
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
    resolved = await resolve(definitions=definitions)
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
    resolved = await resolve(definitions=definitions)
    assert isinstance(resolved[Proto][0], MyDep)
    assert resolved[Proto][0].meth() == "foo"
    assert (await resolved[MyDep][0].ablah()) == "ablah"
    assert isinstance(resolved[MyDepWithDeps][0], MyDepWithDeps)
    assert (await resolved[MyDepWithDeps][0].ablah()) == "blah-ablah"


async def test_resolver_with_implementation():
    definitions = [
        ImplementationDefinition(
            type=MyDep,
            satisfied_types={MyDep, Proto},
            implementation=MyDep(),
            dependencies=set(),
            factory=None,
            factory_is_async=False,
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
    resolved = await resolve(definitions=definitions)
    assert isinstance(resolved[Proto][0], MyDep)
    assert resolved[Proto][0].meth() == "foo"
    assert (await resolved[MyDep][0].ablah()) == "ablah"
    assert isinstance(resolved[MyDepWithDeps][0], MyDepWithDeps)
    assert (await resolved[MyDepWithDeps][0].ablah()) == "blah-ablah"


async def test_resolver_with_mandatory_dep():
    definitions = [
        ImplementationDefinition(
            type=MyDepWithDeps,
            satisfied_types={MyDepWithDeps},
            implementation=None,
            dependencies={Proto},
            factory=my_dep_with_deps_builder,
            factory_is_async=True,
        ),
    ]
    with pytest.raises(ComponentNotFoundError):
        await resolve(definitions=definitions)


async def test_resolver_with_class_accepting_list():
    definitions = [
        ImplementationDefinition(
            type=MyDep,
            satisfied_types={MyDep, Proto},
            implementation=None,
            dependencies=set(),
            factory=None,
            factory_is_async=False,
        ),
        ImplementationDefinition(
            type=MyDep2,
            satisfied_types={MyDep2, Proto},
            implementation=None,
            dependencies=set(),
            factory=None,
            factory_is_async=False,
        ),
        ImplementationDefinition(
            type=MyClassWithList,
            satisfied_types={MyClassWithList},
            implementation=None,
            dependencies={list[Proto]},
            factory=None,
            factory_is_async=False,
        ),
    ]
    resolved = await resolve(definitions=definitions)
    assert isinstance(resolved[MyClassWithList][0], MyClassWithList)
    assert resolved[MyClassWithList][0].dep_count() == 2


async def test_resolver_with_class_accepting_list_which_can_be_empty():
    definitions = [
        ImplementationDefinition(
            type=MyClassWithList,
            satisfied_types={MyClassWithList},
            implementation=None,
            dependencies={list[Proto]},
            factory=None,
            factory_is_async=False,
        ),
    ]
    resolved = await resolve(definitions=definitions)
    assert isinstance(resolved[MyClassWithList][0], MyClassWithList)
    assert resolved[MyClassWithList][0].dep_count() == 0
