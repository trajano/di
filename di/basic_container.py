import dataclasses
import inspect
import typing
from .container import Container, ContainerError

T = typing.TypeVar("T")


@dataclasses.dataclass
class ImplementationDefinition(typing.Generic[T]):
    type: typing.Type[T]
    """The primary type (class) of the implementation."""

    satisfied_types: typing.Set[typing.Type[typing.Any]]
    """A set of types satisfied by the implementation (excluding 'object')."""

    dependencies: typing.Set[typing.Type[typing.Any]]
    """A set of types that are constructor dependencies of the implementation."""

    implementation: T | None
    """The resolved instance of the implementation, if already constructed."""


class BasicContainer(Container):
    def __init__(self):
        self._definitions: list[ImplementationDefinition] = []
        self._type_map: dict[type, typing.Any] = {}
        self._instances: set[typing.Any] = set()
        self._locked: bool = False

    def add_component_type(self, component_type: typing.Type[T]) -> typing.Self:
        if self._locked:
            raise ContainerError("Container is locked after first resolution.")

        ctor = inspect.signature(component_type.__init__)
        deps = set(
            p.annotation
            for n, p in ctor.parameters.items()
            if n != "self" and p.annotation != inspect.Parameter.empty
        )
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

    def get_component(self, component_type: typing.Type[T]) -> T:
        """
        Gets a single component from the container that satisfies the given type.
        This resolves all constructor dependencies for the component.

        Raises:
            ContainerError: If no components or more than one satisfy the type.
        """
        maybe_component = self.get_optional_component(component_type)
        if maybe_component is None:
            msg = (
                f"Unable to find component of type={component_type} in container={self}"
            )
            raise ContainerError(msg)
        else:
            return maybe_component

    def get_components(self, component_type: typing.Type[T]) -> typing.List[T]:
        if not self._locked:
            self._resolve_all()
        return [impl for impl in self._instances if isinstance(impl, component_type)]

    def get_optional_component(self, component_type: typing.Type[T]) -> T | None:
        if not self._locked:
            self._resolve_all()
        return self._type_map.get(component_type)

    def _resolve_all(self):
        self._locked = True
        for definition in self._definitions:
            init_hints = typing.get_type_hints(definition.type.__init__)
            kwargs = {
                param: self.get_component(dep_type)
                for param, dep_type in init_hints.items()
                if param != "return" and param != "self"
            }

            instance = definition.type(**kwargs)
            definition.implementation = instance
            self._instances.add(instance)
            for satisfied_type in definition.satisfied_types:
                self._type_map[satisfied_type] = instance

    def __len__(self) -> int:
        return len(self._definitions)

    def __getitem__(self, component_type: typing.Type[T]) -> T:
        return self.get_component(component_type)

    def __contains__(self, component_type: typing.Type[typing.Any]) -> bool:
        if not self._locked:
            self._resolve_all()
        return component_type in self._type_map
