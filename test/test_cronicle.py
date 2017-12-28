#!/usr/bin/env python

import os
import unittest
from cronicle import find_config, config

RSRC = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'rsrc')
FILENAME = '%s/prefix_01_suffix.ext' % RSRC


config.add({
    RSRC + '/prefix_*_suffix.ext': {'daily': 1}})


class Test(unittest.TestCase):

    def test_find_config_ok(self):
        res = find_config('rsrc/prefix_01_suffix.ext', config)
        self.assertEqual(res['daily'], 1)

    def test_find_config_ko(self):
        res = find_config('rsrc/prefix_01_suffix', config)
        self.assertEqual(res, None)
