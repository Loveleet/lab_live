#!/bin/bash
# Run server.js 24/7 — restarts on exit. Telegram alerts are sent by server.js itself.
cd "$(dirname "$0")/.." || exit 1
echo "Starting server.js 24/7 loop..."
while true; do
  node server/server.js
  code=$?
  echo "[run-server-24-7] server.js exited with code $code. Restarting in 5s..."
  sleep 5
done
