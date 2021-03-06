import re
import dns.resolver
import dns.tsigkeyring
import dns.update
import dns.reversename
import logging

from misc import Misc


class DNSOps:

    def __init__(self, config):
        self.logger = logging.getLogger("DNSWatch.DNSOps")
        self.misc = Misc(self.logger)
        self.config = config
        self.keyring = None
        self.key_algorithm = None

    def setup_key(self):
        update_key = self.config["update_key"]
        name = update_key["name"]
        key = update_key["key"]
        algorithm = update_key["algorithm"]

        self.logger.debug(
            "Creating keyring for domain '{}' with key '{}...'.".format(
                name, key[:10]))
        self.keyring = dns.tsigkeyring.from_text({name: key}) 

        self.logger.debug("Setting key algorithm to '{}'.".format(algorithm))
        self.key_algorithm = getattr(dns.tsig, algorithm)

    def get_masters(self):
        zone = self.config["zone"]
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

    def get_slaves(self, masters):
        zone = self.config["zone"]
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

    def add_host(self, dnsserver, host, ip, ptr=False):
        self._operate_record("add", dnsserver, host, "A", ip)
        if ptr:
            self.add_ptr(dnsserver, host, ip)

    def delete_host(self, dnsserver, host, ip, ptr=False):
        self._operate_record("delete", dnsserver, host, "A", ip)
        if ptr:
            self.delete_ptr(dnsserver, host, ip)

    def update_host(self, dnsserver, host, ip, ptr=False):
        self._operate_record("replace", dnsserver, host, "A", ip)
        if ptr:
            self.update_ptr(dnsserver, host, ip)

    def add_ptr(self, dnsserver, host, ip):
        ptr_record = dns.reversename.from_address(ip)
        self._operate_record("add", dnsserver, ptr_record, "PTR", self._ensure_fqdn(host))

    def delete_ptr(self, dnsserver, host, ip):
        ptr_record = dns.reversename.from_address(ip)
        self._operate_record("delete", dnsserver, ptr_record, "PTR", self._ensure_fqdn(host))

    def update_ptr(self, dnsserver, host, ip):
        ptr_record = dns.reversename.from_address(ip)
        self._operate_record("replace", dnsserver, ptr_record, "PTR", self._ensure_fqdn(host))

    def add_alias(self, dnsserver, cname, hostname):
        self._operate_record("add", dnsserver, cname, "CNAME", self._ensure_fqdn(hostname))

    def delete_alias(self, dnsserver, cname, hostname):
        self._operate_record("delete", dnsserver, cname, "CNAME", self._ensure_fqdn(hostname))

    def update_alias(self, dnsserver, cname, hostname):
        self._operate_record("replace", dnsserver, cname, "CNAME", self._ensure_fqdn(hostname))

    def _operate_record(self, action, dnsserver, rdname, rdtype, data):
        if not action in ["add", "delete", "replace"]:
            self.misc.die("{} with DNS record isn't supported".format(action))
        if not self.keyring:
            self.misc.die("Keyring for DNS action not found")
        if not self.key_algorithm:
            self.misc.die("Key algorithm for DNS action not specified")
        self.logger.debug("Doing {} of '{}':'{}' record at {} with data '{}'.".format(
            action, rdtype, rdname, dnsserver, data))

        # Adjusting variables
        if rdtype == "PTR":
            rdname, origin = str(rdname).split(".", 1)
        else:
            origin = dns.name.from_text(self.config["zone"])
            rdname = dns.name.from_text(rdname) - origin
        data = data.encode("utf-8")

        # Collecting arguments for DNS update
        args = list()
        if action in ["add", "replace"]:
            args.append(self.config["ttl"])
        args.append(rdtype)        
        if action in ["add", "replace"]:
            args.append(data)

        # Doing DNS update
        update = dns.update.Update(
            origin,
            keyring=self.keyring, 
            keyalgorithm=self.key_algorithm)  
        eval('update.{}(rdname, *args)'.format(action))

        result = dns.query.tcp(update, dnsserver, timeout=self.config["timeout"])

        rcode = self._compile_rcode(result)
        if rcode[0] != 0:
            self.misc.die("DNS update failed: rcode={}; message='{}'".format(rcode[0], rcode[1]))
        else:
            self.logger.debug("DNS update done: rcode={}; message='{}'.".format(rcode[0], rcode[1]))

    def _compile_rcode(self, message):
        text = str()
        code = message.rcode()
        for line in message.to_text().splitlines():
            match = re.match("^rcode\s(.+)$", line)
            if match:
                text = match.group(1)
        return [ code, text ]

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

    def _ensure_fqdn(self, name):
        """Make a proper FQDN from name"""
        if name[-1:] != ".":
            return "%s." % name
        else:
            return name
