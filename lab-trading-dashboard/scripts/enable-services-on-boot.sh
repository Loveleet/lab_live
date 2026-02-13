#!/usr/bin/env bash
# Run this ON THE CLOUD SERVER once so the site works after every reboot and crash.
#
# Ensures:
#   - PostgreSQL starts on boot (so the API can connect to the DB).
#   - lab-trading-dashboard (Node API) starts on boot and restarts on crash.
#   - api-signals (Python signals API) starts on boot and restarts on crash (for Information + Binance Data sections).
#
# Usage on cloud:
#   sudo bash /root/lab-trading-dashboard/scripts/enable-services-on-boot.sh
#
# Or from laptop:
#   scp scripts/enable-services-on-boot.sh root@150.241.244.130:/root/lab-trading-dashboard/scripts/
#   ssh root@150.241.244.130 "sudo bash /root/lab-trading-dashboard/scripts/enable-services-on-boot.sh"

set -e
SERVICE_NAME="lab-trading-dashboard"
PYTHON_SIGNALS_SERVICE="api-signals"

echo "=============================================="
echo "Enable LAB Dashboard services on boot"
echo "=============================================="

# 1. Enable PostgreSQL so DB is up after reboot
if systemctl list-unit-files | grep -q 'postgresql'; then
  systemctl enable postgresql 2>/dev/null || systemctl enable postgresql.service 2>/dev/null || true
  echo "[OK] PostgreSQL enabled for boot"
else
  echo "[SKIP] PostgreSQL unit not found (DB may be on another host)"
fi

# 2. Enable Node API so it starts on boot and restarts on crash
if [ ! -f "/etc/systemd/system/${SERVICE_NAME}.service" ]; then
  echo "[WARN] ${SERVICE_NAME}.service not installed."
  echo "       Copy lab-trading-dashboard.service to /etc/systemd/system/ and run:"
  echo "       sudo systemctl daemon-reload"
  echo "       Then run this script again."
  exit 1
fi
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
echo "[OK] $SERVICE_NAME enabled for boot (and will restart on crash)"

# 3. Enable Python signals API (Information + Binance Data sections)
if [ -f "/etc/systemd/system/${PYTHON_SIGNALS_SERVICE}.service" ]; then
  systemctl enable "$PYTHON_SIGNALS_SERVICE" 2>/dev/null || true
  if ! systemctl is-active --quiet "$PYTHON_SIGNALS_SERVICE"; then
    systemctl start "$PYTHON_SIGNALS_SERVICE"
    echo "[OK] $PYTHON_SIGNALS_SERVICE started"
  else
    echo "[OK] $PYTHON_SIGNALS_SERVICE already running"
  fi
else
  echo "[SKIP] $PYTHON_SIGNALS_SERVICE.service not installed (copy scripts/api-signals.service to /etc/systemd/system/)"
fi

# 4. Start Node now if not already running
if ! systemctl is-active --quiet "$SERVICE_NAME"; then
  systemctl start "$SERVICE_NAME"
  echo "[OK] $SERVICE_NAME started"
else
  echo "[OK] $SERVICE_NAME already running"
fi

echo ""
echo "Done. After a reboot, the API (api.clubinfotech.com) and Python signals should come up automatically."
echo "Check: systemctl status $SERVICE_NAME  &&  systemctl status $PYTHON_SIGNALS_SERVICE"
echo "Logs:  journalctl -u $SERVICE_NAME -f   or   journalctl -u $PYTHON_SIGNALS_SERVICE -f"
