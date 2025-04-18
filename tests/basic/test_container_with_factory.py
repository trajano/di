import typing
from logging import Logger

import pytest

from di import BasicContainer, ContainerError
from di.exceptions import DuplicateRegistrationError


@typing.runtime_checkable
class Proto(typing.Protocol):
    def meth(self) -> str: ...


class MyDep(Proto):
    def meth(self):
        return "foo"


class MyDepWithDeps:
    def __init__(self, *, proto: Proto):
        self._proto = proto

    def blah(self):
        return f"blah-{self._proto.meth()}"


def my_dep_builder() -> MyDep:
    return MyDep()


def my_dep_with_deps_builder(my_dep: Proto) -> MyDepWithDeps:
    return MyDepWithDeps(proto=my_dep)


def bad_builder():
    """Does nothing."""


class MyClass:
    def __init__(self, *, my_dep: MyDep):
        self._my_dep = my_dep

    def foo(self):
        return self._my_dep.meth()


def test_simple_usage():
    my_container = BasicContainer()
    my_container.add_component_factory(my_dep_builder)
    my_container.add_component_factory(my_dep_with_deps_builder)
    my_container.add_component_type(MyClass)
    my_class_impl = my_container.get_component(MyClass)
    assert my_class_impl.foo() == "foo"
    my_dep = my_container.get_component(MyDep)
    assert my_dep.meth() == "foo"
    my_dep_with_deps = my_container.get_component(MyDepWithDeps)
    assert my_dep_with_deps.blah() == "blah-foo"


def test_get_components():
    my_container = BasicContainer()
    my_container.add_component_type(MyDep)
    my_container.add_component_type(MyClass)
    my_classes = my_container.get_components(MyClass)
    assert len(my_classes) == 1


def test_get_optional_component():
    my_container = BasicContainer()
    my_container.add_component_type(MyDep)
    my_container.add_component_type(MyClass)
    assert my_container.get_optional_component(Logger) is None
    my_classes = my_container.get_components(Logger)
    assert len(my_classes) == 0


def test_missing_component():
    my_container = BasicContainer()
    with pytest.raises(ContainerError):
        my_container.get_component(Logger)


def test_contains():
    my_container = BasicContainer()
    my_container += my_dep_builder
    my_container += MyClass
    assert MyClass in my_container


def test_invalid_type():
    my_container = BasicContainer()
    my_container.add_component_factory(my_dep_builder)
    with pytest.raises(TypeError):
        my_container += 649  # pyright: ignore[reportOperatorIssue]


def test_adding_after_get():
    my_container = BasicContainer()
    my_container.add_component_type(MyDep)
    assert isinstance(my_container.get_component(MyDep), Proto)
    assert isinstance(my_container.get_component(MyDep), MyDep)
    with pytest.raises(ContainerError):
        my_container.add_component_factory(my_dep_builder)


def test_bad_builder():
    my_container = BasicContainer()
    with pytest.raises(TypeError):
        my_container.add_component_factory(bad_builder)


def test_double_registration():
    my_container = BasicContainer()
    my_container.add_component_type(MyDep)

    with pytest.raises(DuplicateRegistrationError):
        my_container.add_component_type(MyDep)


def test_double_registration_factory():
    my_container = BasicContainer()
    my_container.add_component_factory(my_dep_builder)

    with pytest.raises(DuplicateRegistrationError):
        my_container.add_component_factory(my_dep_builder)
