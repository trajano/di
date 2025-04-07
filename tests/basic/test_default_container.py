"""
Test for the `@component` decorator and default container registration.

This test ensures that components decorated with `@component` are correctly
registered in the `default_container` and their dependencies are resolved.
"""

import typing

import pytest

from di import component, autowired, default_container


@typing.runtime_checkable
class Proto(typing.Protocol):
    def meth(self) -> str:
        """Protocol method to be implemented by dependencies."""
        raise NotImplementedError()


@component
class FirstDependency(Proto):
    def meth(self) -> str:
        return "foo"


@component
class SecondDependency(Proto):
    def meth(self) -> str:
        return "mydep2"


class ForgottenDependency(Proto):
    def meth(self) -> str:
        return "mydep2"


@component
class MainService:
    def __init__(self, *, my_dep: FirstDependency):
        self._my_dep = my_dep

    def foo(self) -> str:
        """Returns the result from the injected dependency."""
        return self._my_dep.meth()


@autowired
def autowired_sample(in_: str, *, my_service: MainService) -> str:
    return f"{in_} - {my_service.foo()}"


@autowired
def autowired_sample_with_extra_kwargs(
    in_: str, *, extra: str, my_service: MainService
) -> str:
    return f"{in_} - {my_service.foo()} - {extra}"


def test_autowired():
    """Simple autowiring test."""
    assert autowired_sample("abc") == "abc - foo"


def test_autowired_with_extra():
    assert autowired_sample_with_extra_kwargs("abc", extra="aa") == "abc - foo - aa"


def test_autowired_with_forgotten():
    """Checks for the scenario where the dependency was forgotten.

    The definition needs to be done inside as
    if it were done outside the decorator would have raised the TypeError already."""
    with pytest.raises(TypeError):

        @autowired
        def autowired_sample_with_forgotten_dep(
            in_: str,
            *,
            extra: str,
            my_service: MainService,
            forgotten: ForgottenDependency,
        ) -> str:
            return f"{in_} - {my_service.foo()} - {extra} - {forgotten}"

        autowired_sample_with_forgotten_dep("abc", extra="aa")


def test_component_decorator_registers_to_default_container():
    """
    Test that `@component` correctly registers classes in the default container
    and that dependencies are properly injected.
    """
    service = default_container[MainService]
    assert service.foo() == "foo"
    assert isinstance(service, MainService)
    assert isinstance(default_container[FirstDependency], FirstDependency)
    assert isinstance(default_container[SecondDependency], SecondDependency)
