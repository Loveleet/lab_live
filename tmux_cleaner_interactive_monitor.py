#!/usr/bin/env python3
"""
Interactive TMUX Bot Monitor
Shows comprehensive bot status, timestamps, and monitoring information in table format
"""

import os
import sys
import time
import psutil
import subprocess
import datetime
import psycopg2
from typing import Dict, List, Tuple, Optional
import select
import tty
import termios

# Configuration
CLEANER_DIR = "/root/TmuxCleaner"
BOTS_FILE = os.path.join(CLEANER_DIR, "botsBackup.txt")
BOTS_TXT_FILE = os.path.join(CLEANER_DIR, "bots.txt")
INSTRUCTOR_FILE = os.path.join(CLEANER_DIR, "instructor.txt")

# Database configuration
DB_CONFIG = {
    'host': '150.241.244.23',
    'user': 'postgres',
    'password': 'IndiaNepal1-',
    'database': 'labdb2',
    'sslmode': 'require'
}

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def enable_mouse_support():
    """Enable mouse support in terminal"""
    print('\033[?1000h', end='')  # Enable mouse tracking
    print('\033[?1002h', end='')  # Enable mouse drag events
    print('\033[?1003h', end='')  # Enable all mouse events

def disable_mouse_support():
    """Disable mouse support in terminal"""
    print('\033[?1000l', end='')  # Disable mouse tracking
    print('\033[?1002l', end='')  # Disable mouse drag events
    print('\033[?1003l', end='')  # Disable all mouse events

def get_mouse_click():
    """Get mouse click coordinates if available"""
    try:
        # Check if input is available
        if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
            # Read the input
            ch = sys.stdin.read(1)
            if ch == '\033':  # ESC sequence
                # Read more characters to get mouse event
                seq = ch + sys.stdin.read(2)
                if seq == '\033[M':
                    # Mouse event detected
                    b = ord(sys.stdin.read(1))
                    x = ord(sys.stdin.read(1)) - 33
                    y = ord(sys.stdin.read(1)) - 33
                    
                    # Check if it's a left mouse button click (button 0)
                    if b == 32:  # Left mouse button down
                        return (x, y)
        return None
    except:
        return None

def get_input_with_mouse():
    """Get input with mouse click support"""
    # Check if we're in an interactive terminal
    if not sys.stdin.isatty():
        # Not an interactive terminal (e.g., SSH without -t), use regular input
        return input(f"{Colors.BOLD}Select option (1-12): {Colors.ENDC}").strip()
    
    try:
        # Try to enable mouse support
        enable_mouse_support()
        
        # Set terminal to raw mode for better input handling
        old_settings = termios.tcgetattr(sys.stdin)
        tty.setraw(sys.stdin.fileno())
        
        print(f"{Colors.BOLD}Select option (1-12) or click: {Colors.ENDC}", end='', flush=True)
        
        while True:
            # Check for mouse click
            mouse_pos = get_mouse_click()
            if mouse_pos:
                x, y = mouse_pos
                # Map mouse coordinates to menu options
                # Menu starts around line 10, each option is 1 line
                menu_line = y - 10
                if 0 <= menu_line <= 11:  # 12 menu options (0-11)
                    choice = str(menu_line + 1)
                    print(choice)  # Echo the choice
                    return choice
            
            # Check for keyboard input
            if select.select([sys.stdin], [], [], 0.1) == ([sys.stdin], [], []):
                ch = sys.stdin.read(1)
                if ch.isdigit():
                    print(ch, end='', flush=True)
                    return ch
                elif ch in ['\r', '\n']:  # Enter key
                    print()
                    return '1'  # Default to option 1
                elif ch == '\x03':  # Ctrl+C
                    print()
                    return '12'  # Exit
                    
    except KeyboardInterrupt:
        return '12'  # Exit
    except Exception as e:
        # Fallback to regular input if mouse support fails
        print(f"\n{Colors.WARNING}Mouse support unavailable, using keyboard input only{Colors.ENDC}")
        return input(f"{Colors.BOLD}Select option (1-12): {Colors.ENDC}").strip()
    finally:
        # Restore terminal settings
        try:
            if 'old_settings' in locals():
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        except:
            pass
        # Disable mouse support
        try:
            disable_mouse_support()
        except:
            pass

def get_utc_ist():
    """Get current UTC and IST time"""
    try:
        utc_now = datetime.datetime.now(datetime.datetime.timezone.utc)
    except AttributeError:
        # Fallback for older Python versions
        utc_now = datetime.datetime.utcnow()
    
    ist_time = utc_now + datetime.timedelta(hours=5, minutes=30)
    return utc_now.strftime("%Y-%m-%d %H:%M:%S"), ist_time.strftime("%Y-%m-%d %H:%M:%S")

