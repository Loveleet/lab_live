#!/usr/bin/env bash
# Step-by-step: set DATABASE_URL on the cloud so the site shows real data (cloud runs Node.js server only; no third-party hosting).
# Usage:
#   ./scripts/set-render-db-on-cloud.sh
#   # or with URL ready:
#   RENDER_DATABASE_URL='postgres://user:pass@host:5432/db' ./scripts/set-render-db-on-cloud.sh
#
# Requires: .env with DEPLOY_HOST (e.g. root@150.241.244.130). Optional: DEPLOY_PASSWORD for non-interactive SSH.

set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"
[ -f .env ] && set -a && . ./.env && set +a

DEPLOY_HOST="${DEPLOY_HOST:-}"
if [ -z "$DEPLOY_HOST" ]; then
  echo "Add DEPLOY_HOST=root@150.241.244.130 to .env"
  exit 1
fi

run_ssh() {
  if [ -n "${DEPLOY_PASSWORD:-}" ]; then
    SSHPASS="$DEPLOY_PASSWORD" sshpass -e ssh -o StrictHostKeyChecking=no "$DEPLOY_HOST" "$@"
  else
    ssh "$DEPLOY_HOST" "$@"
  fi
}

run_scp() {
  local src="$1"
  local dest="$2"
  if [ -n "${DEPLOY_PASSWORD:-}" ]; then
    SSHPASS="$DEPLOY_PASSWORD" sshpass -e scp -o StrictHostKeyChecking=no "$src" "$DEPLOY_HOST:$dest"
  else
    scp "$src" "$DEPLOY_HOST:$dest"
  fi
}

echo "=============================================="
echo "  Get real data on cloud (step-by-step)"
echo "=============================================="
echo ""

# Step 1: Get Postgres database URL
if [ -n "${RENDER_DATABASE_URL:-}" ]; then
  echo "[Step 1] Using RENDER_DATABASE_URL from environment."
  URL="$RENDER_DATABASE_URL"
else
  echo "[Step 1] Paste your Postgres database URL"
  echo "  (e.g. postgres://user:password@host:5432/dbname)"
  echo ""
  read -r -p "URL: " URL
  if [ -z "$URL" ]; then
    echo "No URL entered. Exiting."
    exit 1
  fi
fi
echo ""

# Step 2: Write DATABASE_URL line to env file on server (avoid injection by using a file)
echo "[Step 2] Writing DATABASE_URL to /etc/lab-trading-dashboard.env on server..."
TMPFILE=$(mktemp)
cleanup() { rm -f "$TMPFILE"; }
trap cleanup EXIT
# Remove any existing DATABASE_URL line and add new one (use printf so URL special chars are safe)
run_ssh "sudo cat /etc/lab-trading-dashboard.env 2>/dev/null || true" | grep -v '^[[:space:]]*DATABASE_URL=' > "$TMPFILE" || true
printf 'DATABASE_URL=%s\n' "$URL" >> "$TMPFILE"
run_scp "$TMPFILE" "/tmp/lab-trading-dashboard.env.new"
run_ssh "sudo mv /tmp/lab-trading-dashboard.env.new /etc/lab-trading-dashboard.env && sudo chmod 600 /etc/lab-trading-dashboard.env"
echo "  Done."
echo ""

# Step 3: Restart the app
echo "[Step 3] Restarting lab-trading-dashboard service..."
run_ssh "sudo systemctl restart lab-trading-dashboard"
echo "  Done."
echo ""

# Step 4: Wait and check
echo "[Step 4] Waiting 25s for app to connect to your DB..."
sleep 25
echo ""
echo "Checking /api/debug..."
if command -v curl &>/dev/null; then
  DEBUG=$(curl -s "http://150.241.244.130:10000/api/debug" 2>/dev/null || true)
  if echo "$DEBUG" | grep -q '"ok":true'; then
    COUNTS=$(echo "$DEBUG" | grep -o '"alltraderecords":[0-9]*' || true)
    echo "  $COUNTS"
    if echo "$DEBUG" | grep -q 'DATABASE_URL'; then
      echo "  dbSource: DATABASE_URL (remote) — connected."
    fi
  else
    echo "  Response: $DEBUG"
  fi
else
  echo "  (curl not found; open http://150.241.244.130:10000/api/debug in browser)"
fi
echo ""
echo "=============================================="
echo "  Open http://150.241.244.130:10000 and refresh to see real data."
echo "=============================================="
