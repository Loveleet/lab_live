#!/usr/bin/env bash
# Transfer this project to your Ubuntu server and build + run there.
#
# Usage:
#   export DEPLOY_HOST=ubuntu@YOUR_SERVER_IP
#   ./scripts/deploy-to-server.sh
#
# Or one-liner:
#   DEPLOY_HOST=ubuntu@1.2.3.4 ./scripts/deploy-to-server.sh
#
# First time on server: ensure Node 20 is installed and (optional) systemd is set up.
# See docs/DEPLOY_DASHBOARD_UBUNTU.md for one-time server setup.

set -euo pipefail

if [ -z "${DEPLOY_HOST:-}" ]; then
  echo "Error: set DEPLOY_HOST (e.g. ubuntu@YOUR_SERVER_IP)"
  echo "  export DEPLOY_HOST=ubuntu@1.2.3.4"
  echo "  ./scripts/deploy-to-server.sh"
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REMOTE_APP_PATH="/opt/apps/lab-trading-dashboard"

echo "→ Ensuring $REMOTE_APP_PATH exists on server ..."
ssh "$DEPLOY_HOST" "sudo mkdir -p $REMOTE_APP_PATH; sudo chown -R \$(whoami):\$(whoami) /opt/apps 2>/dev/null || true"

echo "→ Syncing code to $DEPLOY_HOST:$REMOTE_APP_PATH (excluding node_modules, .env, dist) ..."
rsync -avz --delete \
  --exclude 'node_modules' \
  --exclude 'server/node_modules' \
  --exclude 'server/mcp-server/node_modules' \
  --exclude 'dist' \
  --exclude '.env' \
  --exclude '.env.shadow' \
  --exclude '.git' \
  --exclude '.DS_Store' \
  "$REPO_ROOT/" \
  "$DEPLOY_HOST:$REMOTE_APP_PATH/"

echo "→ On server: install deps, build, restart ..."
ssh "$DEPLOY_HOST" "set -e
  command -v node >/dev/null 2>&1 || { echo 'Node not found. Run one-time setup: docs/DEPLOY_DASHBOARD_UBUNTU.md (install Node 20)'; exit 1; }
  cd $REMOTE_APP_PATH
  npm ci
  npm run build
  cd server && npm ci && cd ..
  if systemctl is-active --quiet lab-trading-dashboard 2>/dev/null; then
    sudo systemctl restart lab-trading-dashboard
    echo 'Restarted lab-trading-dashboard service.'
  elif [ -f /etc/systemd/system/lab-trading-dashboard.service ]; then
    sudo systemctl start lab-trading-dashboard
    echo 'Started lab-trading-dashboard service.'
  else
    echo 'Systemd not set up. Starting Node API in background (kill with: pkill -f \"node server.js\").'
    (cd $REMOTE_APP_PATH/server && nohup node server.js >> /tmp/lab-dashboard.log 2>&1 &)
    sleep 1
    echo 'API running in background. Logs: tail -f /tmp/lab-dashboard.log'
  fi
"

echo "Done. API should be running on the server (default port 10000)."
