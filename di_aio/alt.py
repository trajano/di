"""Alternate container support.

Package that provides alternate container creation to allow multiple DI
containers.
"""

from ._configurable_container import ConfigurableAioContainer
from ._context import AioContext
from .decorators import autowired, component, factory
from .enums import ComponentScope
from .exceptions import ContainerError
from .future_context import FutureContext

__all__ = [
    "AioContext",
    "ComponentScope",
    "ConfigurableAioContainer",
    "ContainerError",
    "FutureContext",
    "autowired",
    "component",
    "factory",
]
