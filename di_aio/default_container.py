"""Provide the default container."""

from ._configurable_container import ConfigurableAioContainer

DEFAULT_CONFIGURABLE_CONTAINER = ConfigurableAioContainer(is_default=True)
