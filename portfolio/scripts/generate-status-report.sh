#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
OUTPUT_DIR="$PROJECT_DIR/static"
REPORT_FILE="$OUTPUT_DIR/status-report.html"

mkdir -p "$OUTPUT_DIR"

GENERATED_AT="$(date '+%Y-%m-%d %H:%M:%S %Z (%z)')"
UPTIME="$(uptime -p)"
DISK_USAGE="$(df -P / | awk 'NR == 2 { gsub(/%/, "", $5); print $5 }')"
DISK_STATUS=""
RAM_INFO="$(free -h | awk '/^Mem:/ { printf "%s total, %s available", $2, $7 }')"

get_disk_status() {
    local usage_percent="$1"

    if [[ ! "$usage_percent" =~ ^[0-9]+$ ]]; then
        printf 'Invalid disk usage percentage: %s\n' "$usage_percent" >&2
        return 1
    fi

    if (( usage_percent < 80 )); then
        printf 'OK'
    else
        printf 'WARNING'
    fi
}

if [[ "${1:-}" == "--test-status" ]]; then
    for test_usage in 50 80 90; do
        printf '%s%% -> %s\n' "$test_usage" "$(get_disk_status "$test_usage")"
    done
    exit 0
fi

DISK_STATUS="$(get_disk_status "$DISK_USAGE")"
TEMP_FILE="$(mktemp "$OUTPUT_DIR/.status-report.XXXXXX")"
trap 'rm -f -- "$TEMP_FILE"' EXIT

cat > "$TEMP_FILE" <<EOF
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Server Status Report</title>
<style>
body { font-family: system-ui, sans-serif; margin: 0; padding: 1rem; line-height: 1.6; background: #102947; color: #fff; }
h1 { margin-top: 0; font-size: 1.5rem; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: .65rem; border: 1px solid #54708c; text-align: left; }
th { width: 40%; background: #173858; }
.status { font-weight: 700; }
</style>
</head>
<body>
<h1>Server Status Report</h1>
<table>
<tbody>
<tr><th>Report generated</th><td>$GENERATED_AT</td></tr>
<tr><th>Server uptime</th><td>$UPTIME</td></tr>
<tr><th>Root filesystem usage</th><td>$DISK_USAGE%</td></tr>
<tr><th>Disk space status</th><td class="status">$DISK_STATUS</td></tr>
<tr><th>Memory</th><td>$RAM_INFO</td></tr>
</tbody>
</table>
</body>
</html>
EOF

mv -- "$TEMP_FILE" "$REPORT_FILE"
trap - EXIT
printf 'Report written to %s\n' "$REPORT_FILE"