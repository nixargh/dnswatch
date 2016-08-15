import requests

from log import Log
from cloud import Cloud

class AWS:

    def __init__(self):
        self.logger = Log.get_logger(self.__class__.__name__)
        metadata = { 
                "url": "http://169.254.169.254/latest/meta-data",
                "headers": ""
            }
        self.cloud = Cloud(metadata)

    def is_inside(self):
        return self.cloud.is_inside()
