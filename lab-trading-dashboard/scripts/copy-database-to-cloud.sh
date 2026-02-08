#!/usr/bin/env bash
# Copy labdb2 from DB server (150.241.245.36) to app server (150.241.244.130).
# Run from laptop: needs .env with DEPLOY_HOST, DEPLOY_PASSWORD, and optionally DB_SERVER, DB_SERVER_PASSWORD.
# Run on app server as root from /opt/apps/lab-trading-dashboard: uses /etc/lab-trading-dashboard.env, no SSH to DB needed if 5432 is reachable.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

# When running ON the app server as root from /opt: use system env so permissions work
if [ -f /etc/lab-trading-dashboard.env ] && [ "$(whoami)" = "root" ] && [[ "$REPO_ROOT" == /opt/* ]]; then
  echo "→ Running on app server (root in /opt). Using /etc/lab-trading-dashboard.env"
  set -a && . /etc/lab-trading-dashboard.env && set +a
  DB_PASS="${DB_PASSWORD:-IndiaNepal1-}"
  echo "→ Step 1: pg_dump from this host to DB 150.241.245.36..."
  if PGPASSWORD="$DB_PASS" pg_dump -h 150.241.245.36 -U postgres -d labdb2 -F c -f /tmp/labdb2.dump 2>/dev/null; then
    echo "→ Dump created. Restoring locally..."
    sudo -u postgres psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'labdb2' AND pid <> pg_backend_pid();" 2>/dev/null || true
    sudo -u postgres psql -c "DROP DATABASE IF EXISTS labdb2;"
    sudo -u postgres psql -c "CREATE DATABASE labdb2 OWNER postgres;"
    sudo -u postgres pg_restore -d labdb2 -F c /tmp/labdb2.dump || true
    sudo systemctl restart lab-trading-dashboard
    echo "→ Done. Refresh http://150.241.244.130:10000"
    exit 0
  else
    echo "→ Direct pg_dump failed (is 150.241.245.36:5432 open for this host?). Use copy from laptop or open DB port."
    exit 1
  fi
fi

# From laptop: load .env
[ -f .env ] && set -a && . ./.env && set +a
DB_SERVER="${DB_SERVER:-root@150.241.245.36}"
DB_SERVER_PASSWORD="${DB_SERVER_PASSWORD:-$DEPLOY_PASSWORD}"
APP_SERVER="${DEPLOY_HOST:?Set DEPLOY_HOST in .env}"

if [ -z "${DEPLOY_PASSWORD:-}" ]; then
  echo "Set DEPLOY_PASSWORD (and optionally DB_SERVER_PASSWORD) in .env"
  exit 1
fi

# Ensure app server has this script (root in /opt), then run it there
echo "→ Step 1a: Run copy on app server (root in /opt/apps/lab-trading-dashboard)..."
SSHPASS="$DEPLOY_PASSWORD" sshpass -e scp -o StrictHostKeyChecking=no "$REPO_ROOT/scripts/copy-database-to-cloud.sh" "$APP_SERVER:/opt/apps/lab-trading-dashboard/scripts/" 2>/dev/null || true
if SSHPASS="$DEPLOY_PASSWORD" sshpass -e ssh -o StrictHostKeyChecking=no "$APP_SERVER" \
  "cd /opt/apps/lab-trading-dashboard && sudo ./scripts/copy-database-to-cloud.sh"; then
  echo "→ Database copy complete. Refresh http://150.241.244.130:10000"
  exit 0
fi

# Fallback: run pg_dump on app server (root in /opt) via single SSH
echo "→ Step 1b: Run copy script on app server (root in /opt)..."
if SSHPASS="$DEPLOY_PASSWORD" sshpass -e ssh -o StrictHostKeyChecking=no "$APP_SERVER" \
  "cd /opt/apps/lab-trading-dashboard && sudo ./scripts/copy-database-to-cloud.sh"; then
  echo "→ Database copy complete. Refresh http://150.241.244.130:10000"
  exit 0
fi

# Legacy: dump on DB server via SSH, then scp
echo "→ Step 1c: Dump on DB server ($DB_SERVER) via SSH..."
if SSHPASS="$DB_SERVER_PASSWORD" sshpass -e ssh -o StrictHostKeyChecking=accept-new "$DB_SERVER" \
  "PGPASSWORD='IndiaNepal1-' pg_dump -h 127.0.0.1 -U postgres -d labdb2 -F c -f /tmp/labdb2.dump && ls -la /tmp/labdb2.dump"; then
  echo "→ Step 2: Copy dump to app server..."
  SSHPASS="$DB_SERVER_PASSWORD" sshpass -e scp -o StrictHostKeyChecking=no "$DB_SERVER:/tmp/labdb2.dump" /tmp/labdb2.dump
  SSHPASS="$DEPLOY_PASSWORD" sshpass -e scp -o StrictHostKeyChecking=no /tmp/labdb2.dump "$APP_SERVER:/tmp/labdb2.dump"
else
  echo "Failed: Open 150.241.245.36:5432 for app server and run on app server: cd /opt/apps/lab-trading-dashboard && sudo ./scripts/copy-database-to-cloud.sh"
  exit 1
fi

echo "→ Step 3: Restore on app server and restart service..."
SSHPASS="$DEPLOY_PASSWORD" sshpass -e ssh -o StrictHostKeyChecking=no "$APP_SERVER" "set -e
  sudo -u postgres psql -c \"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'labdb2' AND pid <> pg_backend_pid();\" 2>/dev/null || true
  sudo -u postgres psql -c 'DROP DATABASE IF EXISTS labdb2;'
  sudo -u postgres psql -c 'CREATE DATABASE labdb2 OWNER postgres;'
  sudo -u postgres pg_restore -d labdb2 -F c /tmp/labdb2.dump || true
  sudo systemctl restart lab-trading-dashboard
  echo Done."
echo "→ Database copy complete. Refresh http://150.241.244.130:10000"
