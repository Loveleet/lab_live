#!/usr/bin/env bash
# Copy server folder (including server.js) from this repo to the cloud.
# Run from lab-trading-dashboard directory: ./scripts/copy-server-to-cloud.sh
# Or from repo root: lab-trading-dashboard/scripts/copy-server-to-cloud.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DASHBOARD_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SERVER_DIR="$DASHBOARD_DIR/server"
CLOUD_USER="${1:-root}"
CLOUD_HOST="${2:-150.241.244.130}"
CLOUD_PATH="${3:-/root/lab-trading-dashboard}"

if [ ! -f "$SERVER_DIR/server.js" ]; then
  echo "ERROR: server/server.js not found at $SERVER_DIR/server.js"
  echo "Run this script from the repo that contains your server.js (e.g. lab-trading-dashboard or lab_live)."
  exit 1
fi

echo "Copying server/ to ${CLOUD_USER}@${CLOUD_HOST}:${CLOUD_PATH}/"
echo "Source: $SERVER_DIR"
if command -v rsync >/dev/null 2>&1; then
  rsync -avz --progress "$SERVER_DIR/" "${CLOUD_USER}@${CLOUD_HOST}:${CLOUD_PATH}/server/" \
    --exclude 'node_modules' \
    --exclude '.env' \
    --exclude 'secrets.env'
else
  ssh "${CLOUD_USER}@${CLOUD_HOST}" "mkdir -p ${CLOUD_PATH}"
  scp -r "$SERVER_DIR" "${CLOUD_USER}@${CLOUD_HOST}:${CLOUD_PATH}/"
fi

echo ""
echo "Done. On the cloud, verify with:"
echo "  ssh ${CLOUD_USER}@${CLOUD_HOST} \"ls -la ${CLOUD_PATH}/server/server.js\""
