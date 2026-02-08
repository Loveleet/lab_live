#!/bin/bash

# Backup script for tmux files
# Usage: ./backup_tmux_files.sh [description]

BACKUP_DIR="tmux_backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DESCRIPTION=${1:-"manual_backup"}

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo "🔄 Creating backup of tmux files..."

# Backup main tmux cleaner file
if [ -f "tmux_bot_cleaner.py" ]; then
    cp "tmux_bot_cleaner.py" "$BACKUP_DIR/tmux_bot_cleaner_${TIMESTAMP}_${DESCRIPTION}.py"
    echo "✅ Backed up: tmux_bot_cleaner.py"
fi

# Backup other tmux files if they exist
for file in tmux_cleaner_*.py tmux_bot_cleaner_*.py; do
    if [ -f "$file" ]; then
        cp "$file" "$BACKUP_DIR/${file%.py}_${TIMESTAMP}_${DESCRIPTION}.py"
        echo "✅ Backed up: $file"
    fi
done

echo "📁 Backup completed: $BACKUP_DIR/"
echo "📅 Timestamp: $TIMESTAMP"
echo "📝 Description: $DESCRIPTION"

# Show recent backups
echo ""
echo "📋 Recent backups:"
ls -la "$BACKUP_DIR/" | tail -5
