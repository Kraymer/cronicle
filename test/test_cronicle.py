#!/usr/bin/env python

import os
import unittest
from cronicle import find_archives


RSRC = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'rsrc')

class Test(unittest.TestCase):

    def test_find_archives(self):
        archives = find_archives('%s/prefix_01_suffix.ext' % RSRC)
        self.assertEqual(archives, ['prefix_2_suffix.ext'])
