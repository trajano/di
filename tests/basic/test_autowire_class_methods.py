import logging

from di import autowired, component

log=logging.getLogger(__name__)


@component
class Config:
    def __init__(self):
        self.value = "example"


class Logger:
    @autowired
    def log(self, *, config: Config):
        log.info("Logging with config value: %s", config.value)


def test_something():
    logger = Logger()
    # Automatically injects Config from the default container
    logger.log()
