import requests

from log import Log

class GCE:

    def __init__(self):
        self.logger = Log.get_logger(self.__class__.__name__)
        self.metadata = { 
                "url": "http://metadata.google.internal/computeMetadata/v1",
                "headers": { "Metadata-Flavor": "Google" }
            }

    def get_private_ip(self):
        return self._get_data("instance/network-interfaces/0/ip")

    def get_public_ip(self):
        return self._get_data("instance/network-interfaces/0/access-configs/0/external-ip")

    def _get_data(self, path):
        data = None
        request = "{}/{}".format(self.metadata["url"], path)
        try:
            data = requests.get(request, headers=self.metadata["headers"])
        except requests.exceptions.ConnectionError as e:
            self.logger.error("Connection to {} failed: {}.".format(request, e[0][1]))
        return data
