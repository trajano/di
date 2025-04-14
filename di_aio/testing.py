"""Testing support."""

from .decorators import autowired_with_context
from .default_aio_container_future import default_context_holder


def reset_default_aio_context() -> None:
    """Reset the default AIO context.

    This should only be called for testing purposes.

    :raises ContainerError: If reset is called improperly (internally).
    """
    default_context_holder.reset()


__all__ = ["autowired_with_context", "reset_default_aio_context"]
