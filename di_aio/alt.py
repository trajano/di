"""
Package that provides alternate container creation to allow multiple DI
containers.
"""

from .autowired import autowired, autowired_with_container
from .component import component
from .configurable_container import ConfigurableAioContainer
from .context import AioContext
from .factory import factory

__all__ = [
    "AioContext",
    "ConfigurableAioContainer",
    "autowired",
    "autowired_with_container",
    "component",
    "factory",
]
