#!/usr/bin/env bash
# Copy open-db-port-for-cloud.sh to the DB server and run it there.
# Uses DB_SERVER_PASSWORD from .env so you don't type the password.
# If you get "Permission denied", the password for 150.241.245.36 is wrong or the server only accepts SSH keys.
#
# Usage: ./scripts/run-open-db-port-on-db-server.sh

set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] && set -a && . ./.env && set +a

DB_SERVER="${DB_SERVER:-root@150.241.245.36}"
SCRIPT="scripts/open-db-port-for-cloud.sh"

if [ -z "${DB_SERVER_PASSWORD:-}" ]; then
  echo "Add DB_SERVER_PASSWORD=your_password to .env (password for $DB_SERVER)"
  exit 1
fi

echo "→ Copying $SCRIPT to $DB_SERVER..."
SSHPASS="$DB_SERVER_PASSWORD" sshpass -e scp -o StrictHostKeyChecking=no "$SCRIPT" "$DB_SERVER:/tmp/open-db-port-for-cloud.sh"

echo "→ Running script on DB server..."
SSHPASS="$DB_SERVER_PASSWORD" sshpass -e ssh -o StrictHostKeyChecking=no "$DB_SERVER" "sudo bash /tmp/open-db-port-for-cloud.sh"

echo "→ Done. Now run: ./scripts/point-cloud-at-db-server.sh"
