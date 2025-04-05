# di

A lightweight and extensible **Dependency Injection (DI)** framework for Python.

This project provides a minimalistic yet powerful way to define and resolve dependencies in your Python applications using container-based injection and a class decorator for automatic registration.

---

## Features

- 📦 **Component Registration**: Use `@component` to register classes into a DI container.
- ⚙️ **Method Injection**: Use `@autowired` to inject dependencies into arbitrary methods or functions.
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
from di.default_container import default_container

@component
class ServiceA:
    def greet(self):
        return "Hello from ServiceA"

@component
class ServiceB:
    def __init__(self, *, service_a: ServiceA):
        self.service_a = service_a

    def call_a(self):
        return self.service_a.greet()

# Retrieving a component from the default container
service_b = default_container[ServiceB]
print(service_b.call_a())  # Output: Hello from ServiceA
```

---

### Method Injection with `@autowired`

Use the `@autowired` decorator to inject dependencies into any function or method using parameter type hints.

```python
from di import component, autowired

@component
class Config:
    def __init__(self):
        self.value = "example"

class Logger:
    @autowired
    def log(self, *, config: Config):
        print("Logging with config value:", config.value)

logger = Logger()
logger.log()  # Automatically injects Config from the default container
```

The `@autowired` decorator resolves arguments from the default container (or a specified one), allowing clean and decoupled code even for non-component functions.

---

## License

This project is licensed under the **Eclipse Public License 2.0**.\
See the [LICENSE](LICENSE) file for more information.

