import click
import glob
import logging
import os

from collections import OrderedDict
from datetime import datetime
from dateutil.relativedelta import relativedelta

from .config import config


__author__ = 'Fabrice Laporte <kraymer@gmail.com>'
__version__ = '0.1.0'
logger = logging.getLogger(__name__)

DELTA_DAYS = {
    'DAILY': 1,
    'WEEKLY': 7,
    'MONTHLY': 30,
    'YEARLY': 365,
}
CONFIG_PATH = os.path.join(config.config_dir(), 'config.yaml')


def set_logging(verbose=False):
    """Set logging level based on verbose flag.
    """
    levels = {0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}
    logger.setLevel(levels[verbose])
    ch = logging.StreamHandler()
    ch.setLevel(levels[verbose])
    ch.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    logger.addHandler(ch)


def get_symlinks_dates(folder, pattern='*'):
    """Return OrderedDict of symlinks sorted by creation dates (used as keys).
    """
    creation_dates = {}
    for x in glob.glob(os.path.join(os.getcwd(), folder, pattern)):  # join with current dir
        if os.path.islink(x):
            creation_dates[datetime.fromtimestamp(os.lstat(x).st_birthtime)] = x
    res = OrderedDict(sorted(creation_dates.items()))
    return res


def delta_days(folder):
    """Return nb of elapsed days since last archive in given periodic folder.
       period: one of 'daily', 'weekly', 'monthly', 'yearly'
    """
    files_dates = get_symlinks_dates(folder)
    if files_dates:
        last_file_date = files_dates.keys()[-1]
        res = relativedelta(datetime.now(), last_file_date)
        return res.days


def symlink(filename, target, dry_run):
    logger.info('Symlinking %s => %s' % (target, filename))
    if dry_run:
        return
    target_dir = os.path.dirname(target)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    os.symlink(filename, target)


def unlink(link, dry_run):
    if dry_run:
        logger.info('Unlinking %s' % link)
        return
    else:
        os.unlink(link)


def timed_symlink(filename, folder, cfg, dry_run):
    """Create daily, ..., yearly symlinks for filename if enough days elapsed since last archive.
    """
    days_elapsed = delta_days(folder)
    if (days_elapsed is not None) and days_elapsed < DELTA_DAYS[folder]:
        logger.info('Too short delay since last archive')
        return
    target_dir = os.path.join(os.path.dirname(filename), folder)
    target = os.path.abspath(os.path.join(target_dir, os.path.basename(filename)))

    if not os.path.lexists(target):
        symlink(filename, target)
    else:
        logger.error('%s already exists' % target)


def rotate(filename, folder, cfg, dry_run=False):
    """Keep only the n last links of folder that matches same pattern than filename.
    """
    links = get_symlinks_dates(folder, cfg['pattern']).values()[::-1]
    for link in links[cfg[folder.lower()]:]:  # sort newest -> oldest
        unlink(link)


def find_config(filename, cfg=None):
    """Return the config matched by filename or the default one.
    """
    res = {'daily': 0, 'weekly': 0, 'monthly': 0, 'yearly': 0,
           'pattern': '*'}
    dirname, basename = os.path.split(filename)

    if not cfg:
        cfg = config
    # Overwrite default config fields with matched config ones
    for key in cfg.keys():
        abskey = os.path.join(dirname, key) if not os.path.isabs(key) else key
        for x in glob.glob(abskey):
            if x.endswith(filename):
                res.update(config[key].get())
                res['pattern'] = key
                return res


@click.command(context_settings=dict(help_option_names=['-h', '--help']),
               help=('Keep rotated time-spaced archives of a file. FILE name must match one of '
                     ' the patterns present in %s.' % CONFIG_PATH),
               epilog=('See https://github.com/Kraymer/cronicle/blob/master/README.md#usage for '
                       ' more infos.'))
@click.argument('filename', type=click.Path(exists=True), metavar='FILE')
@click.option('-d', '--dry-run', count=True,
              help=('Just print instead of writing on filesystem.'))
@click.option('-v', '--verbose', count=True)
@click.version_option(__version__)
def cronicle_cli(filename, dry_run, verbose):
    """Blah bla plop"""
    set_logging(max(verbose, dry_run))
    filename = os.path.abspath(filename)
    cfg = find_config(filename)
    if not cfg:
        logger.error('No pattern found in %s that matches %s.' % (
            CONFIG_PATH, filename))
        exit(1)

    for period in DELTA_DAYS.keys():
        if cfg[period.lower()]:
            timed_symlink(filename, period, cfg, dry_run)
            rotate(filename, period, cfg, dry_run)


if __name__ == "__main__":
    cronicle_cli()
