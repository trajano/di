from enum import Enum


class ComponentScope(Enum):
    """
    Represent the lifetime scope of a component within the DI container.

    :cvar CONTAINER: A container-scoped component is created once and reused
        for the lifetime of the container. It may only depend on other
        container-scoped components.

    :cvar FUNCTION: A function-scoped component is created afresh for each
        `resolve()` call. It can depend on container-scoped or other
        function-scoped components.
    """

    CONTAINER = 1
    FUNCTION = 2


class ContainerState(Enum):
    """
    Represents the internal state of the container lifecycle.

    :cvar INITIALIZING: Component registration phase.
    :cvar VALIDATING: Container-scoped components are being validated or resolved.
    :cvar SERVICING: Ready for resolving function-scoped components.
    :cvar RESOLVING: Actively resolving dependencies.
    :cvar RUNNING: Active use of resolved components.
    :cvar CLOSING: Shutting down and cleaning up.
    """

    INITIALIZING = 1
    VALIDATING = 2
    SERVICING = 3
    RESOLVING = 4
    RUNNING = 5
    CLOSING = 6
