#!/usr/bin/env bash
# One script to fix real data: open port on DB server (if we can SSH), then point cloud at DB server.
# Passwords: cloud = DEPLOY_PASSWORD (9988609709), Postgres on DB server = IndiaNepal1-
#
# Usage: ./scripts/fix-real-data.sh

set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] && set -a && . ./.env && set +a

DEPLOY_HOST="${DEPLOY_HOST:?}"
DB_SERVER="${DB_SERVER:-root@150.241.245.36}"
DB_SERVER_IP="150.241.245.36"
# Same as Render (server copy.js): postgres / IndiaNepal1- / labdb2 / port 5432 / no SSL
DB_USER="postgres"
PG_PASS="IndiaNepal1-"
DB_PORT="5432"
DB_NAME="labdb2"

echo "=============================================="
echo "  Fix real data on cloud"
echo "=============================================="

# Step 1: Try to run open-db-port on DB server (SSH with password from .env)
echo ""
echo "→ Step 1: Open port 5432 on DB server (150.241.245.36)..."
if [ -n "${DB_SERVER_PASSWORD:-}" ]; then
  if SSHPASS="$DB_SERVER_PASSWORD" sshpass -e scp -o StrictHostKeyChecking=no -o ConnectTimeout=10 scripts/open-db-port-for-cloud.sh "$DB_SERVER:/tmp/" 2>/dev/null; then
    SSHPASS="$DB_SERVER_PASSWORD" sshpass -e ssh -o StrictHostKeyChecking=no "$DB_SERVER" "sudo bash /tmp/open-db-port-for-cloud.sh" && echo "  Port opened."
  else
    echo "  SSH to DB server failed (wrong password or key-only). Run open-db-port-for-cloud.sh manually on 150.241.245.36 (see FIX_REAL_DATA.md), then run this script again."
  fi
else
  echo "  Set DB_SERVER_PASSWORD in .env for SSH to DB server, or run open-db-port manually on the DB server."
fi

# Step 2: From cloud, check if port is reachable
echo ""
echo "→ Step 2: Check if cloud can reach DB server:5432..."
if SSHPASS="$DEPLOY_PASSWORD" sshpass -e ssh -o StrictHostKeyChecking=no "$DEPLOY_HOST" "timeout 3 bash -c 'echo > /dev/tcp/$DB_SERVER_IP/5432' 2>/dev/null"; then
  echo "  Port 5432 is reachable from cloud."
else
  echo "  Port 5432 NOT reachable from cloud. Open it on the DB server (see Step 1), then run: ./scripts/point-cloud-at-db-server.sh"
  exit 1
fi

# Step 3: Point cloud at DB server with same credentials as Render (server copy.js)
echo ""
echo "→ Step 3: Point cloud at DB server (postgres / labdb2 / IndiaNepal1-)..."
SSHPASS="$DEPLOY_PASSWORD" sshpass -e ssh -o StrictHostKeyChecking=no "$DEPLOY_HOST" "
  sudo sed -i 's/^DB_HOST=.*/DB_HOST=$DB_SERVER_IP/' /etc/lab-trading-dashboard.env
  sudo sed -i 's/^DB_USER=.*/DB_USER=$DB_USER/' /etc/lab-trading-dashboard.env
  sudo sed -i 's/^DB_PASSWORD=.*/DB_PASSWORD=$PG_PASS/' /etc/lab-trading-dashboard.env
  sudo sed -i 's/^DB_PORT=.*/DB_PORT=$DB_PORT/' /etc/lab-trading-dashboard.env
  sudo sed -i 's/^DB_NAME=.*/DB_NAME=$DB_NAME/' /etc/lab-trading-dashboard.env
  sudo systemctl restart lab-trading-dashboard
"
echo "  Restarted app. Waiting 35s for DB connection..."
sleep 35

# Step 4: Verify
echo ""
echo "→ Step 4: Verify /api/debug..."
curl -s "http://150.241.244.130:10000/api/debug" | python3 -m json.tool 2>/dev/null || curl -s "http://150.241.244.130:10000/api/debug"
echo ""
echo "=============================================="
echo "  Refresh http://150.241.244.130:10000 for real data."
echo "=============================================="
