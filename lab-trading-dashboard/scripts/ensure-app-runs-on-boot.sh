#!/usr/bin/env bash
# Ensure the dashboard app is managed by systemd: starts on boot and restarts if it crashes.
# Run ON the cloud server (e.g. after SSH in), or from laptop: ./scripts/run-ensure-on-boot-on-cloud.sh
#
# Usage on server:
#   cd /opt/apps/lab-trading-dashboard && sudo bash scripts/ensure-app-runs-on-boot.sh
# Or from laptop (uses .env DEPLOY_HOST, DEPLOY_PASSWORD):
#   ./scripts/run-ensure-on-boot-on-cloud.sh

set -euo pipefail

APP_DIR="${APP_DIR:-/opt/apps/lab-trading-dashboard}"
RUN_AS_USER="${RUN_AS_USER:-root}"

# If we're in the repo, detect APP_DIR
if [ -f "$(dirname "$0")/../package.json" ] && [ -d "$(dirname "$0")/../server" ]; then
  APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
fi

echo "→ App directory: $APP_DIR"
echo "→ Run as user:   $RUN_AS_USER"

if [ ! -d "$APP_DIR/server" ] || [ ! -f "$APP_DIR/server/server.js" ]; then
  echo "Error: $APP_DIR/server/server.js not found. Deploy the app first (e.g. ./scripts/upload-dist.sh)."
  exit 1
fi

echo "→ Installing systemd service lab-trading-dashboard (start on boot + restart on crash) ..."
sudo tee /etc/systemd/system/lab-trading-dashboard.service << SVCEOF
[Unit]
Description=Lab Trading Dashboard (Node API)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$RUN_AS_USER
Group=$RUN_AS_USER
WorkingDirectory=$APP_DIR/server
EnvironmentFile=-/etc/lab-trading-dashboard.env
ExecStart=/usr/bin/node server.js
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SVCEOF

sudo systemctl daemon-reload
sudo systemctl enable lab-trading-dashboard
sudo systemctl start lab-trading-dashboard

echo ""
echo "✅ Done. The app will:"
echo "   - Start automatically when the server boots"
echo "   - Restart automatically if it crashes (after 10s)"
echo ""
echo "Commands:"
echo "  status:  sudo systemctl status lab-trading-dashboard"
echo "  logs:    journalctl -u lab-trading-dashboard -f"
echo "  restart: sudo systemctl restart lab-trading-dashboard"
