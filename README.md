## cronicle

> /ˈkɹɒnɪkəl/
>     1. *n.* a factual written account of important events in the order of their occurrence
>     2. *n.* software, to trigger via cron job, that archives the *N* most recent versions of a file in a folder named after the job frequency

Originally, `cronicle` has been conceived as a solution to this particular [serverfault](https://serverfault.com) question :   [How to keep: daily backups for a week, weekly for a month, monthly for a year, and yearly after that](https://serverfault.com/questions/575163/how-to-keep-daily-backups-for-a-week-weekly-for-a-month-monthly-for-a-year-a)

### Features

- **simplicity:** add one line to your `crontab` and you're done
- **files rotation:** keep the N most recent versions of a file
- **space efficient:** use symlinks in target directories to store a single occurence of each file instead of performing copies. When removing a link, remove the underlying file if no other link point to it.

### Usage

    cronicle FILE

    Keep rotated time-spaced archives of a file.


### `crontab` example

    # Backup a postgres database keeping 7 daily backups, 4 weekly and 12 monthly
    @daily pg_dump -Fc mydb > /home/bob/backups/mydb-`date +%F`.dump.bin
    @daily cronicle /home/bob/backups/mydb-`date +%F`.dump.bin

And in your `config.yaml` :

    mydb-*.dump.bin:
        daily: 7
        weekly: 4
        monthly: 12


