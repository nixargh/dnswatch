import logging
import boto3

from misc import Misc


class Route53:

    def __init__(self, config, sync=True):
        self.logger = logging.getLogger("DNSWatch.Route53")
        self.misc = Misc(self.logger)
        self.config = config
        self.sync = sync
        self.unchecked_requests = list()
        self.client = boto3.client(
                        "route53",
                        aws_access_key_id=config["update_key"]["name"],
                        aws_secret_access_key=config["update_key"]["key"])

    def update_host(self, host, ip, ptr=False):
        result = True
        return result

    def get_zones(self):
        self.logger.debug("Getting hosted DNS zones.")
        zones = dict()
        response = self.client.list_hosted_zones()

        if not response["IsTruncated"]:
            zones_info = response["HostedZones"]
        else:
            self.misc.die(("Truncated aswers are not supported yet"))

        for zone in zones_info:
            zone_id = self._extract_id(zone["Id"])
            zones[zone_id] = {
                "Name": zone["Name"],
                "Private": zone["Config"]["PrivateZone"]
            }
        return zones

    def add_host(self, zone_id, hostname, ip, ptr=False):
        self._operate_record("create", zone_id, hostname, "A", ip)

    def delete_host(self, zone_id, hostname, ip, ptr=False):
        self._operate_record("delete", zone_id, hostname, "A", ip)

    def update_host(self, zone_id, hostname, ip, ptr=False):
        self._operate_record("upsert", zone_id, hostname, "A", ip)

    def add_ptr(self, zone_id, ptr_name, hostname):
        self._operate_record("create", zone_id, ptr_name, "PTR", self._ensure_fqdn(hostname))

    def delete_ptr(self, zone_id, ptr_name, hostname):
        self._operate_record("delete", zone_id, ptr_name, "PTR", self._ensure_fqdn(hostname))

    def update_ptr(self, zone_id, ptr_name, hostname):
        self._operate_record("upsert", zone_id, ptr_name, "PTR", self._ensure_fqdn(hostname))

    def add_alias(self, zone_id, cname, hostname):
        self._operate_record("create", zone_id, cname, "CNAME", self._ensure_fqdn(hostname))

    def delete_alias(self, zone_id, cname, hostname):
        self._operate_record("delete", zone_id, cname, "CNAME", self._ensure_fqdn(hostname))

    def update_alias(self, zone_id, cname, hostname):
        self._operate_record("upsert", zone_id, cname, "CNAME", self._ensure_fqdn(hostname))

    def _operate_record(self, action, zone_id, rdname, rdtype, data):
        action = action.upper()
        if not action in ["CREATE", "DELETE", "UPSERT"]:
            self.misc.die("{} with DNS record isn't supported".format(action))

        self.logger.debug("Requesting {} of '{}':'{}' record at {} with data '{}'.".format(
            action, rdtype, rdname, zone_id, data))

        response = self.client.change_resource_record_sets(
            HostedZoneId=zone_id,
            ChangeBatch={
                "Comment": "made by dnswatch",
                "Changes": [
                    {
                        "Action": action,
                        "ResourceRecordSet": {
                            "Name": rdname,
                            "Type": rdtype,
                            "TTL": self.config["ttl"],
                            "ResourceRecords": [
                                { "Value": data },
                            ]
                        },
                    },
                ],
            }
        )

        request_id = self._extract_id(response["ChangeInfo"]["Id"])
        self.logger.debug("Request sent: %s." % request_id)

        if self.sync:
            self._wait_request(request_id)
        else:
            self.unchecked_requests.append(request_id)

    def check_request_status(self, request_id=None):
        if request_id:
            self._wait_request(request_id)
            self.unchecked_requests(request_id)
        else:
            for request_id in self.unchecked_requests:
                self._wait_request(request_id)
                self.unchecked_requests.remove(request_id)

    def _ensure_fqdn(self, name):
        """Make a proper FQDN from name"""
        if name[-1:] != ".":
            return "%s." % name
        else:
            return name

    def _extract_id(self, dirty_id):
        """Delete /prefix from Id returned by Amazon API"""
        if dirty_id[:1] == "/":
            return dirty_id.split("/")[-1]
        else:
            return dirty_id

    def _wait_request(self, request_id):
            self.logger.debug("Checking request: %s." % request_id)
            waiter = self.client.get_waiter('resource_record_sets_changed')
            try:
                waiter.wait(Id=request_id)
                self.logger.debug("Request completed: %s." % request_id)
                return True
            except:
                self.logger.error("Request failed: %s." % request_id)
                return False
