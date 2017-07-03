#!/usr/bin/env python
import os
import re
from setuptools import setup, find_packages

<<<<<<< HEAD
def get_version(vfile):
    version = None
    version_line = open(vfile, "r").read()
=======
def get_version(file):
    version = None
    version_line = open(file, "r").read()
>>>>>>> 59ed5eec90df781060c3439a5ca2940dcdb5fdb9
    version_re = r"^__version__ = ['\"]([^'\"]*)['\"]"
    mo = re.search(version_re, version_line, re.M)
    if mo:
        version = mo.group(1)
    return version

<<<<<<< HEAD
def get_requires(rfile):
    requires = list()
    with open(rfile, "r") as f:
        for line in f.readlines():
            requires.append(line.strip())
    return requires

=======
>>>>>>> 59ed5eec90df781060c3439a5ca2940dcdb5fdb9
setup(
    name = 'dnswatch',
    version = get_version("./dnswatch/__init__.py"),
    packages = find_packages(),
    description = 'Tool for automatic DNS configuration',
<<<<<<< HEAD
    long_description = "Update zone on remote DNS server and configure local dhclient",
    author = "nixargh",
    author_email='nixargh@protonmail.com',
=======
    long_description = "Update zone on remote bind server and configure local dhclient",
    author = "nixargh",
    author_email='nixargh@gmail.com',
>>>>>>> 59ed5eec90df781060c3439a5ca2940dcdb5fdb9
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
<<<<<<< HEAD
    install_requires = get_requires("./requirements.txt")
=======
    install_requires = ["pyyaml", "dnspython", "psutil", "lockfile"]
>>>>>>> 59ed5eec90df781060c3439a5ca2940dcdb5fdb9
)
