#!/usr/bin/env bash
# Start full dev stack: Python signals API → Node server → Vite frontend.
# Run from lab-trading-dashboard: ./scripts/start-dev.sh
# On Ctrl+C, all three processes are stopped.

set -e
cd "$(dirname "$0")/.."
ROOT="$(pwd)"

PYTHON_PID=""
NODE_PID=""

cleanup() {
  echo ""
  echo "[start-dev] Stopping services..."
  if [ -n "$NODE_PID" ] && kill -0 "$NODE_PID" 2>/dev/null; then
    kill "$NODE_PID" 2>/dev/null || true
    echo "[start-dev] Node server (PID $NODE_PID) stopped."
  fi
  if [ -n "$PYTHON_PID" ] && kill -0 "$PYTHON_PID" 2>/dev/null; then
    kill "$PYTHON_PID" 2>/dev/null || true
    echo "[start-dev] Python signals API (PID $PYTHON_PID) stopped."
  fi
  echo "[start-dev] Done."
  exit 0
}

trap cleanup EXIT INT TERM

# Free ports so we can start clean (optional; comment out if you want to keep existing processes)
PY_PORT="${PYTHON_SIGNALS_PORT:-5001}"
NODE_PORT="10000"
for port in "$PY_PORT" "$NODE_PORT"; do
  pid=$(lsof -ti ":$port" 2>/dev/null) || true
  if [ -n "$pid" ]; then
    echo "[start-dev] Freeing port $port (PID $pid)..."
    kill $pid 2>/dev/null || true
    sleep 1
  fi
done

echo "[start-dev] 1/3 Starting Python signals API (port ${PY_PORT})..."
(cd "$ROOT/python" && exec python api_signals.py) &
PYTHON_PID=$!
sleep 2
if ! kill -0 "$PYTHON_PID" 2>/dev/null; then
  echo "[start-dev] ERROR: Python API failed to start."
  exit 1
fi
echo "[start-dev] Python API started (PID $PYTHON_PID)."

echo "[start-dev] 2/3 Starting Node server (port 10000)..."
(exec node "$ROOT/server/server.js") &
NODE_PID=$!
sleep 2
if ! kill -0 "$NODE_PID" 2>/dev/null; then
  echo "[start-dev] ERROR: Node server failed to start."
  cleanup
fi
echo "[start-dev] Node server started (PID $NODE_PID)."

echo "[start-dev] 3/3 Starting Vite dev server (port 5173)..."
echo "[start-dev] Press Ctrl+C to stop all services."
echo ""

cd "$ROOT"
npm run dev
