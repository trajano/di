from typing import Any, Dict, Set, Type, TypeVar, get_type_hints

from di.exceptions import ComponentNotFoundError, CycleDetectedError

from .implementation_definition import ImplementationDefinition

T = TypeVar("T")


class Resolver:
    """Resolves components and their dependencies using constructor injection.
    """

    def __init__(
        self,
        definitions: list[ImplementationDefinition[Any]],
        type_map: dict[Type, Any],
        instances: set[Any],
    ):
        self._definitions = definitions
        self._type_map = type_map
        self._instances = instances
        self._resolving: Set[Type] = set()
        self._type_to_definition: Dict[Type, ImplementationDefinition] = {
            d.type: d for d in definitions
        }

    def resolve_all(self):
        """Resolves all component types in the container and their dependencies.
        """
        for definition in self._definitions:
            self._resolve(definition.type)

    def _resolve(self, component_type: Type[T]) -> T:
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
