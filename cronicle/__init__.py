#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2018 Fabrice Laporte - kray.me
# The MIT License http://www.opensource.org/licenses/mit-license.php

"""Use cron to rotate backup files!
"""

import click
import copy
import glob
import logging
import os

from collections import OrderedDict
import datetime as dt
from dateutil.relativedelta import relativedelta
from shutil import rmtree

from .config import config, set_logging


__version__ = "0.3.1"

logger = logging.getLogger(__name__)
DEFAULT_CFG = {"daily": 0, "weekly": 0, "monthly": 0, "yearly": 0, "pattern": "*"}
set_logging()

# Names of frequency folders that will host symlinks, and minimum delta elapsed between 2 archives
FREQUENCY_FOLDER_DAYS = {
    "DAILY": ("days", 1),
    "HOURLY": ("hours", 1),
    "WEEKLY": ("days", 7),
    "MONTHLY": ("months", 1),
    "YEARLY": ("months", 12),
}
CONFIG_PATH = os.path.join(config.config_dir(), "config.yaml")


def frequency_folder_days(freq_dir):
    """Return minimum delta between 2 archives inside given folder"""
    try:
        return FREQUENCY_FOLDER_DAYS[os.path.basename(freq_dir).upper()]
    except KeyError:
        pass
    try:
        return int(freq_dir.split("|")[-1])
    except Exception:
        return None


def file_create_date(filepath):
    """Return file creation date with a daily precision."""
    try:
        filedate = os.lstat(os.path.realpath(filepath)).st_birthtime
    except AttributeError:
        filedate = os.lstat(os.path.realpath(filepath)).st_mtime
    return dt.date.fromtimestamp(filedate)


def is_symlinked(filepath, folders):
    """Return True if filepath has symlinks pointing to it in given folders."""
    dirname, basename = os.path.split(filepath)
    for folder in folders:
        target = os.path.abspath(os.path.join(dirname, folder, basename))
        if os.path.lexists(target):
            return True
    return False


def find_config(filename, cfg=None):
    """Return the config matched by filename"""
    res = copy.deepcopy(DEFAULT_CFG)
    dirname, basename = os.path.split(filename)

    if not cfg:
        cfg = config
    # Overwrite default config fields with matched config ones
    for pattern in cfg.keys():
        abspattern = (
            os.path.join(dirname, pattern) if not os.path.isabs(pattern) else pattern
        )
        for x in glob.glob(abspattern):
            if not x.endswith(filename):
                continue
            pattern_cfg = cfg[pattern] if isinstance(cfg, dict) else cfg[pattern].get()
            res.update(pattern_cfg)
            for frequency in pattern_cfg:
                if frequency_folder_days(frequency) is None:
                    logger.error("Invalid configuration attribute '%s'" % pattern)
                    exit(1)
            res["pattern"] = pattern
            return res


class Cronicle:
    def __init__(self, filenames, remove=False, config=None):
        for filename in [os.path.abspath(x) for x in filenames]:
            self.cfg = find_config(filename, config)

            if not self.cfg:
                logger.error(
                    "No pattern found in %s that matches %s." % (CONFIG_PATH, filename)
                )
                exit(1)
            freq_dirs = [
                x.upper()
                for x in set(self.cfg.keys()) - set(["pattern"])
                if self.cfg[x]
            ]
            for freq_dir in freq_dirs:
                self.timed_symlink(filename, freq_dir)
            for freq_dir in freq_dirs:
                self.rotate(filename, freq_dir, remove)


    def last_archive_date(self, filename, folder, pattern):
        """Return last archive date for given folder"""
        archives = self.archives_create_dates(folder, pattern)
        if archives:
            return list(archives.keys())[-1]

    def archives_create_dates(self, folder, pattern="*"):
        """Return OrderedDict of valid archives symlinks sorted by creation dates (used as keys)."""
        creation_dates = {}

        abs_pattern = os.path.join(folder, os.path.basename(pattern))
        for filepath in glob.glob(abs_pattern):
            if os.path.islink(filepath):
                if os.path.exists(filepath):
                    creation_dates[file_create_date(filepath)] = filepath
                else:
                    logger.info(
                        "No source file found at %s, deleting obsolete symlink %s."
                        % (os.path.realpath(filepath), filepath)
                    )
                    self.unlink(filepath)
        return OrderedDict(sorted(creation_dates.items()))

    def is_spaced_enough(self, filename, target_dir):
        """Return True if enough time elapsed between last archive
        and filename creation dates according to target_dir frequency.
        """
        file_date = file_create_date(filename)
        _last_archive_date = self.last_archive_date(
            filename, target_dir, self.cfg["pattern"]
        )
        if _last_archive_date:
            delta = relativedelta(file_date, _last_archive_date)
            delta_unit, delta_min = frequency_folder_days(target_dir)
            return getattr(delta, delta_unit) >= delta_min

        return True

    def timed_symlink(self, filename, freq_dir):
        """Create symlink for filename in freq_dir if enough days elapsed since last archive.
        Return True if symlink created.
        """
        target_dir = os.path.abspath(
            os.path.join(os.path.dirname(filename), freq_dir.split("|")[0])
        )

        if not self.is_spaced_enough(filename, target_dir):
            logger.info("No symlink created : too short delay since last archive")
            return
        target = os.path.join(target_dir, os.path.basename(filename))
        if not os.path.lexists(target):
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
            logger.info("Creating symlink %s" % target)
            os.symlink(os.path.relpath(filename, start=target_dir), target)
        else:
            logger.error("%s already exists" % target)
            return
        return True

    def rotate(self, filename, freq_dir, remove):
        """Keep only the n last links of folder that matches same pattern than filename."""

        others_freq_dirs = [
            x.split("|")[0].upper() for x in set(self.cfg.keys()) - set([freq_dir])
        ]
        target_dir = os.path.abspath(
            os.path.join(os.path.dirname(filename), freq_dir.split("|")[0])
        )
        # sort new -> old
        links = list(self.archives_create_dates(target_dir, self.cfg["pattern"]).values())[
            ::-1
        ]

        for link in links[self.cfg[freq_dir.lower()] :]:  # skip the n most recents
            filepath = os.path.realpath(link)
            logger.info("Unlinking %s" % link)
            os.unlink(link)
            if remove and not is_symlinked(filepath, others_freq_dirs):
                if os.path.isfile(filepath):
                    os.remove(filepath)
                elif os.path.isdir(filepath):
                    rmtree(filepath)


@click.command(
    context_settings=dict(help_option_names=["-h", "--help"]),
    help=(
        "Keep rotated time-spaced archives of files. FILES names must match one of "
        " the patterns present in %s." % CONFIG_PATH
    ),
    epilog=(
        "See https://github.com/Kraymer/cronicle/blob/master/README.md#usage for "
        "more infos"
    ),
)
@click.argument("filenames", type=click.Path(exists=True), metavar="FILES", nargs=-1)
@click.option(
    "-r",
    "--remove",
    "remove",
    help="Remove previous file backup when no symlink points to it.",
    default=False,
    is_flag=True,
)
@click.option(
    "-d", "--dry-run", count=True, help="Just print instead of writing on filesystem."
)
@click.option("-v", "--verbose", count=True)
@click.version_option(__version__)
def cronicle_cli(filenames, remove, dry_run, verbose):
    set_logging(max(verbose, dry_run))
    if dry_run:  # disable functions performing filesystem operations
        globals().update(
            {func: lambda *x: None for func in ("remove", "symlink", "unlink")}
        )
    Cronicle(filenames, remove)


if __name__ == "__main__":
    cronicle_cli()
