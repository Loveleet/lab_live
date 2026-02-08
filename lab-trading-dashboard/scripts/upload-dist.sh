#!/usr/bin/env bash
# Build frontend and upload dist/ to cloud server. Restart service.
# Usage:
#   ./scripts/upload-dist.sh
# Optional: set DEPLOY_PASSWORD in .env (or export) to avoid typing password.
# Requires: DEPLOY_HOST in .env (e.g. root@150.241.244.130)

set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] && set -a && . ./.env && set +a

if [ -z "${DEPLOY_HOST:-}" ]; then
  echo "Add DEPLOY_HOST=root@YOUR_IP to .env"
  exit 1
fi

echo "→ Building frontend..."
npm run build

echo "→ Uploading dist/ and server.example.js (as server.js) to $DEPLOY_HOST ..."
if [ -n "${DEPLOY_PASSWORD:-}" ]; then
  SSHPASS="$DEPLOY_PASSWORD" sshpass -e rsync -avz -e "ssh -o StrictHostKeyChecking=no" dist/ "$DEPLOY_HOST:/opt/apps/lab-trading-dashboard/dist/"
  SSHPASS="$DEPLOY_PASSWORD" sshpass -e rsync -avz -e "ssh -o StrictHostKeyChecking=no" server/server.example.js "$DEPLOY_HOST:/opt/apps/lab-trading-dashboard/server/server.js"
  echo "→ Restarting service..."
  SSHPASS="$DEPLOY_PASSWORD" sshpass -e ssh -o StrictHostKeyChecking=no "$DEPLOY_HOST" "sudo systemctl restart lab-trading-dashboard"
else
  rsync -avz dist/ "$DEPLOY_HOST:/opt/apps/lab-trading-dashboard/dist/"
  rsync -avz server/server.example.js "$DEPLOY_HOST:/opt/apps/lab-trading-dashboard/server/server.js"
  echo "→ Restarting service..."
  ssh "$DEPLOY_HOST" "sudo systemctl restart lab-trading-dashboard"
fi

echo "Done. Hard-refresh the page (Cmd+Shift+R) at http://150.241.244.130:10000"
