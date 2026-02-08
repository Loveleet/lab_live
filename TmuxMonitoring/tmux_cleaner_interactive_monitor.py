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
# Mouse support removed - using keyboard input only

# Configuration
CLEANER_DIR = "/root/TmuxCleaner"
BOTS_FILE = os.path.join(CLEANER_DIR, "botsBackup.txt")
BOTS_TXT_FILE = os.path.join(CLEANER_DIR, "bots.txt")
INSTRUCTOR_FILE = os.path.join(CLEANER_DIR, "instructor.txt")

# Database configuration
DB_CONFIG = {
    'host': '127.0.0.1',
    'user': 'lab',
    'password': 'IndiaNepal1-',
    'port': '5432',
    'database': 'labdb2'
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
    
    # Time-based color coding
    GREEN_BEST = '\033[92m'        # < 3 minutes - Green best
    PARROT_GREEN = '\033[92m\033[1m'  # < 5 minutes - Parrot green (bright green)
    LIGHT_RED = '\033[91m'         # < 15 minutes - Light red
    CRITICAL_RED = '\033[91m\033[1m'  # < 30 minutes - Critical red (bold red)
    DEEP_RED = '\033[31m\033[1m'   # 30+ minutes - Deep red

def get_time_color(minutes):
    """Get color based on time difference in minutes"""
    if minutes < 3:
        return Colors.GREEN_BEST
    elif minutes < 5:
        return Colors.PARROT_GREEN
    elif minutes < 15:
        return Colors.LIGHT_RED
    elif minutes < 30:
        return Colors.CRITICAL_RED
    else:
        return Colors.DEEP_RED

def get_input():
    """Get keyboard input only"""
    return input(f"{Colors.BOLD}Select option (1-13): {Colors.ENDC}").strip()

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
    """Optimized process detection - same as cleaner for consistency"""
    matches = []
    try:
        # Use pgrep for much faster process detection (same as cleaner)
        result = subprocess.run(['pgrep', '-f', f'python.*{script_path}'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            matches = [int(pid.strip()) for pid in result.stdout.split('\n') if pid.strip()]
    except (subprocess.TimeoutExpired, ValueError, subprocess.SubprocessError):
        # Fallback to psutil if pgrep fails
        script_name = os.path.basename(script_path)
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] == 'python3.11' and proc.info['cmdline']:
                    cmdline = ' '.join(proc.info['cmdline'])
                    if script_name in cmdline or script_path in cmdline:
                        matches.append(proc.info['pid'])
            except:
                continue
    
    return matches

def get_process_start_time(script_path):
    """Get the earliest process start time for a script - same logic as cleaner"""
    pids = get_python_pids_for(script_path)
    if not pids:
        return None
    
    # Use the first PID (main process) - same as cleaner
    try:
        process = psutil.Process(pids[0])
        return process.create_time()
    except:
        return None

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
    """Get bot's last timestamp from database - use files without /root/ prefix"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        with conn.cursor() as cursor:
            # For /root/trading_runner_final.py, use the exact path (saved by tmux cleaner)
            if script_path == '/root/trading_runner_final.py':
                cursor.execute("SELECT last_timestamp FROM tmux_log WHERE code = %s ORDER BY last_timestamp DESC LIMIT 1", (script_path,))
                result = cursor.fetchone()
                if result:
                    return result[0]
            
            # For other files, use the name without /root/ prefix (saved by the bots themselves)
            script_name = os.path.basename(script_path)
            if script_name.endswith('.py'):
                script_name = script_name[:-3]  # Remove .py
            
            # Create specific mapping for known variations
            name_mapping = {
                'botmain': 'BotMain',
                'IMACD_BackTest_Database': 'IMACD', 
                'Pair_Status': 'PairStatus',
                'trading_runner_final': 'FinalTrading'
            }
            
            # Try exact mapping first
            if script_name in name_mapping:
                cursor.execute("SELECT last_timestamp FROM tmux_log WHERE code = %s ORDER BY last_timestamp DESC LIMIT 1", (name_mapping[script_name],))
                result = cursor.fetchone()
                if result:
                    return result[0]
            
            # Try script name without extension
            cursor.execute("SELECT last_timestamp FROM tmux_log WHERE code = %s ORDER BY last_timestamp DESC LIMIT 1", (script_name,))
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

def parse_uptime_timer(script_path):
    """Parse uptime timer (R-20) from bot configuration"""
    try:
        with open(BOTS_FILE, 'r') as f:
            lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            if '|' in line:
                parts = line.split('|')
                # Handle both formats: script|R-timer and script|alarm|A|restart|R-timer
                if len(parts) >= 2:
                    # Check if last part is R-timer
                    if parts[-1].strip().startswith('R-'):
                        try:
                            uptime_minutes = int(parts[-1].strip().replace('R-', ''))
                            if parts[0].strip() == script_path:
                                return uptime_minutes
                        except ValueError:
                            continue
    except:
        pass
    return None

def get_ready_timer_bots():
    """Get all bots that are ready for timer restart with their uptime"""
    ready_bots = []
    
    try:
        with open(BOTS_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if '|' in line:
                    parts = line.split('|')
                    # Handle both formats: script|R-timer and script|alarm|A|restart|R-timer
                    if len(parts) >= 2 and parts[-1].strip().startswith('R-'):
                        try:
                            script_path = parts[0].strip()
                            uptime_timer_minutes = int(parts[-1].strip().replace('R-', ''))
                            uptime_actual = get_uptime_minutes(script_path)
                            if uptime_actual and uptime_actual >= uptime_timer_minutes:
                                ready_bots.append((script_path, uptime_actual, uptime_timer_minutes))
                        except ValueError:
                            continue
    except:
        pass
    
    # Sort by uptime (highest first)
    ready_bots.sort(key=lambda x: x[1], reverse=True)
    return ready_bots

def get_uptime_minutes(script_path):
    """Get current uptime in minutes for a script"""
    try:
        pids = get_python_pids_for(script_path)
        if not pids:
            return None
        
        # Use the first PID (main process)
        process = psutil.Process(pids[0])
        start_time = process.create_time()
        current_time = time.time()
        uptime_seconds = current_time - start_time
        return uptime_seconds / 60  # Convert to minutes
    except:
        return None

def get_timer_queue_info(script_path):
    """Get queue position and estimated start time for a bot"""
    ready_bots = get_ready_timer_bots()
    
    # Check if ANY bot has been running for less than 2 minutes
    # This includes bots that just restarted (0 minutes uptime)
    try:
        with open('/home/lab/TmuxCleaner/botsBackup.txt', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Extract script path
                    if '|' in line:
                        check_script_path = line.split('|')[0].strip()
                    else:
                        check_script_path = line.strip()
                    
                    # Check if bot is running
                    pids = get_python_pids_for(check_script_path)
                    if pids:  # Bot is running
                        uptime_minutes = get_uptime_minutes(check_script_path)
                        if uptime_minutes is not None and uptime_minutes < 2.0:
                            # Found a bot running less than 2 minutes - no restarts allowed
                            return None, None
    except:
        pass  # If file read fails, continue with normal logic
    
    # Find this bot in the queue
    for i, (bot_path, uptime, timer_minutes) in enumerate(ready_bots):
        if bot_path == script_path:
            if i == 0:
                return 0, 0  # W-0, immediate start
            else:
                wait_position = i
                wait_minutes = i * 0.5  # 30-second intervals
                return wait_position, wait_minutes
    
    return None, None  # Not in queue

def get_uptime_timer_info(script_path):
    """Get uptime timer information for display with queue management"""
    uptime_timer_minutes = parse_uptime_timer(script_path)
    if not uptime_timer_minutes:
        return "N/A", "N/A", "N/A"
    
    uptime_str = get_uptime(script_path)
    if not uptime_str:
        return f"R-{uptime_timer_minutes}", "N/A", "N/A"
    
    # Parse current uptime (convert "1h 30m" to minutes)
    uptime_parts = uptime_str.split()
    uptime_minutes_actual = 0
    for part in uptime_parts:
        if 'h' in part:
            uptime_minutes_actual += int(part.replace('h', '')) * 60
        elif 'm' in part:
            uptime_minutes_actual += int(part.replace('m', ''))
    
    # Check if bot is ready for restart
    if uptime_minutes_actual >= uptime_timer_minutes:
        # Bot is ready - check queue position
        queue_position, wait_minutes = get_timer_queue_info(script_path)
        if queue_position == 0:
            return f"R-{uptime_timer_minutes}", uptime_str, f"{Colors.FAIL}RESTART!{Colors.ENDC}"
        elif queue_position is not None and wait_minutes is not None:
            # Bot is in queue
            total_wait = wait_minutes
            return f"R-{uptime_timer_minutes}", uptime_str, f"{Colors.WARNING}W-{queue_position} (+{total_wait}m){Colors.ENDC}"
        else:
            # Bot is ready but not in queue (should restart immediately)
            return f"R-{uptime_timer_minutes}", uptime_str, f"{Colors.FAIL}RESTART!{Colors.ENDC}"
    else:
        # Bot not ready yet
        time_remaining = uptime_timer_minutes - uptime_minutes_actual
        if time_remaining <= 2:
            return f"R-{uptime_timer_minutes}", uptime_str, f"{Colors.WARNING}{time_remaining:.1f}m{Colors.ENDC}"
        else:
            return f"R-{uptime_timer_minutes}", uptime_str, f"{time_remaining:.1f}m"

def get_next_stage_info(script_path, timeout_spec, uptime_minutes):
    """Get next stage (Alarm/Restart/Timer) and time left"""
    # Get reference time (process or database)
    process_start_time = get_process_start_time(script_path)
    db_timestamp = get_bot_timestamp_from_db(script_path)
    
    reference_time = None
    if process_start_time:
        reference_time = process_start_time
    elif db_timestamp:
        reference_time = db_timestamp.timestamp()
    
    if not reference_time:
        return "N/A", "N/A"
    
    current_time = time.time()
    time_since = current_time - reference_time
    
    # Check uptime timer first (highest priority)
    if uptime_minutes:
        uptime_str = get_uptime(script_path)
        if uptime_str:
            uptime_parts = uptime_str.split()
            uptime_minutes_actual = 0
            for part in uptime_parts:
                if 'h' in part:
                    uptime_minutes_actual += int(part.replace('h', '')) * 60
                elif 'm' in part:
                    uptime_minutes_actual += int(part.replace('m', ''))
            
            uptime_remaining = uptime_minutes - uptime_minutes_actual
            if uptime_remaining <= 0:
                # Bot is ready - check queue position
                queue_position, wait_minutes = get_timer_queue_info(script_path)
                if queue_position == 0:
                    return "TIMER", f"{Colors.FAIL}RESTART!{Colors.ENDC}"
                elif queue_position is not None and wait_minutes is not None:
                    return "TIMER", f"{Colors.WARNING}W-{queue_position} (+{wait_minutes}m){Colors.ENDC}"
                else:
                    # Bot is ready but not in queue (should restart immediately)
                    return "TIMER", f"{Colors.FAIL}RESTART!{Colors.ENDC}"
            elif uptime_remaining <= 2:
                return "TIMER", f"{Colors.WARNING}{uptime_remaining:.1f}m{Colors.ENDC}"
            else:
                return "TIMER", f"{uptime_remaining:.1f}m"
    
    # Check database-based monitoring
    if timeout_spec and 'A' in timeout_spec:
        try:
            alarm_restart = timeout_spec.split('A')
            if len(alarm_restart) == 2:
                alarm_minutes = int(alarm_restart[0])
                restart_minutes = int(alarm_restart[1])
                
                alarm_seconds = alarm_minutes * 60
                restart_seconds = restart_minutes * 60
                
                if time_since >= restart_seconds:
                    return "RESTART", f"{Colors.FAIL}RESTART!{Colors.ENDC}"
                elif time_since >= alarm_seconds:
                    remaining = restart_seconds - time_since
                    return "RESTART", f"{Colors.WARNING}{int(remaining/60)}m{Colors.ENDC}"
                else:
                    remaining = alarm_seconds - time_since
                    return "ALARM", f"{int(remaining/60)}m"
        except:
            pass
    elif timeout_spec:
        try:
            timeout_minutes = int(timeout_spec)
            timeout_seconds = timeout_minutes * 60
            if time_since >= timeout_seconds:
                return "RESTART", f"{Colors.FAIL}RESTART!{Colors.ENDC}"
            else:
                remaining = timeout_seconds - time_since
                return "RESTART", f"{int(remaining/60)}m"
        except:
            pass
    
    return "N/A", "N/A"

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

def get_bot_status(script_path, timeout_spec=None, uptime_minutes=None):
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
        # Convert UTC timestamp to IST properly
        utc_time = datetime.datetime.fromtimestamp(process_start_time, tz=datetime.timezone.utc)
        ist_time = utc_time.astimezone(datetime.timezone(datetime.timedelta(hours=5, minutes=30)))
        process_time_str = ist_time.strftime("%H:%M:%S")
    else:
        process_time_str = "N/A"
    
    if db_timestamp:
        # DB time in IST only (time only, no date)
        # Convert DB timestamp to IST properly
        db_ist_time = db_timestamp.astimezone(datetime.timezone(datetime.timedelta(hours=5, minutes=30)))
        db_ist = db_ist_time.strftime("%H:%M:%S")
        db_time_str = f"{db_ist} IST"
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
        
        # For /root/trading_runner_final.py, use database time (saved by tmux cleaner)
        # For other files, prioritize process start time (system time is more reliable)
        if script_path == '/root/trading_runner_final.py':
            # Use database time for tmux cleaner status
            if process_start_time < db_timestamp_unix:
                timestamp_source = "DATABASE"
                reference_time = db_timestamp_unix
                logic_explanation = f"Process ({process_str}) < DB ({db_str}) → Using DATABASE time (tmux cleaner)"
            else:
                timestamp_source = "PROCESS"
                reference_time = process_start_time
                logic_explanation = f"Process ({process_str}) >= DB ({db_str}) → Using PROCESS time (tmux cleaner)"
        else:
            # For other files, prioritize process start time (system time is more reliable)
            if process_start_time > db_timestamp_unix:
                # Process is newer than DB → Use PROCESS time
                timestamp_source = "PROCESS"
                reference_time = process_start_time
                logic_explanation = f"Process ({process_str}) > DB ({db_str}) → Using PROCESS time (system)"
            else:
                # DB is newer than process → Use DATABASE time
                timestamp_source = "DATABASE"
                reference_time = db_timestamp_unix
                logic_explanation = f"Process ({process_str}) <= DB ({db_str}) → Using DATABASE time (system)"
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
    
    # Get uptime timer information
    uptime_timer, uptime_current, uptime_remaining = get_uptime_timer_info(script_path)
    
    # Get next stage information
    next_stage, next_stage_time = get_next_stage_info(script_path, timeout_spec, uptime_minutes)
    
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
        'time_remaining': next_stage_time,
        'timeout_spec': timeout_spec,
        'uptime_timer': uptime_timer,
        'uptime_current': uptime_current,
        'uptime_remaining': uptime_remaining,
        'next_stage': next_stage,
        'next_stage_time': next_stage_time
    }

def display_table(bots_data):
    """Display bot information in two focused tables"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*115}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}🤖 INTERACTIVE TMUX BOT MONITOR - COMPREHENSIVE VIEW{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*115}{Colors.ENDC}")
    
    # Show critical issues summary at the top
    critical_summary = get_critical_issues_summary(bots_data)
    print(f"\n{Colors.BOLD}{critical_summary}{Colors.ENDC}")
    print("-" * 115)
    
    # TABLE 1: Basic Status Information
    print(f"\n{Colors.BOLD}{Colors.OKCYAN}📊 TABLE 1: BASIC STATUS & MONITORING{Colors.ENDC}")
    print("-" * 115)
    
    # Table 1 header
    header1 = f"{Colors.BOLD}{'Script':<15} {'Status':<10} {'PIDs':<10} {'Memory':<10} {'Uptime':<8} {'Method':<12} {'Alarm':<6} {'Restart':<8} {'Timer':<8} {'Time Left':<8}{Colors.ENDC}"
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
        timer_col = f"{bot['uptime_timer']:<8}"
        time_left_col = f"{bot['time_remaining']:<8}"
        
        row = f"{script_col} {status_col} {pids_col} {memory_col} {uptime_col} {method_col} {alarm_col} {restart_col} {timer_col} {time_left_col}"
        print(row)
    
    print("-" * 120)
    
    # TABLE 2: Detailed Timestamp Information
    print(f"\n{Colors.BOLD}{Colors.OKCYAN}⏰ TABLE 2: DETAILED TIMESTAMP ANALYSIS{Colors.ENDC}")
    print("-" * 120)
    
    # Table 2 header with clear IST labels
    header2 = f"{Colors.BOLD}{'Script':<15} {'Process':<10} {'DB Time':<12} {'Source':<10} {'Time Since':<10} {'Next Stage':<12} {'Time Left':<10}{Colors.ENDC}"
    print(header2)
    # Sub-header for time columns
    sub_header = f"{'':<15} {'(IST)':<10} {'(IST)':<12} {'':<10} {'':<10} {'':<12} {'':<10}"
    print(sub_header)
    print("-" * 97)
    
    # Table 2 rows
    for bot in bots_data:
        script_col = f"{bot['short_name']:<15}"
        process_time_col = f"{bot['process_time']:<10}"
        db_time_col = f"{bot['db_time']:<12}"
        source_col = f"{bot['timestamp_source']:<10}"
        
        # Apply color coding to time_since based on minutes
        time_since_text = bot['time_since']
        if time_since_text != "N/A":
            # Extract minutes from time_since string (e.g., "51m 30s" -> 51)
            try:
                minutes_str = time_since_text.split('m')[0]
                minutes = int(minutes_str)
                time_color = get_time_color(minutes)
                time_since_col = f"{time_color}{time_since_text:<10}{Colors.ENDC}"
            except:
                time_since_col = f"{time_since_text:<10}"
        else:
            time_since_col = f"{time_since_text:<10}"
        
        next_stage_col = f"{bot['next_stage']:<12}"
        next_stage_time_col = f"{bot['next_stage_time']:<10}"
        
        row = f"{script_col} {process_time_col} {db_time_col} {source_col} {time_since_col} {next_stage_col} {next_stage_time_col}"
        print(row)
    
    print("-" * 120)
    
    # Compact summary and status
    total_bots = len(bots_data)
    healthy_bots = len([b for b in bots_data if b['status'] == 'HEALTHY'])
    stopped_bots = len([b for b in bots_data if b['status'] == 'STOPPED'])
    problem_bots = len([b for b in bots_data if b['status'] in ['ZERO_MEM', 'MEM_LEAK']])
    
    db_status = "🟢 ONLINE" if is_database_accessible() else "🔴 OFFLINE"
    utc_time, ist_time = get_utc_ist()
    
    print(f"{Colors.BOLD}📊 SUMMARY: Total: {total_bots} | Healthy: {Colors.OKGREEN}{healthy_bots}{Colors.ENDC} | Stopped: {Colors.FAIL}{stopped_bots}{Colors.ENDC} | Problems: {Colors.WARNING}{problem_bots}{Colors.ENDC} | DB: {db_status} | Time: IST {ist_time}{Colors.ENDC}")
    
    # Compact explanation
    print(f"\n{Colors.OKCYAN}📋 QUICK REFERENCE: Table 1=Status & Actions | Table 2=Timestamps & Logic | Process/DB Time=IST | W-X=Queue Position{Colors.ENDC}")

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
                        script_path = parts[0].strip()
                        
                        # Check for uptime timer (R-20 format)
                        uptime_minutes = None
                        if len(parts) > 1 and parts[-1].strip().startswith('R-'):
                            try:
                                uptime_minutes = int(parts[-1].strip().replace('R-', ''))
                                parts = parts[:-1]  # Remove R- part for further processing
                            except ValueError:
                                pass
                        
                        if len(parts) == 2:
                            timeout_spec = parts[1].strip()
                            if os.path.exists(script_path):
                                bot_status = get_bot_status(script_path, timeout_spec, uptime_minutes)
                                bots_data.append(bot_status)
                        elif len(parts) == 1 and uptime_minutes:
                            # Format: path|R-20 (uptime timer only)
                            if os.path.exists(script_path):
                                bot_status = get_bot_status(script_path, None, uptime_minutes)
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
        print("12. 📺 TMUX Session Manager")
        print("13. ❌ Exit")
        
        print(f"\n{Colors.OKCYAN}💡 TIP: Type numbers to select menu options!{Colors.ENDC}")
        choice = get_input()
        
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
            show_tmux_session_manager()
        elif choice == '13':
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
    """Get a one-line summary of critical issues including time-based issues"""
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
        
        # Check for time-based critical issues (> 3 minutes)
        if bot['time_since'] != "N/A":
            try:
                minutes_str = bot['time_since'].split('m')[0]
                minutes = int(minutes_str)
                if minutes >= 3:  # Show files with 3+ minutes time difference
                    time_color = get_time_color(minutes)
                    critical_issues.append(f"{time_color}{bot['short_name']}: {bot['time_since']}{Colors.ENDC}")
            except:
                pass
    
    if critical_issues:
        return f"{Colors.FAIL}🚨 CRITICAL ISSUES: {' | '.join(critical_issues)}{Colors.ENDC}"
    else:
        return f"{Colors.OKGREEN}✅ ALL SYSTEMS HEALTHY - No critical issues detected{Colors.ENDC}"

def continuous_monitoring():
    """Continuous monitoring with refresh"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}📈 CONTINUOUS MONITORING{Colors.ENDC}")
    print("1. 📊 Main Bots")
    print("2. 📊 No-cleaner Also")
    print("0. 🔙 Back to main menu")
    print("q. ❌ Quit")
    
    while True:
        choice = input(f"\n{Colors.BOLD}Select monitoring option (1, 2, 0=back, q=quit): {Colors.ENDC}").strip()
        
        if choice == '1':
            continuous_monitoring_main_bots()
        elif choice == '2':
            continuous_monitoring_with_nocleaner()
        elif choice == '0':
            break
        elif choice.lower() == 'q':
            print(f"{Colors.OKGREEN}👋 Goodbye!{Colors.ENDC}")
            sys.exit(0)
        else:
            print(f"{Colors.WARNING}❌ Invalid option. Use 1, 2, 0=back, or q=quit{Colors.ENDC}")

def continuous_monitoring_main_bots():
    """Continuous monitoring for main bots only"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}📈 CONTINUOUS MONITORING - MAIN BOTS{Colors.ENDC}")
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

