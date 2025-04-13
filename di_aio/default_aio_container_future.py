"""Provide the default container"""

from asyncio import Future

default_aio_context_future = Future()


def reset_default_aio_context_future() -> None:
    """Reset the Default AIO Context future.
    This should only be called for testing."""
    global default_aio_context_future
    default_aio_context_future = Future()
