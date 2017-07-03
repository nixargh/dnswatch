#!/usr/bin/env python
# -*- coding: utf-8 -*-
# dnswatch - tool for automatic DNS configuration
##############################################################################
import os
import sys
<<<<<<< HEAD
import logging
import argparse
import traceback
import socket
import time

from core import DNSWatch
from misc import Misc
from config import Config
from killer import Killer

from __init__ import __version__
##############################################################################
def get_logger(name, log_level="DEBUG", log_file=None):
    logger = logging.getLogger(name)
    logger.setLevel(eval("logging.{}".format(log_level.upper())))
    if log_file:
        log_dir = os.path.dirname(log_file)
        if not os.path.isdir(log_dir):
            os.makedirs(log_dir)
        handler = logging.FileHandler(log_file)
    else:
        handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s %(process)-8d %(name)-22s %(levelname)-8s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def _parse_argv():
    parser = argparse.ArgumentParser(prog="dnswatch",
                          description='tool for automatic DNS configuration')

    parser.add_argument('-c', '--config', 
                    metavar='FILE',
                    required=True,
                    help='Config file')
    parser.add_argument('-l', '--logfile',
                    metavar='FILE',
                    help='Log file')
    parser.add_argument('-L', '--loglevel', 
                    metavar=['debug', 'info', 'warning', 'error', 'critical'], 
                    default='info',
                    help='Log level')
    parser.add_argument('-t', '--trace',
                    action='store_true',
                    help='Show python traceback')
    parser.add_argument('-v', '--version',
                    action='version',
                    version="%s %s" % (parser.prog, __version__),
                    help='Show version')
 
    return parser.parse_args()

def get_lock(name, timeout=60):
    # Without holding a reference to our socket somewhere it gets garbage
    # collected when the function exits
    get_lock._lock_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)

    try:
        get_lock._lock_socket.bind('\0' + name)
        return True
    except:
        time.sleep(timeout)
        try:
            get_lock._lock_socket.bind('\0' + name)
            return True
        except socket.error:
            return False

###############################################################################
def main():
    killer = Killer()

    args = _parse_argv()

    logger = get_logger("DNSWatch", log_level=args.loglevel, log_file=args.logfile)
    logger.info("Starting dnswatch v.{}.".format(__version__))

    misc = Misc(logger)

    try: 
        exit_code = 2

        if not get_lock("dnswatch", timeout=5):
            misc.die("Lock exists")

        c = Config()
        action = None
        while True:
            config = c.read(args.config)
            dw = DNSWatch(config)

            if action == 'reload':
                dw.reload_config()
            else:
                dw.initial_config()
            
            try: 
                action = dw.watch(pause=config["watch"]["pause"])
            except: 
                action = dw.watch()

            if action == "kill":
                # Do DNS cleanup and exit loop
                dw.cleanup()
                break
            elif action == "softkill":
                # Exit loop without DNS cleanup
                break
            elif action == "reload":
                # Do nothing
                pass
            else:
                misc.die("Unknown action requested: {}".format(action))

        logger.info("Finished successfully.")
        exit_code = 0
    except SystemExit:
        exit_code = sys.exc_info()[1]
    except:
        logger.error("Exiting with errors.")
        if args.trace:
            print(sys.exc_info())
            trace = sys.exc_info()[2]
            traceback.print_tb(trace)
            exit_code = 1
    finally:
        sys.exit(exit_code)
=======
import time
import argparse
import lockfile

from __init__ import __version__
from log import Log
from instance_info import InstanceInfo
from config import Config
from gce import GCE
from aws import AWS
from dnsops import DNSOps
from dhclient import DHClient
from killer import Killer
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
        self.logger.info("Doing initial configuration.")

        self.masters = self.dnso.get_masters()
        self.slaves = self.dnso.get_slaves(self.masters)

        self.dnso.update_host(
            self.masters["private"][0], self.fqdn, self.private_ip, ptr=True)
        self.dnso.update_host(
            self.masters["public"][0], self.fqdn, self.public_ip)

        self._setup_resolver(
            self.slaves["private"], [self.config["nsupdate"]["zone"]])

    def watch(self, pause=10):
        self.logger.info("Starting watch.")

        killer = Killer()
        while True:
            time.sleep(pause)
            self.logger.debug("Sending new watcher.")	
            if killer.kill_now:
                self.logger.info("Got kill signal, finishing watch.")
                break
            
            new_slaves = self.dnso.get_slaves(self.masters)
            if self._slaves_changed(
                    self.slaves["private"], new_slaves["private"]):
                self.logger.warning("Slaves list changed.")
                self.slaves = dict(new_slaves)
                self._setup_resolver(
                    self.slaves["private"], [self.config["nsupdate"]["zone"]])

    def cleanup(self):
        self.logger.info("Cleaning DNS before shutdown.")
        self.dnso.delete_host(
            self.masters["private"][0], self.fqdn, self.private_ip, ptr=True)
        self.dnso.delete_host(
            self.masters["public"][0], self.fqdn, self.public_ip)
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

    def _setup_resolver(self, servers, domain):
        self.logger.info(
            "Configuring local resolver with: NS={}; domain={}.".format(
                servers, domain))
        dhcl = DHClient()
        dhcl.set_nameserver(servers)
        dhcl.set_search(domain)
        dhcl.renew_lease()

    def _slaves_changed(self, first, second):
        self.logger.debug("Comparing slaves: {} vs {}.".format(first, second))
        if len(first) != len(second):
            return True
        else:
            for i, slave in enumerate(first):
                if slave != second[i]:
                    return True
            return False

###############################################################################
def _parse_argv():
    parser = argparse.ArgumentParser(prog="dnswatch",
                          description='tool for automatic DNS configuration')

    parser.add_argument('-c', '--config', 
                    metavar='FILE',
                    required=True,
                    help='Config file')
    parser.add_argument('-l', '--logfile', metavar='FILE',
                    help='Log file')
    parser.add_argument('-L', '--loglevel', 
                    metavar=['debug', 'info', 'warning', 'error', 'critical'], 
                    default='info',
                    help='Log level')
    parser.add_argument('-v', '--version',
                    action='version',
                    version="%s %s" % (parser.prog, __version__),
                    help='Show version')
 
    return parser.parse_args()

###############################################################################
def main():
    lock_file = "/run/lock/dnswatch.lock"
    lock = lockfile.FileLock(lock_file.split(".")[0])

    try:
        lock.acquire(5)

        try: 
            exit_code = 2
            args = _parse_argv()

            logger = Log.get_logger("DNSWatch",
                                    log_level=args.loglevel, log_file=args.logfile)
            logger.info("Starting dnswatch v.{}.".format(__version__))

            c = Config()
            config = c.read(args.config)

            dw = DNSWatch(logger, config)
            dw.initial_config()
            dw.watch()
            dw.cleanup()

            logger.info("Finished successfully.")
            exit_code = 0
        except:
            print("'{}' dnswatch failed.".format(sys.exc_info()))
            exit_code = 1
        finally:
            lock.release()
            sys.exit(exit_code)

    except lockfile.AlreadyLocked:
        print("'{}' is locked already.".format(lock_file))
    except lockfile.LockFailed:
        print("'{}' can't be locked.".format(lock_file))
    except lockfile.LockTimeout:
        print("'{}' lock wait timeout.".format(lock_file))
    else:
        print("'{}' locked.".format(lock_file))
>>>>>>> 59ed5eec90df781060c3439a5ca2940dcdb5fdb9

if __name__ == '__main__':
    main()
