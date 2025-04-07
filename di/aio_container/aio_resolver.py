import inspect
from collections.abc import Callable
from typing import Any, TypeVar, get_args, get_origin

from di.exceptions import ComponentNotFoundError

from .component_definition import ComponentDefinition

T = TypeVar("T")
A = TypeVar("A")


async def resolve(
    definitions: list[ComponentDefinition[A]],
) -> dict[type, list]:
    collected: dict[type, list] = {}
    constructed: dict[type, Any] = {}
    constructed_from_factory: dict[Callable[..., Any], Any] = {}
    implementation_provided: set = set()

    async def resolve_one(defn: ComponentDefinition[T]) -> T:
        # short-circuit if there's no factory (i.e., class-only resolution)
        if defn.type in constructed and defn.factory is None:
            return constructed[defn.type]

        # Short circuit if the factory already built
        if defn.factory in constructed_from_factory:
            return constructed_from_factory[defn.factory]

        # Short circuit if implementation is already there
        if defn.implementation in implementation_provided:
            if not isinstance(defn.implementation, defn.type):
                msg = "Implementation didn't match type"  # pragma: no cover
                raise TypeError(msg)  # pragma: no cover
            return defn.implementation

        resolved_args = {}
        for dep_type in defn.dependencies:
            origin = get_origin(dep_type)
            args = get_args(dep_type)

            if origin in {list, set} and args:
                inner_type = args[0]

                # Ensure all inner dependencies are resolved first
                for d in definitions:
                    if inner_type in d.satisfied_types or d.type == inner_type:
                        await resolve_one(d)

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
                raise ComponentNotFoundError(component_type=dep_type)

            dep_instance = await resolve_one(dep_def)
            resolved_args[dep_type] = dep_instance

        if defn.implementation is not None:
            implementation_provided.add(defn.implementation)
            instance = defn.implementation
        elif defn.factory is not None:
            factory = defn.factory
            kwargs = _match_args_by_type(factory, resolved_args)
            if defn.factory_is_async:
                if not inspect.iscoroutinefunction(factory):
                    msg = "factory method was expected to be async"  # pragma: no cover
                    raise TypeError(msg)  # pragma: no cover
                instance = await factory(**kwargs)
            else:
                instance = factory(**kwargs)
            constructed_from_factory[defn.factory] = instance
        else:
            kwargs = _match_args_by_type(defn.type, resolved_args)
            instance = defn.type(**kwargs)
            constructed[defn.type] = instance

        for typ in defn.satisfied_types:
            collected.setdefault(typ, []).append(instance)

        if not isinstance(instance, defn.type):
            msg = "Instance had unexpected type"  # pragma: no cover
            raise TypeError(msg)  # pragma: no cover
        return instance

    async def resolve_all() -> None:
        for defn in definitions:
            await resolve_one(defn)

    await resolve_all()
    return collected


def _match_args_by_type(fn: Callable, resolved_deps: dict[type, Any]) -> dict[str, Any]:
    """Match resolved dependency values to parameter names by their annotated type."""
    sig = inspect.signature(fn)
    matched = {}
    for name, param in sig.parameters.items():
        if param.annotation in resolved_deps:
            matched[name] = resolved_deps[param.annotation]
    return matched
