from di import component, default_container


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


def test_simple_example():
    # Retrieving a component from the default container
    service_b = default_container[ServiceB]
    print(service_b.call_a())  # Output: Hello from ServiceA
