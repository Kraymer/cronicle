#!/usr/bin/env python

import itertools
import os
import tempfile
import unittest
import datetime as dt
import glob
import mock
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
                    self.rootdir.name, "foo_{}_{:02d}h".format(str(date), hour)
                )
                with open(abspath, "w"):
                    pass
        print(abspath)

        self.last_file = abspath

    @mock.patch("cronicle.file_create_day", side_effect=mock_file_create_day)
    def test_number_of_archives(self, mock):
        config.add(
            {
                os.path.join(self.rootdir.name, "foo_*"): {
                    "daily": 3,
                    "weekly": 4,
                    "monthly": 4,
                    "yearly": 4,
                }
            }
        )
        files = sorted(glob.glob(os.path.join(self.rootdir.name, "foo_*")))
        cronicle(files)
        self.assertEqual(
            set(os.listdir(os.path.join(self.rootdir.name, "DAILY"))),
            {
                # Archives done at 9h are kept instead of those at 14h as
                # symlinking the latter fail because of too short delay since
                # last archive
                "foo_2020-02-26_09h",
                "foo_2020-02-27_09h",
                "foo_2020-02-28_09h",
            },
        )
