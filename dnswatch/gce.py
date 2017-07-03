import requests
import logging

from cloud import Cloud

class GCE:

    def __init__(self):
        self.logger = logging.getLogger("DNSWatch.GCE")
        metadata = { 
                "url": "http://169.254.169.254/computeMetadata/v1/instance",
                "headers": { "Metadata-Flavor": "Google" }
            }
        self.cloud = Cloud(metadata)

    def is_inside(self):
        return self.cloud.is_inside()

    def get_private_ip(self):
        return self.cloud.get_data("network-interfaces/0/ip").text

    def get_public_ip(self):
        return self.cloud.get_data("network-interfaces/0/access-configs/0/external-ip").text
