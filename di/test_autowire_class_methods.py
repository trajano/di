from di import component, autowired

@component
class Config:
    def __init__(self):
        self.value = "example"

class Logger:
    @autowired
    def log(self,*, config: Config):
        print("Logging with config value:", config.value)

def test_something():
    logger = Logger()
    logger.log()  # Automatically injects Config from the default container