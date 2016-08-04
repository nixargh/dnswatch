#!/usr/bin/env python
# -*- coding: utf-8 -*-
# dnswatch - tool to automate DNS setup
##############################################################################
import sys
import logging
import yaml
import dns.resolver
import dns.tsigkeyring

##############################################################################
logger = None
##############################################################################
class DNSWatch:
    def __init__(self, logger, config):
        self.logger = logger
        self.config = config
        self.keyring = self._create_keyring(config["nsupdate"]["update_key"])

    def initial_config(self):
        self.logger.debug("Doing initial configuration.")
        self.masters = self._get_masters(self.config["nsupdate"]["update_key"]["domain"])
        self.slaves = self._get_slaves(
            self.masters["private"], self.config["nsupdate"]["domain"])

        self._update_zone(self.masters["private"][0], self.private_ip)
        self._update_zone(self.masters["public"][0], self.public_ip)

        self._setup_resolver(self.slaves["private"])

    def watch(self):
        pass

    def cleanup(self):
        pass

    def _create_keyring(self, update_key):
        domain = update_key["domain"]
        key = update_key["key"]
        self.logger.debug(
            "Creating keyring for domain '{}' with key '{}'.".format(
                domain, key))
        return dns.tsigkeyring.from_text({domain: key}) 

    def _get_masters(self, domain):
        self.logger.debug("Getting DNS masters.")

        masters = dict()
        for mtype in ["private", "public"]:
            answer = dns.resolver.query(
                "dns-master-{}.{}".format(mtype, domain), "TXT")
            masters[mtype] = answer[0].strings

        self.logger.debug("Masters: {}".format(masters))
        return masters

    def _get_slaves(self, masters, domain):
        resolver = dns.resolver.Resolver()
        resolver.nameservers = ["146.148.112.135", "104.155.34.12"]
        answer = resolver.query("dns-slave.{}".format(domain), "TXT")
        for st in answer[0].strings:
            print st
        #return self._get_masters(domain)

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
