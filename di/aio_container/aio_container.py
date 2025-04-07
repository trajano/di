from typing import (
    Type,
    Self,
    Callable,
    List,
    ParamSpec,
    TypeVar,
    Any,
    Awaitable,
)
import inspect
from di import ContainerError, ComponentNotFoundError
from di.util import (
    extract_dependencies_from_signature,
    extract_satisfied_types_from_type,
    extract_satisfied_types_from_return_of_callable,
)
from .aio_resolver import resolve
from .implementation_definition import ImplementationDefinition
from ..exceptions import ContainerLockedError, DuplicateRegistrationError

P = ParamSpec("P")
T = TypeVar("T")


class AioContainer:
    def __init__(self):
        self._definitions: list[ImplementationDefinition[Any]] = []
        self._type_map: dict[type, list] | None = None
        self._registered: set = set()

    def add_component_type(self, component_type: type) -> None:
        if self._type_map is not None:
            raise ContainerLockedError()
        if component_type in self._registered:
            raise DuplicateRegistrationError(type_or_factory=component_type)
        self._registered.add(component_type)
        deps = extract_dependencies_from_signature(component_type.__init__)
        satisfied_types = extract_satisfied_types_from_type(component_type)
        self._definitions.append(
            ImplementationDefinition(
                type=component_type,
                satisfied_types=satisfied_types,
                dependencies=deps,
                implementation=None,
                factory=None,
                factory_is_async=False,
            )
        )

    def add_component_implementation(self, implementation: Any) -> None:
        if self._type_map is not None:
            raise ContainerLockedError()
        if implementation in self._registered:
            raise DuplicateRegistrationError(type_or_factory=implementation)
        self._registered.add(implementation)
        component_type = type(implementation)
        satisfied_types = extract_satisfied_types_from_type(component_type)
        self._definitions.append(
            ImplementationDefinition(
                type=component_type,
                satisfied_types=satisfied_types,
                dependencies=set(),
                implementation=implementation,
                factory=None,
                factory_is_async=False,
            )
        )

    def add_component_factory(
        self, factory: Callable[P, T] | Callable[P, Awaitable[T]]
    ) -> None:
        if self._type_map is not None:
            raise ContainerLockedError()
        if factory in self._registered:
            raise DuplicateRegistrationError(type_or_factory=factory)
        self._registered.add(factory)

        deps = extract_dependencies_from_signature(factory)
        return_type, satisfied_types = extract_satisfied_types_from_return_of_callable(
            factory
        )

        self._definitions.append(
            ImplementationDefinition(
                type=return_type,
                satisfied_types=satisfied_types,
                dependencies=deps,
                implementation=None,
                factory=factory,
                factory_is_async=inspect.iscoroutinefunction(factory),
            )
        )

    def __iadd__(self, other: Any) -> Self:
        if inspect.isclass(other):
            self.add_component_type(other)
            return self
        elif callable(other):
            self.add_component_factory(other)
            return self
        else:
            self.add_component_implementation(other)
            return self

    async def get_component(self, component_type: Type[T]) -> T:
        maybe_component = await self.get_optional_component(component_type)
        if maybe_component is None:
            raise ComponentNotFoundError(component_type=component_type)
        else:
            return maybe_component

    async def get_optional_component(self, component_type: Type[T]) -> T | None:
        component_list = await self.get_components(component_type)
        if len(component_list) == 0:
            return None
        elif len(component_list) == 1:
            return component_list[0]
        else:
            raise ContainerError(
                f"Multiple components of type {component_type} registered"
            )

    async def get_components(self, component_type: Type[T]) -> List[T]:
        self._type_map = self._type_map or (await resolve(self._definitions))
        return self._type_map.get(component_type, [])
