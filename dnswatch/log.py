import logging
import sys
import os

class Log:

    @staticmethod
    def get_logger(name, log_level="DEBUG", log_file=None):
        logger = logging.getLogger(name)
        logger.setLevel(eval("logging.{}".format(log_level.upper())))
        if log_file:
            log_dir = os.path.dirname(log_file)
            if not os.path.isdir(log_dir):
                os.makedirs(log_dir)
            handler = logging.FileHandler(log_file)
        else:
            handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s %(process)d %(name)-22s %(levelname)-8s %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
