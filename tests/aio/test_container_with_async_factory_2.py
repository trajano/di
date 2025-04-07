import pytest
import asyncio
import typing
from logging import Logger

from di.aio import (
    ContainerError,
    AioContainer,
    ContainerLockedError,
    DuplicateRegistrationError,
)
from di.util import (
    extract_satisfied_types_from_type,
    extract_satisfied_types_from_return_of_callable,
)


@typing.runtime_checkable
class Proto(typing.Protocol):
    def meth(self) -> str: ...


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
    def __init__(self, *, protos: set[Proto]):
        self._protos = protos

    async def dep_count(self):
        await asyncio.sleep(0.001)
        return len(self._protos)


async def my_dep_builder() -> MyDep:
    await asyncio.sleep(0.001)
    return MyDep()


def my_other_dep_builder() -> MyDep:
    return MyDep()


async def my_other_async_dep_builder() -> MyDep:
    await asyncio.sleep(0.001)
    return MyDep()


async def my_dep_with_deps_builder(*, my_deps: set[Proto]) -> MyDepWithDeps:
    await asyncio.sleep(0.001)
    return MyDepWithDeps(protos=my_deps)


def bad_builder():
    """Does nothing.  The return type will not be known so using this will raise an error"""
    pass


class MyClass:
    def __init__(self, *, my_dep: MyDep):
        self._my_dep = my_dep

    def foo(self):
        return self._my_dep.meth()


def test_bad_builder_from_util():
    with pytest.raises(TypeError):
        extract_satisfied_types_from_return_of_callable(bad_builder)


async def test_understanding_of_set():
    a = await my_dep_builder()
    b = my_other_dep_builder()
    assert a != b
    assert len({a, b}) == 2


async def test_single_factory():
    my_container = AioContainer()
    my_container.add_component_factory(my_dep_builder)
    my_dep = await my_container.get_component(MyDep)
    assert my_dep.meth() == "foo"
    assert (await my_dep.ablah()) == "ablah"


async def test_two_protos_and_class():
    my_container = AioContainer()
    my_container += MyDep
    my_container += MyDep2
    my_container += MyDepWithDeps
    my_dep = await my_container.get_component(MyDepWithDeps)
    assert await my_dep.dep_count() == 2


async def test_one_proto_one_factory_and_class():
    my_container = AioContainer()
    my_container += my_dep_builder
    my_container += MyDep2
    my_container += MyDepWithDeps
    my_dep = await my_container.get_component(MyDepWithDeps)
    assert await my_dep.dep_count() == 2


async def test_get_multiple_but_only_want_one():
    my_container = AioContainer()
    my_container += my_dep_builder
    my_container += MyDep2
    my_container += MyDepWithDeps
    with pytest.raises(ContainerError):
        await my_container.get_component(Proto)


def test_satisfies():
    p, satisfied_types = extract_satisfied_types_from_return_of_callable(my_dep_builder)
    assert Proto in satisfied_types
    assert p == MyDep

    p, satisfied_types = extract_satisfied_types_from_return_of_callable(
        my_other_async_dep_builder
    )
    assert Proto in satisfied_types
    assert p == MyDep

    p, satisfied_types = extract_satisfied_types_from_return_of_callable(my_dep_builder)
    assert Proto in satisfied_types
    assert p == MyDep

    assert Proto in extract_satisfied_types_from_type(MyDep)
    assert Proto in extract_satisfied_types_from_type(MyDep2)


async def test_get_components2():
    my_container = AioContainer()
    my_container += my_dep_builder
    my_container += my_other_dep_builder
    my_container += my_other_async_dep_builder
    my_container += MyDep
    my_container += MyDep2
    protos = await my_container.get_components(Proto)
    print(protos)
    assert len(protos) == 5


async def test_one_proto_one_sync_factory_one_async_factory_and_class():
    my_container = AioContainer()
    my_container += my_dep_builder
    my_container += my_other_dep_builder
    my_container += MyDep2
    my_container += MyDepWithDeps
    print(await my_container.get_components(Proto))
    assert len(await my_container.get_components(Proto)) == 3
    my_dep = await my_container.get_component(MyDepWithDeps)
    assert await my_dep.dep_count() == 3


async def test_one_proto_one_factory_and_class_factory():
    my_container = AioContainer()
    my_container += my_dep_builder
    my_container += MyDep2
    my_container += my_dep_with_deps_builder
    my_dep = await my_container.get_component(MyDepWithDeps)
    assert await my_dep.dep_count() == 2


async def test_simple_usage():
    my_container = AioContainer()
    my_container.add_component_factory(my_dep_builder)
    my_container.add_component_type(MyClass)
    my_class_impl = await my_container.get_component(MyClass)
    assert my_class_impl.foo() == "foo"


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


async def test_add_implementation():
    my_container = AioContainer()
    my_container.add_component_factory(my_dep_builder)
    my_container += 649
    assert (await my_container.get_component(int)) == 649


async def test_adding_after_get():
    my_container = AioContainer()
    my_container.add_component_type(MyDep)
    assert isinstance(await my_container.get_component(MyDep), Proto)
    assert isinstance(await my_container.get_component(MyDep), MyDep)
    with pytest.raises(ContainerLockedError):
        my_container.add_component_factory(my_dep_builder)
    with pytest.raises(ContainerLockedError):
        my_container.add_component_type(MyDep2)
    with pytest.raises(ContainerLockedError):
        my_container.add_component_implementation(123)


async def test_bad_builder():
    my_container = AioContainer()
    with pytest.raises(TypeError):
        my_container.add_component_factory(bad_builder)


async def test_double_registration():
    my_container = AioContainer()
    my_container += MyDep2

    with pytest.raises(DuplicateRegistrationError):
        my_container.add_component_type(MyDep2)


async def test_double_registration_factory():
    my_container = AioContainer()
    my_container.add_component_factory(my_dep_builder)

    with pytest.raises(ContainerError):
        my_container.add_component_factory(my_dep_builder)


async def test_double_registration_implementation():
    my_container = AioContainer()
    f = MyDep2()
    my_container += f

    with pytest.raises(DuplicateRegistrationError):
        my_container.add_component_implementation(f)
