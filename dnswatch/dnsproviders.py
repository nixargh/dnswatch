import logging
import re
import dns.reversename

from dnsops import DNSOps
from route53 import Route53
from dhclient import DHClient
from misc import Misc
        

class Provider:

    @staticmethod
    def _look_for_alias(hostname, zone, alias_dict):
        """Check if hostname match any alias"""
        aliases_list = None
        for host_re, aliases in alias_dict.iteritems():
            match = re.match(host_re, hostname)
            if match:
                host = match.group(0)
                aliases_list = [ alias + "." + zone for alias in aliases ]
        return aliases_list

    @staticmethod
    def _ensure_fqdn(name):
        """Make a proper FQDN from name"""
        if name[-1:] != ".":
            return "%s." % name
        else:
            return name


class BindProvider:

    def __init__(self, config):
        self.logger = logging.getLogger("DNSWatch.BindProvider")
        self.misc = Misc(self.logger)
        self.dhcl = DHClient()
        self.dnso = DNSOps(config["dnsupdate"])

        self.zone = config["dnsupdate"]["zone"]
        self.fqdn = config["host"]["fqdn"]
        self.private_ip = config["host"]["private_ip"]
        self.public_ip = config["host"]["public_ip"]
        self.alias_dict = config["dnsupdate"]["alias"]
        self.aliases = None

    def initial_config(self):
        """To do on start"""
        self._initial_config_wo_resolvers()

        if len(self.slaves["private"]) > 0:
            self._setup_resolver(
                self.slaves["private"], [self.zone])
        else:
            self.misc.die("No private DNS slaves found: {}.".format(self.slaves))

    def reload_config(self):
        """To do on reload"""
        self._initial_config_wo_resolvers()

    def _initial_config_wo_resolvers(self):
        self.dnso.setup_key()

        self.masters = self.dnso.get_masters()
        self.aliases = Provider()._look_for_alias(self.fqdn, self.zone, self.alias_dict)

        if not self._update_records(self.masters['private'], self.private_ip, ptr=True):
            self.misc.die("DNS update of PRIVATE view failed on all masters: {}".format(self.masters['private']))
        if not self._update_records(self.masters['public'],self.public_ip, ptr=False):
            self.misc.die("DNS update of PUBLIC view failed on all masters: {}".format(self.masters['public']))

        self.slaves = self.dnso.get_slaves(self.masters)

    def watch(self):
        """Some periodic actions"""
    	# Check if masters changed
        new_masters = self.dnso.get_masters()
        if (self._list_changed(self.masters["private"], new_masters["private"])
            or self._list_changed(self.masters["public"], new_masters["public"])):
            self.logger.warning("Masters list changed.")
            self.initial_config()
        else:
            # Check if slaves list was changed
            new_slaves = self.dnso.get_slaves(self.masters)
            if len(new_slaves["private"]) > 0:
                old_slaves = self.dhcl.get_nameserver()
                if self._list_changed(old_slaves, new_slaves["private"]):
                    self.logger.warning("Slaves list changed.")
                    self.slaves = dict(new_slaves)
                    self._setup_resolver(self.slaves["private"], [self.zone])
            else:
                self.logger.error("No private DNS slaves found: {}.".format(new_slaves))

    def cleanup(self):
        """To do on shutdown"""
        # Delete aliases if any
        if self.aliases:
            for alias in self.aliases:
                self.dnso.delete_alias(self.masters["private"][0], alias, self.fqdn)
                self.dnso.delete_alias(self.masters["public"][0], alias, self.fqdn)

        # Delete hosts' records
        self.dnso.delete_host(
            self.masters["private"][0], self.fqdn, self.private_ip, ptr=True)
        self.dnso.delete_host(
            self.masters["public"][0], self.fqdn, self.public_ip)

    def _update_records(self, masters, ip, ptr):
        """Try update on any master"""
        for master in masters:
            self.logger.debug("Trying update at master: {}.".format(master))
            try:
                self.dnso.update_host(master, self.fqdn, ip, ptr=ptr)

                # Add aliases if any
                if self.aliases:
                    for alias in self.aliases:
                        self.dnso.update_alias(master, alias, self.fqdn)
                return True
            except:
                continue
        return False

    def _setup_resolver(self, servers, domain):
        self.logger.info(
            "Configuring local resolver with: NS={}; domain={}.".format(
                servers, domain))
        self.dhcl.set_nameserver(servers)
        self.dhcl.set_search(domain)
        if self.dhcl.config_updated:
            self.dhcl.renew_lease()

    def _list_changed(self, first, second):
        self.logger.debug("Comparing lists: {} vs {}.".format(first, second))
        if len(first) != len(second):
            return True
        else:
            for i, element in enumerate(first):
                if element != second[i]:
                    return True
            return False


class Route53Provider:

    def __init__(self, config):
        self.logger = logging.getLogger("DNSWatch.Route53Provider")

        self.route = Route53(config["dnsupdate"], sync=False)

        self.zone = config["dnsupdate"]["zone"]
        self.fqdn = config["host"]["fqdn"]
        self.private_ip = config["host"]["private_ip"]
        self.public_ip = config["host"]["public_ip"]
        self.alias_dict = config["dnsupdate"]["alias"]
        self.aliases = None

    def initial_config(self):
        """To do on start"""
        zones = self.route.get_zones()

        zone = Provider()._ensure_fqdn(self.zone)

        # Compile PTR record for private IP and PTR zone name
        self.ptr_name = str(dns.reversename.from_address(self.private_ip))
        ptr_zone_name = self.ptr_name.split(".", 1)[-1]

        # Find IDs for zones
        for zone_id, zone_info in zones.iteritems():
            if zone_info["Name"] == zone:
                if zone_info["Private"]:
                    self.private_zone_id = zone_id
                else:
                    self.public_zone_id = zone_id
            elif zone_info["Name"] == ptr_zone_name:
                    self.private_ptr_zone_id = zone_id
        
        # Update zones
        self.route.update_host(self.private_zone_id, self.fqdn, self.private_ip)
        self.route.update_host(self.public_zone_id, self.fqdn, self.public_ip)
        self.route.update_ptr(self.private_ptr_zone_id, self.ptr_name, self.fqdn)

        self.aliases = Provider()._look_for_alias(self.fqdn, self.zone, self.alias_dict)

        # Add aliases if any
        if self.aliases:
            for alias in self.aliases:
                self.route.update_alias(self.private_zone_id, alias, self.fqdn)
                self.route.update_alias(self.public_zone_id, alias, self.fqdn)

    def reload_config(self):
        """To do on reload"""
        self.initial_config()

    def watch(self):
        """Some periodic actions"""
        # Check if all request got 'SYNCED' status
        self.route.check_request_status()

    def cleanup(self):
        """To do on shutdown"""
        # Delete aliases if any
        if self.aliases:
            for alias in self.aliases:
                self.route.delete_alias(self.private_zone_id, alias, self.fqdn)
                self.route.delete_alias(self.public_zone_id, alias, self.fqdn)
        
        # Delete hosts' records
        self.route.delete_host(self.private_zone_id, self.fqdn, self.private_ip)
        self.route.delete_host(self.public_zone_id, self.fqdn, self.public_ip)
        self.route.delete_ptr(self.private_ptr_zone_id, self.ptr_name, self.fqdn)
