from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from typing import Any, Generic, ParamSpec, Protocol, TypeVar

from .enums import ComponentScope

P = ParamSpec("P")
I_co = TypeVar("I_co", covariant=True)
T = TypeVar("T")
AnyType = type[Any]


class ContainerAsyncFactory(Protocol[I_co, P]):
    """Factory that provides a asynchronous context-managed instance.

    Represents a factory that returns an asynchronous context-managed instance
    of type `I_co`.

    This factory can be called with any combination of arguments described by `P`,
    and returns an AbstractAsyncContextManager yielding `I_co`.

    :returns: An async context manager yielding an instance of the target type.
    """

    def __call__(
        self, *args: P.args, **kwargs: P.kwargs,
    ) -> AbstractAsyncContextManager[I_co]: ...


@dataclass
class ComponentDefinition(Generic[T]):
    """Component definition structure containing metadata about a registered component.

    :param satisfied_types: All types (interfaces or base classes) satisfied by the
      component.
    :param dependencies: Constructor-injected types this component depends on.
    :param factory: A callable factory that produces the component wrapped in an
      async context manager.
    :param scope: The lifetime scope of the component (e.g., container or function
      scoped).
    """

    type: type[T]
    satisfied_types: set[AnyType]
    """A set of types satisfied by the implementation (excluding 'object')."""

    dependencies: set[AnyType]
    """A set of types that are constructor dependencies of the implementation."""
    collection_dependencies: set[AnyType]

    factory: ContainerAsyncFactory[T, Any]
    """
    Factory to build the implementation.

    Must accept keyword-only arguments and return an async context-managed instance.
    """

    scope: ComponentScope
    """
    The lifetime scope of the component:

    - CONTAINER: Singleton for the lifetime of the container.
    - FUNCTION: Transient, created on each resolve call.
    """


@dataclass
class ResolvedComponent(Generic[T]):
    """A component that is resolved."""

    satisfied_types: set[AnyType]
    """A set of types satisfied by the implementation (excluding 'object')."""
    context_manager: AbstractAsyncContextManager[T]
    """The context manager for the instance."""
    instance: T
    """The active instance."""
