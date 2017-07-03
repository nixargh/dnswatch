#!/usr/bin/env python
import os
import re
from setuptools import setup, find_packages

def get_version(vfile):
    version = None
    version_line = open(vfile, "r").read()
    version_re = r"^__version__ = ['\"]([^'\"]*)['\"]"
    mo = re.search(version_re, version_line, re.M)
    if mo:
        version = mo.group(1)
    return version

def get_requires(rfile):
    requires = list()
    with open(rfile, "r") as f:
        for line in f.readlines():
            requires.append(line.strip())
    return requires

setup(
    name = 'dnswatch',
    version = get_version("./dnswatch/__init__.py"),
    packages = find_packages(),
    description = 'Tool for automatic DNS configuration',
    long_description = "Update zone on remote DNS server and configure local dhclient",
    author = "Konstantin Vinogradov",
    author_email = "<nixargh@protonmail.com>"
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
    install_requires = get_requires("./requirements.txt")
)
