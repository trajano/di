"""Provide the default container"""

from .protocols import Context

default_context_holder: set[Context] = set()


def reset_default_aio_context() -> None:
    """Reset the Default AIO Context future.
    This should only be called for testing."""
    default_context_holder.clear()
