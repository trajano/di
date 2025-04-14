import inspect
import typing
from types import NoneType, UnionType
from typing import Any

from di_aio._util import maybe_dependency
from di_aio.types import ComponentDefinition


def maybe_collection_dependency(
    param: inspect.Parameter,
    definition: ComponentDefinition,
) -> bool:
    dep_type = param.annotation
    origin = typing.get_origin(dep_type)
    args = typing.get_args(dep_type)

    is_collection = origin in (list, set)
    if len(args) == 0:
        return False
    is_arg_in_collection_dependencies = args[0] in definition.collection_dependencies
    return is_collection and is_arg_in_collection_dependencies


def maybe_optional_dependency(param: inspect.Parameter) -> bool:
    dep_type = param.annotation
    origin = typing.get_origin(dep_type)
    args = typing.get_args(dep_type)

    return origin == UnionType and NoneType in args


def extract_kwargs_from_type_constructor(
    definition: ComponentDefinition[Any], constructed: dict[type, Any]
) -> dict[str, Any]:
    if definition.constructor:
        sig = inspect.signature(definition.constructor)
    else:
        sig = inspect.signature(definition.type.__init__)
    kwargs = {}
    for name, param in sig.parameters.items():
        # Only consider typed keyword-only parameters without defaults
        if not maybe_dependency(param):
            continue

        dep_type = param.annotation
        args = typing.get_args(dep_type)

        if maybe_collection_dependency(param, definition):
            expected_type = args[0]
            kwargs[name] = [
                instance
                for typ, instance in constructed.items()
                if isinstance(instance, expected_type)
            ]
            continue
        if maybe_optional_dependency(param):
            expected_type = args[0]
            candidates = [
                instance
                for typ, instance in constructed.items()
                if isinstance(instance, expected_type)
            ]
            if len(candidates) == 0:
                kwargs[name] = None
            elif len(candidates) == 1:
                kwargs[name] = candidates[0]
            else:
                msg = "multiple candidates found"
                raise LookupError(msg)
            continue
        kwargs[name] = constructed[dep_type]
    return kwargs
