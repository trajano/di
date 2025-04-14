"""Testing support.

When testing with the default containers, add this block to ensure the default
container is in a clean slate before testing:

.. code-block:: python

    import pytest
    from di_aio.testing import reset_default_container, reset_default_aio_context

    @pytest.fixture(autouse=True)
    def reset():
      reset_default_aio_context()

    reset_default_container()
"""

from .decorators import autowired_with_context
from .default_aio_container_future import DEFAULT_CONTEXT_HOLDER
from .default_container import DEFAULT_CONFIGURABLE_CONTAINER


def reset_default_container() -> None:
    """Reset the default container.

    This should only be called for testing purposes.
    """
    DEFAULT_CONFIGURABLE_CONTAINER.clear()


def reset_default_aio_context() -> None:
    """Reset the default AIO context.

    This should only be called for testing purposes.
    """
    DEFAULT_CONTEXT_HOLDER.reset()


__all__ = [
    "autowired_with_context",
    "reset_default_aio_context",
    "reset_default_container",
]
