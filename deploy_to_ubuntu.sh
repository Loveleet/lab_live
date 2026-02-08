#!/bin/bash

# Ubuntu 24 Cloud Deployment Script for Tmux Bot Cleaner
# Run this script on your Ubuntu cloud server

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/home/ubuntu/lab_code"
SERVICE_NAME="tmux-bot-cleaner"
PYTHON_SCRIPT="tmux_bot_cleaner_postgrey.py"
SERVICE_FILE="tmux-bot-cleaner.service"

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root. Run as ubuntu user."
   exit 1
fi

print_status "Starting Ubuntu 24 deployment for Tmux Bot Cleaner..."

# Step 1: Update system
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Step 2: Install dependencies
print_status "Installing Python dependencies..."
sudo apt install -y python3 python3-pip tmux postgresql-client
pip3 install psutil --break-system-packages

# Step 3: Create project directory
print_status "Creating project directory..."
mkdir -p "$PROJECT_DIR"
mkdir -p "$PROJECT_DIR/TmuxCleaner"

# Step 4: Copy files (assuming they're uploaded to /tmp or current directory)
print_status "Setting up files..."
if [ -f "$PYTHON_SCRIPT" ]; then
    cp "$PYTHON_SCRIPT" "$PROJECT_DIR/"
    print_success "Copied $PYTHON_SCRIPT"
else
    print_warning "$PYTHON_SCRIPT not found in current directory"
fi

if [ -f "$SERVICE_FILE" ]; then
    sudo cp "$SERVICE_FILE" "/etc/systemd/system/"
    print_success "Copied service file"
else
    print_warning "$SERVICE_FILE not found in current directory"
fi

# Step 5: Set permissions
print_status "Setting permissions..."
chmod +x "$PROJECT_DIR/$PYTHON_SCRIPT" 2>/dev/null || true
chown -R ubuntu:ubuntu "$PROJECT_DIR"

# Step 6: Create configuration files if they don't exist
print_status "Creating configuration files..."
touch "$PROJECT_DIR/TmuxCleaner/bots.txt"
touch "$PROJECT_DIR/TmuxCleaner/botsBackup.txt"
touch "$PROJECT_DIR/TmuxCleaner/nocleaner.txt"
echo "# Add your bot scripts here, one per line" > "$PROJECT_DIR/TmuxCleaner/bots.txt"
echo "# Add *db to enable PostgreSQL monitoring" >> "$PROJECT_DIR/TmuxCleaner/bots.txt"

# Step 7: Configure sudo permissions for systemctl
print_status "Configuring sudo permissions..."
echo "ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl restart postgresql, /bin/systemctl restart postgresql.service, /usr/bin/pkill, /sbin/reboot" | sudo tee /etc/sudoers.d/tmux-bot-cleaner

# Step 8: Install and start service
print_status "Installing and starting systemd service..."
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME.service"

# Step 9: Test the service
print_status "Testing service configuration..."
if sudo systemctl start "$SERVICE_NAME.service"; then
    print_success "Service started successfully!"
    sleep 5
    
    if sudo systemctl is-active --quiet "$SERVICE_NAME.service"; then
        print_success "Service is running!"
    else
        print_error "Service failed to start. Check logs with: sudo journalctl -u $SERVICE_NAME.service -f"
    fi
else
    print_error "Failed to start service"
fi

# Step 10: Show status and next steps
print_status "Deployment completed!"
echo ""
echo "=== SERVICE MANAGEMENT COMMANDS ==="
echo "Check status:    sudo systemctl status $SERVICE_NAME.service"
echo "View logs:       sudo journalctl -u $SERVICE_NAME.service -f"
echo "Restart:         sudo systemctl restart $SERVICE_NAME.service"
echo "Stop:            sudo systemctl stop $SERVICE_NAME.service"
echo "Disable:         sudo systemctl disable $SERVICE_NAME.service"
echo ""
echo "=== CONFIGURATION FILES ==="
echo "Bot list:        $PROJECT_DIR/TmuxCleaner/bots.txt"
echo "Backup bots:     $PROJECT_DIR/TmuxCleaner/botsBackup.txt"
echo "Protected bots:  $PROJECT_DIR/TmuxCleaner/nocleaner.txt"
echo "Logs:            $PROJECT_DIR/TmuxCleaner/monitoring.log"
echo ""
echo "=== NEXT STEPS ==="
echo "1. Add your bot scripts to: $PROJECT_DIR/TmuxCleaner/bots.txt"
echo "2. Add '*db' to bots.txt to enable PostgreSQL monitoring"
echo "3. Test the service: sudo systemctl status $SERVICE_NAME.service"
echo ""
print_success "Tmux Bot Cleaner is now installed and running!"
