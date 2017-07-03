import os
import yaml
import logging

class Config:
    def __init__(self):
        self.logger = logging.getLogger("DNSWatch.Config")
        self.dnsprovider = None
        self.dnszone = None

    def read(self, config_file):
        self.logger.debug("Loading configuration from {}".format(config_file))
        with open(os.path.realpath(config_file), "r") as f:
            config = yaml.load(f)

        # For backward compatibility with 0.2.* config
        if "nsupdate" in config:
            config["dnsupdate"] = config.pop("nsupdate")

        # DNS query timeout is optional
        if not "timeout" in config["dnsupdate"]:
            config["dnsupdate"]["timeout"] = 10

        # TTL is optional
        if not "ttl" in config["dnsupdate"]:
            config["dnsupdate"]["ttl"] = 300

        # Aliases is optional
        if not "alias" in config["dnsupdate"]:
            config["dnsupdate"]["alias"] = dict()

        # Do not rewrite DNS provider and zone under reload
        if self.dnsprovider:
            new_dnsprovider = config["dnsupdate"]["provider"]
            if self.dnsprovider != new_dnsprovider:
                self.logger.warning(
                    "DNS provider change ignored by reload: '{}' -> '{}'.".format(
                        self.dnsprovider, new_dnsprovider))
                config["dnsupdate"]["provider"] = self.dnsprovider
        else:
            self.dnsprovider = config["dnsupdate"]["provider"]

        if self.dnszone:
            new_dnszone = config["dnsupdate"]["zone"]
            if self.dnszone != new_dnszone:
                self.logger.warning(
                    "DNS zone change ignored by reload: '{}' -> '{}'.".format(
                        self.dnszone, new_dnszone))
                config["dnsupdate"]["zone"] = self.dnszone
        else:
            self.dnszone = config["dnsupdate"]["zone"]

        self.logger.debug("Configuration loaded.")    
        return config
