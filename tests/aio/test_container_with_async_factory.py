import asyncio
import typing
from logging import Logger

import pytest

from di import ComponentNotFoundError
from di.aio import AioContainer, ContainerError


@typing.runtime_checkable
class Proto(typing.Protocol):
    def meth(self) -> str: ...


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
        return f"blah-{self._proto.meth()}"


async def my_dep_builder() -> MyDep:
    await asyncio.sleep(0.001)
    return MyDep()


async def my_dep_with_deps_builder(*, my_dep: Proto) -> MyDepWithDeps:
    await asyncio.sleep(0.001)
    return MyDepWithDeps(proto=my_dep)


def bad_builder():
    """Does nothing."""


class MyClass:
    def __init__(self, *, my_dep: MyDep):
        self._my_dep = my_dep

    def foo(self):
        return self._my_dep.meth()


async def test_single_factory():
    my_container = AioContainer()
    my_container.add_component_factory(my_dep_builder)
    my_dep = await my_container.get_component(MyDep)
    assert my_dep.meth() == "foo"
    assert (await my_dep.ablah()) == "ablah"


async def test_two_factories():
    my_container = AioContainer()
    my_container.add_component_factory(my_dep_builder)
    my_container.add_component_factory(my_dep_with_deps_builder)
    my_dep = await my_container.get_component(MyDep)
    assert my_dep.meth() == "foo"
    my_dep_with_deps = await my_container.get_component(MyDepWithDeps)
    assert my_dep_with_deps.blah() == "blah-foo"
    assert (await my_dep_with_deps.ablah()) == "blah-foo"


async def test_two_factories_and_class():
    my_container = AioContainer()
    my_container += my_dep_builder
    my_container += my_dep_with_deps_builder
    my_container += MyClass
    my_dep = await my_container.get_component(MyDep)
    assert my_dep.meth() == "foo"
    my_dep_with_deps = await my_container.get_component(MyDepWithDeps)
    assert my_dep_with_deps.blah() == "blah-foo"
    assert (await my_dep_with_deps.ablah()) == "blah-foo"
    my_class_impl = await my_container.get_component(MyClass)
    assert my_class_impl.foo() == "foo"


async def test_simple_usage():
    my_container = AioContainer()
    my_container.add_component_factory(my_dep_builder)
    my_container.add_component_type(MyClass)
    my_class_impl = await my_container.get_component(MyClass)
    assert my_class_impl.foo() == "foo"

    my_class_impl_optional = await my_container.get_optional_component(MyClass)
    assert my_class_impl == my_class_impl_optional


async def test_missing_dependency():
    my_container = AioContainer()
    my_container.add_component_type(MyClass)
    with pytest.raises(ComponentNotFoundError):
        await my_container.get_component(MyClass)


async def test_with_implementation():
    my_container = AioContainer()
    my_container.add_component_implementation(MyDep())
    my_container.add_component_type(MyClass)
    my_class_impl = await my_container.get_component(MyClass)
    assert my_class_impl.foo() == "foo"

    my_class_impl_optional = await my_container.get_optional_component(MyClass)
    assert my_class_impl == my_class_impl_optional


async def test_get_components():
    my_container = AioContainer()
    my_container.add_component_type(MyDep)
    my_container.add_component_type(MyClass)
    my_classes = await my_container.get_components(MyClass)
    assert len(my_classes) == 1


async def test_get_optional_component():
    my_container = AioContainer()
    my_container.add_component_type(MyDep)
    my_container.add_component_type(MyClass)
    assert await my_container.get_optional_component(Logger) is None
    my_classes = await my_container.get_components(Logger)
    assert len(my_classes) == 0


async def test_missing_component():
    my_container = AioContainer()
    with pytest.raises(ContainerError):
        await my_container.get_component(Logger)
