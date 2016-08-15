import socket
import fcntl
import struct

from log import Log
from gce import GCE

class InstanceInfo:
    def __init__(self, provider="other"):
        self.logger = Log.get_logger(self.__class__.__name__)
        self.provider = provider

    def get_private_ip(self):
        """
        Return one IP address belongs to network interfaces used for
        external connections.
        """
        self.logger.debug("Detecting private IP.")
        if self.provider == "aws":
            pass
        elif self.provider == "gce":
            pass
        else:
            return self._get_private_ip_other()

    def _get_private_ip_other(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ip = None

        interfaces = self._get_interfaces()

        if len(interfaces) > 1:
            self.logger.debug(
                "More than one interface found, using external "\
                    "connect to find proper IP.")
            # First method        
            s.connect(("8.8.8.8", 53))
            ip = s.getsockname()[0]
        else:
            interface = interfaces[0]

            # Second method        
            ip = socket.inet_ntoa(fcntl.ioctl(
                s.fileno(),
                0x8915,  # SIOCGIFADDR
                struct.pack('256s', interface))[20:24])

        s.close()
        self.logger.debug("My private IP: {}.".format(ip))
        return ip

    def get_public_ip(self):
        self.logger.debug("Detecting public IP.")
        if self.provider == "aws":
            pass
        elif self.provider == "gce":
            self._get_public_ip_gce()
        else:
            return self._get_public_ip_other()

    def _get_public_ip_other(self):
        ip = None

        try:
            name = socket.gethostbyaddr(self.private_ip)[0]
            ip = self._query(name, "A", ["8.8.8.8", "8.8.4.4"])[0]
            #ip = self._query(name, "A", ["127.0.1.1"])[0]
        except:
            self.logger.error("Failed to find public IP.")

        self.logger.debug("My public IP: {}.".format(ip))
        return ip

    def _get_public_ip_gce(self):
        gce = GCE()
        return gce.get_public_ip()

    def _get_interfaces(self):
        self.logger.debug("Getting network interfaces.")
        interfaces = list()
        with open("/proc/net/dev", "r") as dev_file:
            devices = dev_file.readlines()
            for dev in devices[2:]:
                dev_name = dev.split(":")[0].strip()
                if dev_name != "lo":
                    interfaces.append(dev_name)
        self.logger.debug("Interfaces: {}.".format(interfaces))
        return interfaces
