from typing import Type, Self, Callable, Union, List, ParamSpec, TypeVar, Any, Awaitable
import typing
import inspect
from di import ContainerError, ComponentNotFoundError
from di.util import (
    extract_dependencies_from_signature,
    extract_satisfied_types_from_type,
)
from .aio_resolver import resolve
from .implementation_definition import ImplementationDefinition

P = ParamSpec("P")
T = TypeVar("T")


class AioContainer:
    def __init__(self):
        self._definitions: list[ImplementationDefinition[Any]] = []
        self._type_map: dict[type, list] | None = None
        self._instances: set | None = None

    def add_component_type(self, component_type: Type[T]) -> Self:
        if self._type_map is not None:
            raise ContainerError("Container is locked after first resolution.")
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
        return self

    def add_component_factory(
        self, factory: Callable[P, T] | Callable[P, Awaitable[T]]
    ) -> Self:
        if self._type_map is not None:
            raise ContainerError("Container is locked after first resolution.")

        # Attempt to get the return type of the factory
        return_type = typing.get_type_hints(factory).get("return")
        if return_type is None:
            raise ContainerError("Factory must have a return type annotation.")

        deps = extract_dependencies_from_signature(factory)
        satisfied_types = extract_satisfied_types_from_type(return_type)

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
        return self

    def __iadd__(self, other: Union[Type[T], Callable[..., T]]) -> Self:
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
        if self._type_map is None:
            (self._type_map, self._instances) = await resolve(self._definitions)
        return self._type_map[component_type]
