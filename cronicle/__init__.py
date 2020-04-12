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
from os import (lstat, makedirs, path, remove, symlink, unlink)
from shutil import rmtree

from .config import config

__author__ = 'Fabrice Laporte <kraymer@gmail.com>'
__version__ = '0.1.0'
logger = logging.getLogger(__name__)

DEFAULT_CFG = {'daily': 0, 'weekly': 0, 'monthly': 0, 'yearly': 0, 'pattern': '*'}

# Names of frequency folders that will host symlinks, and minimum number of days between 2 archives
FREQUENCY_FOLDER_DAYS = {
    'DAILY': 1,
    'WEEKLY': 7,
    'MONTHLY': 30,
    'YEARLY': 365,
}
CONFIG_PATH = path.join(config.config_dir(), 'config.yaml')


def set_logging(verbose=False):
    """Set logging level based on verbose flag.
    """
    levels = {0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}
    logging.basicConfig(level=levels[verbose], format='%(levelname)s: %(message)s')


def frequency_folder_days(ffolder):
    """Return minimum number of days between 2 archives inside given folder
    """
    try:
        return FREQUENCY_FOLDER_DAYS[ffolder.upper()]
    except KeyError:
        pass
    try:
        return int(ffolder.split('|')[-1])
    except:
        return None


def file_create_day(filepath):
    """Return file creation date with a daily precision.
    """
    try:
        filedate = lstat(path.realpath(filepath)).st_birthtime
    except AttributeError:
        filedate = lstat(path.realpath(filepath)).st_mtime
    return datetime.fromtimestamp(filedate).replace(hour=0, minute=0, second=0, microsecond=0)


def archives_create_days(folder, pattern='*'):
    """Return OrderedDict of archives symlinks sorted by creation days (used as keys).
    """
    creation_dates = {}
    abs_pattern = path.join(folder, path.basename(pattern))
    for x in glob.glob(abs_pattern):
        if path.islink(x):
            creation_dates[file_create_day(x)] = x
    return OrderedDict(sorted(creation_dates.items()))


def delta_days(filename, folder, cfg):
    """Return nb of elapsed days since last archive in given folder.
    """
    archives = archives_create_days(folder, cfg['pattern'])
    if archives:
        last_archive_day = list(archives.keys())[-1]
        return (file_create_day(filename) - last_archive_day).days


def timed_symlink(filename, ffolder, cfg):
    """Create symlink for filename in ffolder if enough days elapsed since last archive.
       Return True if symlink created.
    """
    target_dir = path.abspath(path.join(path.dirname(filename), ffolder.split('|')[0]))
    days_elapsed = delta_days(filename, target_dir, cfg)
    if (days_elapsed is not None) and days_elapsed < frequency_folder_days(ffolder):
        logger.info('No symlink created : too short delay since last archive')
        return
    target = path.join(target_dir, path.basename(filename))

    if not path.lexists(target):
        if not path.exists(target_dir):
            makedirs(target_dir)
        logger.info('Creating symlink %s' % target)
        symlink(path.join('..', path.basename(filename)), target)
    else:
        logger.error('%s already exists' % target)
        return
    return True


def rotate(filename, ffolder, _remove, cfg):
    """Keep only the n last links of folder that matches same pattern than filename.
    """
    others_ffolders = [x.split('|')[0].upper() for x in set(cfg.keys()) - set([ffolder])]
    target_dir = path.abspath(path.join(path.dirname(filename), ffolder.split('|')[0]))
    # sort new -> old
    links = list(archives_create_days(target_dir, cfg['pattern']).values())[::-1]

    for link in links[cfg[ffolder.lower()]:]:  # skip the n most recents
        filepath = path.realpath(link)
        logger.info('Unlinking %s' % link)
        unlink(link)
        if _remove and not is_symlinked(filepath, others_ffolders):
            if path.isfile(filepath):
                remove(filepath)
            elif path.isdir(filepath):
                rmtree(filepath)


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
                res['pattern'] = key
                return res


@click.command(context_settings=dict(help_option_names=['-h', '--help']),
               help=('Keep rotated time-spaced archives of files. FILES names must match one of '
                     ' the patterns present in %s.' % CONFIG_PATH),
               epilog=('See https://github.com/Kraymer/cronicle/blob/master/README.md#usage for '
                       'more infos'))
@click.argument('filenames', type=click.Path(exists=True), metavar='FILES', nargs=-1)
@click.option('-r', '--remove', '_remove',
    help='Remove previous file backup when no symlink points to it.',
    default=False, is_flag=True)
@click.option('-d', '--dry-run', count=True,
              help='Just print instead of writing on filesystem.')
@click.option('-v', '--verbose', count=True)
@click.version_option(__version__)
def cronicle_cli(filenames, _remove, dry_run, verbose):
    set_logging(max(verbose, dry_run))
    if dry_run:  # disable functions performing filesystem operations
        globals().update({func: lambda *x: None for func in ('remove', 'symlink', 'unlink')})

    for filename in filenames:
        filename = path.abspath(filename)
        cfg = find_config(filename)
        logger.debug('Config is %s' % cfg)

        if not cfg:
            logger.error('No pattern found in %s that matches %s.' % (
                CONFIG_PATH, filename))
            exit(1)

        for ffolder in [x.upper() for x in set(cfg.keys()) - set(['pattern'])]:
            timed_symlink(filename, ffolder, cfg)
        for ffolder in [x.upper() for x in set(cfg.keys()) - set(['pattern'])]:
            rotate(filename, ffolder, _remove, cfg)


if __name__ == "__main__":
    cronicle_cli()
