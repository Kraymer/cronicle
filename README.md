## cronicle

> /ˈkɹɒnɪkəl/
>     1. *n.* a factual written account of important events in the order of their occurrence
>     2. *n.* software triggered via cron job to archive the N most recent versions of a file in a folder named after the job frequency

Originally, `cronicle` has been conceived as a solution to this particular [serverfault](https://serverfault.com) question : [How to keep: daily backups for a week, weekly for a month, monthly for a year, and yearly after that](https://serverfault.com/questions/575163/how-to-keep-daily-backups-for-a-week-weekly-for-a-month-monthly-for-a-year-a)

### Features

- add one line to your `crontab` and you're done
- keep the N most recent versions of a file
- use symlinks in target directories to store a single occurence of each file instead of performing copies

### `crontab` example

    # Backup a postgres database keeping 7 daily backups,
    # 4 weekly and 12 monthly.
    @daily pg_dump -Fc mydb > mydb-`date +%F`.dump.bin
    @daily cronicle mydb-`date +%F`.dump.bin /home/bob/backups/ DAILY 7
    @weekly cronicle mydb-`date +%F`.dump.bin /home/bob/backups/ WEEKLY 4
    @monthly cronicle mydb-`date +%F`.dump.bin /home/bob/backups/ MONTHLY 12




