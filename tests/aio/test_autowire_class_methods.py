from di.aio import autowired, component


@component
class Config:
    def __init__(self):
        self.value = "example"


class Logger:
    @autowired
    async def log(self, *, config: Config):
        print("Logging with config value:", config.value)


async def test_something():
    logger = Logger()
    await logger.log()  # Automatically injects Config from the default container
