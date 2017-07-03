#!/usr/bin/env python
# -*- coding: utf-8 -*-
# dnswatch - tool for automatic DNS configuration
##############################################################################
import os
import sys
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

if __name__ == '__main__':
    main()
