#!/usr/bin/env bash
# Build the frontend and copy dist/ to the cloud so http://YOUR-CLOUD-IP:10000 serves the app.
# Run from repo root: lab-trading-dashboard/scripts/deploy-frontend-to-cloud.sh
# Or from lab-trading-dashboard: ./scripts/deploy-frontend-to-cloud.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DASHBOARD_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CLOUD_USER="${1:-root}"
CLOUD_HOST="${2:-150.241.244.130}"
CLOUD_PATH="${3:-/root/lab-trading-dashboard}"

cd "$DASHBOARD_DIR"

echo "Building frontend for cloud (same-origin at http://${CLOUD_HOST}:10000)..."
# Base path / so the app works at http://IP:10000/ (no subpath)
VITE_BASE_PATH=/ VITE_API_BASE_URL= npm run build

if [ ! -d "dist" ] || [ ! -f "dist/index.html" ]; then
  echo "ERROR: dist/ or dist/index.html not found after build"
  exit 1
fi

echo "Copying dist/ to ${CLOUD_USER}@${CLOUD_HOST}:${CLOUD_PATH}/dist/"
if command -v rsync >/dev/null 2>&1; then
  rsync -avz --progress dist/ "${CLOUD_USER}@${CLOUD_HOST}:${CLOUD_PATH}/dist/"
else
  ssh "${CLOUD_USER}@${CLOUD_HOST}" "mkdir -p ${CLOUD_PATH}/dist"
  scp -r dist/* "${CLOUD_USER}@${CLOUD_HOST}:${CLOUD_PATH}/dist/"
fi

echo ""
echo "Done. Restart the server on the cloud so it picks up the new files:"
echo "  ssh ${CLOUD_USER}@${CLOUD_HOST} \"sudo systemctl restart lab-trading-dashboard\""
echo ""
echo "Then open: http://${CLOUD_HOST}:10000"
