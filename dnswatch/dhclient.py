import psutil
import re
import os
import time
import logging

from subprocess import check_call, STDOUT
from shutil import copyfile
from misc import Misc


class DHClient:

    def __init__(self):
        self.logger = logging.getLogger("DNSWatch.DHClient")
        self.misc = Misc(self.logger)
        self.args = self._collect_args()
        self.config_files = ["/etc/dhcp/dhclient.conf"]
        self.config_updated = False

    def _collect_args(self):
        self.logger.debug("Looking for dhclient process arguments.")

        default_cmdline = ['dhclient',
                '-1',
                '-v',
                '-pf',
                '/run/dhclient.eth0.pid',
                '-lf',
                '/var/lib/dhcp/dhclient.eth0.leases',
                'eth0']
        for proc in psutil.process_iter():
            if re.match("^dhclient\d*$", proc.name):
                self.logger.debug("dhclient cmdline: '{}'.".format(
                                    " ".join(proc.cmdline)))
                return proc.cmdline

        self.logger.warning(
            "dhclient process not found. Falling back to default: '{}'.".format(
                " ".join(default_cmdline)))
        self._request_lease(default_cmdline)
        return default_cmdline

    def set_nameserver(self, ns):
        self.logger.debug("Setting nameserver: {}.".format(ns))
        if not self._set_option("supersede", "domain-name-servers", ", ".join(ns)):
            self.misc.die("Failed to set nameserver for dhclient")

    def get_nameserver(self):
        self.logger.debug("Getting nameserver from dhclient config.")
        return self._get_option("domain-name-servers", otype="supersede")[2]

    def set_search(self, domain):
        self.logger.debug("Setting search domain: {}.".format(domain))
        if not self._set_option("prepend", "domain-name", '"{} "'.format(" ".join(domain))):
            self.misc.die("Failed to set search domain for dhclient")

    def renew_lease(self):
        self._release_lease(self.args)
        self._request_lease(self.args)
        self.config_updated = False

    def _release_lease(self, args_list):
        self.logger.debug("Releasing DHCP lease.")
        args = list(args_list)
        args.append("-r")
        FNULL = open(os.devnull, 'w')
        # If close_fds is true, all file descriptors except 0, 1 and 2 will be
        # closed before the child process is executed. (Unix only).
        check_call(args, stdout=FNULL, stderr=STDOUT, close_fds=True)

    def _request_lease(self, args_list):
        self.logger.debug("Requesting DHCP lease.")
        FNULL = open(os.devnull, 'w')
        # If close_fds is true, all file descriptors except 0, 1 and 2 will be
        # closed before the child process is executed. (Unix only).
        #
        # Here it's a must because in other case dhclient will inherit lock
        # file/socket. Which will prevent future starts.
        check_call(args_list, stdout=FNULL, stderr=STDOUT, close_fds=True)

    def _set_option(self, otype, option, value):
        if not otype in ["append", "prepend", "supersede"]:
            self.misc.die("Unknown dhclient option type: {}".format(otype))

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
            if self._write_config(new_config, config_file):
                self.config_updated = True
                return True
            else:
                return False
        else:
            return True

    def _get_option(self, option, otype=".+"):
        config_file = self._get_config_file()
        config = self._read_config(config_file)
        return self._read_option(option, config, otype)

    def _read_option(self, option, config, otype):
        result = None
        for line in config:
            rm = re.match("^({})\s+{}\s+(.+);$".format(otype, option), line)
            if rm:
                otype = rm.group(1)
                value = [ e.strip() for e in rm.group(2).split(",")]
                result = [otype, option, value]
        return result

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
