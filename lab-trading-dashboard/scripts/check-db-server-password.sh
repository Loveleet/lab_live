#!/usr/bin/env bash
# Test if a password works for SSH to the DB server (150.241.245.36).
# Usage:
#   ./scripts/check-db-server-password.sh              # uses DB_SERVER_PASSWORD from .env
#   PASSWORD=yourpass ./scripts/check-db-server-password.sh   # test a specific password
#
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] && set -a && . ./.env && set +a

DB_SERVER="${DB_SERVER:-root@150.241.245.36}"
PASS="${PASSWORD:-${DB_SERVER_PASSWORD:-}}"

if [ -z "$PASS" ]; then
  echo "No password to test."
  echo "  Set DB_SERVER_PASSWORD=... in .env, or run: PASSWORD=yourpass $0"
  exit 1
fi

echo "Testing SSH to $DB_SERVER (password from .env or PASSWORD env)..."
if SSHPASS="$PASS" sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$DB_SERVER" "echo OK"; then
  echo "→ Password works. You can run: ./scripts/run-open-db-port-on-db-server.sh"
else
  echo "→ Password failed (Permission denied). Update DB_SERVER_PASSWORD in .env with the correct root password for $DB_SERVER"
  exit 1
fi
