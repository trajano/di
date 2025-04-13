"""Provide the default container context object."""

from .future_context import FutureContext

default_context_holder = FutureContext()


def reset_default_aio_context() -> None:
    """Reset the default AIO context.

    This should only be called for testing purposes.

    :raises ContainerError: If reset is called improperly (internally).
    """
    default_context_holder.reset()
