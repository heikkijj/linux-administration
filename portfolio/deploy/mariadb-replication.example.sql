-- Run on Server A. Replace the placeholder locally; never commit a real secret.
CREATE USER 'replicator'@'192.168.1.33' IDENTIFIED BY '<SET_SECRET_LOCALLY>';
GRANT REPLICATION SLAVE ON *.* TO 'replicator'@'192.168.1.33';

-- Run on Server B after importing A's matching initial database snapshot.
-- Use the binary-log file and position recorded in that snapshot.
CHANGE MASTER TO
    MASTER_HOST = '192.168.1.189',
    MASTER_USER = 'replicator',
    MASTER_PASSWORD = '<SET_SECRET_LOCALLY>',
    MASTER_LOG_FILE = '<SNAPSHOT_BINLOG_FILE>',
    MASTER_LOG_POS = <SNAPSHOT_BINLOG_POSITION>;
START SLAVE;

-- Check that both replication threads are running and there are no errors.
SHOW SLAVE STATUS\G
