#!/usr/bin/env bash
# Deploy lab-trading-dashboard to this server. Run from repo root (e.g. on cloud after git pull, or via GitHub Actions).
# Server code: server.example.js is in Git; server.js is created on the server from it (secrets live only in /etc/lab-trading-dashboard.env).

set -euo pipefail
cd "$(dirname "$0")"
git fetch origin main
git reset --hard origin/main
npm ci
VITE_API_BASE_URL= npm run build
cd server && npm ci && cd ..
# Server runs server.js; repo only has server.example.js (no secrets). Copy template so cloud uses latest code; secrets stay in env file.
cp -f server/server.example.js server/server.js
sudo systemctl restart lab-trading-dashboard
echo "Deploy done."
