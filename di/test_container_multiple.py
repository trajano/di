import typing
from logging import Logger

from di import BasicContainer


@typing.runtime_checkable
class Proto(typing.Protocol):
    def meth(self) -> str: ...


class FirstDependency(Proto):
    def meth(self):
        return "foo"


class SecondDependency(Proto):
    def meth(self):
        return "mydep2"


class MainService:
    def __init__(self, *, my_dep: FirstDependency):
        self._my_dep = my_dep

    def foo(self):
        return self._my_dep.meth()


def test_container_resolution():
    container = BasicContainer()
    container += FirstDependency
    container += SecondDependency
    container += MainService

    resolved_service = container.get_component(MainService)
    assert resolved_service.foo() == "foo"
    assert resolved_service == container.get_optional_component(MainService)
    assert container.get_optional_component(Logger) is None

    resolved_first_dep = container[FirstDependency]
    assert resolved_first_dep.meth() == "foo"

    all_services = container.get_components(MainService)
    assert all_services == [resolved_service]

    all_protos = container.get_components(Proto)
    assert len(all_protos) == 2
    assert resolved_first_dep in all_protos
    assert all_protos[0].meth()
    assert all_protos[1].meth()
    assert len(container) == 3
    assert SecondDependency in container
