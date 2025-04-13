import inspect
from collections.abc import Callable
from typing import Any, get_args, get_origin


def extract_dependencies_from_callable(
    fn: Callable[..., Any],
) -> tuple[set[type], set[type]]:
    """Extracts mandatory constructor dependencies and collection dependencies from
    a callable (e.g., __init__ or a factory).

    Dependencies must be keyword-only parameters with type annotations and no defaults.
    Collection dependencies are recognized as `list[T]` or `set[T]`.

    :param fn: The function or method to inspect.
    :return: A tuple of (single_dependencies, collection_dependencies)
    """
    single_deps: set[type] = set()
    collection_deps: set[type] = set()

    for param in inspect.signature(fn).parameters.values():
        if param.kind != param.KEYWORD_ONLY:
            continue
        if param.annotation is inspect.Parameter.empty:
            continue
        if param.default is not inspect.Parameter.empty:
            continue

        annotation = param.annotation
        origin = get_origin(annotation)
        args = get_args(annotation)

        if origin in (list, set) and args:
            collection_deps.add(args[0])
        else:
            single_deps.add(annotation)

    return single_deps, collection_deps
