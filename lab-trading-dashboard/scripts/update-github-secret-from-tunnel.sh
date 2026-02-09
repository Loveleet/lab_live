#!/usr/bin/env bash
# Run on the CLOUD. Reads the tunnel URL from the log, updates GitHub secret API_BASE_URL,
# and triggers "Update API config" with api_url so gh-pages gets the new api-config.json (frontend uses it at runtime).
#
# Requires: GH_TOKEN in /etc/lab-trading-dashboard.env (create at https://github.com/settings/tokens, repo scope)
# Optional: GITHUB_REPO (default: Loveleet/lab_live)

set -e
[ -f /etc/lab-trading-dashboard.env ] && set -a && . /etc/lab-trading-dashboard.env && set +a
LOG="${1:-/var/log/cloudflared-tunnel.log}"
REPO="${GITHUB_REPO:-Loveleet/lab_live}"

# Wait for URL to appear (retry up to 12 times, 5s apart, so tunnel is up after reboot)
for i in 1 2 3 4 5 6 7 8 9 10 11 12; do
  [ "$i" -gt 1 ] && sleep 5
  [ -f "$LOG" ] || continue
  URL=$(grep -oE "https://[a-zA-Z0-9.-]+\.trycloudflare\.com" "$LOG" 2>/dev/null | tail -1)
  [ -n "$URL" ] && break
done
if [ -z "$URL" ]; then
  echo "No tunnel URL found in $LOG"
  exit 1
fi
echo "$URL" > /var/run/lab-tunnel-url 2>/dev/null || true
echo "Tunnel URL: $URL"

TOKEN="${GH_TOKEN:-$GITHUB_TOKEN}"
if [ -n "$TOKEN" ]; then
  if command -v gh &>/dev/null; then
    if GH_TOKEN="$TOKEN" gh secret set API_BASE_URL --body "$URL" --repo "$REPO"; then
      echo "Updated GitHub secret API_BASE_URL"
    fi
    # Trigger Update API config so api-config.json on gh-pages is updated immediately (frontend reads it at runtime)
    GH_TOKEN="$TOKEN" gh workflow run "Update API config" --ref main --repo "$REPO" -f "api_url=$URL" && echo "Triggered Update API config with api_url"
  else
    echo "Install gh CLI: apt install gh"
  fi
else
  echo "Set GH_TOKEN in /etc/lab-trading-dashboard.env to auto-update."
fi
