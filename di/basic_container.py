import dataclasses
import inspect
from typing import TypeVar, Type, Set, Generic, Dict, List, Self, get_type_hints, Any

from . import CycleDetectedError
from .container import Container
from .exceptions import ContainerError, ComponentNotFoundError

T = TypeVar("T")


@dataclasses.dataclass
class ImplementationDefinition(Generic[T]):
    type: Type[T]
    """The primary type (class) of the implementation."""

    satisfied_types: Set[Type[Any]]
    """A set of types satisfied by the implementation (excluding 'object')."""

    dependencies: Set[Type[Any]]
    """A set of types that are constructor dependencies of the implementation."""

    implementation: T | None
    """The resolved instance of the implementation, if already constructed."""


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
            raise ContainerError(f"Component type {component_type} is already registered.")

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
        resolving: set[Type] = set()

        type_to_definition : Dict[Type, ImplementationDefinition]= {d.type: d for d in self._definitions}

        def resolve(component_type: Type[T]) -> T:
            if component_type in self._type_map:
                return self._type_map[component_type]

            if component_type in resolving:
                raise CycleDetectedError(component_type=component_type)

            if component_type not in type_to_definition:
                raise ComponentNotFoundError(component_type=component_type)

            resolving.add(component_type)

            resolved_definition = type_to_definition[component_type]
            init_hints = get_type_hints(resolved_definition.type.__init__)
            kwargs = {
                param: resolve(dep_type)
                for param, dep_type in init_hints.items()
                if param not in ("return", "self")
            }

            instance = resolved_definition.type(**kwargs)
            resolved_definition.implementation = instance
            self._instances.add(instance)
            for satisfied_type in resolved_definition.satisfied_types:
                self._type_map[satisfied_type] = instance

            resolving.remove(component_type)
            return instance

        for definition in self._definitions:
            resolve(definition.type)

    def __len__(self) -> int:
        return len(self._definitions)

    def __getitem__(self, component_type: Type[T]) -> T:
        return self.get_component(component_type)

    def __contains__(self, component_type: Type[Any]) -> bool:
        if not self._locked:
            self._resolve_all()
        return component_type in self._type_map
