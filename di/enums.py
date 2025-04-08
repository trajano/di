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
