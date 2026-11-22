# Portfolio

A Flask portfolio site for the Linux administration course. Install dependencies
with `pip install -r requirements.txt` and run the app with `python app.py`.
The default counter backend is the local SQLite database.

## Week 4 deployment

The site uses two cPouta servers. Server A runs the application as the source;
Server B runs a read-only replica. The Week 4 page documents the deployment
and test results.

For MariaDB, set `COUNTER_BACKEND=mariadb`, `COUNTER_ROLE=source` on A or
`COUNTER_ROLE=replica` on B, and `COUNTER_DB_CONFIG` to a private client
configuration file. Keep database passwords and SSH keys outside the
repository.

Sanitized replication examples are in `deploy/mariadb-source.example.cnf`,
`deploy/mariadb-replica.example.cnf`, and
`deploy/mariadb-replication.example.sql`. Check the server addresses and use
the binary-log coordinates from the initial database snapshot before applying
them. Restrict MariaDB network access to the required server addresses.

## Website backups

Server A's `ubuntu` cron runs `scripts/backup-website.sh` every 15 minutes.
Server B receives timestamped archives under
`/home/ubuntu/backups/portfolio`, outside the public web directory, and keeps
the 96 newest. A records each run in
`~/.local/state/portfolio-backup/backup.log`.
Recorded backup and replication checks are in
[week4-verification.txt](week4-verification.txt).

The archive covers the website files, not the live database or private
system-level configuration. MariaDB replication is not a substitute for
versioned backups because unwanted changes can replicate too.

## Tests

Run the tests from the repository root with:

```sh
python -m unittest discover -s portfolio
```
