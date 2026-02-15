#!/usr/bin/env bash
# Run this ON THE CLOUD SERVER to verify api_signals.py is running and Node can reach it.
# If Information / Binance Data sections show "Loading signals..." or "Failed to fetch", run this.
#
# Usage: bash /root/lab-trading-dashboard/scripts/check-python-signals-on-cloud.sh

set -e
PYTHON_PORT=5001
PYTHON_URL="http://127.0.0.1:${PYTHON_PORT}"
SECRETS_FILE="/etc/lab-trading-dashboard.secrets.env"

echo "=============================================="
echo "Check Python signals (api_signals.py) on cloud"
echo "=============================================="
echo ""

# 1. Is api-signals service installed and running?
echo "1. Service api-signals:"
if systemctl list-unit-files 2>/dev/null | grep -q api-signals; then
  if systemctl is-active --quiet api-signals; then
    echo "   [OK] api-signals is running"
  else
    echo "   [FAIL] api-signals is not running. Start it: sudo systemctl start api-signals"
    echo "   Logs: sudo journalctl -u api-signals -n 30 --no-pager"
  fi
else
  echo "   [SKIP] api-signals.service not installed. Copy scripts/api-signals.service to /etc/systemd/system/ and run daemon-reload, enable, start."
fi
echo ""

# 2. Is Python listening on port 5001?
echo "2. Python API on port ${PYTHON_PORT}:"
if command -v curl >/dev/null 2>&1; then
  code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 "${PYTHON_URL}/api/calculate-signals/health" 2>/dev/null || echo "000")
  if [ "$code" = "000" ]; then
    echo "   [FAIL] Nothing responding at ${PYTHON_URL} (connection refused or timeout)."
    echo "   → Start api_signals: sudo systemctl start api-signals"
    echo "   → If service fails, check: sudo journalctl -u api-signals -n 50 --no-pager"
  else
    echo "   [OK] Got HTTP ${code} from ${PYTHON_URL}/api/calculate-signals/health"
  fi
else
  echo "   [SKIP] curl not found; cannot test port."
fi
echo ""

# 3. Does Node have PYTHON_SIGNALS_URL set?
echo "3. Node env (PYTHON_SIGNALS_URL):"
if [ -f "$SECRETS_FILE" ]; then
  if grep -q "PYTHON_SIGNALS_URL" "$SECRETS_FILE" 2>/dev/null; then
    echo "   [OK] PYTHON_SIGNALS_URL is set in $SECRETS_FILE"
    grep "PYTHON_SIGNALS_URL" "$SECRETS_FILE" | sed 's/^/   /'
  else
    echo "   [FAIL] PYTHON_SIGNALS_URL not found in $SECRETS_FILE"
    echo "   Add this line and restart Node:"
    echo "   PYTHON_SIGNALS_URL=http://127.0.0.1:5001"
    echo "   Then: sudo systemctl restart lab-trading-dashboard"
  fi
else
  echo "   [WARN] Secrets file not found: $SECRETS_FILE"
  echo "   Create it and add: PYTHON_SIGNALS_URL=http://127.0.0.1:5001"
  echo "   Then: sudo systemctl restart lab-trading-dashboard"
fi
echo ""

# 4. Quick test: Node proxy to Python (if we have curl)
echo "4. Test Node → Python proxy (from this server):"
node_status=$(systemctl is-active lab-trading-dashboard 2>/dev/null || echo "inactive")
if [ "$node_status" = "active" ] && command -v curl >/dev/null 2>&1; then
  # We can't easily test /api/calculate-signals (POST, needs auth) so just remind
  echo "   Node service is running. In browser or with auth cookie, POST /api/calculate-signals is proxied to Python."
  echo "   Check Node logs for proxy errors: sudo journalctl -u lab-trading-dashboard -n 20 --no-pager | grep -E 'calculate-signals|open-position|PYTHON_SIGNALS'"
else
  echo "   [SKIP] Node not running or curl not available."
fi
echo ""
echo "=============================================="
echo "If all above are OK and UI still fails, hard-refresh the page and check browser Network tab for 502 (Python unreachable) or 401 (not logged in)."
echo "=============================================="
