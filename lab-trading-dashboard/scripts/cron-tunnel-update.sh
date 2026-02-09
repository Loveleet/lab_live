#!/usr/bin/env bash
# Cron wrapper: log and run the update script (so tunnel URL is synced to GitHub after reboot / every 10 min).
# Install via install-cron-tunnel-update.sh (from laptop: fix-api-config-and-cloud.sh).

set -e
LOG="/var/log/lab-tunnel-update.log"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "$(date -Iseconds) Running cron-tunnel-update.sh" >> "$LOG"
"$SCRIPT_DIR/update-github-secret-from-tunnel.sh" >> "$LOG" 2>&1
