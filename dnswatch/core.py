import time
import logging

from instance_info import InstanceInfo
from dnsproviders import BindProvider, Route53Provider
from gce import GCE
from aws import AWS
from killer import Killer
from misc import Misc


class DNSWatch:
    def __init__(self, config):
        self.logger = logging.getLogger("DNSWatch.Main")

        # Detect cloud provider
        provider = self._detect_provider()

        # Add private & public IPs into config
        ii = InstanceInfo(provider)
        private_ip = ii.get_private_ip()
        public_ip = ii.get_public_ip()
        hostname = ii.get_hostname()
        fqdn = "{}.{}".format(hostname, config["dnsupdate"]["zone"])
        config["host"] = {
            "fqdn": fqdn,
            "private_ip": private_ip,
            "public_ip": public_ip
        }

        # Select DNS provider
        dns_provider = config["dnsupdate"]["provider"]
        self.logger.info("DNS provider is: {}.".format(dns_provider))
        if dns_provider == "bind":
            self.dp = BindProvider(config)
        elif dns_provider == "route53":
            self.dp = Route53Provider(config)
        else:
            self.logger.error("DNS provider {} isn't supported.".format(dns_provider))

    def initial_config(self):
        self.logger.info("Doing initial configuration.")
        self.dp.initial_config()

    def reload_config(self):
        self.logger.info("Doing reload of configuration.")
        self.dp.reload_config()

    def watch(self, pause=10):
        self.logger.info("Starting watch.")
        killer = Killer()
        while True:
            time.sleep(pause)
            if killer.kill_now:
                self.logger.info("Got kill signal, finishing watch.")
                if killer.cleanup:
                    return "kill"
                else:
                    self.logger.warning("Soft kill requested. It means no "\
                        "cleanup of DNS records.")
                    return "softkill"
            if killer.reload_now:
                self.logger.info("Got reload signal, finishing watch.")
                return "reload"
            else:
                self.logger.debug("Sending new watcher.")	
                self.dp.watch()

    def cleanup(self):
        self.logger.info("Cleaning DNS before shutdown.")
        self.dp.cleanup()
        self.logger.info("Cleanup finished.")

    def _detect_provider(self):
        self.logger.info("Detecting cloud provider.")
        provider = "other"
        gce = GCE()
        aws = AWS()

        if gce.is_inside():
            provider = "gce"
        elif aws.is_inside():
            provider = "aws"
        
        self.logger.info("My cloud provider is: {}.".format(provider))
        return provider
