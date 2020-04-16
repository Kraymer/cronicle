#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2018 Fabrice Laporte - kray.me
# The MIT License http://www.opensource.org/licenses/mit-license.php

"""Use cron to rotate backup files!
"""

import click
import glob
import logging

from collections import OrderedDict
from datetime import datetime
from os import lstat, makedirs, path, remove, symlink, unlink
from shutil import rmtree

from .config import config, set_logging

with codecs.open(
    os.path.join(os.path.dirname(__file__), "VERSION"), encoding="utf-8"
) as _file:
    __version__ = _file.read().strip()

logger = logging.getLogger(__name__)
DEFAULT_CFG = {"daily": 0, "weekly": 0, "monthly": 0, "yearly": 0, "pattern": "*"}
set_logging()

# Names of frequency folders that will host symlinks, and minimum number of days between 2 archives
FREQUENCY_FOLDER_DAYS = {
    "DAILY": 1,
    "WEEKLY": 7,
    "MONTHLY": 30,
    "YEARLY": 365,
}
CONFIG_PATH = path.join(config.config_dir(), "config.yaml")




def frequency_folder_days(freq_dir):
    """Return minimum number of days between 2 archives inside given folder
    """
    try:
        return FREQUENCY_FOLDER_DAYS[freq_dir.upper()]
    except KeyError:
        pass
    try:
        return int(freq_dir.split("|")[-1])
    except Exception:
        return None


def file_create_day(filepath):
    """Return file creation date with a daily precision.
    """
    try:
        filedate = lstat(path.realpath(filepath)).st_birthtime
    except AttributeError:
        filedate = lstat(path.realpath(filepath)).st_mtime
    return datetime.fromtimestamp(filedate).replace(
        hour=0, minute=0, second=0, microsecond=0
    )


def archives_create_days(folder, pattern="*"):
    """Return OrderedDict of archives symlinks sorted by creation days (used as keys).
    """
    creation_dates = {}

    abs_pattern = path.join(folder, path.basename(pattern))
    for x in glob.glob(abs_pattern):
        if path.islink(x):
            creation_dates[file_create_day(x)] = x
    return OrderedDict(sorted(creation_dates.items()))


def is_symlinked(filepath, folders):
    """Return True if filepath has symlinks pointing to it in given folders.
    """
    dirname, basename = path.split(filepath)
    for folder in folders:
        target = path.abspath(path.join(dirname, folder, basename))
        if path.lexists(target):
            return True
    return False


def find_config(filename, cfg=None):
    """Return the config matched by filename or the default one.
    """
    res = DEFAULT_CFG
    dirname, basename = path.split(filename)

    if not cfg:
        cfg = config
    # Overwrite default config fields with matched config ones
    for key in cfg.keys():
        abskey = path.join(dirname, key) if not path.isabs(key) else key
        for x in glob.glob(abskey):
            if x.endswith(filename):
                cfg = config[key].get()
                res.update(cfg)
                for frequency in cfg:
                    if frequency_folder_days(frequency) is None:
                        logger.error("Invalid configuration attribute '%s'" % key)
                        exit(1)
                res["pattern"] = key
                return res


class Cronicle:
    def __init__(self, filenames, _remove=False):
        for filename in [path.abspath(x) for x in filenames]:
            self.cfg = find_config(filename)
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
                self.rotate(filename, freq_dir, _remove)

    def days_since_last_archive(self, filename, folder):
        """Return nb of elapsed days since last archive in given folder.
        """
        archives = archives_create_days(folder, self.cfg["pattern"])
        if archives:
            last_archive_day = list(archives.keys())[-1]
            return (file_create_day(filename) - last_archive_day).days

    def timed_symlink(self, filename, freq_dir):
        """Create symlink for filename in freq_dir if enough days elapsed since last archive.
           Return True if symlink created.
        """
        target_dir = path.abspath(
            path.join(path.dirname(filename), freq_dir.split("|")[0])
        )
        days_elapsed = self.days_since_last_archive(filename, target_dir)
        if (days_elapsed is not None) and days_elapsed < frequency_folder_days(
            freq_dir
        ):
            logger.info("No symlink created : too short delay since last archive")
            return
        target = path.join(target_dir, path.basename(filename))
        if not path.lexists(target):
            if not path.exists(target_dir):
                makedirs(target_dir)
            logger.info("Creating symlink %s" % target)
            symlink(filename, target)
        else:
            logger.error("%s already exists" % target)
            return
        return True

    def rotate(self, filename, freq_dir, _remove):
        """Keep only the n last links of folder that matches same pattern than filename.
        """
        others_freq_dirs = [
            x.split("|")[0].upper() for x in set(self.cfg.keys()) - set([freq_dir])
        ]
        target_dir = path.abspath(
            path.join(path.dirname(filename), freq_dir.split("|")[0])
        )
        # sort new -> old
        links = list(archives_create_days(target_dir, self.cfg["pattern"]).values())[
            ::-1
        ]

        for link in links[self.cfg[freq_dir.lower()] :]:  # skip the n most recents
            filepath = path.realpath(link)
            logger.info("Unlinking %s" % link)
            unlink(link)
            if _remove and not is_symlinked(filepath, others_freq_dirs):
                if path.isfile(filepath):
                    remove(filepath)
                elif path.isdir(filepath):
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
    "_remove",
    help="Remove previous file backup when no symlink points to it.",
    default=False,
    is_flag=True,
)
@click.option(
    "-d", "--dry-run", count=True, help="Just print instead of writing on filesystem."
)
@click.option("-v", "--verbose", count=True)
@click.version_option(__version__)
def cronicle_cli(filenames, _remove, dry_run, verbose):
    set_logging(max(verbose, dry_run))
    if dry_run:  # disable functions performing filesystem operations
        globals().update(
            {func: lambda *x: None for func in ("remove", "symlink", "unlink")}
        )
    Cronicle(filenames, _remove)


if __name__ == "__main__":
    cronicle_cli()
