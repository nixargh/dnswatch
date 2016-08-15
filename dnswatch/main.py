#!/usr/bin/env python
# -*- coding: utf-8 -*-
# dnswatch - tool to automate DNS setup
##############################################################################
import sys
import dns.resolver
import dns.tsigkeyring
import re

from instance_info import InstanceInfo
from log import Log
from config import Config
##############################################################################
class DNSWatch:
    def __init__(self, logger, config):
        self.logger = logger
        self.config = config
        self.keyring = self._create_keyring(config["nsupdate"]["update_key"])

        ii = InstanceInfo("gce")
        self.private_ip = ii.get_private_ip()
        self.public_ip = ii.get_public_ip()

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
def main():
    logger = Log.get_logger("DNSWatch")
    logger.debug("Starting.")

    c = Config()
    config = c.read(sys.argv[1])

    dw = DNSWatch(logger, config)
    dw.initial_config()
    dw.watch()
    dw.cleanup()

    logger.debug("Finished successfully.")
    sys.exit(0)

if __name__ == '__main__':
    main()
