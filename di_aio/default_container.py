"""Provide the default container."""

from ._configurable_container import ConfigurableAioContainer
from .protocols import Context

DEFAULT_CONFIGURABLE_CONTAINER = ConfigurableAioContainer(is_default=True)


def get_default_context() -> Context:
    """Get default context from default container."""
    return DEFAULT_CONFIGURABLE_CONTAINER.context()
