from collections.abc import Callable
from typing import TypeVar

from .protocols import ComponentAddable

T = TypeVar("T")
R = TypeVar("R")


def register_class_to_container(
    cls: type[T] | None, container: ComponentAddable
) -> type[T] | Callable[[type[T]], type[T]]:
    def wrap(target_cls: type[T]) -> type[T]:
        container.add_component_type(target_cls)
        return target_cls

    if cls is None:
        return wrap
    return wrap(cls)


def register_factory_to_container(
    fn: Callable[..., R] | None, container: ComponentAddable
) -> Callable[..., R] | Callable[[Callable[..., R]], Callable[..., R]]:
    def wrap(target_fn: Callable[..., R]) -> Callable[..., R]:
        container.add_component_factory(target_fn)
        return target_fn

    if fn is None:
        return wrap
    return wrap(fn)
