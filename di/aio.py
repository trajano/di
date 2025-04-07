"""Async IO only API"""

from .aio_container import AioContainer
from .decorators import component, autowired
from .exceptions import (
    ContainerError,
    CycleDetectedError,
    ComponentNotFoundError,
    DuplicateRegistrationError,
)

__all__ = [
    "AioContainer",
    "CycleDetectedError",
    "ComponentNotFoundError",
    "ContainerError",
    "DuplicateRegistrationError",
    "component",
    "autowired",
    "default_aio_container",
]

default_aio_container = AioContainer()
