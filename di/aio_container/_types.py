from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from typing import Protocol, TypeVar, Generic, Type

from di.enums import ComponentScope

I_co = TypeVar("I_co", covariant=True)
I = TypeVar("I")


class ContainerAsyncFactory(Protocol[I_co]):
    """
    Represents a factory that returns an asynchronous context-managed instance
    of type `I_co`.

    This factory, when called with keyword-only arguments, produces an
    `AbstractAsyncContextManager[I_co]` suitable for use with `async with`.

    :returns: An async context manager yielding an instance of the target type.
    """

    def __call__(self, *args, **kwargs) -> AbstractAsyncContextManager[I_co]: ...


@dataclass
class ComponentDefinition(Generic[I]):
    """
    Component definition structure containing metadata about a registered component.

    :param type: The main implementation class/type for the component.
    :param satisfied_types: All types (interfaces or base classes) satisfied by the component.
    :param dependencies: Constructor-injected types this component depends on.
    :param factory: A callable factory that produces the component wrapped in an async context manager.
    :param component_scope: The lifetime scope of the component (e.g., container or function scoped).
    """

    type: type[I]
    """The primary type (class) of the implementation."""

    satisfied_types: set[Type]
    """A set of types satisfied by the implementation (excluding 'object')."""

    dependencies: set[Type]
    """A set of types that are constructor dependencies of the implementation."""

    factory: ContainerAsyncFactory[I]
    """
    Factory to build the implementation.

    Must accept keyword-only arguments and return an async context-managed instance.
    """

    component_scope: ComponentScope
    """
    The lifetime scope of the component:

    - CONTAINER: Singleton for the lifetime of the container.
    - FUNCTION: Transient, created on each resolve call.
    """
