#!/usr/bin/env python
import os
import re
from setuptools import setup, find_packages

def get_version(file):
    version = None
    version_line = open(file, "r").read()
    version_re = r"^__version__ = ['\"]([^'\"]*)['\"]"
    mo = re.search(version_re, version_line, re.M)
    if mo:
        version = mo.group(1)
    return version

setup(
    name = 'dnswatch',
    version = get_version("./dnswatch/__init__.py"),
    packages = find_packages(),
    description = 'Tool for automatic DNS configuration',
    long_description = "Update zone on remote bind server and configure local dhclient",
    author = "nixargh",
    author_email='nixargh@gmail.com',
    license = "GNU GPL",
    url = "https://github.com/nixargh/dnswatch",
    entry_points = {
        'console_scripts':
            ['dnswatch = dnswatch.main:main']
    },
    data_files = [ 
        ("/etc/dnswatch/", ["config.yaml.example"]),
        ("/etc/init/", ["dnswatch.conf"]),
    ],
    install_requires = ["pyyaml", "dnspython", "psutil", "lockfile"]
)
