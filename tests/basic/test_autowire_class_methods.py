from di import autowired, component


@component
class Config:
    def __init__(self):
        self.value = "example"


class Logger:
    @autowired
    def log(self, *, config: Config):
        print("Logging with config value:", config.value)


def test_something():
    logger = Logger()
    # Automatically injects Config from the default container
    logger.log()
