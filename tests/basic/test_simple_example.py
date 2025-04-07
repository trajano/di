import logging

from di import component, default_container

log=logging.getLogger(__name__)

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
    service_b = default_container[ServiceB]
    log.info(service_b.call_a())  # Output: Hello from ServiceA
