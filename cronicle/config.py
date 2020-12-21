import logging
import confuse

config = confuse.Configuration("cronicle", __name__)


def set_logging(verbose=False):
    """Set logging level based on verbose flag."""
    levels = {0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}
    logging.basicConfig(level=levels[verbose], format="%(levelname)s: %(message)s")
