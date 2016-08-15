import dns.resolver
import dns.tsigkeyring
import dns.update

from log import Log

class DNSOps:

    def __init__(self, config):
        self.logger = Log.get_logger(self.__class__.__name__)
        self.config = config
        self.keyring = None
        self.key_algorithm = None

    def setup_key(self):
        update_key = self.config["update_key"]
        name = update_key["name"]
        key = update_key["key"]
        algorithm = update_key["algorithm"]

        self.logger.debug(
            "Creating keyring for domain '{}' with key '{}'.".format(
                name, key))
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

    def update_zone(self, dnsserver, host, ip):
        if not self.keyring:
            self.logger.error("Keyring for DNS update not found")
            raise Exception("Keyring for DNS update not found")
        if not self.key_algorithm:
            self.logger.error("Key algorithm for DNS update not specified")
            raise Exception("Key algorithm for DNS update not specified")
        self.logger.debug("Updating {} host at {} with IP {}.".format(
            host, dnsserver, ip))
        update = dns.update.Update(
            self.config["zone"],
            keyring=self.keyring, 
            keyalgorithm=self.key_algorithm)  
        update.replace(host, self.config["ttl"], "A", ip)
        response = self.query.tcp(update, dnsserver)
        print dns.rcode.to_text(response.rcode())

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
