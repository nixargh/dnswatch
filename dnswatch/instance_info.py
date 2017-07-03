import socket
import fcntl
import struct
import logging

from gce import GCE
from aws import AWS

class InstanceInfo:
    def __init__(self, provider="other"):
        self.logger = logging.getLogger("DNSWatch.InstanceInfo")
        self.provider = provider
        if provider == "gce":
            self.cloud = GCE()
        elif provider == "aws":
            self.cloud = AWS()

    def get_fqdn(self):
        return socket.getfqdn()

<<<<<<< HEAD
    def get_hostname(self):
        """Return only name before first dot."""
        hostname = socket.gethostname()
        if hostname:
            try:
                hostname = hostname.split(".")[0]
            except ValueError:
                pass
            return hostname
        else:
            return None

=======
>>>>>>> 59ed5eec90df781060c3439a5ca2940dcdb5fdb9
    def get_private_ip(self):
        """
        Return one IP address belongs to network interfaces used for
        external connections.
        """
        self.logger.debug("Detecting private IP.")
        ip = None

<<<<<<< HEAD
        if self.provider in ["aws", "gce"]:
=======
        if self.provider == "aws":
            self.logger.error("AWS isn't implemeted yet.")
            raise Exception("AWS isn't implemeted yet.")
        elif self.provider == "gce":
>>>>>>> 59ed5eec90df781060c3439a5ca2940dcdb5fdb9
            ip = self._get_private_ip_cloud()
        else:
            ip = self._get_private_ip_other()

        self.logger.debug("My private IP: {}.".format(ip))
        return ip

    def get_public_ip(self):
        self.logger.debug("Detecting public IP.")
        ip = None

<<<<<<< HEAD
        if self.provider in ["aws", "gce"]:
=======
        if self.provider == "aws":
            self.logger.error("AWS isn't implemeted yet.")
            raise Exception("AWS isn't implemeted yet.")
        elif self.provider == "gce":
>>>>>>> 59ed5eec90df781060c3439a5ca2940dcdb5fdb9
            ip = self._get_public_ip_cloud()
        else:
            ip = self._get_public_ip_other()

        self.logger.debug("My public IP: {}.".format(ip))
        return ip

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
        return ip

    def _get_private_ip_cloud(self):
        return self.cloud.get_private_ip()

    def _get_public_ip_other(self):
        ip = None

        try:
            name = socket.gethostbyaddr(self.private_ip)[0]
            ip = self._query(name, "A", ["8.8.8.8", "8.8.4.4"])[0]
            #ip = self._query(name, "A", ["127.0.1.1"])[0]
        except:
            self.logger.error("Failed to find public IP.")
        return ip

    def _get_public_ip_cloud(self):
        return self.cloud.get_public_ip()

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
