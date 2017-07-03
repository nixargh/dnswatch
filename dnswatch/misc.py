import logging

class Misc:

    def __init__(self, ext_logger):
        self.ext_logger = ext_logger
        self.logger = logging.getLogger("DNSWatch.Misc")

    def die(self, message):
        self.ext_logger.error(message + ".")
        self.logger.debug("Raising exception.")
        raise Exception(message)
