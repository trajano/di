# di

A lightweight and extensible **Dependency Injection (DI)** framework for Python.

This project provides a minimalistic yet powerful way to define and resolve dependencies in your Python applications using container-based injection and a class decorator for automatic registration.

---

## Features

- 📦 **Component Registration**: Use `@component` to register classes into a DI container.
- 🔄 **Automatic Dependency Resolution**: Constructor dependencies are resolved and injected automatically.
- 🧱 **Custom Containers**: Define and manage multiple containers for different contexts.
- 🔍 **Type-safe Lookup**: Retrieve components by type using indexing, `get_component`, or `get_optional_component`.
- 🔒 **Immutable After Use**: Containers lock after first resolution to guarantee consistency.

---

## Installation

> No external dependencies are required. Just include the `di` module in your project.

---

## Usage

### Registering Components

```python
from di import component

@component
class ServiceA:
    ...

@component
class ServiceB:
    def __init__(self, *, service_a: ServiceA):
        self.service_a = service_a
```

The decorator automatically registers your class in the default container and resolves constructor dependencies.

---

### Custom Containers

```python
from di import BasicContainer, component

custom_container = BasicContainer()

@component(container=custom_container)
class CustomService:
    ...
```

You can register components in any `Container`-compatible instance.

---

### Retrieving Components

```python
from di.default_container import default_container

service = default_container[ServiceB]
# or
service = default_container.get_component(ServiceB)
```

You can also retrieve all matching components:

```python
services = default_container.get_components(ServiceA)
```

---

## Testing

The project uses `pytest`. To run the tests:

```bash
pytest
```

Test files are located in:

- `test_container.py`
- `test_container_multiple.py`
- `test_alternate_container.py`
- `test_default_container.py`

---

## API Overview

### `@component`

Registers a class into a DI container.

```python
@component
class MyService: ...
```

Or with a specific container:

```python
@component(container=my_container)
class MyService: ...
```

---

### `Container` Interface

Supports:

- `add_component_type(component_cls)`
- `get_component(cls)`
- `get_optional_component(cls)`
- `get_components(cls)`
- Indexing: `container[cls]`
- Membership: `cls in container`

---

## License

This project is licensed under the **Eclipse Public License 2.0**.  
See the [LICENSE](LICENSE) file for more information.
```
