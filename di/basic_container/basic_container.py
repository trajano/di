import inspect
from collections.abc import Callable
from typing import TypeVar, Any, Type, Self, List, ParamSpec, Union
import typing

from di.util import extract_satisfied_types_from_return_of_callable
from di.util import extract_satisfied_types_from_type
from di.exceptions import (
    ContainerError,
    ComponentNotFoundError,
    DuplicateRegistrationError,
)
from .implementation_definition import ImplementationDefinition
from .resolver import Resolver
from .container import Container

P = ParamSpec("P")
T = TypeVar("T")


class BasicContainer(Container):
    """Basic Container that only supports synchronized calls."""

    def __init__(self):
        self._definitions: list[ImplementationDefinition[Any]] = []
        self._type_map: dict[Type, Any] = {}
        self._instances: set[Any] = set()
        self._locked: bool = False
        self._registered: set = set()

    def add_component_type(self, component_type: Type[T]) -> Self:
        if self._locked:
            raise ContainerError("Container is locked after first resolution.")
        if component_type in self._registered:
            raise DuplicateRegistrationError(type_or_factory=component_type)
        self._registered.add(component_type)

        ctor = inspect.signature(component_type.__init__)
        deps = {
            p.annotation
            for n, p in ctor.parameters.items()
            if n != "self" and p.annotation != inspect.Parameter.empty
        }
        satisfied_types = extract_satisfied_types_from_type(component_type)

        self._definitions.append(
            ImplementationDefinition(
                type=component_type,
                satisfied_types=satisfied_types,
                dependencies=deps,
                implementation=None,
                factory=None,
            )
        )
        return self

    def add_component_factory(self, factory: typing.Callable[..., T]) -> typing.Self:
        if self._locked:
            raise ContainerError("Container is locked after first resolution.")
        if factory in self._registered:
            raise DuplicateRegistrationError(type_or_factory=factory)
        self._registered.add(factory)

        deps = set(
            param.annotation
            for name, param in inspect.signature(factory).parameters.items()
            if param.annotation != inspect.Parameter.empty
        )
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
            instances=self._instances,
        )
        resolver.resolve_all()

    def __iadd__(self, other: Union[Type[T], Callable[..., T]]) -> Self:
        if inspect.isclass(other):
            return self.add_component_type(other)
        elif callable(other):
            return self.add_component_factory(other)
        raise TypeError(f"Unsupported component type: {type(other)}")

    def __len__(self) -> int:
        return len(self._definitions)

    def __getitem__(self, component_type: Type[T]) -> T:
        return self.get_component(component_type)

    def __contains__(self, component_type: Type[Any]) -> bool:
        if not self._locked:
            self._resolve_all()
        return component_type in self._type_map
