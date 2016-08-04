#!/usr/bin/env python
# -*- coding: utf-8 -*-
# dnswatch - tool to automate DNS setup
##############################################################################
import sys
import logging

##############################################################################
class DNSWatch:
    def __init__(self, logger, config):
        self.logger = logger

##############################################################################
def configure_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s %(process)d %(name)-16s %(levelname)-8s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def main():
    logger = configure_logger("DNSWatch")
    logger.debug("Starting.")

    dw = DNSWatch(logger, config)
    dw.initial_config()
    dw.watch()
    dw.cleanup()

    logger.debug("Finished successfully.")
    sys.exit(0)

if __name__ == '__main__':
    main()
