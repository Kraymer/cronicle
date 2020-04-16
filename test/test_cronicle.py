#!/usr/bin/env python

import itertools
import os
import tempfile
import unittest
import datetime as dt
from dateutil import parser

from cronicle import find_config, cronicle
from cronicle.config import config

RSRC = os.path.join(os.path.realpath(os.path.dirname(__file__)), "rsrc")
FILENAME = "%s/prefix_01_suffix.ext" % RSRC


config.add({RSRC + "/prefix_*_suffix.ext": {"daily": 1}})


def date_generator():
    """Generate dates starting at 1st Dec 2019 by 1 day step increment"""
    from_date = dt.date(2019, 12, 1)
    while True:
        yield from_date
        from_date = from_date + dt.timedelta(days=1)


def mock_file_create_day(filepath):
    """Interpret date in filename and returns it as creation date.
    """
    return parser.parse(filepath.split("/")[-1][4:].replace("_", " ")).replace(
        hour=0, minute=0, second=0, microsecond=0
    )


class ConfigTest(unittest.TestCase):
    def test_find_config_ok(self):
        res = find_config("rsrc/prefix_01_suffix.ext", config)
        self.assertEqual(res["daily"], 1)

    def test_find_config_ko(self):
        res = find_config("rsrc/prefix_01_suffix", config)
        self.assertEqual(res, None)


class Test(unittest.TestCase):
    def setUp(self):
        config.clear()
        self.rootdir = tempfile.TemporaryDirectory(prefix="cronicle_")
        for date in itertools.islice(date_generator(), 90):
            for hour in (9, 14):
                abspath = os.path.join(
                    self.rootdir.name, "foo_{}_{}h".format(str(date), hour)
                )
                with open(abspath, "w"):
                    pass
        print(abspath)

        self.last_file = abspath

    def test_archives_folders(self):
        """Check that no empty archive folder is created."""
        config.add({os.path.join(self.rootdir.name, "foo_*"): {"daily": 3}})
        cronicle([self.last_file])
        self.assertTrue(os.path.exists(os.path.join(self.rootdir.name, "DAILY")))
        self.assertFalse(
            any(
                [
                    os.path.exists(os.path.join(self.rootdir.name, x))
                    for x in (u"MONTHLY", u"WEEKLY", u"YEARLY")
                ]
            )
        )
