#!/usr/bin/env bash
# Run this ONCE on your Ubuntu cloud server to install Node, clone the repo, and run the app.
#
# Usage ON THE SERVER (after SSH in):
#   First, get this script onto the server. From your laptop:
#     scp scripts/setup-server-once.sh ubuntu@YOUR_SERVER_IP:/tmp/
#   Then on the server:
#     REPO_URL=https://github.com/YOUR_USER/lab-trading-dashboard.git /bin/bash /tmp/setup-server-once.sh
#
# Or if the repo is already cloned in /tmp (e.g. you cloned to copy the script):
#     cd /tmp/lab-trading-dashboard && REPO_URL=https://github.com/YOUR_USER/lab-trading-dashboard.git ./scripts/setup-server-once.sh
#
# Required: REPO_URL (your GitHub repo clone URL, HTTPS or SSH).
# Optional: RUN_AS_USER (default: current user), SKIP_CLONE=1 (if repo already at /opt/apps/lab-trading-dashboard).

set -euo pipefail

REPO_URL="${REPO_URL:-}"
RUN_AS_USER="${RUN_AS_USER:-$(whoami)}"
APP_DIR="/opt/apps/lab-trading-dashboard"
SKIP_CLONE="${SKIP_CLONE:-0}"

if [ -z "$REPO_URL" ]; then
  echo "Usage: REPO_URL=https://github.com/youruser/lab-trading-dashboard.git $0"
  echo "Optional: RUN_AS_USER=ubuntu (default: current user)"
  exit 1
fi

echo "=== One-time server setup: Node 20, clone repo, systemd ==="
echo "REPO_URL=$REPO_URL"
echo "RUN_AS_USER=$RUN_AS_USER"
echo "APP_DIR=$APP_DIR"

# 1) Install git and Node 20
echo "→ Installing git and Node.js 20 ..."
sudo apt-get update -qq
sudo apt-get install -y git
if ! command -v node >/dev/null 2>&1 || [ "$(node -v | cut -d. -f1 | tr -d 'v')" -lt 20 ]; then
  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
  sudo apt-get install -y nodejs
fi
node -v
npm -v

# 2) App directory and clone
sudo mkdir -p /opt/apps
sudo chown -R "$RUN_AS_USER:$RUN_AS_USER" /opt/apps

if [ "$SKIP_CLONE" != "1" ]; then
  echo "→ Cloning repo to $APP_DIR ..."
  if [ -d "$APP_DIR/.git" ]; then
    (cd "$APP_DIR" && git fetch origin && git reset --hard origin/main)
  else
    git clone "$REPO_URL" "$APP_DIR"
  fi
fi

cd "$APP_DIR"
chmod +x deploy.sh 2>/dev/null || true

# 3) Build
echo "→ Installing deps and building ..."
npm ci
npm run build
cd server && npm ci && cd ..
# Server runs server.js; repo has only server.example.js (no secrets in Git). Create server.js from template.
cp -f server/server.example.js server/server.js

# 4) Env file (secrets only here – edit with: sudo nano /etc/lab-trading-dashboard.env)
if [ ! -f /etc/lab-trading-dashboard.env ]; then
  echo "→ Creating /etc/lab-trading-dashboard.env (edit later if you need PORT or DB vars) ..."
  sudo tee /etc/lab-trading-dashboard.env << 'ENVEOF'
PORT=10000
# Add any env vars your server/server.js needs
ENVEOF
  sudo chmod 600 /etc/lab-trading-dashboard.env
  sudo chown root:root /etc/lab-trading-dashboard.env
fi

# 5) Systemd service
echo "→ Installing systemd service lab-trading-dashboard ..."
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
sudo systemctl status lab-trading-dashboard --no-pager || true

echo ""
echo "=== Setup done. API should be running (default port 10000). ==="
echo "Logs:  journalctl -u lab-trading-dashboard -f"
echo "Next:  Add GitHub Secrets (SSH_HOST, SSH_USER, SSH_KEY) so push-to-main auto-deploys. See docs/SETUP_CHECKLIST.md"
