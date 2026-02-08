#!/bin/bash

# Deployment script for Queue Management System
# Usage: ./deploy_queue_management.sh [your_username@your_cloud_ip]
# Default: Uses lab@150.241.244.130 (from server.js configuration)

if [ $# -eq 0 ]; then
    # Use default cloud machine from server.js
    CLOUD_HOST="127.0.0.1"
    echo "Using default cloud machine: $CLOUD_HOST"
else
    CLOUD_HOST="$1"
fi

ROOT_DIR="/root"
TMUXCLEANER_DIR="/root/TmuxCleaner"
TMUXMONITORING_DIR="/root/TmuxMonitoring"

echo "🚀 Deploying Queue Management System to $CLOUD_HOST"
echo "📁 File Organization:"
echo "   • tmux_bot_cleaner.py → $ROOT_DIR/"
echo "   • tmux_cleaner_interactive_monitor.py → $TMUXMONITORING_DIR/"
echo "   • Test files → $TMUXCLEANER_DIR/"
echo "=" * 60

# Check if files exist locally
if [ ! -f "tmux_bot_cleaner.py" ]; then
    echo "❌ tmux_bot_cleaner.py not found in current directory"
    exit 1
fi

if [ ! -f "tmux_cleaner_interactive_monitor.py" ]; then
    echo "❌ tmux_cleaner_interactive_monitor.py not found in current directory"
    exit 1
fi

echo "📁 Uploading main cleaner file to /root/..."
scp tmux_bot_cleaner.py $CLOUD_HOST:$ROOT_DIR/

echo "📁 Uploading interactive monitor file to /root/TmuxMonitoring/..."
scp tmux_cleaner_interactive_monitor.py $CLOUD_HOST:$TMUXMONITORING_DIR/

echo "📁 Uploading test files to /root/TmuxCleaner/..."
scp test_bot_1.py $CLOUD_HOST:$TMUXCLEANER_DIR/
scp test_bot_2.py $CLOUD_HOST:$TMUXCLEANER_DIR/
scp test_bots_config.txt $CLOUD_HOST:$TMUXCLEANER_DIR/
scp test_queue_management.py $CLOUD_HOST:$TMUXCLEANER_DIR/

echo "🔧 Setting permissions..."
ssh $CLOUD_HOST "chmod +x $ROOT_DIR/tmux_bot_cleaner.py"
ssh $CLOUD_HOST "chmod +x $TMUXMONITORING_DIR/tmux_cleaner_interactive_monitor.py"
ssh $CLOUD_HOST "chmod +x $TMUXCLEANER_DIR/test_queue_management.py"

echo "✅ Deployment complete!"
echo ""
echo "🎯 Next steps on your cloud machine:"
echo "1. Test the queue management: python3 $TMUXCLEANER_DIR/test_queue_management.py"
echo "2. Update your botsBackup.txt with R- timers for testing"
echo "3. Restart the tmux cleaner to use the new queue system"
echo "4. Monitor with: python3 $TMUXMONITORING_DIR/tmux_cleaner_interactive_monitor.py"
toring also