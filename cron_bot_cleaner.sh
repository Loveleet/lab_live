#!/bin/bash

# Enhanced Crontab Script with Auto-restart
# Add this to crontab: @reboot /path/to/cron_bot_cleaner.sh

SCRIPT_DIR="/Users/apple/Desktop/lab_code"
SCRIPT_NAME="tmux_bot_cleaner_postgrey.py"
PID_FILE="/tmp/tmux_bot_cleaner.pid"
LOG_FILE="/Users/apple/Desktop/lab_code/TmuxCleaner/cron.log"

log_msg() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Wait for system to be ready
sleep 60

# Wait for PostgreSQL to be ready
while ! pgrep -x "postgres" > /dev/null; do
    log_msg "Waiting for PostgreSQL to start..."
    sleep 10
done

cd "$SCRIPT_DIR"

# Start the script
nohup python3 "$SCRIPT_NAME" > /dev/null 2>&1 &
echo $! > "$PID_FILE"
log_msg "Bot cleaner started with PID: $(cat $PID_FILE)"

# Monitor and restart if needed (runs every 5 minutes)
while true; do
    sleep 300  # 5 minutes
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ! ps -p "$PID" > /dev/null 2>&1; then
            log_msg "Bot cleaner died, restarting..."
            cd "$SCRIPT_DIR"
            nohup python3 "$SCRIPT_NAME" > /dev/null 2>&1 &
            echo $! > "$PID_FILE"
            log_msg "Bot cleaner restarted with PID: $(cat $PID_FILE)"
        fi
    else
        log_msg "PID file missing, starting bot cleaner..."
        cd "$SCRIPT_DIR"
        nohup python3 "$SCRIPT_NAME" > /dev/null 2>&1 &
        echo $! > "$PID_FILE"
        log_msg "Bot cleaner started with PID: $(cat $PID_FILE)"
    fi
done
