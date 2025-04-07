import inspect
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from typing import Any, TypeVar, get_args, get_origin

from di.exceptions import ComponentNotFoundError
from .component_definition import ComponentDefinition

T = TypeVar("T")
A = TypeVar("A")


async def resolve(
        definitions: list[ComponentDefinition[A]],
) -> dict[type, list]:
    collected_instances: dict[type, list] = {}
    constructed_instances: dict[type, Any] = {}
    singleton_instances_by_factory: dict[Callable[..., Any], Any] = {}
    provided_implementations: set = set()
    active_async_contexts: list[tuple[AbstractAsyncContextManager, Callable]] = []

    async def resolve_one(defn: ComponentDefinition[T]) -> T:
        if defn.factory in singleton_instances_by_factory and defn.factory_builds_singleton:
            return singleton_instances_by_factory[defn.factory]

        if defn.implementation in provided_implementations:
            if not isinstance(defn.implementation, defn.type):
                raise TypeError("Implementation didn't match type")  # pragma: no cover
            return defn.implementation

        # 🔁 Check for already constructed component singleton here
        if defn.factory is None:
            for satisfied_type in defn.satisfied_types:
                if satisfied_type in constructed_instances:
                    return constructed_instances[satisfied_type]

        resolved_args = {}
        for dep_type in defn.dependencies:
            origin = get_origin(dep_type)
            args = get_args(dep_type)

            if origin in {list, set} and args:
                inner_type = args[0]
                for candidate_defn in definitions:
                    if inner_type in candidate_defn.satisfied_types or candidate_defn.type == inner_type:
                        await resolve_one(candidate_defn)

                values = collected_instances.get(inner_type, [])
                resolved_args[dep_type] = (
                    list(values) if origin is list else set(values)
                )
                continue

            matching_defn = next(
                (
                    d
                    for d in definitions
                    if dep_type in d.satisfied_types or d.type == dep_type
                ),
                None,
            )
            if not matching_defn:
                raise ComponentNotFoundError(component_type=dep_type)

            dep_instance = await resolve_one(matching_defn)
            resolved_args[dep_type] = dep_instance

        # Instance construction (factory or constructor)
        if defn.implementation is not None:
            provided_implementations.add(defn.implementation)
            instance_obj = defn.implementation
        elif defn.factory is not None:
            factory_fn = defn.factory
            kwargs = _match_args_by_type(factory_fn, resolved_args)
            if defn.factory_is_async:
                if not inspect.iscoroutinefunction(factory_fn):
                    raise TypeError("factory method was expected to be async")  # pragma: no cover
                instance_obj = await factory_fn(**kwargs)
            else:
                instance_obj = factory_fn(**kwargs)

            if isinstance(instance_obj, AbstractAsyncContextManager):
                if defn.factory_builds_singleton:
                    entered_obj = await instance_obj.__aenter__()
                    singleton_instances_by_factory[defn.factory] = entered_obj
                    instance_obj = entered_obj
                else:
                    entered_obj = await instance_obj.__aenter__()
                    active_async_contexts.append((entered_obj, instance_obj.__aexit__))
                    instance_obj = entered_obj
            elif defn.factory_builds_singleton:
                singleton_instances_by_factory[defn.factory] = instance_obj
        else:
            kwargs = _match_args_by_type(defn.type, resolved_args)
            raw_instance = defn.type(**kwargs)

            if isinstance(raw_instance, AbstractAsyncContextManager):
                entered_instance = await raw_instance.__aenter__()
                instance_obj = entered_instance

                # Assume constructor-based are singleton-like if already cached
                if not any(stype in constructed_instances for stype in defn.satisfied_types):
                    active_async_contexts.append((raw_instance, raw_instance.__aexit__))
            else:
                instance_obj = raw_instance

            for satisfied_type in defn.satisfied_types:
                constructed_instances[satisfied_type] = instance_obj

        for satisfied_type in defn.satisfied_types:
            collected_instances.setdefault(satisfied_type, []).append(instance_obj)

        if not isinstance(instance_obj, defn.type):
            raise TypeError("Instance had unexpected type")  # pragma: no cover
        return instance_obj

    async def resolve_all() -> None:
        for definition in definitions:
            await resolve_one(definition)

    try:
        await resolve_all()
        return collected_instances
    finally:
        for context_instance, aexit in reversed(active_async_contexts):
            await aexit(None, None, None)

def _match_args_by_type(fn: Callable, resolved_deps: dict[type, Any]) -> dict[str, Any]:
    """Match resolved dependency values to parameter names by their annotated type."""
    sig = inspect.signature(fn)
    matched = {}
    for name, param in sig.parameters.items():
        if param.annotation in resolved_deps:
            matched[name] = resolved_deps[param.annotation]
    return matched
