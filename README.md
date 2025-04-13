# di_aio

A Dependency Injection (DI) framework for Python that works with AsyncIO.

---

## Features

- 📦 **reasonable defaults** — Uses default instances (which can be overridden) to satisfy general usage.
- 📦 **Component Registration** — Use `@component` to register classes into a DI container.
- ⚙️ **Method Injection** — Use `@autowired` to inject dependencies into arbitrary methods or functions.
- 🔄 **Automatic Dependency Resolution** — Constructor dependencies are automatically resolved and injected.
- 🧱 **Custom Containers** — Manage multiple containers for different contexts or scopes.
- 🔍 **Type-safe Lookup** — Retrieve components by type using indexing, `get_instance`, `get_optional_instance` or `get_instances`.
- 🔒 **Immutable Containers** — Containers become immutable after first use to ensure consistent state.
- ⏳ **Async Support** — Works seamlessly with `async def` functions and methods, including `@autowired` injection.

---

## Installation

FYI this project is not published to pypi.  Use uv workspaces and git submodules to integrate with your app.

---

## Usage



## Example

This is an example of how to register components using decorators and autowiring.

```python
import asyncio
from di_aio import autowired, component, default_container


@component
class AsyncService:
    async def fetch(self):
        await asyncio.sleep(0.1)
        return "Fetched async result"

@component
class AsyncWorker:
    @autowired
    async def work(self, *, async_service: AsyncService):
        result = await async_service.fetch()
        print("Result:", result)

async def service():
    async with default_container.context() as context:
        worker = await context.get_instance(AsyncWorker)
        await worker.work()

asyncio.run(service())
```

The `@autowired` decorator can be used outside of classes as well

```python
import asyncio
from di_aio.aio import component, autowired


@component
class AsyncService:
    async def fetch(self):
        await asyncio.sleep(0.1)
        return "Fetched async result"


@autowired
async def work(self, *, async_service: AsyncService):
    result = await async_service.fetch()
    print("Result:", result)


asyncio.run(work())
```
---

## License

This project is licensed under the **Eclipse Public License 2.0**.
See the [LICENSE](LICENSE) file for more details.

