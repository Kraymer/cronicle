#!/usr/bin/env python

import itertools
import mock
import os
import tempfile
import unittest
import datetime as dt
from dateutil import parser

from cronicle import find_config, config, file_create_day

RSRC = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'rsrc')
FILENAME = '%s/prefix_01_suffix.ext' % RSRC


config.add({
    RSRC + '/prefix_*_suffix.ext': {'daily': 1}})

def date_generator(delta=12):
    """Generate dates starting at 1st Jan 2020"""
    from_date = dt.date(2020, 1, 1)
    while True:
        yield from_date
        from_date = from_date + dt.timedelta(days=1)

def mock_file_create_day(filepath):
    return parser.parse(filepath).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

class ConfigTest(unittest.TestCase):

    def test_find_config_ok(self):
        res = find_config('rsrc/prefix_01_suffix.ext', config)
        self.assertEqual(res['daily'], 1)

    def test_find_config_ko(self):
        res = find_config('rsrc/prefix_01_suffix', config)
        self.assertEqual(res, None)


class Test(unittest.TestCase):

    def setUp(self):

        self.rootdir = tempfile.TemporaryDirectory(prefix='cronicle_')
        for date in itertools.islice(date_generator(), 366):
            for hour in (9, 14):
                abspath = os.path.join(self.rootdir.name, "a_{}_{}h".format(
                    str(date), hour))
                print(abspath)
                with open(abspath, 'w'):
                    pass
        self.last_file = abspath

    @mock.patch(
        "cronicle.file_create_day", side_effect=mock_file_create_day
    )
    def test_daily_rotation(self, mock):
        cfg = {os.path.join(self.rootdir.name, "a_*"): {'daily': 3}}
        import ipdb;ipdb.set_trace()

        config.add(cfg)

        cronicle_cli([self.last_file], verbose=3)
        import ipdb;ipdb.set_trace()
    #     cronicle()
    #     assert(ls(rootdir) = ["test_20201229", "test_20201230", "test_20201231"])

    # def test_weekly_rotation:
    #     config.add({
    #         RSRC + '/prefix_*_suffix.ext': {'weekly: 3'}})
    #     cronicle()
    #     assert(ls(rootdir) = [])

    # def test_monthly_rotation:
    #     config.add({
    #         RSRC + '/prefix_*_suffix.ext': {'monthly': 3}})
    #     cronicle()
    #     assert(ls(rootdir) = ["test_20201229", "test_20201230", "test_20201231"])

