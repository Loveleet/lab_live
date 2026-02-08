#!/usr/bin/env bash
# Point the cloud app at the DB server (150.241.245.36) so it shows real data.
# Run this FROM YOUR LAPTOP after you have opened port 5432 on the DB server (run open-db-port-for-cloud.sh on 150.241.245.36 first).
#
# Usage: ./scripts/point-cloud-at-db-server.sh

set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] && set -a && . ./.env && set +a

DEPLOY_HOST="${DEPLOY_HOST:?Set DEPLOY_HOST in .env}"
# Same credentials as Render used (server copy.js): 150.241.245.36, postgres, IndiaNepal1-, labdb2, no SSL
DB_SERVER_IP="150.241.245.36"
DB_USER="postgres"
DB_PASS="IndiaNepal1-"
DB_PORT="5432"
DB_NAME="labdb2"

echo "→ Pointing cloud at DB server $DB_SERVER_IP (postgres / labdb2, same as Render)..."
# Ensure all five vars (server copy.js). Sed replaces if line exists; app defaults are postgres/5432/labdb2 anyway.
SSHPASS="$DEPLOY_PASSWORD" sshpass -e ssh -o StrictHostKeyChecking=no "$DEPLOY_HOST" "
  sudo sed -i 's/^DB_HOST=.*/DB_HOST=$DB_SERVER_IP/' /etc/lab-trading-dashboard.env
  sudo sed -i 's/^DB_USER=.*/DB_USER=$DB_USER/' /etc/lab-trading-dashboard.env
  sudo sed -i 's/^DB_PASSWORD=.*/DB_PASSWORD=$DB_PASS/' /etc/lab-trading-dashboard.env
  sudo sed -i 's/^DB_PORT=.*/DB_PORT=$DB_PORT/' /etc/lab-trading-dashboard.env
  sudo sed -i 's/^DB_NAME=.*/DB_NAME=$DB_NAME/' /etc/lab-trading-dashboard.env
  grep -E '^DB_HOST=|^DB_USER=|^DB_NAME=' /etc/lab-trading-dashboard.env || true
  sudo systemctl restart lab-trading-dashboard
"
echo "→ Waiting 30s for app to connect..."
sleep 30
echo "→ Checking /api/debug..."
curl -s "http://150.241.244.130:10000/api/debug" | python3 -m json.tool 2>/dev/null || curl -s "http://150.241.244.130:10000/api/debug"
echo ""
echo "→ If alltraderecords is now 500+, refresh http://150.241.244.130:10000 for real data."
echo "→ If still 2 or connection failed, run open-db-port-for-cloud.sh ON the DB server (150.241.245.36) first."
