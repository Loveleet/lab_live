#!/usr/bin/env bash
# Run FROM LAPTOP (one time). Copies update script to cloud and installs cron
# so API_BASE_URL is kept in sync after reboot and every 10 min.
# Pages URL: https://loveleet.github.io/lab_live/
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"
[ -f .env ] && set -a && . ./.env && set +a
[ -f ../.env ] && set -a && . ../.env && set +a
DEPLOY_HOST="${DEPLOY_HOST:?}"
APP_DIR="/opt/apps/lab-trading-dashboard"
LOG="/var/log/lab-tunnel-update.log"

echo "→ Copying update script to cloud..."
SSHPASS="${DEPLOY_PASSWORD}" sshpass -e scp -o StrictHostKeyChecking=no \
  "$SCRIPT_DIR/update-github-secret-from-tunnel.sh" \
  "$DEPLOY_HOST:/tmp/"

echo "→ Installing script and crontab on cloud..."
SSHPASS="$DEPLOY_PASSWORD" sshpass -e ssh -o StrictHostKeyChecking=no "$DEPLOY_HOST" "
  sudo mkdir -p $APP_DIR/scripts
  sudo mv /tmp/update-github-secret-from-tunnel.sh $APP_DIR/scripts/
  sudo chmod +x $APP_DIR/scripts/update-github-secret-from-tunnel.sh
  (crontab -l 2>/dev/null | grep -v 'update-github-secret-from-tunnel' | grep -v 'lab-tunnel-update'; echo '@reboot sleep 90 && /opt/apps/lab-trading-dashboard/scripts/update-github-secret-from-tunnel.sh >> /var/log/lab-tunnel-update.log 2>&1'; echo '*/10 * * * * /opt/apps/lab-trading-dashboard/scripts/update-github-secret-from-tunnel.sh >> /var/log/lab-tunnel-update.log 2>&1') | crontab -
"
echo "→ Done. After cloud reboot, tunnel URL will be synced to GitHub; then open https://loveleet.github.io/lab_live/ and hard-refresh."