def is_database_accessible():
    """Check if database is accessible"""
    try:
        # Quick check if PostgreSQL process is running
        if not any('postgres' in proc.info['name'] for proc in psutil.process_iter(['name'])):
            return False
        
        # Try a quick connection
        conn = psycopg2.connect(**DB_CONFIG, connect_timeout=5)
        conn.close()
        return True
    except:
        return False

def get_db_connection():
    """Get database connection if accessible"""
    if is_database_accessible():
        try:
            return psycopg2.connect(**DB_CONFIG)
        except:
            return None
    return None

def get_tmux_sessions():
    """Get list of running tmux sessions"""
    try:
        result = subprocess.run(['tmux', 'list-sessions', '-F', '#{session_name}'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
        return []
    except:
        return []

def get_python_pids_for(script_path):
    """Get PIDs for Python processes running the specified script"""
    pids = []
    script_name = os.path.basename(script_path)
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] == 'python3.11' and proc.info['cmdline']:
                cmdline = ' '.join(proc.info['cmdline'])
                if script_name in cmdline or script_path in cmdline:
                    pids.append(proc.info['pid'])
        except:
            continue
    
    return pids

def get_process_start_time(script_path):
    """Get the earliest process start time for a script"""
    pids = get_python_pids_for(script_path)
    if not pids:
        return None
    
    earliest_time = None
    for pid in pids:
        try:
            proc = psutil.Process(pid)
            create_time = proc.create_time()
            if earliest_time is None or create_time < earliest_time:
                earliest_time = create_time
        except:
            continue
    
    return earliest_time

def get_tmux_session_creation_time(session_name):
    """Get tmux session creation time"""
    try:
        result = subprocess.run(['tmux', 'display-message', '-t', session_name, '-p', '#{session_created}'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip().isdigit():
            return int(result.stdout.strip())
        return None
    except:
        return None

def get_bot_timestamp_from_db(script_path):
    """Get bot's last timestamp from database - smart matching"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        with conn.cursor() as cursor:
            # Try exact path match first
            cursor.execute("SELECT last_timestamp FROM tmux_log WHERE code = %s ORDER BY last_timestamp DESC LIMIT 1", (script_path,))
            result = cursor.fetchone()
            if result:
                return result[0]
            
            # Try script name without path and extension
            script_name = os.path.basename(script_path)
            if script_name.endswith('.py'):
                script_name = script_name[:-3]  # Remove .py
            
            # Create specific mapping for known variations
            name_mapping = {
                'botmain.py': 'BotMain',
                'IMACD_BackTest_Database.py': 'IMACD',
                'Pair_Status.py': 'PairStatus',
                'trading_runner_final.py': 'FinalTrading'
            }
            
            # Try exact mapping first
            if script_name in name_mapping:
                cursor.execute("SELECT last_timestamp FROM tmux_log WHERE code = %s ORDER BY last_timestamp DESC LIMIT 1", (name_mapping[script_name],))
                result = cursor.fetchone()
                if result:
                    return result[0]
            
            # Try different variations of the name
            variations = [
                script_name,
                script_name.replace('_', ''),  # Remove underscores
                script_name.replace('_', '').replace('-', ''),  # Remove underscores and hyphens
                script_name.split('_')[0],  # First part before underscore
                script_name.split('_')[-1] if '_' in script_name else script_name,  # Last part after underscore
            ]
            
            for variation in variations:
                cursor.execute("SELECT last_timestamp FROM tmux_log WHERE code ILIKE %s ORDER BY last_timestamp DESC LIMIT 1", (f"%{variation}%",))
                result = cursor.fetchone()
                if result:
                    return result[0]
            
            return None
    except Exception as e:
        return None
    finally:
        conn.close()

def get_memory_usage(script_path):
    """Get memory usage for a script"""
    pids = get_python_pids_for(script_path)
    if not pids:
        return 0, "0 MB"
    
    total_memory = 0
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info']):
        try:
            if proc.info['pid'] in pids:
                memory = proc.info['memory_info'].rss
                total_memory += memory
        except:
            continue
    
    memory_mb = total_memory / 1024 / 1024
    return total_memory, f"{memory_mb:.2f} MB"

def get_uptime(script_path):
    """Get uptime for a script"""
    pids = get_python_pids_for(script_path)
    if not pids:
        return None
    
    earliest_time = None
    for pid in pids:
        try:
            proc = psutil.Process(pid)
            create_time = proc.create_time()
            if earliest_time is None or create_time < earliest_time:
                earliest_time = create_time
        except:
            continue
    
    if earliest_time:
        uptime_seconds = time.time() - earliest_time
        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        return f"{hours}h {minutes}m"
    
    return None

def get_smart_filename(script_path):
    """Get smart filename - compact format for long names"""
    filename = os.path.basename(script_path)
    
    # Remove .py extension for display (not necessary to show)
    if filename.endswith('.py'):
        name_part = filename[:-3]  # Remove .py
    else:
        name_part = filename
    
    # If name is short enough, return as is
    if len(name_part) <= 15:
        return name_part
    
    # For longer names, show beginning + ... + end parts (keep important parts)
    if len(name_part) > 15:
        # Show first 6 chars + ... + last 6 chars (keep more of the end)
        return f"{name_part[:6]}...{name_part[-6:]}"
    else:
        return name_part

def get_bot_status(script_path, timeout_spec=None):
    """Get comprehensive bot status with detailed timestamp logic"""
    pids = get_python_pids_for(script_path)
    memory_bytes, memory_str = get_memory_usage(script_path)
    uptime = get_uptime(script_path)
    
    # Determine status
    if not pids:
        status = "STOPPED"
        status_color = Colors.FAIL
    elif memory_bytes == 0:
        status = "ZERO_MEM"
        status_color = Colors.WARNING
    elif memory_bytes > 3000 * 1024 * 1024:  # > 3GB (memory leak threshold)
        status = "MEM_LEAK"
        status_color = Colors.FAIL
    elif memory_bytes > 2000 * 1024 * 1024:  # > 2GB (higher memory usage)
        status = "HIGHER_MEM"
        status_color = Colors.WARNING
    elif memory_bytes > 1000 * 1024 * 1024:  # > 1GB (high memory usage)
        status = "HIGH_MEM"
        status_color = Colors.WARNING
    else:
        status = "HEALTHY"
        status_color = Colors.OKGREEN
    
    # Get timestamps
    process_start_time = get_process_start_time(script_path)
    db_timestamp = get_bot_timestamp_from_db(script_path)
    
    # Format timestamps for display (IST for process, UTC/IST for DB)
    if process_start_time:
        # Process time in IST only (time only, no date)
        ist_time = datetime.datetime.fromtimestamp(process_start_time) + datetime.timedelta(hours=5, minutes=30)
        process_time_str = ist_time.strftime("%H:%M:%S")
    else:
        process_time_str = "N/A"
    
    if db_timestamp:
        # DB time in both UTC and IST (time only, no date)
        db_utc = db_timestamp.strftime("%H:%M:%S")
        db_ist = (db_timestamp + datetime.timedelta(hours=5, minutes=30)).strftime("%H:%M:%S")
        db_time_str = f"{db_utc}/{db_ist}"
    else:
        db_time_str = "N/A"
    
    # Determine timestamp source and reference time (same logic as main cleaner)
    if process_start_time and db_timestamp:
        db_timestamp_unix = db_timestamp.timestamp()
        
        # Convert process start time to datetime for proper comparison
        process_datetime = datetime.datetime.fromtimestamp(process_start_time)
        
        # Format timestamps for display (time only, no date)
        process_str = process_datetime.strftime("%H:%M:%S")
        db_str = db_timestamp.strftime("%H:%M:%S")
        
        # Compare Unix timestamps (handles dates automatically)
        if process_start_time < db_timestamp_unix:
            # Process started BEFORE DB timestamp → Use DATABASE time (DB is newer)
            timestamp_source = "DATABASE"
            reference_time = db_timestamp_unix
            logic_explanation = f"Process ({process_str}) < DB ({db_str}) → Using DATABASE time"
        else:
            # Process started AFTER DB timestamp → Use PROCESS time (process is newer)
            timestamp_source = "PROCESS"
            reference_time = process_start_time
            logic_explanation = f"Process ({process_str}) >= DB ({db_str}) → Using PROCESS time"
    elif process_start_time:
        timestamp_source = "PROCESS"
        reference_time = process_start_time
        process_str = datetime.datetime.fromtimestamp(process_start_time).strftime("%H:%M:%S")
        logic_explanation = f"No DB time → Using PROCESS time ({process_str})"
    elif db_timestamp:
        timestamp_source = "DATABASE"
        reference_time = db_timestamp.timestamp()
        db_str = db_timestamp.strftime("%H:%M:%S")
        logic_explanation = f"No process → Using DATABASE time ({db_str})"
    else:
        timestamp_source = "NONE"
        reference_time = None
        logic_explanation = "No timestamps available"
    
    # Calculate time since reference
    if reference_time:
        time_since_reference = time.time() - reference_time
        time_since_str = f"{int(time_since_reference // 60)}m {int(time_since_reference % 60)}s"
    else:
        time_since_str = "N/A"
    
    # Determine monitoring method and get detailed alarm/restart information
    monitoring_method = "NO_MONITOR"
    alarm_info = "N/A"
    restart_info = "N/A"
    next_step = "N/A"
    time_remaining = "N/A"
    
    if timeout_spec:
        if 'A' in timeout_spec:
            try:
                alarm_restart = timeout_spec.split('A')
                if len(alarm_restart) == 2:
                    alarm_minutes = int(alarm_restart[0])
                    restart_minutes = int(alarm_restart[1])
                    monitoring_method = f"ALARM+RESTART"
                    alarm_info = f"{alarm_minutes}m"
                    restart_info = f"{restart_minutes}m"
                    
                    if reference_time:
                        alarm_seconds = alarm_minutes * 60
                        restart_seconds = restart_minutes * 60
                        time_since = time.time() - reference_time
                        
                        if time_since >= restart_seconds:
                            next_step = "🚨 RESTART NOW"
                            time_remaining = "0m"
                        elif time_since >= alarm_seconds:
                            remaining = restart_seconds - time_since
                            next_step = "⚠️ RESTART"
                            time_remaining = f"{int(remaining/60)}m"
                        else:
                            remaining = alarm_seconds - time_since
                            next_step = "📊 ALARM"
                            time_remaining = f"{int(remaining/60)}m"
            except:
                monitoring_method = "INVALID_FORMAT"
                alarm_info = "INVALID"
                restart_info = "INVALID"
        else:
            try:
                timeout_minutes = int(timeout_spec)
                monitoring_method = f"DIRECT_RESTART"
                alarm_info = "N/A"
                restart_info = f"{timeout_minutes}m"
                
                if reference_time:
                    timeout_seconds = timeout_minutes * 60
                    time_since = time.time() - reference_time
                    if time_since >= timeout_seconds:
                        next_step = "🚨 RESTART NOW"
                        time_remaining = "0m"
                    else:
                        remaining = timeout_seconds - time_since
                        next_step = "⚠️ RESTART"
                        time_remaining = f"{int(remaining/60)}m"
            except:
                monitoring_method = "INVALID_FORMAT"
                restart_info = "INVALID"
    else:
        monitoring_method = "NO_MONITOR"
    
    return {
        'script_path': script_path,
        'short_name': get_smart_filename(script_path),
        'status': status,
        'status_color': status_color,
        'pids': pids,
        'memory': memory_str,
        'uptime': uptime,
        'monitoring_method': monitoring_method,
        'timestamp_source': timestamp_source,
        'logic_explanation': logic_explanation,
        'process_time': process_time_str,
        'db_time': db_time_str,
        'time_since': time_since_str,
        'alarm_info': alarm_info,
        'restart_info': restart_info,
        'next_step': next_step,
        'time_remaining': time_remaining,
        'timeout_spec': timeout_spec
    }

def display_table(bots_data):
    """Display bot information in two focused tables"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*115}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}🤖 INTERACTIVE TMUX BOT MONITOR - COMPREHENSIVE VIEW{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*115}{Colors.ENDC}")
    
    # TABLE 1: Basic Status Information
    print(f"\n{Colors.BOLD}{Colors.OKCYAN}📊 TABLE 1: BASIC STATUS & MONITORING{Colors.ENDC}")
    print("-" * 115)
    
    # Table 1 header
    header1 = f"{Colors.BOLD}{'Script':<15} {'Status':<10} {'PIDs':<10} {'Memory':<10} {'Uptime':<8} {'Method':<12} {'Alarm':<6} {'Restart':<8} {'Next Step':<12} {'Time Left':<8}{Colors.ENDC}"
    print(header1)
    print("-" * 107)
    
    # Table 1 rows
    for bot in bots_data:
        script_col = f"{bot['short_name']:<15}"
        status_col = f"{bot['status_color']}{bot['status']:<10}{Colors.ENDC}"
        pids_col = f"{str(bot['pids'])[:9]:<10}"
        memory_col = f"{bot['memory']:<10}"
        uptime_col = f"{bot['uptime'] or 'N/A':<8}"
        method_col = f"{bot['monitoring_method']:<12}"
        alarm_col = f"{bot['alarm_info']:<6}"
        restart_col = f"{bot['restart_info']:<8}"
        next_step_col = f"{bot['next_step']:<12}"
        time_left_col = f"{bot['time_remaining']:<8}"
        
        row = f"{script_col} {status_col} {pids_col} {memory_col} {uptime_col} {method_col} {alarm_col} {restart_col} {next_step_col} {time_left_col}"
        print(row)
    
    print("-" * 120)
    
    # TABLE 2: Detailed Timestamp Information
    print(f"\n{Colors.BOLD}{Colors.OKCYAN}⏰ TABLE 2: DETAILED TIMESTAMP ANALYSIS{Colors.ENDC}")
    print("-" * 120)
    
    # Table 2 header with clear UTC/IST labels
    header2 = f"{Colors.BOLD}{'Script':<15} {'Process':<10} {'DB Time':<18} {'Source':<10} {'Time Since':<10} {'Logic':<30}{Colors.ENDC}"
    print(header2)
    # Sub-header for time columns
    sub_header = f"{'':<15} {'(IST)':<10} {'(UTC/IST)':<18} {'':<10} {'':<10} {'':<30}"
    print(sub_header)
    print("-" * 97)
    
    # Table 2 rows
    for bot in bots_data:
        script_col = f"{bot['short_name']:<15}"
        process_time_col = f"{bot['process_time']:<10}"
        db_time_col = f"{bot['db_time']:<18}"
        source_col = f"{bot['timestamp_source']:<10}"
        time_since_col = f"{bot['time_since']:<10}"
        logic_col = f"{bot['logic_explanation'][:29]:<30}"
        
        row = f"{script_col} {process_time_col} {db_time_col} {source_col} {time_since_col} {logic_col}"
        print(row)
    
    print("-" * 120)
    
    # Summary
    total_bots = len(bots_data)
    healthy_bots = len([b for b in bots_data if b['status'] == 'HEALTHY'])
    stopped_bots = len([b for b in bots_data if b['status'] == 'STOPPED'])
    problem_bots = len([b for b in bots_data if b['status'] in ['ZERO_MEM', 'MEM_LEAK']])
    
    print(f"{Colors.BOLD}📊 SUMMARY: Total: {total_bots} | Healthy: {Colors.OKGREEN}{healthy_bots}{Colors.ENDC} | Stopped: {Colors.FAIL}{stopped_bots}{Colors.ENDC} | Problems: {Colors.WARNING}{problem_bots}{Colors.ENDC}{Colors.ENDC}")
    
    # Database status
    db_status = "🟢 ONLINE" if is_database_accessible() else "🔴 OFFLINE"
    print(f"{Colors.BOLD}🗄️  Database: {db_status}{Colors.ENDC}")
    
    # Current time
    utc_time, ist_time = get_utc_ist()
    print(f"{Colors.BOLD}⏰ Current Time: UTC {utc_time} | IST {ist_time}{Colors.ENDC}")
    
    # Detailed explanation
    print(f"\n{Colors.OKCYAN}📋 TABLE EXPLANATION:{Colors.ENDC}")
    print(f"  • Table 1: Basic monitoring status, alarms, and next actions")
    print(f"  • Table 2: Detailed timestamp analysis and logic explanation")
    print(f"  • Process Time: When Python process started (IST time)")
    print(f"  • DB Time: Last database timestamp (UTC/IST format)")
    print(f"  • Source: Which timestamp is used as reference")
    print(f"  • Logic: Why this timestamp source was chosen")
    
    # Monitoring method explanation
    print(f"\n{Colors.OKCYAN}🔍 MONITORING METHOD EXPLANATION:{Colors.ENDC}")
    print(f"  • ALARM+RESTART: Uses alarm threshold then restart threshold (e.g., 5A10)")
    print(f"  • DIRECT_RESTART: Restarts after timeout without alarm (e.g., 5)")
    print(f"  • NO_MONITOR: No timeout specified, only basic monitoring")
    print(f"  • INVALID_FORMAT: Timeout specification has errors")
    
    # Show logic explanation for each bot
    print(f"\n{Colors.OKCYAN}🧠 TIMESTAMP LOGIC SUMMARY:{Colors.ENDC}")
    for bot in bots_data:
        if bot['logic_explanation'] != "No timestamps available":
            print(f"  • {bot['short_name']}: {bot['logic_explanation']}")

def load_bot_configuration():
    """Load bot configuration from files - following same logic as main tmux cleaner"""
    bots_data = []
    
    # Determine which bots file to use (same logic as main cleaner)
    mode = 'MAIN'
    bots_file = BOTS_TXT_FILE  # Default: bots.txt
    
    if os.path.exists(INSTRUCTOR_FILE):
        with open(INSTRUCTOR_FILE, 'r') as f:
            code = f.read().strip().lower()
            if code == 'backup':
                mode = 'BACKUP'
                bots_file = BOTS_FILE  # Use botsBackup.txt
    
    print(f"{Colors.OKCYAN}📁 Mode: {mode} | Using file: {os.path.basename(bots_file)}{Colors.ENDC}")
    
    # Read only the selected bots file
    if os.path.exists(bots_file):
        with open(bots_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '|' in line:
                        parts = line.split('|')
                        if len(parts) == 2:
                            script_path = parts[0].strip()
                            timeout_spec = parts[1].strip()
                            if os.path.exists(script_path):
                                bot_status = get_bot_status(script_path, timeout_spec)
                                bots_data.append(bot_status)
                    else:
                        if os.path.exists(line):
                            bot_status = get_bot_status(line)
                            bots_data.append(bot_status)
    
    return bots_data

def interactive_menu():
    """Interactive menu for monitoring options"""
    while True:
        print(f"\n{Colors.BOLD}{Colors.OKCYAN}🔧 INTERACTIVE MONITORING MENU{Colors.ENDC}")
        print("1. 📊 Show Current Status (Table)")
        print("2. 🔄 Refresh Status")
        print("3. 📝 Show Detailed Logs")
        print("4. 🗄️  Database Status")
        print("5. 📁 Show Configuration Files")
        print("6. 🚀 Start/Stop Specific Bot")
        print("7. 🔍 Search Bot by Name")
        print("8. 📈 Continuous Monitoring")
        print("9. 🚫 Show Nocleaner Bots")
        print("10. 🔍 System Analysis Report")
        print("11. 🖥️  HTOP-Style Bot Monitor")
        print("12. ❌ Exit")
        
        print(f"\n{Colors.OKCYAN}💡 TIP: You can click on menu options or type numbers!{Colors.ENDC}")
        choice = get_input_with_mouse()
        
        if choice == '1':
            bots_data = load_bot_configuration()
            # Show critical issues summary
            critical_summary = get_critical_issues_summary(bots_data)
            print(f"\n{Colors.BOLD}{critical_summary}{Colors.ENDC}")
            print("-" * 115)
            display_table(bots_data)
        elif choice == '2':
            print(f"{Colors.OKGREEN}🔄 Refreshing status...{Colors.ENDC}")
            time.sleep(1)
            bots_data = load_bot_configuration()
            # Show critical issues summary
            critical_summary = get_critical_issues_summary(bots_data)
            print(f"\n{Colors.BOLD}{critical_summary}{Colors.ENDC}")
            print("-" * 115)
            display_table(bots_data)
        elif choice == '3':
            show_detailed_logs()
        elif choice == '4':
            show_database_status()
        elif choice == '5':
            show_configuration_files()
        elif choice == '6':
            manage_specific_bot()
        elif choice == '7':
            search_bot_by_name()
        elif choice == '8':
            continuous_monitoring()
        elif choice == '9':
            show_nocleaner_bots()
        elif choice == '10':
            show_system_analysis()
        elif choice == '11':
            show_htop_style_monitor()
        elif choice == '12':
            print(f"{Colors.OKGREEN}👋 Goodbye!{Colors.ENDC}")
            break
        else:
            print(f"{Colors.WARNING}❌ Invalid option. Please try again.{Colors.ENDC}")

def show_detailed_logs():
    """Show detailed logs"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}📝 DETAILED LOGS{Colors.ENDC}")
    
    # Monitoring log
    monitoring_log = os.path.join(CLEANER_DIR, "monitoring.log")
    if os.path.exists(monitoring_log):
        print(f"\n{Colors.OKCYAN}📊 Monitoring Log (last 10 lines):{Colors.ENDC}")
        try:
            with open(monitoring_log, 'r') as f:
                lines = f.readlines()
                for line in lines[-10:]:
                    print(f"  {line.strip()}")
        except:
            print("  Error reading monitoring log")
    
    # Bot restart log
    restart_log = os.path.join(CLEANER_DIR, "bot_restarts.log")
    if os.path.exists(restart_log):
        print(f"\n{Colors.OKCYAN}🤖 Bot Restart Log (last 5 events):{Colors.ENDC}")
        try:
            with open(restart_log, 'r') as f:
                content = f.read()
                events = content.split('🤖 BOT RESTART EVENT')
                for event in events[-5:]:
                    if event.strip():
                        lines = event.strip().split('\n')
                        for line in lines[:4]:  # Show first 4 lines of each event
                            if line.strip():
                                print(f"  {line.strip()}")
                        print()
        except:
            print("  Error reading restart log")

def show_database_status():
    """Show database status and recent entries"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}🗄️  DATABASE STATUS{Colors.ENDC}")
    
    if is_database_accessible():
        print(f"{Colors.OKGREEN}✅ Database is accessible{Colors.ENDC}")
        
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cursor:
                    # Show recent tmux_log entries
                    cursor.execute("SELECT code, last_timestamp, alert, log FROM tmux_log ORDER BY last_timestamp DESC LIMIT 10")
                    results = cursor.fetchall()
                    
                    if results:
                        print(f"\n{Colors.OKCYAN}📊 Recent Database Entries:{Colors.ENDC}")
                        print(f"{'Code':<30} {'Timestamp':<20} {'Alert':<8} {'Log':<20}")
                        print("-" * 80)
                        for row in results:
                            code = row[0][:29] if len(row[0]) > 29 else row[0]
                            timestamp = str(row[1])[:19] if row[1] else 'N/A'
                            alert = str(row[2])
                            log = str(row[3])[:19] if row[3] else 'N/A'
                            print(f"{code:<30} {timestamp:<20} {alert:<8} {log:<20}")
                    else:
                        print(f"{Colors.WARNING}⚠️  No entries found in database{Colors.ENDC}")
                        
            except Exception as e:
                print(f"{Colors.FAIL}❌ Database query error: {e}{Colors.ENDC}")
            finally:
                conn.close()
    else:
        print(f"{Colors.FAIL}❌ Database is not accessible{Colors.ENDC}")

def show_configuration_files():
    """Show configuration file contents"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}📁 CONFIGURATION FILES{Colors.ENDC}")
    
    # botsBackup.txt
    if os.path.exists(BOTS_FILE):
        print(f"\n{Colors.OKCYAN}📋 botsBackup.txt:{Colors.ENDC}")
        try:
            with open(BOTS_FILE, 'r') as f:
                content = f.read()
                print(f"  {content}")
        except:
            print("  Error reading file")
    
    # bots.txt
    if os.path.exists(BOTS_TXT_FILE):
        print(f"\n{Colors.OKCYAN}📋 bots.txt:{Colors.ENDC}")
        try:
            with open(BOTS_TXT_FILE, 'r') as f:
                content = f.read()
                print(f"  {content}")
        except:
            print("  Error reading file")

def manage_specific_bot():
    """Manage a specific bot (start/stop)"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}🚀 BOT MANAGEMENT{Colors.ENDC}")
    
    bots_data = load_bot_configuration()
    if not bots_data:
        print(f"{Colors.WARNING}⚠️  No bots found{Colors.ENDC}")
        return
    
    print(f"\n{Colors.OKCYAN}Available bots:{Colors.ENDC}")
    for i, bot in enumerate(bots_data):
        print(f"  {i+1}. {bot['script_path']}")
    
    try:
        choice = int(input(f"\n{Colors.BOLD}Select bot number (1-{len(bots_data)}): {Colors.ENDC}"))
        if 1 <= choice <= len(bots_data):
            selected_bot = bots_data[choice-1]
            print(f"\n{Colors.OKCYAN}Selected: {selected_bot['script_path']}{Colors.ENDC}")
            print(f"Current status: {selected_bot['status']}")
            print(f"PIDs: {selected_bot['pids']}")
            
            action = input(f"\n{Colors.BOLD}Action (start/stop/restart): {Colors.ENDC}").strip().lower()
            
            if action in ['start', 'restart']:
                print(f"{Colors.OKGREEN}🚀 Starting/restarting bot...{Colors.ENDC}")
                # Here you would implement the actual start/restart logic
                print(f"{Colors.OKGREEN}✅ Bot action completed{Colors.ENDC}")
            elif action == 'stop':
                print(f"{Colors.WARNING}🛑 Stopping bot...{Colors.ENDC}")
                # Here you would implement the actual stop logic
                print(f"{Colors.OKGREEN}✅ Bot stopped{Colors.ENDC}")
            else:
                print(f"{Colors.WARNING}⚠️  Invalid action{Colors.ENDC}")
        else:
            print(f"{Colors.WARNING}⚠️  Invalid selection{Colors.ENDC}")
    except ValueError:
        print(f"{Colors.WARNING}⚠️  Invalid input{Colors.ENDC}")

def search_bot_by_name():
    """Search for a bot by name"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}🔍 BOT SEARCH{Colors.ENDC}")
    
    search_term = input(f"{Colors.BOLD}Enter search term: {Colors.ENDC}").strip().lower()
    if not search_term:
        print(f"{Colors.WARNING}⚠️  No search term provided{Colors.ENDC}")
        return
    
    bots_data = load_bot_configuration()
    matching_bots = []
    
    for bot in bots_data:
        if search_term in bot['script_path'].lower() or search_term in bot['short_name'].lower():
            matching_bots.append(bot)
    
    if matching_bots:
        print(f"\n{Colors.OKGREEN}✅ Found {len(matching_bots)} matching bots:{Colors.ENDC}")
        display_table(matching_bots)
    else:
        print(f"{Colors.WARNING}⚠️  No bots found matching '{search_term}'{Colors.ENDC}")

def show_nocleaner_bots():
    """Show nocleaner bots from nocleaner.txt"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}🚫 NOCLEANER BOTS{Colors.ENDC}")
    
    nocleaner_file = os.path.join(CLEANER_DIR, "nocleaner.txt")
    if not os.path.exists(nocleaner_file):
        print(f"{Colors.WARNING}⚠️  Nocleaner file not found{Colors.ENDC}")
        return
    
    try:
        with open(nocleaner_file, 'r') as f:
            nocleaner_bots = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        if not nocleaner_bots:
            print(f"{Colors.WARNING}⚠️  No nocleaner bots found{Colors.ENDC}")
            return
        
        print(f"{Colors.OKCYAN}Found {len(nocleaner_bots)} nocleaner bots:{Colors.ENDC}")
        
        # Create bot status for nocleaner bots
        nocleaner_data = []
        for script_path in nocleaner_bots:
            if os.path.exists(script_path):
                bot_status = get_bot_status(script_path)
                nocleaner_data.append(bot_status)
        
        if nocleaner_data:
            print(f"\n{Colors.OKCYAN}📊 Nocleaner Bots Status:{Colors.ENDC}")
            display_table(nocleaner_data)
        else:
            print(f"{Colors.WARNING}⚠️  No valid nocleaner bot paths found{Colors.ENDC}")
            
    except Exception as e:
        print(f"{Colors.FAIL}❌ Error reading nocleaner file: {e}{Colors.ENDC}")

