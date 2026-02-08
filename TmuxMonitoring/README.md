# TmuxMonitoring Directory

This directory contains all the tmux monitoring and analysis tools, organized separately from the main bot cleaner.

## 📁 Directory Structure

```
/root/
├── tmux_bot_cleaner_stopped.py            # Main bot cleaner (currently stopped)
└── TmuxMonitoring/                        # All monitoring tools
    ├── tmux_cleaner_interactive_monitor.py    # Interactive monitoring interface
    ├── tmux_htop_style_monitor.py             # HTOP-style real-time monitor
    ├── tmux_system_analyzer_simple.py         # System analysis tool (simplified)
    ├── tmux_system_analyzer.py                # System analysis tool (full version)
    ├── tmux_cleaner_live_monitor.py           # Live monitoring tool
    ├── tmux_cleaner_backupHelthCheck.py       # Backup health check tool
    ├── system_analyzer_standalone.py          # Standalone system analyzer
    ├── tmux_session_manager.py                # TMUX session manager
    ├── mouse_demo.py                           # Mouse click demo
    └── README.md                               # This file
```

## 🚀 Quick Start

### Main Bot Cleaner
```bash
# Run the main bot cleaner (from root directory)
# Note: Currently renamed to tmux_bot_cleaner_stopped.py (not running)
python3.11 /root/tmux_bot_cleaner_stopped.py
```

### Interactive Monitor
```bash
# Run the interactive monitoring interface (keyboard input only)
python3.11 /root/TmuxMonitoring/tmux_cleaner_interactive_monitor.py
```

### HTOP-Style Monitor
```bash
# Run the HTOP-style real-time monitor
python3.11 /root/TmuxMonitoring/tmux_htop_style_monitor.py
```

### System Analyzer
```bash
# Run the system analysis tool
python3.11 /root/TmuxMonitoring/tmux_system_analyzer_simple.py
```

### TMUX Session Manager
```bash
# Manage tmux sessions with process monitoring (keyboard input only)
python3.11 /root/TmuxMonitoring/tmux_session_manager.py
```

### Mouse Demo
```bash
# Test mouse click functionality
python3.11 /root/TmuxMonitoring/mouse_demo.py
```

## 📋 File Descriptions

### `tmux_cleaner_interactive_monitor.py`
- **Purpose**: Main interactive monitoring interface
- **Features**: 
  - Table-based bot status display
  - Mouse click support for menu navigation
  - Database integration
  - Critical issues summary
  - Access to all other monitoring tools
- **Usage**: Primary interface for monitoring bot status

### `tmux_htop_style_monitor.py`
- **Purpose**: Real-time HTOP-style process monitor
- **Features**:
  - Live process monitoring
  - CPU core usage tracking
  - Memory and thread analysis
  - Interactive keyboard controls
  - Real-time updates
- **Usage**: Detailed process analysis and monitoring

### `tmux_system_analyzer_simple.py`
- **Purpose**: Comprehensive system analysis tool
- **Features**:
  - CPU, memory, disk, network analysis
  - Process categorization
  - System health scoring
  - Detailed explanations of metrics
  - Performance recommendations
- **Usage**: System troubleshooting and optimization

### `tmux_system_analyzer.py`
- **Purpose**: Full-featured system analysis tool
- **Features**:
  - Comprehensive system analysis
  - Detailed process monitoring
  - Advanced system metrics
  - Performance analysis
- **Usage**: Advanced system troubleshooting and analysis

### `tmux_cleaner_live_monitor.py`
- **Purpose**: Live monitoring tool for bot processes
- **Features**:
  - Real-time bot monitoring
  - Live status updates
  - Process tracking
- **Usage**: Monitor bots in real-time

### `tmux_cleaner_backupHelthCheck.py`
- **Purpose**: Backup health check tool
- **Features**:
  - Health monitoring for backup systems
  - Backup status checking
  - System health validation
- **Usage**: Monitor backup system health

### `system_analyzer_standalone.py`
- **Purpose**: Standalone system analyzer wrapper
- **Features**:
  - Independent system analysis
  - Standalone execution
  - System metrics collection
- **Usage**: Run system analysis independently

### `tmux_session_manager.py`
- **Purpose**: Interactive tmux session management
- **Features**:
  - List all active tmux sessions
  - Show processes running in each session
  - Attach to sessions with keyboard commands
  - Delete sessions with confirmation
  - Real-time process monitoring (PID, memory, CPU, uptime)
  - Keyboard-based navigation
- **Usage**: Manage tmux sessions and monitor their processes

### `mouse_demo.py`
- **Purpose**: Mouse click functionality demonstration
- **Features**:
  - Mouse coordinate tracking
  - Terminal mouse support testing
  - Interactive click detection
- **Usage**: Testing mouse functionality in terminals

## 🔧 Integration

The interactive monitor (`tmux_cleaner_interactive_monitor.py`) serves as the main hub and can launch all other tools:

- **Option 10**: System Analysis Report → `tmux_system_analyzer_simple.py`
- **Option 11**: HTOP-Style Bot Monitor → `tmux_htop_style_monitor.py`

## 📝 Notes

- The main `tmux_bot_cleaner_stopped.py` remains in the root directory (currently not running)
- All monitoring tools are organized in this directory for better structure
- File paths are updated to reflect the new organization
- Keyboard input only for maximum compatibility
- All tools work in any terminal environment

## 🔧 Troubleshooting

### Input Method
All tools now use **keyboard input only** for maximum compatibility and reliability:

- **Type numbers** to select menu options (1-13)
- **Type commands** for session manager (A1, D1, R1, etc.)
- **No mouse required** - works in all terminals
- **SSH compatible** - works over SSH without special flags

### Terminal Compatibility
- **All terminals supported** - No special requirements
- **SSH compatible** - Works over SSH without `-t` flag
- **Non-interactive terminals** - Works in all environments
- **Older terminals** - Full compatibility

## 🚀 Future Enhancements

- Additional monitoring tools can be added to this directory
- Centralized configuration management
- Automated tool discovery and integration
- Enhanced logging and reporting capabilities
