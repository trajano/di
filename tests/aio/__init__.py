"""
Dependency Injection Framework
===============================

This framework defines a dependency injection system
that supports container and function-scoped components with context-managed
lifetimes.

Key Features:
-------------
- **@component**: Registers a type or instance with the default container.
- **@factory**: Registers a factory that produces a component. The factory declares
  dependencies through keyword arguments. Optional scope parameter.
- **@autowired**: Injects dependencies into an async function based on type hints.
  Supports function-scoped lifecycle with automatic cleanup.
- **default_container**: Provides a globally accessible AioContainer used by decorators.
- **Lifecycle Enforcement**: Initializes and disposes components through async
  context management.

Component Registration:
------------------------
Register components to a container using the following methods:
- `add_component_type(cls: type)` — registers a concrete class as its own provider.
- `add_component_implementation(instance: Any)` — registers an existing instance.
- `add_component_factory(factory: Callable, scope: ComponentScope)` — registers
  a factory function that produces a component (container- or function-scoped).

Component Normalization:
------------------------
The container normalizes all sources into async factories:
- **Types** become factories with extracted keyword dependencies.
- **Instances** are wrapped in no-op async context managers.
- **Sync factories** are converted to async factories.
- **Return values** are wrapped in context managers if necessary.

Validation Rules:
-----------------
- Every component (container- and function-scoped) must have its dependencies
  satisfied.
- The system rejects cyclic dependencies. On detection, it raises
  `CycleDetectedError`.
- Container-scoped components must only depend on other container-scoped components.
- Multi-injection dependencies (`list[T]`, `set[T]`) require all satisfying
  components to be container-scoped.

Resolution:
-----------
- The system orders components topologically to guarantee valid instantiation
  sequences.
- For multi-injection (`list[T]` / `set[T]`), the container resolves all matching
  container-scoped components.
- The system resolves function-scoped components per function call and disposes
  of them after execution.

Container Lifecycle (AioContainer):
-----------------------------------
The container follows these lifecycle phases:
- `INITIALIZING`: Accepts component registrations.
- `VALIDATING`: Checks all definitions for integrity and completeness.
- `SERVICING`: Makes container-scoped components available for resolution.
- `RESOLVING`: Resolves dependencies for autowired functions.
- `RUNNING`: Executes user-defined logic.
- `CLOSING`: Cleans up context-managed resources.

The container resolves and enters all container-scoped components during
`__aenter__()`. It stores them as `ContainerScopeComponent` entries containing:
- The satisfied types
- The active context manager
- The resolved instance

During `__aexit__()`, it exits each component’s context manager in reverse order.

Behavioral Notes:
------------------
- The container performs validation eagerly on entry.
- It constructs container-scoped components eagerly in topological order.
- The system prohibits cycles and fails fast with clear error reporting.
- Dependency resolution uses only declared type hints. It performs no runtime
  introspection.

Lifecycle Usage:
----------------
```python
async def main():
    async with AioContainer() as container:
        di.set_default_container(container)
        await your_entrypoint()

# OR
async def run(container: AioContainer):
    await something(container)

asyncio.run(di.with_container(run))
```
"""
