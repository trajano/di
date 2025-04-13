"""Provide the default container."""

from ._configurable_container import ConfigurableAioContainer

default_container = ConfigurableAioContainer(is_default=True)
