import requests
import logging

from cloud import Cloud

class AWS:

    def __init__(self):
        self.logger = logging.getLogger("DNSWatch.AWS")
        metadata = { 
                "url": "http://169.254.169.254/latest/meta-data",
                "headers": ""
            }
        self.cloud = Cloud(metadata)

    def is_inside(self):
        return self.cloud.is_inside()
