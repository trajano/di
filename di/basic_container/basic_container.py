import inspect
from typing import TypeVar, Any, Type, Self, List

from di.container import Container
from di.exceptions import ContainerError, ComponentNotFoundError
from .implementation_definition import ImplementationDefinition
from .resolver import Resolver

T = TypeVar("T")


class BasicContainer(Container):
    def __init__(self):
        self._definitions: list[ImplementationDefinition[Any]] = []
        self._type_map: dict[Type, Any] = {}
        self._instances: set[Any] = set()
        self._locked: bool = False

    def add_component_type(self, component_type: Type[T]) -> Self:
        if self._locked:
            raise ContainerError("Container is locked after first resolution.")

        if any(d.type is component_type for d in self._definitions):
            raise ContainerError(
                f"Component type {component_type} is already registered."
            )

        ctor = inspect.signature(component_type.__init__)
        deps = {
            p.annotation
            for n, p in ctor.parameters.items()
            if n != "self" and p.annotation != inspect.Parameter.empty
        }
        satisfied_types = {
            base
            for base in inspect.getmro(component_type)
            if base not in (object, component_type)
        } | {component_type}

        self._definitions.append(
            ImplementationDefinition(
                type=component_type,
                satisfied_types=satisfied_types,
                dependencies=deps,
                implementation=None,
            )
        )
        return self

    def get_component(self, component_type: Type[T]) -> T:
        """
        Gets a single component from the container that satisfies the given type.
        This resolves all constructor dependencies for the component.

        Raises:
            ContainerError: If no components or more than one satisfy the type.
        """
        maybe_component = self.get_optional_component(component_type)
        if maybe_component is None:
            raise ComponentNotFoundError(component_type=component_type)
        else:
            return maybe_component

    def get_components(self, component_type: Type[T]) -> List[T]:
        if not self._locked:
            self._resolve_all()
        return [impl for impl in self._instances if isinstance(impl, component_type)]

    def get_optional_component(self, component_type: Type[T]) -> T | None:
        if not self._locked:
            self._resolve_all()
        return self._type_map.get(component_type)

    def _resolve_all(self):
        self._locked = True
        resolver = Resolver(
            definitions=self._definitions,
            type_map=self._type_map,
            instances=self._instances
        )
        resolver.resolve_all()

    def __len__(self) -> int:
        return len(self._definitions)

    def __getitem__(self, component_type: Type[T]) -> T:
        return self.get_component(component_type)

    def __contains__(self, component_type: Type[Any]) -> bool:
        if not self._locked:
            self._resolve_all()
        return component_type in self._type_map
