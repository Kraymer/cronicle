#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2018-2020 Fabrice Laporte - kray.me
# The MIT License http://www.opensource.org/licenses/mit-license.php

import os
import time
from setuptools import setup

PKG_NAME = "cronicle"
DIRPATH = os.path.dirname(__file__)

def read_rsrc(filename):
    with open(os.path.join(DIRPATH, filename)) as _file:
        return _file.read().strip()

VERSION = read_rsrc(os.path.join(PKG_NAME, "VERSION"))
if VERSION.endswith("dev"):
    VERSION += str(int(time.time()))

# Deploy: python3 setup.py sdist bdist_wheel; twine upload --verbose dist/*
setup(name=PKG_NAME,
      version=VERSION,
      description="Use cron to rotate backup files!",
      long_description=read_rsrc("README.rst"),
      author='Fabrice Laporte',
      author_email='kraymer@gmail.com',
      url='https://github.com/KraYmer/cronicle',
      license='MIT',
      platforms='ALL',
      packages=['cronicle', ],
      entry_points={
          'console_scripts': [
              'cronicle = cronicle:cronicle_cli',
          ],
      },
      install_requires=read_rsrc("requirements.txt").split("\n"),
      classifiers=[
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python',
          'Environment :: Console',
          'Topic :: System :: Filesystems',
      ],
      keywords="cron rotate backup",
      )
