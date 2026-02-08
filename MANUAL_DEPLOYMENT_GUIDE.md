# Manual Deployment Guide for CPU & RAM Monitors

## 🚀 Deploy to Remote Machine: root@150.241.244.130

### Method 1: Using SCP Commands (Recommended)

Run these commands one by one from your local machine:

```bash
# Navigate to the lab_code directory
cd /Users/apple/Desktop/lab_code

# Create remote directory
ssh root@150.241.244.130 "mkdir -p /root/TmuxMonitoring"

# Transfer the new CPU & RAM monitors
scp TmuxMonitoring/simple_cpu_ram_monitor.py root@150.241.244.130:/root/TmuxMonitoring/
scp TmuxMonitoring/trading_bot_cpu_monitor.py root@150.241.244.130:/root/TmuxMonitoring/
scp TmuxMonitoring/cpu_ram_process_monitor.py root@150.241.244.130:/root/TmuxMonitoring/
scp TmuxMonitoring/launch_monitor.py root@150.241.244.130:/root/TmuxMonitoring/
scp TmuxMonitoring/CPU_RAM_MONITOR_README.md root@150.241.244.130:/root/TmuxMonitoring/

# Transfer existing monitoring files (if they exist)
scp TmuxMonitoring/tmux_htop_style_monitor.py root@150.241.244.130:/root/TmuxMonitoring/
scp TmuxMonitoring/tmux_system_analyzer_simple.py root@150.241.244.130:/root/TmuxMonitoring/
scp TmuxMonitoring/README.md root@150.241.244.130:/root/TmuxMonitoring/

# Make files executable on remote machine
ssh root@150.241.244.130 "chmod +x /root/TmuxMonitoring/*.py"

# Verify deployment
ssh root@150.241.244.130 "ls -la /root/TmuxMonitoring/"
```

### Method 2: Using rsync (Alternative)

```bash
# Sync the entire TmuxMonitoring directory
rsync -avz --progress TmuxMonitoring/ root@150.241.244.130:/root/TmuxMonitoring/

# Make files executable
ssh root@150.241.244.130 "chmod +x /root/TmuxMonitoring/*.py"
```

### Method 3: Manual File Transfer

If you prefer to transfer files manually:

1. **SSH to the remote machine:**
   ```bash
   ssh root@150.241.244.130
   ```

2. **Create the directory:**
   ```bash
   mkdir -p /root/TmuxMonitoring
   ```

3. **Transfer files using your preferred method** (SFTP, SCP, etc.)

4. **Make files executable:**
   ```bash
   chmod +x /root/TmuxMonitoring/*.py
   ```

## 📋 Files to Transfer

### New CPU & RAM Monitoring Files:
- `simple_cpu_ram_monitor.py` - Simple CPU & RAM monitor
- `trading_bot_cpu_monitor.py` - Trading bot specific monitor
- `cpu_ram_process_monitor.py` - Advanced monitor with controls
- `launch_monitor.py` - Easy launcher for all monitors
- `CPU_RAM_MONITOR_README.md` - Documentation

### Existing Files (if present):
- `tmux_htop_style_monitor.py` - HTOP-style monitor
- `tmux_system_analyzer_simple.py` - System analyzer
- `README.md` - Original documentation

## ✅ After Deployment

### 1. SSH to the remote machine:
```bash
ssh root@150.241.244.130
```

### 2. Navigate to the monitoring directory:
```bash
cd /root/TmuxMonitoring
```

### 3. Run the launcher:
```bash
python3 launch_monitor.py
```

### 4. Or run individual monitors:
```bash
# Simple monitor (recommended for daily use)
python3 simple_cpu_ram_monitor.py

# Trading bot monitor (for bot management)
python3 trading_bot_cpu_monitor.py

# Advanced monitor (with interactive controls)
python3 cpu_ram_process_monitor.py
```

## 🔧 Troubleshooting

### If you get permission errors:
```bash
chmod +x /root/TmuxMonitoring/*.py
```

### If Python files don't run:
```bash
# Check Python version
python3 --version

# Try with python instead of python3
python launch_monitor.py
```

### If files are missing:
```bash
# Check what files are in the directory
ls -la /root/TmuxMonitoring/

# Re-transfer missing files
scp /path/to/missing/file.py root@150.241.244.130:/root/TmuxMonitoring/
```

## 📖 Documentation

After deployment, read the documentation:
```bash
cat /root/TmuxMonitoring/CPU_RAM_MONITOR_README.md
```

## 🎯 Quick Start

Once deployed, the easiest way to use the monitors is:

1. SSH to the machine
2. Run: `cd /root/TmuxMonitoring && python3 launch_monitor.py`
3. Choose option 1 for simple monitoring or option 2 for trading bot monitoring

---

**The monitors are specifically designed for your 16-core trading bot system and will show you exactly which processes are using which CPU cores and how much RAM!** 🚀
