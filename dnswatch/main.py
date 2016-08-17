#!/usr/bin/env python
# -*- coding: utf-8 -*-
# dnswatch - tool to automate DNS setup
##############################################################################
import sys

from log import Log
from instance_info import InstanceInfo
from config import Config
from gce import GCE
from aws import AWS
from dnsops import DNSOps
from dhclient import DHClient
##############################################################################
class DNSWatch:
    def __init__(self, logger, config):
        self.logger = logger
        self.config = config

        provider = self._detect_provider()
        ii = InstanceInfo(provider)
        self.private_ip = ii.get_private_ip()
        self.public_ip = ii.get_public_ip()
        self.fqdn = ii.get_fqdn()

        self.dnso = DNSOps(config["nsupdate"])
        self.dnso.setup_key()

    def initial_config(self):
        self.logger.debug("Doing initial configuration.")

        self.masters = self.dnso.get_masters()
        self.slaves = self.dnso.get_slaves(self.masters)

        self.dnso.update_host(self.masters["private"][0], self.fqdn, self.private_ip, ptr=True)
        self.dnso.update_host(self.masters["public"][0], self.fqdn, self.public_ip)

        self._setup_resolver(self.slaves["private"], [self.config["nsupdate"]["zone"]])

    def watch(self):
        pass

    def cleanup(self):
        pass

    def _detect_provider(self):
        self.logger.debug("Detecting cloud provider.")
        provider = "other"
        gce = GCE()
        aws = AWS()

        if gce.is_inside():
            provider = "gce"
        elif aws.is_inside():
            provider = "aws"
        
        self.logger.debug("My cloud provider is: {}.".format(provider))
        return provider

    def _setup_resolver(self, servers, domain):
        self.logger.debug("Configuring local resolver with: NS={}; domain={}.".format(servers, domain))
        dhcl = DHClient()
        dhcl.set_nameserver(servers)
        dhcl.set_search(domain)
        dhcl.renew_lease()

##############################################################################
def main():
    if len(sys.argv) < 2:
        print("Configuration file not specified.\n\tusage: dnswatch config.yaml")
        sys.exit(2)

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
