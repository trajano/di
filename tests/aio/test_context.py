"""
High-Level Design: Dependency Injection Container

This design addresses scoped lifetimes, context-managed components, factory normalization, and container state management.

==========================================
SCOPE MODEL
==========================================

Supported scopes:
- "container": Singleton-like. One instance for container lifetime.
- "function" : Transient. New instance per call to `resolve()`.

Scope rules:
- Container-scoped components:
  - May only depend on other container-scoped components.
  - Must raise ContainerInitializationError if violated.
- Function-scoped components:
  - May depend on both container- and function-scoped components.

==========================================
CONTEXT MANAGEMENT
==========================================

All components are accessed through async context managers:
- If a component does NOT implement AbstractAsyncContextManager,
  it will be wrapped in a no-op async context manager.

No-op Context Manager:

class NoOpAsyncContext:
    def __init__(self, value):
        self._value = value

    async def __aenter__(self):
        return self._value

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

==========================================
COMPONENT SOURCES
==========================================

Terminology:
- component source: a factory function, a type, or a literal instance.
- factory method: a `def` or `async def` that returns a component instance.
- component: the result of the factory method.
- container-scoped components: components that live for the container's lifetime.

All component sources are normalized into `async def` factory functions.

Note: If a provided factory is a synchronous function (`def`), it will
be automatically wrapped into an `async def` to ensure a consistent
async resolution flow. This avoids the need to handle separate code
paths for sync and async factories.

Three levels of factory decoration exist:

1. **Type-based Component Source**:
   - If the source is a class/type, the system introspects its `__init__` method.
   - All keyword-only parameters (with no default) are extracted as dependencies.
   - A factory is generated as:

     Example:

     class A:
         def __init__(self, *, x: Boo):
             ...

     becomes:

         def factory(x: Boo) -> A:
             return A(x=x)

2. **Registered Implementation Source**:
   - If a literal instance is provided as the component source, it is always
     wrapped in a no-op async context manager using a factory that returns it.
   - This wrapping occurs even if the instance is an AbstractAsyncContextManager.
   - This ensures that the container lifecycle never interferes with externally
     created or manually managed instances.

3. **Context Wrapping of Factory Output**:
   - Once the component factory is resolved, the resulting object is checked.
   - If it **is not** an instance of `contextlib.AbstractAsyncContextManager`,
     it is wrapped in a no-op async context manager.
   - This ensures all components—regardless of origin—can be used with
     `async with`.
   - If it **is** a context manager, it is passed through unchanged.

==========================================
SCENARIO MATRIX
==========================================

+-------------+-------------------+-----------------------------+
| Scope       | Context Managed   | Example                     |
+-------------+-------------------+-----------------------------+
| Container   | No                | Config object               |
| Container   | Yes               | DB pool                     |
| Function    | No                | DTO factories               |
| Function    | Yes               | Request resources           |
+-------------+-------------------+-----------------------------+

==========================================
CONTAINER LIFECYCLE STATES
==========================================

(States are for documentation and tracking; may not be explicitly coded.)

- INITIALIZING:
  - Component registration phase.
  - Component sources are added, duplicate registration disallowed.
  - Dependencies and satisfied types are computed.

- VALIDATING:
  - Triggered by the first `get_component`/`resolve()`.
  - Container-scoped components are all resolved and instantiated.
  - Function-scope components are validated but not instantiated.

- SERVICING:
  - Transition occurs after successful validation.
  - Container is now operational for normal `resolve()` calls.

- RESOLVING:
  - Actively resolving a function-scoped component.
  - Failures in this state raise and propagate exceptions.
  - Failures bubble to the container's async context manager.

- RUNNING:
  - Resolution succeeded.
  - Objects are live and available within their context-managed scope.
  - After completion, the container returns to the SERVICING state for
    further operations.

- CLOSING:
  - Invoked during container's `__aexit__()`.
  - Triggers teardown of all container-scoped objects (if context managed).

==========================================
BEHAVIORAL NOTES
==========================================
- Minimal design: The container is intentionally minimal. It avoids features
  such as component tagging, runtime overrides, diagnostics, introspection
  utilities, or custom shutdown hooks.

- Only context-managed components: The container supports lifecycle handling
  only for components that are `AbstractAsyncContextManager` instances. Others
  are wrapped to ensure compatibility, but no additional shutdown behavior
  is introduced.

- Multi-type injection supported: Injection targets may include `list[T]` or
  `set[T]`, allowing multiple implementations of a type to be resolved into
  a collection.


- No lazy-loading: All container-scoped components are initialized upfront.
- No retries: Resolution failure results in exception propagation.
- No cycle detection: Dependency cycles are not checked. Developers must avoid
  introducing cyclic references unless they are explicitly handling them (e.g.,
  via forward references or `__future__.annotations`).

"""
