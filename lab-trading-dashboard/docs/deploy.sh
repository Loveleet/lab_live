#!/usr/bin/env bash
# Copy to your bot repo and to server at /opt/apps/<your-repo-dir>/deploy.sh
# On server: chmod +x deploy.sh

set -euo pipefail
cd "$(dirname "$0")"
git fetch origin main
git reset --hard origin/main
.venv/bin/pip install -q -r requirements.txt
sudo systemctl restart tradingbot
echo "Deploy done."