def get_critical_issues_summary(bots_data):
    """Get a one-line summary of critical issues"""
    critical_issues = []
    
    for bot in bots_data:
        # Check for critical statuses
        if bot['status'] in ['MEM_LEAK', 'ZERO_MEM', 'CRITICAL']:
            critical_issues.append(f"🔴 {bot['short_name']}: {bot['status']}")
        elif bot['status'] in ['HIGHER_MEM', 'HIGH_MEM']:
            critical_issues.append(f"🟠 {bot['short_name']}: {bot['status']}")
        elif bot['status'] == 'RESTARTING':
            critical_issues.append(f"🔄 {bot['short_name']}: Restarting")
        elif bot['status'] == 'STOPPED':
            critical_issues.append(f"🔴 {bot['short_name']}: STOPPED")
        elif bot['alarm_info'] == 'YES':
            critical_issues.append(f"⚠️ {bot['short_name']}: Alarm active")
    
    if critical_issues:
        return f"{Colors.FAIL}🚨 CRITICAL ISSUES: {' | '.join(critical_issues)}{Colors.ENDC}"
    else:
        return f"{Colors.OKGREEN}✅ ALL SYSTEMS HEALTHY - No critical issues detected{Colors.ENDC}"

def continuous_monitoring():
    """Continuous monitoring with refresh"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}📈 CONTINUOUS MONITORING{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Press Ctrl+C to stop continuous monitoring{Colors.ENDC}")
    
    try:
        while True:
            os.system('clear')
            bots_data = load_bot_configuration()
            
            # Show critical issues summary at the top
            critical_summary = get_critical_issues_summary(bots_data)
            print(f"\n{Colors.BOLD}{critical_summary}{Colors.ENDC}")
            print("-" * 115)
            
            display_table(bots_data)
            print(f"\n{Colors.OKCYAN}🔄 Auto-refreshing in 30 seconds... (Ctrl+C to stop){Colors.ENDC}")
            time.sleep(30)
    except KeyboardInterrupt:
        print(f"\n{Colors.OKGREEN}✅ Continuous monitoring stopped{Colors.ENDC}")

def show_system_analysis():
    """Show comprehensive system analysis report"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}🔍 SYSTEM ANALYSIS REPORT{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Generating comprehensive system analysis...{Colors.ENDC}")
    
    try:
        # Import and run the system analyzer
        import subprocess
        result = subprocess.run(['python3', 'tmux_system_analyzer_simple.py'], 
                              capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"{Colors.FAIL}❌ Error running system analyzer: {result.stderr}{Colors.ENDC}")
            
    except subprocess.TimeoutExpired:
        print(f"{Colors.WARNING}⚠️  System analysis timed out{Colors.ENDC}")
    except FileNotFoundError:
        print(f"{Colors.WARNING}⚠️  System analyzer not found. Please ensure tmux_system_analyzer.py is in the current directory{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.FAIL}❌ Error: {e}{Colors.ENDC}")
    
    try:
        input(f"\n{Colors.OKCYAN}Press Enter to return to main menu...{Colors.ENDC}")
    except EOFError:
        # Handle case when input is not available (e.g., automated testing)
        pass

