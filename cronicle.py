import click
import glob
import os
from dateutil.parser import parse as date_parse


def get_diff(basename, candidate):
    """
    Return candidate truncated from its common prefix and suffix with basename.
    """
    start = end = None
    for idx, _ in enumerate(candidate):
        try:
            if not start and candidate[idx] != basename[idx]:
                start = idx
            if not end and candidate[-1 - idx] != basename[-1 - idx]:
                end = 0 - idx
        except IndexError:
            return
    return candidate[start:end]


def find_archives(filename, target_dir):
    """
    Return archives of filename.
    An archive is a file located in target_dir and that is named same as filename except for a date
    or numbering section.
    """
    archives = []
    _, basename = os.path.split(filename)
    candidates = [os.path.basename(x) for x in
        glob.glob('%s/*%s' % (target_dir, os.path.splitext(filename)[1]))]
    for candidate in candidates:
        diff = get_diff(basename, candidate)
        try:
            if diff.isdigit() or date_parse(diff):
                archives.append(candidate)
        except ValueError:  # parse error
            pass
    return archives


def prune_dir(_dir, filename, max_files):
    """Prune directory to keep only the max_files most recent archives.
    """
    archives = find_archives(filename, _dir)
    print(archives)



@click.argument('filename', type=click.Path(exists=True), metavar='FILE')
@click.argument('target_dir', type=click.Path(exists=True), metavar='DIR')
@click.argument('num_archives', type=int, metavar='NUM_ARCHIVES')
def cronicle_cli(filename, target_dir, num_archives=3):
    # cd target_dir
    # if not last_instance:
    #     ln -symlink
    os.chdir(target_dir)
    os.symlink(filename, filename.basename())
    prune_dir(target_dir, filename, num_archives)

    # if len(archives) > NUM_ARCHIVES:
    #     for archive in archives[NUM_ARCHIVES:]:
    #         cd(dir(pattern))
    #         links = find -L . -samefile ${OUTDATED_FILES[$i]} | wc -l | xargs
    #         if no links:
    #             delete
    #         else:
    #             unlink

# if __name__ == "__main__":
#     print("""
# cronicle FILENAME DEST_DIR NUM_ARCHIVES

# Add a symlink to FILE_NAME in DEST_DIR, keep last NUM_ARCHIVES links in DEST_DIR that points to a
# previous file archive.
# When removing a link, remove the underlying file if no other link point to it.
#         """)
#     cronicle_cli()
