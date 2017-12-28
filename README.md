## cronicle

> /ˈkɹɒnɪkəl/  
>     1. *n.* a factual written account of important events in the order of their occurrence  
>     2. *n.* software to archive the *N* most recent backups of a file in a folder named after the job frequency. Recommended use is to trigger it via a cron job.

**Originally, `cronicle` has been conceived as a solution to this particular [serverfault](https://serverfault.com) question :   [How to keep: daily backups for a week, weekly for a month, monthly for a year, and yearly after that](https://serverfault.com/questions/575163/how-to-keep-daily-backups-for-a-week-weekly-for-a-month-monthly-for-a-year-a)**

### Features

- **simplicity:** add one line to your `crontab` and you're done
- **files rotation:** keep the N most recent versions of a file
- **space efficient:** use symlinks in target directories to store a single occurence of each backup instead of performing copies. When removing a link, remove the underlying file if no other link point to it.

### Usage

    Usage: cronicle.py [OPTIONS] FILE

      Keep rotated time-spaced archives of backup files. FILE name must match one of the patterns present in /Users/johndoe/.config/cronicle/config.yaml.

    Options:
      -d, --dry-run  Just print instead of writing on filesystem.
      -v, --verbose
      --version      Show the version and exit.
      -h, --help     Show this message and exit.

      See https://github.com/Kraymer/cronicle/blob/master/README.md#usage for more infos

In order to manage a file backups with cronicle, you must have a section
in the `config.yaml` that matches the backups names.
Under it, you can then define values for the four kinds of periodic archives : `daily`, `weekly`, `monthly`, `yearly`.

### Example

If you have dumps of a database in your `$HOME` directory named like `mydb-20170101.dump`, `mydb-20170102.dump`, and want to keep each dump for 7 days ; a working `config.yaml` content would be :

    /home/johndoe/mydb-*.dump:
        daily: 7


### `cron` triggering

For a no-brainer use, I recommend to run cronicle via cron, just after the command in charge of performing the backup. A `crontab` example :

    @daily pg_dump -Fc mydb > /home/bob/backups/mydb-`date +%F`.dump
    @daily cronicle /home/bob/backups/mydb-`date +%F`.dump



