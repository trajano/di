from typing import Any

from di_aio.enums import ComponentScope
from di_aio.types import ComponentDefinition


def is_container_scope(definition: ComponentDefinition[Any]) -> bool:
    """Check if definition is in container scope."""
    return definition.scope == ComponentScope.CONTAINER


def is_function_scope(definition: ComponentDefinition[Any]) -> bool:
    """Check if definition is in function scope."""
    return definition.scope == ComponentScope.FUNCTION


def is_all_scope(_definition: ComponentDefinition[Any]) -> bool:
    """Return true.

    This is the default, usage outside this package is primarily used for testing.
    """
    return True
