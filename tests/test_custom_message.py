from di.exceptions import (
    ComponentNotFoundError,
    ContainerLockedError,
    CycleDetectedError,
    DuplicateRegistrationError,
)


def test_cycle_detected_error_custom_message():
    exc = CycleDetectedError(component_type=str, message="Custom cycle error")
    assert str(exc) == "Custom cycle error"
    assert exc.component_type is str


def test_component_not_found_error_custom_message():
    exc = ComponentNotFoundError(component_type=int, message="Custom not found")
    assert str(exc) == "Custom not found"
    assert exc.component_type is int


def test_duplicate_registration_error():
    exc = DuplicateRegistrationError(type_or_factory=int, message="Custom not found")
    assert str(exc) == "Custom not found"
    assert exc.type_or_factory is int


def test_container_locked_error():
    exc = ContainerLockedError(message="Custom not found")
    assert str(exc) == "Custom not found"
