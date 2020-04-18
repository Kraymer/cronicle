#!/usr/bin/env python

import itertools
import os
import tempfile
import unittest
import datetime as dt
import glob
import mock
from dateutil import parser

from cronicle import Cronicle, find_config


NOOP_CONFIG = {"hourly": 0, "daily": 0, "weekly": 0, "monthly": 0, "yearly": 0}


def date_generator():
    """Generate dates starting at 1st Dec 2019 by 1 day step increment"""
    from_date = dt.date(2019, 12, 1)
    while True:
        yield from_date
        from_date = from_date + dt.timedelta(days=1)


def mock_file_create_day(filepath):
    """Interpret date in filename and returns it as creation date.
    """
    return parser.parse(filepath.split("/")[-1][4:].replace("_", " "))


class ConfigTest(unittest.TestCase):
    def test_find_config_ok(self):
        res = find_config("bar.txt", {"bar*": {"daily": 3}, "foo*": {"weekly": 4}})
        self.assertEqual(
            res, {"daily": 3, "monthly": 0, "pattern": "bar*", "weekly": 0, "yearly": 0}
        )

    def test_find_config_ko(self):
        res = find_config("foo", {"bar*": {"weekly": 3}})
        self.assertEqual(res, None)


class ArchiveTest(unittest.TestCase):
    """Create set of files to archive beforehand, call cronicle and check symlinks created.
    """

    def setUp(self):
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

    def test_archives_folders(self):
        """Check that no empty archive folder is created."""
        Cronicle(
            [self.last_file],
            config={os.path.join(self.rootdir.name, "foo_*"): {"daily": 3}},
        )
        self.assertTrue(os.path.exists(os.path.join(self.rootdir.name, "DAILY")))
        self.assertFalse(
            any(
                [
                    os.path.exists(os.path.join(self.rootdir.name, x))
                    for x in (u"HOURLY", u"MONTHLY", u"WEEKLY", u"YEARLY")
                ]
            )
        )

    @mock.patch("cronicle.file_create_date", side_effect=mock_file_create_day)
    def test_number_of_archives(self, mock):
        files = sorted(glob.glob(os.path.join(self.rootdir.name, "foo_*")))
        Cronicle(
            files,
            config={
                os.path.join(self.rootdir.name, "foo_*"): {
                    "hourly": 3,
                    "daily": 3,
                    "weekly": 4,
                    "monthly": 4,
                    "yearly": 4,
                }
            },
        )
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
        self.assertEqual(
            set(os.listdir(os.path.join(self.rootdir.name, "MONTHLY"))),
            {"foo_2019-12-01_09h", "foo_2020-01-01_09h", "foo_2020-02-01_09h"},
        )
        self.assertEqual(
            set(os.listdir(os.path.join(self.rootdir.name, "HOURLY"))),
            {"foo_2020-02-27_14h", "foo_2020-02-28_09h", "foo_2020-02-28_14h"},
        )


class RotateTest(unittest.TestCase):
    """Call cronicle after each file creation and check files rotation.
    """

    @mock.patch("cronicle.file_create_date", side_effect=mock_file_create_day)
    def test_remove(self, mock):
        self.rootdir = tempfile.TemporaryDirectory(prefix="cronicle_")

        for date in itertools.islice(date_generator(), 30):
            abspath = os.path.join(self.rootdir.name, "bar_{}".format(str(date)))
            with open(abspath, "w"):
                pass
            Cronicle(
                [abspath],
                remove=True,
                config={os.path.join(self.rootdir.name, "bar_*"): {"daily": 3}},
            )

        self.assertEqual(
            set(
                [
                    x
                    for x in os.listdir(self.rootdir.name)
                    if os.path.isfile(os.path.join(self.rootdir.name, x))
                ]
            ),
            {"bar_2019-12-28", "bar_2019-12-30", "bar_2019-12-29"},
        )
