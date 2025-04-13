from .exceptions import ContainerError
from .protocols import Context


class FutureContext:
    def __init__(self):
        self._future: set[Context] = set()

    def set_result(self, context: Context) -> Context:
        if len(self._future) != 0:
            msg = f"context resolved already, {self._future}"
            raise ContainerError(msg)
        self._future.add(context)
        return context

    def result(self) -> Context:
        if len(self._future) != 1:
            msg = "context not yet resolved"
            raise ContainerError(msg)
        return next(iter(self._future))

    def reset(self) -> None:
        """Reset the context.

        For testing this allows reset of the context which Futures normally do not
        allow."""
        self._future.clear()
