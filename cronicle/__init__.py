import click
import glob
import logging

from collections import OrderedDict
from datetime import datetime
from dateutil.relativedelta import relativedelta
from os import (lstat, makedirs, path, remove, symlink, unlink)

from .config import config


__author__ = 'Fabrice Laporte <kraymer@gmail.com>'
__version__ = '0.1.0'
logger = logging.getLogger(__name__)

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


def butterify(functions):
    """Replace functions in global scope by debug functions that print their name and arguments.
       pour du beurre: idiom. for nothing, without effect
    """
    def _butterify(func):
        def beurre(*arg):
            logger.info("Calling '%s' with %s" % (func, list(arg)))
        return beurre

    globals().update({func: _butterify(func) for func in functions})


def get_symlinks_dates(folder, pattern='*'):
    """Return OrderedDict of symlinks sorted by creation dates (used as keys).
    """
    creation_dates = {}
    abs_pattern = path.join(folder, pattern)
    logger.debug('Scanning %s for symlinks' % abs_pattern)
    for x in glob.glob(abs_pattern):
        if path.islink(x):
            creation_dates[datetime.fromtimestamp(lstat(x).st_birthtime)] = x
    res = OrderedDict(sorted(creation_dates.items()))
    return res


def delta_days(folder, cfg):
    """Return nb of elapsed days since last archive in given folder.
    """
    files_dates = get_symlinks_dates(folder, cfg['pattern'])
    if files_dates:
        last_file_date = list(files_dates.keys())[-1]
        return relativedelta(datetime.now(), last_file_date).days


def timed_symlink(filename, ffolder, cfg):
    """Create symlink for filename in ffolder if enough days elapsed since last archive.
       Return True if symlink created.
    """
    target_dir = path.abspath(path.join(path.dirname(filename), ffolder))
    days_elapsed = delta_days(target_dir, cfg)
    if (days_elapsed is not None) and days_elapsed < FREQUENCY_FOLDER_DAYS[ffolder]:
        logger.info('No symlink created : too short delay since last archive')
        return
    target = path.join(target_dir, path.basename(filename))

    if not path.lexists(target):
        if not path.exists(target_dir):
            makedirs(target_dir)
        symlink(filename, target)
    else:
        logger.error('%s already exists' % target)
        return
    return True


def rotate(filename, ffolder, _remove, cfg):
    """Keep only the n last links of folder that matches same pattern than filename.
    """
    others_ffolders = set(FREQUENCY_FOLDER_DAYS.keys()) - set([ffolder])
    target_dir = path.abspath(path.join(path.dirname(filename), ffolder))
    links = list(get_symlinks_dates(target_dir, cfg['pattern']).values())[::-1]  # sort new -> old

    for link in links[cfg[ffolder.lower()]:]:  # skip the n most recents
        filepath = path.realpath(link)
        unlink(link)
        if _remove and not is_symlinked(filepath, others_ffolders):
            remove(filepath)


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
    res = {'daily': 0, 'weekly': 0, 'monthly': 0, 'yearly': 0, 'pattern': '*'}
    dirname, basename = path.split(filename)

    if not cfg:
        cfg = config
    # Overwrite default config fields with matched config ones
    for key in cfg.keys():
        abskey = path.join(dirname, key) if not path.isabs(key) else key
        for x in glob.glob(abskey):
            if x.endswith(filename):
                res.update(config[key].get())
                res['pattern'] = key
                return res


@click.command(context_settings=dict(help_option_names=['-h', '--help']),
               help=('Keep rotated time-spaced archives of files. FILES names must match one of '
                     ' the patterns present in %s.' % CONFIG_PATH),
               epilog=('See https://github.com/Kraymer/cronicle/blob/master/README.md#usage for '
                       'more inf'))
@click.argument('filenames', type=click.Path(exists=True), metavar='FILES', nargs=-1)
@click.option('-r', '--remove', help='Remove previous file backup when no symlink points to it.',
    default=False, is_flag=True)
@click.option('-d', '--dry-run', count=True,
              help='Just print instead of writing on filesystem.')
@click.option('-v', '--verbose', count=True)
@click.version_option(__version__)
def cronicle_cli(filenames, remove, dry_run, verbose):
    set_logging(max(verbose, dry_run))
    if dry_run:
        butterify(('remove', 'symlink', 'unlink'))

    for filename in filenames:
        filename = path.abspath(filename)
        cfg = find_config(filename)
        logger.debug('Config is %s' % cfg)

        if not cfg:
            logger.error('No pattern found in %s that matches %s.' % (
                CONFIG_PATH, filename))
            exit(1)

        for ffolder in FREQUENCY_FOLDER_DAYS.keys():
            if cfg[ffolder.lower()]:
                timed_symlink(filename, ffolder, cfg) and rotate(filename, ffolder, remove, cfg)


if __name__ == "__main__":
    cronicle_cli()
