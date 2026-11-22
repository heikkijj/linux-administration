#!/bin/bash
# Stop on errors and restrict access to newly created files.
set -euo pipefail
umask 077

# Record output and errors in the user's backup log.
state_dir="$HOME/.local/state/portfolio-backup"
mkdir -p "$state_dir" || exit 1
exec >> "$state_dir/backup.log" 2>&1

# Add a UTC timestamp to each log entry.
log() {
    printf '%s %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$1"
}

# Prevent overlapping backup runs.
exec 9>"$state_dir/backup.lock"
if ! flock -n 9; then
    log "FAILED: another backup is still running"
    exit 1
fi

log "START: portfolio backup"
# Create the archive locally first and remove the temporary file afterward.
if archive=$(mktemp "$state_dir/.website-archive.XXXXXXXX"); then
    trap 'rm -f -- "$archive"' EXIT
else
    log "FAILED: could not create temporary archive"
    exit 1
fi

# Exclude the virtual environment, caches and temporary status-report files.
# Find lists the files; tar does not scan the directories again.
if (cd /home/ubuntu && find portfolio \
    \( -path 'portfolio/.venv' -o -name '__pycache__' -o -name '*.pyc' \
       -o -path 'portfolio/static/.status-report.*' \) -prune -o -print0) |
    tar -C /home/ubuntu --null --no-recursion -czf "$archive" -T -; then
    :
else
    result=$?
    log "FAILED: creating archive (exit $result)"
    exit "$result"
fi

# Send the completed archive to B using a dedicated SSH key.
# Verify the server's host key against the previously saved key.
if ssh -F /dev/null -T \
        -i "$HOME/.ssh/portfolio-backup-ed25519" \
        -o IdentitiesOnly=yes \
        -o BatchMode=yes \
        -o ConnectTimeout=15 \
        -o ServerAliveInterval=30 \
        -o ServerAliveCountMax=3 \
        -o StrictHostKeyChecking=yes \
        -o UserKnownHostsFile="$HOME/.ssh/portfolio-backup-known-hosts" \
        -o GlobalKnownHostsFile=/dev/null \
        ubuntu@192.168.1.33 < "$archive"; then
    # A successful SSH command means B accepted and saved the archive.
    log "SUCCESS: portfolio backup"
else
    result=$?
    log "FAILED: portfolio backup (exit $result)"
    exit "$result"
fi
