import typing
from typing import Callable


class ContainerError(RuntimeError):
    """Exception for errors in the container."""

    ...


class CycleDetectedError(ContainerError):
    """
    Exception raised when a circular dependency is detected.

    :param component_type: The type that caused the cycle detection.
    :param message: Optional custom message to override the default one.
    """

    def __init__(
        self,
        component_type: typing.Type[typing.Any],
        message: str | None = None,
    ):
        self.component_type = component_type
        if message is None:
            message = f"Circular dependency detected involving {component_type}"
        super().__init__(message)


class ComponentNotFoundError(ContainerError):
    """
    Exception raised when no component is found for the given type.

    :param component_type: The requested type that could not be resolved.
    :param message: Optional custom message to override the default one.
    """

    def __init__(
        self,
        component_type: typing.Type[typing.Any],
        message: str | None = None,
    ):
        self.component_type = component_type
        if message is None:
            message = f"Component of type {component_type} not found in container"
        super().__init__(message)


class DuplicateRegistrationError(ContainerError):
    """
    Exception raised when two EXACT component types or two EXACT factories are registered.

    :param type_or_factory: The type or factory that caused the error
    :param message: Optional custom message to override the default one.
    """

    def __init__(
        self,
        type_or_factory: type | Callable[..., typing.Any],
        message: str | None = None,
    ):
        self.type_or_factory = type_or_factory
        if message is None:
            message = f"Registering {type_or_factory} twice."
        super().__init__(message)
