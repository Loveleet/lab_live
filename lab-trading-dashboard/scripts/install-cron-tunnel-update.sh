#!/usr/bin/env bash
# Run ON THE CLOUD (one time). Installs cron so the tunnel URL is synced to GitHub after reboot and every 10 min.
# Paths: /opt/apps/lab-trading-dashboard/scripts/cron-tunnel-update.sh and update-github-secret-from-tunnel.sh

set -e
CRON_WRAPPER="/opt/apps/lab-trading-dashboard/scripts/cron-tunnel-update.sh"
LOG="/var/log/lab-tunnel-update.log"

# Remove any old cron entries for these scripts
crontab -l 2>/dev/null | grep -v 'cron-tunnel-update' | grep -v 'update-github-secret-from-tunnel' | grep -v 'lab-tunnel-update' > /tmp/cron.$$ || true
# Add: @reboot after 90s (so tunnel is up) and every 10 min
echo "@reboot sleep 90 && $CRON_WRAPPER" >> /tmp/cron.$$
echo "*/10 * * * * $CRON_WRAPPER" >> /tmp/cron.$$
crontab /tmp/cron.$$
rm -f /tmp/cron.$$
echo "Cron installed. Entries:"
crontab -l
echo "Log: $LOG"
