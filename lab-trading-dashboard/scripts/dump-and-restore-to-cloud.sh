#!/usr/bin/env bash
# Dump the FULL database (from a host you can reach from this machine) and restore it on the cloud.
# Use this when the cloud has only 2 rows and you have access to the DB with 927+ trades (e.g. from laptop to Render DB or 150.241.245.36).
#
# 1. In .env add (use the same host/user/pass as your Render/Vercel backend uses for Postgres):
#    FULL_DB_HOST=your-db-host.example.com
#    FULL_DB_USER=postgres
#    FULL_DB_PASSWORD=yourpassword
#    FULL_DB_NAME=labdb2
# 2. Run from repo root: ./scripts/dump-and-restore-to-cloud.sh
#
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] && set -a && . ./.env && set +a

FULL_DB_HOST="${FULL_DB_HOST:?Set FULL_DB_HOST in .env (the DB that has all the trades)}"
FULL_DB_USER="${FULL_DB_USER:-postgres}"
FULL_DB_PASSWORD="${FULL_DB_PASSWORD:?Set FULL_DB_PASSWORD in .env}"
FULL_DB_NAME="${FULL_DB_NAME:-labdb2}"
DEPLOY_HOST="${DEPLOY_HOST:?Set DEPLOY_HOST in .env}"
DEPLOY_PASSWORD="${DEPLOY_PASSWORD:?Set DEPLOY_PASSWORD in .env}"

DUMP_FILE="/tmp/labdb2-full.dump"
echo "→ Dumping from $FULL_DB_HOST (database: $FULL_DB_NAME)..."
PGPASSWORD="$FULL_DB_PASSWORD" pg_dump -h "$FULL_DB_HOST" -U "$FULL_DB_USER" -d "$FULL_DB_NAME" -F c -f "$DUMP_FILE" || {
  echo "Failed to pg_dump. Can you reach $FULL_DB_HOST:5432 from this machine? Check FULL_DB_* in .env."
  exit 1
}
SIZE=$(ls -la "$DUMP_FILE" | awk '{print $5}')
echo "→ Dump size: $SIZE bytes"

echo "→ Uploading dump to $DEPLOY_HOST..."
SSHPASS="$DEPLOY_PASSWORD" sshpass -e scp -o StrictHostKeyChecking=no "$DUMP_FILE" "$DEPLOY_HOST:/tmp/labdb2.dump"

echo "→ Restoring on cloud and restarting app..."
SSHPASS="$DEPLOY_PASSWORD" sshpass -e ssh -o StrictHostKeyChecking=no "$DEPLOY_HOST" "sudo -u postgres psql -c \"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'labdb2' AND pid <> pg_backend_pid();\" 2>/dev/null || true; sudo -u postgres psql -c 'DROP DATABASE IF EXISTS labdb2;'; sudo -u postgres psql -c 'CREATE DATABASE labdb2 OWNER postgres;'; sudo -u postgres pg_restore -d labdb2 -F c /tmp/labdb2.dump || true; sudo systemctl restart lab-trading-dashboard"
rm -f "$DUMP_FILE"
echo "→ Done. Refresh http://150.241.244.130:10000 and check /api/debug for row counts."
curl -s "http://150.241.244.130:10000/api/debug" | python3 -m json.tool 2>/dev/null || true