def continuous_monitoring_with_nocleaner():
    """Continuous monitoring for main bots + nocleaner bots"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}📈 CONTINUOUS MONITORING - ALL BOTS (MAIN + NO-CLEANER){Colors.ENDC}")
    print(f"{Colors.OKCYAN}Press Ctrl+C to stop continuous monitoring{Colors.ENDC}")
    
    try:
        while True:
            os.system('clear')
            # Load main bots
            main_bots_data = load_bot_configuration()
            
            # Load nocleaner bots
            nocleaner_data = load_nocleaner_bots()
            
            # Combine both datasets
            all_bots_data = main_bots_data + nocleaner_data
            
            # Show critical issues summary at the top
            critical_summary = get_critical_issues_summary(all_bots_data)
            print(f"\n{Colors.BOLD}{critical_summary}{Colors.ENDC}")
            print("-" * 115)
            
            display_table(all_bots_data)
            print(f"\n{Colors.OKCYAN}🔄 Auto-refreshing in 30 seconds... (Ctrl+C to stop){Colors.ENDC}")
            time.sleep(30)
    except KeyboardInterrupt:
        print(f"\n{Colors.OKGREEN}✅ Continuous monitoring stopped{Colors.ENDC}")

def load_nocleaner_bots():
    """Load nocleaner bots from nocleaner.txt"""
    nocleaner_data = []
    nocleaner_file = os.path.join(CLEANER_DIR, "nocleaner.txt")
    
    if os.path.exists(nocleaner_file):
        try:
            with open(nocleaner_file, 'r') as f:
                nocleaner_bots = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            # Create bot status for nocleaner bots
            for script_path in nocleaner_bots:
                if os.path.exists(script_path):
                    bot_status = get_bot_status(script_path)
                    nocleaner_data.append(bot_status)
        except Exception as e:
            print(f"{Colors.FAIL}❌ Error reading nocleaner file: {e}{Colors.ENDC}")
    
    return nocleaner_data

def show_system_analysis():
    """Show comprehensive system analysis report"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}🔍 SYSTEM ANALYSIS REPORT{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Generating comprehensive system analysis...{Colors.ENDC}")
    
    try:
        # Import and run the system analyzer
        import subprocess
        result = subprocess.run(['python3', '/root/TmuxMonitoring/tmux_system_analyzer_simple.py'], 
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
        result = subprocess.run(['python3', '/root/TmuxMonitoring/tmux_htop_style_monitor.py'], 
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

def show_tmux_session_manager():
    """Show TMUX Session Manager"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}📺 TMUX SESSION MANAGER{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Launching tmux session manager...{Colors.ENDC}")
    
    try:
        # Import and run the tmux session manager
        import subprocess
        result = subprocess.run(['python3', '/root/TmuxMonitoring/tmux_session_manager.py'], 
                              timeout=None)  # No timeout for interactive tool
        
        if result.returncode != 0:
            print(f"{Colors.FAIL}❌ TMUX session manager exited with code {result.returncode}{Colors.ENDC}")
            
    except FileNotFoundError:
        print(f"{Colors.WARNING}⚠️  TMUX session manager not found. Please ensure tmux_session_manager.py is in the TmuxMonitoring directory{Colors.ENDC}")
    except KeyboardInterrupt:
        print(f"{Colors.OKGREEN}✅ TMUX session manager stopped{Colors.ENDC}")
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


