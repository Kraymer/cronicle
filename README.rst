.. image:: https://github.com/kraymer/cronicle/workflows/build/badge.svg
   :target: https://github.com/kraymer/cronicle/actions 
   
.. image:: https://coveralls.io/repos/github/Kraymer/cronicle/badge.svg?branch=master
   :target: https://coveralls.io/github/Kraymer/cronicle?branch=master

.. image:: https://img.shields.io/github/v/release/kraymer/cronicle.svg
   :target: https://github.com/Kraymer/cronicle/releases

cronicle :hourglass\_flowing\_sand::arrows\_counterclockwise::floppy\_disk:
===========================================================================

    **/ˈkɹɒnɪkəl/** :

    1. *n.* a factual written account of important events in the order
       of their occurrence
    2. *n.* software to archive the *N* most recent backups of a file in
       a folder named after the job frequency. Recommended use is to
       trigger it via a cron job.

Originally, ``cronicle`` has been conceived as a solution to this
particular `serverfault <https://serverfault.com>`__ question : `How to
keep: daily backups for a week, weekly for a month, monthly for a year,
and yearly after
that <https://serverfault.com/questions/575163/how-to-keep-daily-backups-for-a-week-weekly-for-a-month-monthly-for-a-year-a>`__.

|asciicast|

Features
--------

-  **simplicity:** add one line to your ``crontab`` and you're done
-  **files rotation:** keep the N most recent versions of a file
-  **space efficient:** use symlinks in target directories to store a
   single occurence of each backup instead of performing copies. When
   removing a link, remove the underlying file if no other link point to
   it.

Usage
-----

In order to manage a file backups with cronicle, you must have a section
in the ``config.yaml`` that matches the backups names. Under it you can
then define values (number of archives to keep) for the five kinds of
periodic archives : ``hourly``, ``daily``, ``weekly``, ``monthly``, ``yearly``.

Or define a custom periodicity using the *pipe syntax* eg
``bimonthly|60: 3`` to keep archives every two months over the last six
months.

Example
-------

If you have dumps of a database in a ``~/dumps`` directory named like
``mydb-20170101.dump``, ``mydb-20170102.dump``, and want to keep each
dump for 7 days plus go back up to two months ; a working
``${HOME}/.config/cronicle/config.yaml`` content would be :

::

    /home/johndoe/dumps/mydb-*.dump:
        daily: 7
        monthly: 2

Next ``cronicle`` call will result in the creation of folders ``DAILY``
and ``MONTHLY`` in ``/home/johndoe/dumps/``, each folder containing
symlinks to the .dump files.

Installation
------------

cronicle is written for `Python
2.7 <https://www.python.org/downloads/>`__ and `Python
3 <https://www.python.org/downloads/>`__, is tested on Linux and Mac OS
X.

Install with `pip <https://pip.pypa.io/en/stable/>`__ via
``pip install git+https://github.com/Kraymer/cronicle.git`` command.

``cron`` triggering
-------------------

For a no-brainer use, I recommend to run cronicle via cron, just after
the command in charge of performing the backup. A ``crontab`` example :

::

    @daily pg_dump -Fc mydb > /home/johndoe/dumps/mydb-`date +%F`.dump
    @daily cronicle -r /home/johndoe/dumps/mydb-`date +%F`.dump

If used with the ``config.yaml`` as defined in the previous section,
this daily call to cronicle guarantees that you will keep at most 9
database dumps (7 latest daily + 2 monthly).


.. |asciicast| image:: https://asciinema.org/a/155861.png
   :target: https://asciinema.org/a/155861

