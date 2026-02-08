#!/usr/bin/env bash
# Run on your LAPTOP. Fetches the current tunnel URL from the cloud and writes .env.local
# so "npm run dev" uses the cloud API (useful when the direct cloud IP isn't reachable).
set -e
CLOUD_URL_API="${CLOUD_URL_API:-http://150.241.244.130:10000/api/tunnel-url}"
ENV_LOCAL="${1:-.env.local}"
URL=$(curl -sf "$CLOUD_URL_API" 2>/dev/null || true)
if [ -z "$URL" ]; then
  echo "Could not fetch tunnel URL from $CLOUD_URL_API (cloud down or unreachable)."
  echo "Using direct IP in dev is already the default; if that fails, set VITE_API_BASE_URL in $ENV_LOCAL manually."
  exit 1
fi
echo "VITE_API_BASE_URL=$URL" > "$ENV_LOCAL"
echo "Wrote $ENV_LOCAL with VITE_API_BASE_URL=$URL — run npm run dev to use cloud data."
