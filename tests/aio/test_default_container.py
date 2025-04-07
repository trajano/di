"""
Test for the `@component` decorator and default container registration.

This test ensures that components decorated with `@component` are correctly
registered in the `default_aio_container` and their dependencies are resolved.
"""

import asyncio
import typing

import pytest

from di.aio import component, autowired, default_aio_container


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


@component(container=default_aio_container)
class MainService:
    def __init__(self, *, my_dep: FirstDependency):
        self._my_dep = my_dep

    async def foo(self) -> str:
        """Returns the result from the injected dependency."""
        await asyncio.sleep(0.001)
        return self._my_dep.meth()


@autowired
async def autowired_sample(in_: str, *, my_service: MainService) -> str:
    return f"{in_} - {await my_service.foo()}"


@autowired(container=default_aio_container)
async def autowired_sample_with_extra_kwargs(
    in_: str, *, extra: str, my_service: MainService
) -> str:
    return f"{in_} - {await my_service.foo()} - {extra}"


async def test_autowired():
    assert (await autowired_sample("abc")) == "abc - foo"


async def test_autowired_with_extra():
    assert (
        await autowired_sample_with_extra_kwargs("abc", extra="aa")
    ) == "abc - foo - aa"


async def test_autowired_with_forgotten():
    """Checks for the scenario where the dependency was forgotten.

    The definition needs to be done inside as
    if it were done outside the decorator would have raised the TypeError already."""
    with pytest.raises(TypeError):

        @autowired
        async def autowired_sample_with_forgotten_dep(
            in_: str,
            *,
            extra: str,
            my_service: MainService,
            forgotten: ForgottenDependency,
        ) -> str:
            return f"{in_} - {my_service.foo()} - {extra} - {forgotten}"

        await autowired_sample_with_forgotten_dep("abc", extra="aa")


async def test_autowired_with_sync_method():
    """Checks for using autowired on sync method.

    Pyright will capture the error."""
    with pytest.raises(TypeError):

        @autowired  # pyright: ignore[reportArgumentType]
        def sync_autowired(
            in_: str,
            *,
            extra: str,
            my_service: MainService,
            forgotten: ForgottenDependency,
        ) -> str:
            return f"{in_} - {my_service.foo()} - {extra} - {forgotten}"

        sync_autowired("abc", extra="aa")


async def test_component_decorator_registers_to_default_aio_container():
    """
    Test that `@component` correctly registers classes in the default container
    and that dependencies are properly injected.
    """
    service = await default_aio_container.get_component(MainService)
    result = await service.foo()
    assert result == "foo"
    assert isinstance(service, MainService)
    assert isinstance(
        await default_aio_container.get_component(FirstDependency), FirstDependency
    )
    assert isinstance(
        await default_aio_container.get_component(SecondDependency), SecondDependency
    )
