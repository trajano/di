import inspect
from typing import TypeVar, Any, get_origin, get_args, Callable

from .implementation_definition import ImplementationDefinition
from .. import ContainerError

T = TypeVar("T")


async def resolve(
    definitions: list[ImplementationDefinition[Any]],
) -> dict[type, list]:
    collected: dict[type, list] = {}
    constructed: dict[type, Any] = {}
    constructed_from_factory: dict[Callable[..., Any], Any] = {}

    async def resolve_one(defn: ImplementationDefinition[Any]) -> Any:
        # only short-circuit if there's no factory (i.e., class-only resolution)
        if defn.type in constructed and defn.factory is None:
            return constructed[defn.type]

        # Short circuit if the factory already built
        if defn.factory in constructed_from_factory:
            return constructed_from_factory[defn.factory]

        resolved_args = {}
        for dep_type in defn.dependencies:
            origin = get_origin(dep_type)
            args = get_args(dep_type)

            if origin in {list, set} and args:
                inner_type = args[0]
                values = collected.get(inner_type, [])
                resolved_args[dep_type] = (
                    list(values) if origin is list else set(values)
                )
                continue

            dep_def = next(
                (
                    d
                    for d in definitions
                    if dep_type in d.satisfied_types or d.type == dep_type
                ),
                None,
            )
            if not dep_def:
                raise ContainerError(f"No definition found for dependency: {dep_type}")

            dep_instance = await resolve_one(dep_def)
            resolved_args[dep_type] = dep_instance

        if defn.implementation is not None:
            instance = defn.implementation
        else:
            if defn.factory is not None:
                factory = defn.factory
                kwargs = _match_args_by_type(factory, resolved_args)
                if defn.factory_is_async:
                    instance = await factory(**kwargs)
                else:
                    instance = factory(**kwargs)
                constructed_from_factory[defn.factory] = instance
            else:
                kwargs = _match_args_by_type(defn.type, resolved_args)
                instance = defn.type(**kwargs)
                constructed[defn.type] = instance
            defn.implementation = instance

        for typ in defn.satisfied_types:
            collected.setdefault(typ, []).append(instance)

        return instance

    async def resolve_all():
        for defn in definitions:
            await resolve_one(defn)

    await resolve_all()
    return collected


def _match_args_by_type(fn: Any, resolved_deps: dict[type, Any]) -> dict[str, Any]:
    """Match resolved dependency values to parameter names by their annotated type."""
    sig = inspect.signature(fn)
    matched = {}
    for name, param in sig.parameters.items():
        if param.annotation in resolved_deps:
            matched[name] = resolved_deps[param.annotation]
    return matched
