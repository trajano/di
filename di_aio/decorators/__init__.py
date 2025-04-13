"""Decorators."""

from .autowired import autowired, autowired_with_context
from .component import component
from .factory import factory

__all__ = [
    "autowired",
    "autowired_with_context",
    "component",
    "factory",
]
