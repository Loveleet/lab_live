#!/bin/bash

# Deploy CPU & RAM Monitoring Tools to Remote Machine
# Target: root@150.241.244.130:/root/TmuxMonitoring

echo "🚀 Deploying CPU & RAM Monitoring Tools to Remote Machine..."
echo "Target: root@150.241.244.130:/root/TmuxMonitoring"
echo ""

# Check if we're in the right directory
if [ ! -d "TmuxMonitoring" ]; then
    echo "❌ Error: TmuxMonitoring directory not found in current location"
    echo "Please run this script from the lab_code directory"
    exit 1
fi

# Create the remote directory if it doesn't exist
echo "📁 Creating remote directory..."
ssh root@150.241.244.130 "mkdir -p /root/TmuxMonitoring"

# Transfer all monitoring files
echo "📤 Transferring monitoring files..."

# Transfer the new CPU & RAM monitors
scp TmuxMonitoring/simple_cpu_ram_monitor.py root@150.241.244.130:/root/TmuxMonitoring/
scp TmuxMonitoring/trading_bot_cpu_monitor.py root@150.241.244.130:/root/TmuxMonitoring/
scp TmuxMonitoring/cpu_ram_process_monitor.py root@150.241.244.130:/root/TmuxMonitoring/
scp TmuxMonitoring/launch_monitor.py root@150.241.244.130:/root/TmuxMonitoring/
scp TmuxMonitoring/CPU_RAM_MONITOR_README.md root@150.241.244.130:/root/TmuxMonitoring/

# Transfer existing monitoring files (if they exist)
if [ -f "TmuxMonitoring/tmux_htop_style_monitor.py" ]; then
    scp TmuxMonitoring/tmux_htop_style_monitor.py root@150.241.244.130:/root/TmuxMonitoring/
fi

if [ -f "TmuxMonitoring/tmux_system_analyzer_simple.py" ]; then
    scp TmuxMonitoring/tmux_system_analyzer_simple.py root@150.241.244.130:/root/TmuxMonitoring/
fi

if [ -f "TmuxMonitoring/README.md" ]; then
    scp TmuxMonitoring/README.md root@150.241.244.130:/root/TmuxMonitoring/
fi

# Make all Python files executable on remote machine
echo "🔧 Making files executable on remote machine..."
ssh root@150.241.244.130 "chmod +x /root/TmuxMonitoring/*.py"

# Verify the deployment
echo "✅ Verifying deployment..."
ssh root@150.241.244.130 "ls -la /root/TmuxMonitoring/"

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📋 To use the monitors on the remote machine:"
echo "1. SSH to the machine: ssh root@150.241.244.130"
echo "2. Navigate to: cd /root/TmuxMonitoring"
echo "3. Run the launcher: python3 launch_monitor.py"
echo ""
echo "🚀 Or run individual monitors:"
echo "   python3 simple_cpu_ram_monitor.py"
echo "   python3 trading_bot_cpu_monitor.py"
echo "   python3 cpu_ram_process_monitor.py"
echo ""
echo "📖 Read the documentation: cat CPU_RAM_MONITOR_README.md"
