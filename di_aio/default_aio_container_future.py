"""Provide the default container"""

from .future_context import FutureContext

default_context_holder = FutureContext()


def reset_default_aio_context() -> None:
    """Reset the Default AIO Context future.
    This should only be called for testing."""
    default_context_holder.reset()
