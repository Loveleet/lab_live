#!/usr/bin/env bash
# Run this ON the app server (150.241.244.130) after you have placed
# the dump file at /tmp/labdb2.dump (e.g. from scp root@150.241.245.36:/tmp/labdb2.dump /tmp/ then scp to app server).
# Usage: sudo -u postgres bash -c './restore-db-on-server.sh'  OR  run as root and it uses sudo -u postgres.

set -euo pipefail
DUMP="${1:-/tmp/labdb2.dump}"
if [ ! -f "$DUMP" ]; then
  echo "Usage: $0 /path/to/labdb2.dump"
  echo "Dump file not found: $DUMP"
  echo "First copy the dump from your DB server, e.g.:"
  echo "  scp root@150.241.245.36:/tmp/labdb2.dump /tmp/"
  exit 1
fi
echo "→ Terminating connections to labdb2..."
sudo -u postgres psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'labdb2' AND pid <> pg_backend_pid();" 2>/dev/null || true
echo "→ Dropping and recreating labdb2..."
sudo -u postgres psql -c "DROP DATABASE IF EXISTS labdb2;"
sudo -u postgres psql -c "CREATE DATABASE labdb2 OWNER postgres;"
echo "→ Restoring from $DUMP..."
sudo -u postgres pg_restore -d labdb2 -F c "$DUMP" || true
echo "→ Restarting lab-trading-dashboard..."
sudo systemctl restart lab-trading-dashboard
echo "Done. Refresh http://150.241.244.130:10000"
