import logging
import sys

class Log:

    @staticmethod
    def get_logger(name):
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s %(process)d %(name)-16s %(levelname)-8s %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
