import typing
from logging import Logger

import pytest

from di import BasicContainer, ContainerError


@typing.runtime_checkable
class Proto(typing.Protocol):
    def meth(self) -> str: ...


class MyDep(Proto):
    def meth(self):
        return "foo"


class MyClass:
    def __init__(self, *, my_dep: MyDep):
        self._my_dep = my_dep

    def foo(self):
        return self._my_dep.meth()


def test_simple_usage():
    my_container = BasicContainer()
    my_container.add_component_type(MyDep)
    my_container.add_component_type(MyClass)
    my_class_impl = my_container.get_component(MyClass)
    assert my_class_impl.foo() == "foo"
    my_dep = my_container.get_component(MyDep)
    assert my_dep.meth() == "foo"
    my_classes = my_container.get_components(MyClass)
    assert my_classes == [my_class_impl]


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


def test_contains():
    my_container = BasicContainer()
    my_container.add_component_type(MyDep)
    my_container.add_component_type(MyClass)
    assert MyClass in my_container


def test_adding_after_get():
    my_container = BasicContainer()
    my_container.add_component_type(MyDep)
    assert isinstance(my_container.get_component(MyDep), Proto)
    assert isinstance(my_container.get_component(MyDep), MyDep)
    with pytest.raises(ContainerError):
        my_container.add_component_type(MyClass)
