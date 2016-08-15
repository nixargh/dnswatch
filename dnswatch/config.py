import yaml

from log import Log

class Config:
    def __init__(self):
        self.logger = Log.get_logger(self.__class__.__name__)

    def read(self, config_file):
        self.logger.debug("Loading configuration from {}".format(config_file))
        with open(config_file, "r") as f:
            config = yaml.load(f)

        self.logger.debug("Configuration loaded.")    
        return config
