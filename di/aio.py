"""Async IO only API"""

from .aio_container import AioContainer
from .decorators import component, autowired
from .exceptions import (
    ContainerError,
    ComponentNotFoundError,
    ContainerLockedError,
    DuplicateRegistrationError,
)

__all__ = [
    "AioContainer",
    "ComponentNotFoundError",
    "ContainerError",
    "ContainerLockedError",
    "DuplicateRegistrationError",
    "component",
    "autowired",
    "default_aio_container",
]

default_aio_container = AioContainer()
