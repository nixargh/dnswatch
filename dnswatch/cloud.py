import requests
import logging

class Cloud:

    def __init__(self, metadata):
        self.logger = logging.getLogger("DNSWatch.Cloud")
        self.metadata = metadata

    def is_inside(self):
        return self.get_data("hostname").ok

    def get_data(self, path):
        data = None
        request = "{}/{}".format(self.metadata["url"], path)
        try:
            data = requests.get(request, headers=self.metadata["headers"])
        except requests.exceptions.ConnectionError as e:
            self.logger.error("Connection to {} failed: {}.".format(request, e[0][1]))
        return data
