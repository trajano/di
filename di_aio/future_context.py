from .exceptions import ContainerError
from .protocols import Context


class FutureContext:
    """Resettable container context used in place of a future-like value."""

    def __init__(self) -> None:
        """Initialize with an empty context set."""
        self._future: set[Context] = set()

    def set_result(self, context: Context) -> Context:
        """Set the resolved context.

        :param context: The context to register.
        :returns: The same context after registration.
        :raises ContainerError: If a context has already been set.
        """
        if len(self._future) != 0:
            msg = f"context resolved already, {self._future}"
            raise ContainerError(msg)
        self._future.add(context)
        return context

    def result(self) -> Context:
        """Return the resolved context.

        :returns: The single registered context.
        :raises ContainerError: If the context is not yet resolved.
        """
        if len(self._future) != 1:
            msg = "context not yet resolved"
            raise ContainerError(msg)
        return next(iter(self._future))

    def reset(self) -> None:
        """Reset the context.

        Allows clearing the resolved context, typically for testing.
        """
        self._future.clear()
