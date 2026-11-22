#!/usr/bin/env python3
import gzip
import os
import re
import secrets
import shutil
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path


# Store private backups on B and retain up to 96 timestamped archives.
BACKUP_DIR = Path('/home/ubuntu/backups/portfolio')
KEEP_BACKUPS = 96
BACKUP_NAME = re.compile(r'portfolio-\d{8}T\d{6}Z-[0-9a-f]{16}\.tar\.gz')


def store_backup(source, directory, keep):
    if keep < 1:
        raise ValueError('At least one backup must be retained')
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    # Receive the archive into a temporary file before publishing it.
    fd, temporary = tempfile.mkstemp(prefix='.incoming-', dir=directory)
    try:
        with os.fdopen(fd, 'wb') as destination:
            shutil.copyfileobj(source, destination)
            destination.flush()
            os.fsync(destination.fileno())

        # Check gzip integrity and verify that the essential website files exist.
        with gzip.open(temporary, 'rb') as archive:
            while archive.read(1024 * 1024):
                pass
        with tarfile.open(temporary, 'r:gz') as archive:
            names = {member.name for member in archive if member.isfile()}
        if not {'portfolio/app.py', 'portfolio/requirements.txt',
                'portfolio/templates/week4.html'}.issubset(names):
            raise ValueError('Backup is missing required website files')

        # Publish the verified archive with a UTC timestamp and unique suffix.
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        name = f'portfolio-{timestamp}-{secrets.token_hex(8)}.tar.gz'
        destination = directory / name
        os.link(temporary, destination)
        os.unlink(temporary)

        # Keep the new archive and remove only excess files matching the backup pattern.
        backups = sorted(
            (path for path in directory.iterdir()
             if path != destination and BACKUP_NAME.fullmatch(path.name) and path.is_file()),
            key=lambda path: path.name,
            reverse=True,
        )
        for old_backup in backups[keep - 1:]:
            old_backup.unlink()
        return destination
    finally:
        # Remove incomplete incoming files if validation or publication fails.
        if os.path.exists(temporary):
            os.unlink(temporary)


if __name__ == '__main__':
    # Accept the archive from SSH's standard input with private file permissions.
    os.umask(0o077)
    path = store_backup(sys.stdin.buffer, BACKUP_DIR, KEEP_BACKUPS)
    print(f'Backup saved: {path.name}')
