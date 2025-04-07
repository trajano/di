from typing import Any, TypeVar, get_type_hints

from di.exceptions import ComponentNotFoundError, CycleDetectedError

from .component_definition import ComponentDefinition

T = TypeVar("T")


class Resolver:
    """Resolve components and their dependencies."""

    def __init__(
        self,
        definitions: list[ComponentDefinition[Any]],
        type_map: dict[type, Any],
        instances: set[Any],
    ):
        self._definitions = definitions
        self._type_map = type_map
        self._instances = instances
        self._resolving: set[type] = set()
        self._type_to_definition: dict[type, ComponentDefinition] = {
            d.type: d for d in definitions
        }

    def resolve_all(self) -> None:
        """Resolve all component types in the container."""
        for definition in self._definitions:
            self._resolve(definition.type)

    def _resolve(self, component_type: type[T]) -> T:
        if component_type in self._type_map:
            return self._type_map[component_type]

        if component_type in self._resolving:
            raise CycleDetectedError(component_type=component_type)

        definition = self._type_to_definition.get(component_type)
        if definition is None:
            raise ComponentNotFoundError(component_type=component_type)

        self._resolving.add(component_type)

        if definition.factory is not None:
            factory = definition.factory
            factory_hints = get_type_hints(factory)
            kwargs = {
                param: self._resolve(dep_type)
                for param, dep_type in factory_hints.items()
                if param != "return"
            }
            instance = factory(**kwargs)
        else:
            init_hints = get_type_hints(definition.type.__init__)
            kwargs = {
                param: self._resolve(dep_type)
                for param, dep_type in init_hints.items()
                if param not in ("self", "return")
            }
            instance = definition.type(**kwargs)

        definition.implementation = instance
        self._instances.add(instance)
        for satisfied_type in definition.satisfied_types:
            self._type_map[satisfied_type] = instance

        self._resolving.remove(component_type)
        return instance
