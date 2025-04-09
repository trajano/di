import pytest
from di.enums import ComponentScope
from ._types import ComponentDefinition
from ._convert_to_factory import convert_to_factory
from di._util import (
    extract_satisfied_types_from_type,
    extract_dependencies_from_signature,
)
from di.aio_container import AioContainer


class Config:
    def __init__(self):
        self.value = "abc"


class Service:
    def __init__(self, *, config: Config):
        self.config = config


class Consumer:
    def __init__(self, *, service: Service):
        self.service = service


