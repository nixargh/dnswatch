import psutil
import re
import os
import time
import logging

from subprocess import check_call, STDOUT
from shutil import copyfile

class DHClient:

    def __init__(self):
        self.logger = logging.getLogger("DNSWatch.DHClient")
        self.args = self._collect_args()
        self.config_files = ["/etc/dhcp/dhclient.conf"]

    def _collect_args(self):
        self.logger.debug("Looking for dhclient process arguments.")
        for proc in psutil.process_iter():
            if re.match("^dhclient\d*$", proc.name):
                return proc.cmdline

        msg = "dhclient process not found"
        self.logger.error(msg + ".")
        raise Exception(msg)

    def set_nameserver(self, ns):
        self.logger.debug("Setting nameserver: {}.".format(ns))
        if not self._set_option("supersede", "domain-name-servers", ", ".join(ns)):
            msg = "Failed to set nameserver for dhclient"
            self.logger.error(msg + ".")
            raise Exception(msg)

    def set_search(self, domain):
        self.logger.debug("Setting search domain: {}.".format(domain))
        if not self._set_option("prepend", "domain-name", '"{} "'.format(" ".join(domain))):
            msg = "Failed to set search domain for dhclient"
            self.logger.error(msg + ".")
            raise Exception(msg)

    def renew_lease(self):
        self._release_lease()
        self._request_lease()

    def _release_lease(self):
        self.logger.debug("Releasing DHCP lease.")
        args = list(self.args)
        args.append("-r")
        FNULL = open(os.devnull, 'w')
        check_call(args, stdout=FNULL, stderr=STDOUT)

    def _request_lease(self):
        self.logger.debug("Requesting DHCP lease.")
        FNULL = open(os.devnull, 'w')
        check_call(self.args, stdout=FNULL, stderr=STDOUT)

    def _set_option(self, otype, option, value):
        if not otype in ["append", "prepend", "supersede"]:
            msg = "Unknown dhclient option type: {}".format(otype)
            self.logger.error(msg + ".")
            raise Exception(msg)

        new_line = "{} {} {};".format(otype, option, value)
        new_config = list()
        option_exist = False
        write_config = False

        config_file = self._get_config_file()
        config = self._read_config(config_file)
        for line in config:
            if re.match("^{}\s+{}\s+.*;$".format(otype, option), line):
                option_exist = True
                self.logger.debug("Option '{}' exist, checking value.".format(option))
                if re.match("^{}\s+{}\s+{};$".format(otype, option, value), line):
                    self.logger.debug("Value '{}' is the same, skipping.".format(value))
                    new_config.append(line)
                else:
                    self.logger.debug("Values differ, updating to '{}'.".format(value))
                    write_config = True
                    new_config.append(new_line)
                    continue
            new_config.append(line)

        if not option_exist:
            write_config = True
            new_config.append(new_line)

        if write_config:
            return self._write_config(new_config, config_file)
        else:
            return True

    def _get_config_file(self):
        for config_file in self.config_files:
            if os.path.isfile(config_file):
                return config_file

    def _read_config(self, config_file):
        config = list()
        full_line = ""
        with open(config_file, "r") as cf:
            for line in cf.readlines():
                line = line.strip()
                if not re.match("^(.*#.*|)$", line):
                    if len(full_line) > 0:
                        line = full_line + line
                    if line[-1] != ";":
                        full_line = line
                    else:
                        config.append(line)
                        full_line = ""
        return set(config)

    def _write_config(self, config, config_file):
        self._backup_config(config_file)
        self.logger.debug("Writing new config.")
        with open(config_file, "w") as cf:
            for line in config:
                cf.write("{}\n".format(line))
        return True

    def _backup_config(self, config_file):
        backup_file = "{}.bak-{}".format(config_file, time.time())
        self.logger.debug("Doing backup of {} to {}.".format(config_file, backup_file))
        copyfile(config_file, backup_file)
        return True
