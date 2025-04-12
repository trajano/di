# di_aio

A lightweight and extensible **Dependency Injection (DI)** framework for Python.

This project offers a minimalistic yet powerful approach to defining and resolving dependencies in Python applications using container-based injection and class decorators for automatic registration.

---

## Features

- 📦 **Component Registration** — Use `@component` to register classes into a DI container.
- ⚙️ **Method Injection** — Use `@autowired` to inject dependencies into arbitrary methods or functions.
- 🔄 **Automatic Dependency Resolution** — Constructor dependencies are automatically resolved and injected.
- 🧱 **Custom Containers** — Manage multiple containers for different contexts or scopes.
- 🔍 **Type-safe Lookup** — Retrieve components by type using indexing, `get_component`, or `get_optional_component`.
- 🔒 **Immutable Containers** — Containers become immutable after first use to ensure consistent state.
- ⏳ **Async Support** — Works seamlessly with `async def` functions and methods, including `@autowired` injection.

---

## Installation

> Use the `di.aio` module for asyncio-compatible dependency injection in your project.
> The synchronous API is available in `di` and is documented in [di/basic\_container/README.md](di_aio/basic_container/README.md).

---

## Usage

> For legacy usage examples without asyncio support, see: [di/basic\_container/README.md](di_aio/basic_container/README.md).

## Example

This is an example of how to register components using decorators and autowiring.

```python
import asyncio
from di_aio.aio import component, autowired


@component
class AsyncService:
    async def fetch(self):
        await asyncio.sleep(0.1)
        return "Fetched async result"


class AsyncWorker:
    @autowired
    async def work(self, *, async_service: AsyncService):
        result = await async_service.fetch()
        print("Result:", result)


worker = AsyncWorker()
asyncio.run(worker.work())
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

