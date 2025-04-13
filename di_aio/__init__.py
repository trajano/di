"""Default package.

This package exports functions, classes and objects that uses the API that
utilizes a single default configurable container and runtime context.
"""

from .decorators import autowired, component, factory
from .default_container import default_container
from .protocols import ConfigurableContainer, Context

__all__ = [
    "ConfigurableContainer",
    "Context",
    "autowired",
    "component",
    "default_container",
    "factory",
]
