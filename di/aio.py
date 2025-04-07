"""Async IO only API"""

from .aio_container import AioContainer
from .decorators import component, autowired
from .exceptions import ContainerError, CycleDetectedError, ComponentNotFoundError

__all__ = [
    "AioContainer",
    "CycleDetectedError",
    "ComponentNotFoundError",
    "ContainerError",
    "component",
    "autowired",
    "default_aio_container",
]

default_aio_container = AioContainer()
