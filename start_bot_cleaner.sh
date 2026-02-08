#!/bin/bash

# Tmux Bot Cleaner Startup Script
# This script starts the tmux bot cleaner in the background

# Configuration
SCRIPT_DIR="/Users/apple/Desktop/lab_code"
SCRIPT_NAME="tmux_bot_cleaner_postgrey.py"
LOG_FILE="/Users/apple/Desktop/lab_code/TmuxCleaner/startup.log"
PID_FILE="/tmp/tmux_bot_cleaner.pid"

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Check if script is already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        log_message "Tmux Bot Cleaner is already running with PID: $PID"
        exit 1
    else
        log_message "Removing stale PID file"
        rm -f "$PID_FILE"
    fi
fi

# Wait for system to be ready
log_message "Waiting 30 seconds for system to be ready..."
sleep 30

# Change to script directory
cd "$SCRIPT_DIR" || {
    log_message "ERROR: Cannot change to directory $SCRIPT_DIR"
    exit 1
}

# Start the tmux bot cleaner
log_message "Starting Tmux Bot Cleaner..."
nohup python3 "$SCRIPT_NAME" > /dev/null 2>&1 &
PID=$!

# Save PID
echo "$PID" > "$PID_FILE"
log_message "Tmux Bot Cleaner started with PID: $PID"

# Verify it's running
sleep 5
if ps -p "$PID" > /dev/null 2>&1; then
    log_message "✅ Tmux Bot Cleaner is running successfully"
else
    log_message "❌ Failed to start Tmux Bot Cleaner"
    rm -f "$PID_FILE"
    exit 1
fi
