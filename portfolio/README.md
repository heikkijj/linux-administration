# Linux administration portfolio

This Flask portfolio documents the course assignments. For Week 4, the original
cPouta server (A) was cloned to create server B.

## Live pages

- [Server A: Week 1](http://193.166.24.18/week1/)
- [Server A: Week 2 visitor counter](http://193.166.24.18/week2/)
- [Server A: Week 3 report](http://193.166.24.18/week3/)
- [Server B: Week 4 documentation and replica counter](http://195.148.20.142/week4/)

Loading the Week 2 page on A increments its MariaDB counter. MariaDB
continuously replicates the change to B, where the Week 4 page reads the local
counter without changing it. B's application uses a read-only database account.

## Website backups

Server A backs up `/home/ubuntu/portfolio` every 15 minutes. A creates an
archive and sends it over SSH to B, where it is checked and saved with a
timestamp under `/home/ubuntu/backups/portfolio`. The private backup directory
is outside the public website. B retains the latest 96 archives; A records
each run in `~/.local/state/portfolio-backup/backup.log`.

The website archive does not contain the live MariaDB database or private
system-level configuration. Replication keeps B up to date but is not a
historical database backup: unwanted changes can also be replicated.

## Repository guide

| File | Contents |
| --- | --- |
| [app.py](app.py) | Flask routes and the source and replica counter logic. |
| [templates/week4.html](templates/week4.html) | Week 4 deployment, permissions, tests and lessons learned. |
| [scripts/backup-website.sh](scripts/backup-website.sh) | Creates the website archive and sends it from A to B. |
| [scripts/receive-portfolio-backup.py](scripts/receive-portfolio-backup.py) | Checks and stores archives on B and removes older versions. |
| [deploy/portfolio-backup.cron](deploy/portfolio-backup.cron) | The backup schedule on A. |
| [deploy/mariadb-source.example.cnf](deploy/mariadb-source.example.cnf) and [deploy/mariadb-replica.example.cnf](deploy/mariadb-replica.example.cnf) | Sanitized examples of the MariaDB source and replica settings. |
| [deploy/mariadb-replication.example.sql](deploy/mariadb-replication.example.sql) | Replication account and connection examples without passwords. |
| [week4-verification.txt](week4-verification.txt) | Recorded backup log entries, saved archive names and replication status. |
