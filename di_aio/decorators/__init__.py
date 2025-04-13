"""Decorators."""

from .autowired import autowired, autowired_with_container
from .component import component
from .factory import factory

__all__ = [
    "autowired",
    "autowired_with_container",
    "component",
    "factory",
]