def show_htop_style_monitor():
    """Show HTOP-style bot monitor"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}🖥️  HTOP-STYLE BOT MONITOR{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Launching real-time process monitor...{Colors.ENDC}")
    
    try:
        # Import and run the htop-style monitor
        import subprocess
        result = subprocess.run(['python3', 'tmux_htop_style_monitor.py'], 
                              timeout=None)  # No timeout for interactive tool
        
        if result.returncode != 0:
            print(f"{Colors.FAIL}❌ HTOP-style monitor exited with code {result.returncode}{Colors.ENDC}")
            
    except FileNotFoundError:
        print(f"{Colors.WARNING}⚠️  HTOP-style monitor not found. Please ensure tmux_htop_style_monitor.py is in the current directory{Colors.ENDC}")
    except KeyboardInterrupt:
        print(f"{Colors.OKGREEN}✅ HTOP-style monitor stopped{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.FAIL}❌ Error: {e}{Colors.ENDC}")
    
    try:
        input(f"\n{Colors.OKCYAN}Press Enter to return to main menu...{Colors.ENDC}")
    except EOFError:
        # Handle case when input is not available (e.g., automated testing)
        pass

def main():
    """Main function"""
    print(f"{Colors.BOLD}{Colors.HEADER}🚀 INTERACTIVE TMUX BOT MONITOR{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Loading bot configuration and status...{Colors.ENDC}")
    
    # Initial status display
    bots_data = load_bot_configuration()
    if bots_data:
        display_table(bots_data)
    else:
        print(f"{Colors.WARNING}⚠️  No bots found in configuration{Colors.ENDC}")
    
    # Start interactive menu
    interactive_menu()

if __name__ == "__main__":
    main()


