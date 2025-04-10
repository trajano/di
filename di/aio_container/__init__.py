"""
Dependency Injection Framework
===============================

This package provides a coroutine-friendly dependency injection system
for Python 3.11+ using `async with` lifecycle management.

Overview
--------
This DI system allows for automatic dependency resolution using type hints
from constructors and factory functions. Components can be registered with
container-wide or function-scoped lifecycles.

The container enforces initialization order via topological sorting,
detects cyclic or unsatisfied dependencies, and supports contextual
clean-up through async context managers.

Key Components
--------------

- **ConfigurableAioContainer**:
    Accepts registration of types, instances, or factories before initialization.
    Can be finalized into an `AioContainer` for runtime resolution.

- **AioContainer**:
    Finalized container that supports dependency resolution and manages component
    lifecycles.

- **default_aio_container**:
    A global container used by decorators such as `@component`, `@factory`, and
    `@autowired`.

- **@component**:
    Registers a type or instance into the default container before execution.

- **@factory**:
    Registers a factory (sync or async) that declares dependencies via keyword-only arguments.
    Supports configurable lifecycles (container or function scoped).

- **@autowired**:
    Decorator that injects dependencies into `async def` functions using a specified container.
    Automatically resolves dependencies at call time and handles function-scoped lifetimes.

Lifecycle Phases
----------------
1. **INITIALIZING** — Container accepts component definitions.
2. **VALIDATING** — Ensures correctness of dependencies and lifecycle scoping.
3. **SERVICING** — Constructs and enters container-scoped components.
4. **RESOLVING** — Resolves dependencies for autowired functions.
5. **RUNNING** — Executes user application logic.
6. **CLOSING** — Cleans up container-scoped resources in reverse order.

Supported Dependency Types
---------------------------
- **Direct Dependencies** — Injected by type (e.g., `*, db: Database`)
- **Optional Dependencies** — Type annotated with `Optional[T]` or `T | None`
- **Collection Dependencies** — `list[T]` or `set[T]` inject all matching
  container-scoped components

Constraints
-----------
- Container-scoped components must only depend on other container-scoped components.
- Function-scoped components may depend on either scope.
- All multi-injection dependencies must be satisfied only by container-scoped components.
- Cyclic dependencies are detected and rejected.

Usage
-----
Example of configuring and running with a custom container:

.. code-block:: python

    async def main():
        config = ConfigurableAioContainer()
        config.add_component_type(MyService)
        container = AioContainer(config.get_definitions())
        async with container:
            await entrypoint()

    asyncio.run(main())

You may also use the decorators directly with the default container:

.. code-block:: python

    @component
    class MyConfig: ...

    @factory
    def make_service(*, config: MyConfig) -> Service: ...

    @autowired
    async def handler(*, service: Service): ...

    await handler()
"""

from .aio_container import AioContainer
from .autowired import autowired, autowired_with_container
from .component import component
from .configurable_container import ConfigurableAioContainer
from .container import Container
from .default_container import default_container
from .factory import factory

__all__ = [
    "AioContainer",
    "ConfigurableAioContainer",
    "Container",
    "autowired",
    "autowired_with_container",
    "component",
    "default_container",
    "factory",
]
