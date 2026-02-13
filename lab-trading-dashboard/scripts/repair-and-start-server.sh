#!/usr/bin/env bash
# Run this ON THE CLOUD SERVER (e.g. after: ssh root@150.241.244.130)
# Repairs and starts the Node API (server.js) so api.clubinfotech.com works again.
#
# Usage: sudo bash repair-and-start-server.sh
# Or:    sudo bash /root/lab-trading-dashboard/scripts/repair-and-start-server.sh

set -e
APP_DIR="${1:-/root/lab-trading-dashboard}"
SERVER_DIR="$APP_DIR/server"
SERVICE_NAME="lab-trading-dashboard"
SECRETS_FILE="/etc/lab-trading-dashboard.secrets.env"

echo "=============================================="
echo "LAB Trading Dashboard — repair and start"
echo "=============================================="
echo "App dir: $APP_DIR"
echo "Server dir: $SERVER_DIR"
echo ""

# 1. Check Node
if ! command -v node >/dev/null 2>&1; then
  echo "ERROR: Node.js not found. Install with: apt update && apt install -y nodejs npm"
  exit 1
fi
echo "[OK] Node: $(node -v)"

# 2. Check server.js exists
if [ ! -f "$SERVER_DIR/server.js" ]; then
  echo "ERROR: server.js not found at $SERVER_DIR/server.js"
  echo "Copy it from your repo: ./scripts/copy-server-to-cloud.sh root 150.241.244.130 $APP_DIR"
  exit 1
fi
echo "[OK] server.js found"

# 3. Ensure node_modules for server (server/ has its own package.json with express, pg, etc.)
if [ -f "$SERVER_DIR/package.json" ]; then
  if [ ! -d "$SERVER_DIR/node_modules" ]; then
    echo "Installing dependencies (npm install) in $SERVER_DIR ..."
    (cd "$SERVER_DIR" && npm install --production 2>/dev/null || npm install)
  fi
  echo "[OK] server/node_modules present"
elif [ -f "$APP_DIR/package.json" ] && [ ! -d "$APP_DIR/node_modules" ]; then
  echo "Installing dependencies (npm install) in $APP_DIR ..."
  (cd "$APP_DIR" && npm install --production 2>/dev/null || npm install)
  echo "[OK] node_modules present"
else
  echo "[WARN] No package.json in $SERVER_DIR or $APP_DIR — ensure node_modules exists for server.js"
fi

# 4. Optional: secrets file
if [ -f "$SECRETS_FILE" ]; then
  echo "[OK] Secrets file: $SECRETS_FILE"
else
  echo "[WARN] No secrets file at $SECRETS_FILE — create it for DB and optional PYTHON_SIGNALS_URL"
  echo "        Example: DB_HOST=150.241.244.130 DB_USER=lab DB_PASSWORD=... DB_NAME=olab"
fi

# 5. Reload systemd and restart service
echo ""
echo "Restarting $SERVICE_NAME ..."
systemctl daemon-reload
systemctl enable "$SERVICE_NAME" 2>/dev/null || true
systemctl restart "$SERVICE_NAME"

sleep 2
if systemctl is-active --quiet "$SERVICE_NAME"; then
  echo "[OK] Service is running"
  echo ""
  echo "Quick test:"
  echo "  curl -s http://127.0.0.1:10000/api/health"
  echo "  curl -s http://127.0.0.1:10000/api/server-info"
  echo ""
  echo "View logs: journalctl -u $SERVICE_NAME -f"
else
  echo "[FAIL] Service did not start. Check logs:"
  echo "  journalctl -u $SERVICE_NAME -n 50 --no-pager"
  exit 1
fi
