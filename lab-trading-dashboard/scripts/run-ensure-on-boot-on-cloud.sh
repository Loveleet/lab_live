#!/usr/bin/env bash
# Run ensure-app-runs-on-boot.sh ON the cloud via SSH. Uses .env (DEPLOY_HOST, DEPLOY_PASSWORD).
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] && set -a && . ./.env && set +a
DEPLOY_HOST="${DEPLOY_HOST:?Set DEPLOY_HOST in .env}"
SCRIPT="$(cat scripts/ensure-app-runs-on-boot.sh)"
# Default app path on cloud (match upload-dist.sh and setup-server-once.sh)
APP_DIR="/opt/apps/lab-trading-dashboard"
SSHPASS="${DEPLOY_PASSWORD:-}"
if [ -n "$SSHPASS" ]; then
  SSHPASS="$SSHPASS" sshpass -e ssh -o StrictHostKeyChecking=no "$DEPLOY_HOST" "APP_DIR=$APP_DIR RUN_AS_USER=root bash -s" <<< "$SCRIPT"
else
  ssh "$DEPLOY_HOST" "APP_DIR=$APP_DIR RUN_AS_USER=root bash -s" <<< "$SCRIPT"
fi
