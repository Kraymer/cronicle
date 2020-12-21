#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2018-2020 Fabrice Laporte - kray.me
# The MIT License http://www.opensource.org/licenses/mit-license.php

import codecs
import os
import re
import sys
import time
from setuptools import setup

try:
    from semantic_release import setup_hook

    setup_hook(sys.argv)
except ImportError:
    pass


PKG_NAME = "cronicle"
DIRPATH = os.path.dirname(__file__)


def read_rsrc(filename):
    with codecs.open(os.path.join(DIRPATH, filename), encoding="utf-8") as _file:
        return re.sub(r":(\w+\\?)+:", u"", _file.read().strip())  # no emoji


with codecs.open("cronicle/__init__.py", encoding="utf-8") as fd:
    version = re.search(
        r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', fd.read(), re.MULTILINE
    ).group(1)
    version = version.replace("dev", str(int(time.time())))

# Deploy: python3 setup.py sdist bdist_wheel; twine upload --verbose dist/*
setup(
    name=PKG_NAME,
    version=version,
    description="Use cron to rotate backup files!",
    long_description=read_rsrc("README.rst"),
    author="Fabrice Laporte",
    author_email="kraymer@gmail.com",
    url="https://github.com/KraYmer/cronicle",
    license="MIT",
    platforms="ALL",
    packages=[
        "cronicle",
    ],
    entry_points={"console_scripts": ["cronicle = cronicle:cronicle_cli"]},
    install_requires=read_rsrc("requirements.txt").split("\n"),
    extras_require={
        "test": [
            "coverage>=5,<6",
            "nose>1.3",
            "mock==4.0.2",
            "tox>=3",
        ]
    },
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Environment :: Console",
        "Topic :: System :: Filesystems",
    ],
    keywords="cron rotate backup",
)
