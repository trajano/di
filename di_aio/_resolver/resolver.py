from typing import Any

from di_aio._toposort import _toposort_components
from di_aio.protocols import ScopeFilter
from di_aio.types import ComponentDefinition, ResolvedComponent

from ._util import extract_kwargs_from_type_constructor
from .scope_filters import is_all_scope


async def resolve_scope(
    definitions: list[ComponentDefinition[Any]],
    *,
    parent: list[ResolvedComponent[Any]] | None = None,
    scope_filter: ScopeFilter | None = None,
) -> list[ResolvedComponent[Any]]:
    instances: list[ResolvedComponent[Any]] = (
        parent.copy() if parent is not None else []
    )
    constructed: dict[type, Any] = {
        t: c.instance for c in instances for t in c.satisfied_types
    }

    filter_by = is_all_scope if scope_filter is None else scope_filter

    sorted_types = _toposort_components(definitions)

    # Only keep scoped types for resolution
    parent_types = {t for d in definitions if filter_by(d) for t in d.satisfied_types}

    sorted_types = [t for t in sorted_types if t in parent_types]

    # Index definitions by scope
    type_to_definition = {
        t: d for d in definitions if filter_by(d) for t in d.satisfied_types
    }

    for t in sorted_types:
        definition = type_to_definition[t]
        kwargs = extract_kwargs_from_type_constructor(definition, constructed)

        context_manager = definition.build_context_manager(**kwargs)
        instance = await context_manager.__aenter__()

        instances.append(
            ResolvedComponent(
                satisfied_types=definition.satisfied_types,
                context_manager=context_manager,
                instance=instance,
            ),
        )

        for typ in definition.satisfied_types:
            constructed[typ] = instance

    return instances


