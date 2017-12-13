#!/usr/bin/env python

import os
import unittest
from cronicle import find_archives, prune_dir

RSRC = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'rsrc')
FILENAME = '%s/prefix_01_suffix.ext' % RSRC


class Test(unittest.TestCase):

    def test_find_archives(self):
        archives = find_archives(FILENAME, RSRC)
        self.assertEqual(archives, ['prefix_2_suffix.ext'])

    def test_prune_dir(self):
        prune_dir('%s/DAILY/' % RSRC, 'test.txt', 3)
