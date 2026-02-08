# CPU & RAM Process Monitor for Trading Bots

This directory contains specialized monitoring tools for your 16-core trading bot system. These tools provide real-time CPU and RAM usage monitoring specifically designed for trading bot management.

## 🚀 Quick Start

### Easy Launcher (Recommended)
```bash
cd /Users/apple/Desktop/lab_code/TmuxMonitoring
python3 launch_monitor.py
```

This will show you a menu with all available monitors. Choose the one that best fits your needs.

## 📊 Available Monitors

### 1. Simple CPU & RAM Monitor
**File:** `simple_cpu_ram_monitor.py`
**Best for:** Quick monitoring, easy to use
```bash
python3 simple_cpu_ram_monitor.py
```

**Features:**
- Shows all Python processes
- Real-time CPU and RAM usage
- 16-core CPU display
- System memory breakdown
- Process summary statistics
- Auto-refresh every 3 seconds

### 2. Trading Bot CPU Monitor
**File:** `trading_bot_cpu_monitor.py`
**Best for:** Trading bot specific monitoring
```bash
python3 trading_bot_cpu_monitor.py
```

**Features:**
- Identifies trading bots automatically
- Shows CPU core distribution
- Tracks CPU usage trends (rising/falling/stable)
- Bot-specific metrics
- Core affinity analysis
- Auto-refresh every 2 seconds

### 3. Advanced CPU & RAM Monitor
**File:** `cpu_ram_process_monitor.py`
**Best for:** Detailed analysis with interactive controls
```bash
python3 cpu_ram_process_monitor.py
```

**Features:**
- Interactive keyboard controls
- Detailed process information
- CPU history tracking
- Process filtering and sorting
- Thread and core analysis
- Save current view to file

### 4. System Analyzer
**File:** `tmux_system_analyzer_simple.py`
**Best for:** One-time comprehensive system analysis
```bash
python3 tmux_system_analyzer_simple.py
```

**Features:**
- Comprehensive system report
- Performance recommendations
- Health scoring
- Detailed explanations

### 5. HTOP-Style Monitor
**File:** `tmux_htop_style_monitor.py`
**Best for:** Interactive process management
```bash
python3 tmux_htop_style_monitor.py
```

**Features:**
- HTOP-like interface
- Process control (kill, restart)
- Real-time updates
- Interactive navigation

## 🎯 Which Monitor Should You Use?

### For Daily Monitoring:
- **Simple CPU & RAM Monitor** - Clean, easy to read, perfect for checking system status

### For Trading Bot Management:
- **Trading Bot CPU Monitor** - Specifically designed for your trading bots, shows which bots are using which CPU cores

### For Troubleshooting:
- **Advanced CPU & RAM Monitor** - Detailed analysis with interactive controls

### For System Analysis:
- **System Analyzer** - Comprehensive one-time report with recommendations

### For Process Management:
- **HTOP-Style Monitor** - Interactive process control and management

## 📋 What You'll See

### System Overview
- Overall CPU usage across all 16 cores
- Per-core CPU usage display
- Total system memory usage
- Available memory
- System load average

### Process Information
- **PID:** Process ID
- **Bot Name:** Name of the trading bot
- **%CPU:** CPU usage percentage
- **%MEM:** Memory usage percentage
- **RAM:** Actual memory usage (MB/GB)
- **Threads:** Number of threads
- **Status:** Process status (Running, Sleeping, etc.)
- **Uptime:** How long the process has been running
- **Trend:** CPU usage trend (rising/falling/stable)
- **Cores:** Which CPU cores the process can use

### Color Coding
- 🟢 **Green:** Normal/Low usage
- 🟡 **Yellow:** Moderate usage
- 🔴 **Red:** High usage

## 🔧 Usage Tips

### 1. Start with Simple Monitor
If you're new to these tools, start with the Simple CPU & RAM Monitor. It's the easiest to understand and provides all the essential information.

### 2. Use Trading Bot Monitor for Bot Management
When you need to see which trading bots are using which CPU cores, use the Trading Bot CPU Monitor. It automatically identifies your trading bots and shows their CPU distribution.

### 3. Check Trends
The Trading Bot Monitor shows CPU trends (rising/falling/stable) which helps you identify bots that are becoming more or less CPU-intensive over time.

### 4. Monitor Memory Usage
All monitors show both percentage and actual memory usage. Watch for bots using more than 1GB of RAM as this might indicate memory leaks.

### 5. Use System Analyzer for Health Checks
Run the System Analyzer periodically to get a comprehensive health report of your entire system.

## 🚨 Troubleshooting

### If No Processes Show Up:
- Make sure your trading bots are running
- Check that the bot configuration files exist
- The monitors automatically detect Python processes

### If CPU Usage Seems High:
- Check the per-core display to see if specific cores are overloaded
- Look at the trend indicators to see if usage is increasing
- Use the System Analyzer for detailed recommendations

### If Memory Usage is High:
- Look for processes using more than 1GB of RAM
- Check the memory breakdown in the system overview
- Consider restarting high-memory processes

## 📁 File Locations

All monitor scripts are located in:
```
/Users/apple/Desktop/lab_code/TmuxMonitoring/
```

## 🔄 Auto-Refresh

All monitors automatically refresh every 2-3 seconds to show real-time data. Press `Ctrl+C` to stop any monitor and return to the launcher.

## 💡 Pro Tips

1. **Run the launcher first** - It's the easiest way to access all monitors
2. **Use Simple Monitor for daily checks** - It's clean and easy to read
3. **Use Trading Bot Monitor when managing bots** - It shows bot-specific information
4. **Check trends regularly** - Rising CPU trends might indicate issues
5. **Monitor memory usage** - Watch for memory leaks in long-running bots

## 🆘 Getting Help

If you need help with any monitor:
1. Press `h` in the Advanced Monitor for help
2. Check this README file
3. All monitors show their controls at the bottom of the screen

---

**Happy Monitoring!** 🚀

These tools are specifically designed for your 16-core trading bot system and will help you keep track of CPU and RAM usage across all your processes.
