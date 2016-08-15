import requests

from log import Log

class Cloud:

    def __init__(self, metadata):
        self.logger = Log.get_logger(self.__class__.__name__)
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
