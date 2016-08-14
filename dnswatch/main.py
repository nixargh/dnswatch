#!/usr/bin/env python
# -*- coding: utf-8 -*-
# dnswatch - tool to automate DNS setup
##############################################################################
import sys
import logging
import yaml
import dns.resolver
import dns.tsigkeyring
import socket
import fcntl
import struct
import re

##############################################################################
logger = None
##############################################################################
class DNSWatch:
    def __init__(self, logger, config):
        self.logger = logger
        self.config = config
        self.keyring = self._create_keyring(config["nsupdate"]["update_key"])
        self.private_ip = self._get_private_ip()
        self.public_ip = self._get_public_ip()

    def initial_config(self):
        self.logger.debug("Doing initial configuration.")
        self.masters = self._get_masters(self.config["nsupdate"]["zone"])
        self.slaves = self._get_slaves(
            self.masters, self.config["nsupdate"]["zone"])

        self._update_zone(self.masters["private"][0], self.private_ip)
        self._update_zone(self.masters["public"][0], self.public_ip)

        self._setup_resolver(self.slaves["private"])

    def watch(self):
        pass

    def cleanup(self):
        pass

    def _get_private_ip(self):
        """
        Return one IP address belongs to network interfaces used for
        external connections.
        """
        self.logger.debug("Detecting private IP.")
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

    def _get_public_ip(self):
        self.logger.debug("Detecting public IP.")
        ip = None

        try:
            name = socket.gethostbyaddr(self.private_ip)[0]
            ip = self._query(name, "A", ["8.8.8.8", "8.8.4.4"])[0]
            #ip = self._query(name, "A", ["127.0.1.1"])[0]
        except:
            self.logger.error("Failed to find public IP.")

        self.logger.debug("My public IP: {}.".format(ip))
        return ip

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

    def _create_keyring(self, update_key):
        name = update_key["name"]
        key = update_key["key"]
        self.logger.debug(
            "Creating keyring for domain '{}' with key '{}'.".format(
                name, key))
        return dns.tsigkeyring.from_text({name: key}) 

    def _get_masters(self, zone):
        self.logger.debug("Getting DNS masters for zone {}.".format(zone))

        masters = dict()
        for mtype in ["private", "public"]:
            try:
                record = "dns-master-{}.{}".format(mtype, zone)
                self.logger.debug("Looking for TXT record {}.".format(record))
                answer = self._query(record, "TXT")
            except dns.resolver.NXDOMAIN:
                upper_zone = zone.split(".", 1)[1]
                record = "dns-master-{}.{}".format(mtype, upper_zone)
                self.logger.debug(
                    "Failed. Checking upper zone {}.".format(upper_zone))
                answer = self._query(record, "TXT")

            self.logger.debug("Got {} masters: {}.".format(mtype, answer))
            masters[mtype] = answer

        self.logger.debug("Masters: {}.".format(masters))
        return masters

    def _get_slaves(self, masters, zone):
        self.logger.debug("Getting DNS slaves for zone {}.".format(zone))

        slaves = dict()
        for stype in masters.keys():
            record = "dns-slave.{}".format(zone)
            self.logger.debug("Looking for TXT record {} at {}.".format(
                record, masters[stype]))
            answer = self._query(
                "dns-slave.{}".format(zone), "TXT", masters[stype])
            slaves[stype] = answer

        self.logger.debug("Slaves: {}.".format(slaves))
        return slaves

    def _query(self, name, rtype="A", nameservers=None):
        result = list()
        resolver = dns.resolver.Resolver()
        if nameservers:
            resolver.nameservers = nameservers

        answers = list()
        try:
            answers = resolver.query(name, rtype)
        except dns.exception.Timeout:
            self.logger.error(
                "Timeout reached while getting {} record {} from {}.".format(
                    rtype, name, nameservers))

        for answer in answers:
            if rtype == "TXT":
                for line in answer.strings:
                    line = line.replace('"', "")
                    result.extend(line.split(","))
            else:
                result.append(answer.address)
        return result

    def _update_zone(self, server, ip):
        pass

    def _setup_resolver(self, servers):
        pass

##############################################################################
def configure_logger(name):
    global logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s %(process)d %(name)-16s %(levelname)-8s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def parse_config(config_file):
    logger.debug("Loading configuration from {}".format(config_file))
    with open(config_file, "r") as f:
        config = yaml.load(f)

    logger.debug("Configuration loaded.")    
    return config

def main():
    logger = configure_logger("DNSWatch")
    logger.debug("Starting.")

    config = parse_config(sys.argv[1])

    dw = DNSWatch(logger, config)
    dw.initial_config()
    dw.watch()
    dw.cleanup()

    logger.debug("Finished successfully.")
    sys.exit(0)

if __name__ == '__main__':
    main()
