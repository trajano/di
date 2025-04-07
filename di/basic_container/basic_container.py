import inspect
import typing
from collections.abc import Callable
from typing import Any, ParamSpec, Self, TypeVar

import di.util
from di.exceptions import (
    ComponentNotFoundError,
    ContainerLockedError,
    DuplicateRegistrationError,
)
from di.util import (
    extract_satisfied_types_from_return_of_callable,
    extract_satisfied_types_from_type,
)

from .component_definition import ComponentDefinition
from .container import Container
from .resolver import Resolver

P = ParamSpec("P")
T = TypeVar("T")


class BasicContainer(Container):
    """Basic Container that only supports synchronized calls."""

    def __init__(self):
        self._definitions: list[ComponentDefinition[Any]] = []
        self._type_map: dict[type, Any] = {}
        self._instances: set = set()
        self._locked: bool = False
        self._registered: set = set()

    def add_component_type(self, component_type: type[T]) -> None:
        if self._locked:
            raise ContainerLockedError
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
            ComponentDefinition(
                type=component_type,
                satisfied_types=satisfied_types,
                dependencies=deps,
                implementation=None,
                factory=None,
            )
        )

    def add_component_factory(self, factory: typing.Callable[..., T]) -> None:
        if self._locked:
            raise ContainerLockedError
        if factory in self._registered:
            raise DuplicateRegistrationError(type_or_factory=factory)
        self._registered.add(factory)

        deps = di.util.extract_dependencies_from_signature(factory)
        return_type, satisfied_types = extract_satisfied_types_from_return_of_callable(
            factory
        )

        self._definitions.append(
            ComponentDefinition(
                type=return_type,
                satisfied_types=satisfied_types,
                dependencies=deps,
                implementation=None,
                factory=factory,
            )
        )

    def get_component(self, component_type: type[T]) -> T:
        """Gets a single component from the container that satisfies the given type.
        This resolves all constructor dependencies for the component.

        Raises:
            ContainerError: If no components or more than one satisfy the type.

        """
        maybe_component = self.get_optional_component(component_type)
        if maybe_component is None:
            raise ComponentNotFoundError(component_type=component_type)
        return maybe_component

    def get_components(self, component_type: type[T]) -> list[T]:
        if not self._locked:
            self._resolve_all()
        return [impl for impl in self._instances if isinstance(impl, component_type)]

    def get_optional_component(self, component_type: type[T]) -> T | None:
        if not self._locked:
            self._resolve_all()
        return self._type_map.get(component_type)

    def _resolve_all(self) -> None:
        self._locked = True
        resolver = Resolver(
            definitions=self._definitions,
            type_map=self._type_map,
            instances=self._instances,
        )
        resolver.resolve_all()

    def __iadd__(self, other: type[T] | Callable[..., T]) -> Self:
        if inspect.isclass(other):
            self.add_component_type(other)
            return self
        if callable(other):
            self.add_component_factory(other)
            return self
        msg = f"Unsupported component type: {type(other)}"
        raise TypeError(msg)

    def __len__(self) -> int:
        return len(self._definitions)

    def __getitem__(self, component_type: type[T]) -> T:
        return self.get_component(component_type)

    def __contains__(self, component_type: type[Any]) -> bool:
        """Container contains a component type."""
        if not self._locked:
            self._resolve_all()
        return component_type in self._type_map
