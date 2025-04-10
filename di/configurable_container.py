from contextlib import AbstractContextManager, AbstractAsyncContextManager
from typing import Callable, Protocol, Awaitable, TypeVar, ParamSpec
from di.enums import ComponentScope

P = ParamSpec("P")
T = TypeVar("T")


class ConfigurableContainer(Protocol):
    """
    Protocol defining the registration interface for dependency injection containers
    that support pre-initialization configuration.

    This abstraction decouples the registration of components from their resolution,
    enabling flexible setup patterns such as delayed container finalization or
    decorator-based registrations.
    """

    def add_component_type(self, component_type: type) -> None:
        """
        Register a component type to be constructed by the container.

        The container will extract the constructor signature to determine
        dependencies. The registered type will be used to satisfy itself
        and any supertypes or protocols it implements.

        :param component_type: The class to register.
        """
        ...

    def add_component_implementation(self, implementation: object) -> None:
        """
        Register a concrete instance that satisfies one or more types.

        The instance will be treated as already constructed and wrapped in
        a no-op async context manager during resolution.

        :param implementation: The object instance to register.
        """
        ...

    def add_component_factory(
        self,
        factory: Callable[P, T] | Callable[P, Awaitable[T]],
        *,
        scope: ComponentScope = ComponentScope.CONTAINER,
    ) -> None:
        """
        Register a factory function that constructs a component.

        The factory may be synchronous or asynchronous, and may declare
        dependencies via keyword arguments. It can be associated with either
        a container or function scope.

        :param factory: A callable that produces the component.
        :param scope: The lifecycle scope of the component.
        """
        ...

    def add_context_managed_type(
        self,
        cm_type: type,
        *,
        scope: ComponentScope = ComponentScope.CONTAINER,
    ) -> None:
        """
        Register a component type that implements sync or async context management.

        This ensures that the component's lifecycle is handled via `async with`
        and cleanup is invoked on container exit.

        :param cm_type: A class that implements either `__enter__/__exit__`
                               or `__aenter__/__aexit__`.
        :param scope: The lifecycle scope for the component (default: CONTAINER).
        :raises DuplicateRegistrationError: If the type has already been registered.
        """
        ...
