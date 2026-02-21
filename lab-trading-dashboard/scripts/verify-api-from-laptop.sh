#!/usr/bin/env bash
# Check if api.clubinfotech.com is responding (fixes GitHub Pages 404 when backend is down).
# Run from anywhere. No SSH needed.

set -e
API_URL="${API_URL:-https://api.clubinfotech.com}"
HEALTH="${API_URL}/api/health"
TRADES="${API_URL}/api/trades"

echo "Checking $API_URL ..."
echo ""

# Health
HTTP=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 "$HEALTH" || true)
if [ "$HTTP" = "200" ]; then
  echo "  /api/health  -> $HTTP OK"
else
  echo "  /api/health  -> $HTTP (expected 200)"
  echo ""
  echo "  Backend is not responding. GitHub Pages will get 404 for /api/trade and /auth/me."
  echo "  Fix: SSH to cloud and restart Node:"
  echo "    ssh root@150.241.244.130"
  echo "    sudo systemctl restart lab-trading-dashboard"
  echo "    sudo systemctl status lab-trading-dashboard"
  echo ""
  echo "  Or run: python3 scripts/deploy-server-to-cloud.py  (deploys server.js and restarts)"
  exit 1
fi

# Trades (optional)
HTTP2=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 "$TRADES" || true)
if [ "$HTTP2" = "200" ] || [ "$HTTP2" = "401" ]; then
  echo "  /api/trades  -> $HTTP2 OK"
else
  echo "  /api/trades  -> $HTTP2 (200 or 401 expected)"
fi

echo ""
echo "  API is reachable. If GitHub Pages still shows 404, hard-refresh (Ctrl+Shift+R)."
