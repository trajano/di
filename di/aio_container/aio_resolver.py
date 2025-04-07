from typing import TypeVar, Any
from .implementation_definition import ImplementationDefinition
import inspect


T = TypeVar("T")


async def resolve(
    definitions: list[ImplementationDefinition[Any]],
) -> tuple[dict[type[T], list[T]], set[Any]]:
    collected: dict[type[T], list[T]] = {}
    constructed: dict[type[T], T] = {}

    async def resolve_one(defn: ImplementationDefinition[Any]) -> Any:
        if defn.implementation is not None:
            return defn.implementation

        # Avoid cyclic dependency death spiral 😱
        if defn.type in constructed:
            return constructed[defn.type]

        if not inspect.isclass(defn.type):
            raise TypeError(f"{defn.type} is not a class")

        resolved_args = {}
        for dep_type in defn.dependencies:
            dep_def = next(
                (
                    d
                    for d in definitions
                    if dep_type in d.satisfied_types or d.type == dep_type
                ),
                None,
            )
            if not dep_def:
                raise ValueError(f"No definition found for dependency: {dep_type}")

            dep_instance = await resolve_one(dep_def)
            resolved_args[dep_type] = dep_instance

        if defn.factory is not None:
            factory = defn.factory
            kwargs = _match_args_by_type(factory, resolved_args)
            if defn.factory_is_async:
                instance = await factory(**kwargs)
            else:
                instance = factory(**kwargs)
        else:
            # Default: instantiate the class directly
            kwargs = _match_args_by_type(defn.type, resolved_args)
            instance = defn.type(**kwargs)

        defn.implementation = instance
        constructed[defn.type] = instance

        for typ in defn.satisfied_types | {defn.type}:
            collected.setdefault(typ, []).append(instance)

        return instance

    async def resolve_all():
        for defn in definitions:
            await resolve_one(defn)

    await resolve_all()
    all_instances: set[Any] = {
        instance for instances in collected.values() for instance in instances
    }
    return collected, all_instances


def _match_args_by_type(fn: Any, resolved_deps: dict[type, Any]) -> dict[str, Any]:
    """Match resolved dependency values to parameter names by their annotated type."""
    sig = inspect.signature(fn)
    matched = {}
    for name, param in sig.parameters.items():
        if param.annotation in resolved_deps:
            matched[name] = resolved_deps[param.annotation]
    return matched
