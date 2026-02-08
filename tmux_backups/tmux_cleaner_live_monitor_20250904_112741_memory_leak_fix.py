import os

import subprocess
import time
import psutil
import threading
from datetime import datetime, timedelta

# ---------------- Initialization ----------------
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ---------------- Configuration ----------------
MAX_MEMORY_PERCENT = 90
DB_LOCK_FILE = "/tmp/db_restart_in_progress"
DB_RESTART_TIMEOUT = 120
DB_PROCESS_NAME = "postgres"
PYTHON_PROCESS_NAME = "python3.11"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLEANER_DIR = os.path.join(BASE_DIR, "TmuxCleaner")

INSTRUCTOR_FILE = os.path.join(CLEANER_DIR, "instructor.txt")
MAIN_BOTS_FILE = os.path.join(CLEANER_DIR, "bots.txt")
BACKUP_BOTS_FILE = os.path.join(CLEANER_DIR, "botsBackup.txt")
NOCLEANER_FILE = os.path.join(CLEANER_DIR, "nocleaner.txt")
LOG_FILE = os.path.join(CLEANER_DIR, "monitoring.log")

# ---------------- Color Codes for Status Display ----------------
class Colors:
    GREEN = '\033[92m'      # ✅ Healthy/Good
    YELLOW = '\033[93m'     # ⚠️ Warning/Alarm
    RED = '\033[91m'        # ❌ Critical/Error
    BLUE = '\033[94m'       # ℹ️ Info
    PURPLE = '\033[95m'     # 🔍 Monitoring
    CYAN = '\033[96m'       # 📊 Status
    WHITE = '\033[97m'      # 📝 Normal text
    BOLD = '\033[1m'        # **Bold**
    UNDERLINE = '\033[4m'   # _Underline_
    RESET = '\033[0m'       # Reset all colors

def print_status(message, color=Colors.WHITE, bold=False):
    """Print colored status message"""
    style = Colors.BOLD if bold else ""
    print(f"{style}{color}{message}{Colors.RESET}")

def get_user_interval():
    """Politely ask user for monitoring interval"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}🤖 TMUX CLEANER LIVE MONITOR{Colors.RESET}")
    print(f"{Colors.WHITE}Welcome! I'll help you monitor your system in real-time.{Colors.RESET}\n")
    
    while True:
        try:
            interval = input(f"{Colors.YELLOW}⏰ Please enter the monitoring interval in seconds (e.g., 30, 60, 120): {Colors.RESET}")
            interval = int(interval)
            if interval < 5:
                print(f"{Colors.RED}❌ Please enter at least 5 seconds for monitoring interval.{Colors.RESET}")
                continue
            if interval > 3600:
                print(f"{Colors.RED}❌ Please enter no more than 3600 seconds (1 hour) for monitoring interval.{Colors.RESET}")
                continue
            break
        except ValueError:
            print(f"{Colors.RED}❌ Please enter a valid number.{Colors.RESET}")
    
    print(f"\n{Colors.GREEN}✅ Perfect! I'll monitor your system every {interval} seconds.{Colors.RESET}")
    print(f"{Colors.WHITE}Press Ctrl+C to stop the monitoring.{Colors.RESET}\n")
    
    return interval

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def get_tmux_cleaner_status():
    """Get tmux_cleaner process status"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
        try:
            if 'tmux_cleaner' in ' '.join(proc.info['cmdline']):
                uptime = time.time() - proc.info['create_time']
                uptime_str = f"{int(uptime//3600)}h {int((uptime%3600)//60)}m {int(uptime%60)}s"
                return {
                    'running': True,
                    'pid': proc.info['pid'],
                    'uptime': uptime_str,
                    'memory_mb': proc.info['memory_info'].rss / 1024 / 1024 if hasattr(proc, 'memory_info') else 0
                }
        except:
            continue
    return {'running': False, 'pid': None, 'uptime': 'N/A', 'memory_mb': 0}

def get_detailed_bot_status(script_path, timeout_minutes):
    """Get comprehensive bot status including health, alarms, and timing"""
    current_time = time.time()
    pids = get_python_pids_for(script_path)
    
    # Get file start time
    file_start_time = get_file_start_time(script_path)
    
    # Check if bot is running (either by PID or tmux session)
    base_name = get_session_name(script_path)
    sessions = get_running_tmux_sessions()
    has_tmux_session = any(session.startswith(base_name) for session in sessions)
    
    if not pids and not has_tmux_session:
        return {
            'status': 'stopped',
            'color': Colors.RED,
            'message': '❌ Bot is not running',
            'pids': [],
            'memory_mb': 0,
            'uptime': 'N/A',
            'next_action': 'Will start immediately',
            'time_remaining': '0s',
            'timestamp_source': 'N/A',
            'action_color': Colors.RED
        }
    
    # If we have a tmux session but no PIDs, the bot might be starting up
    if has_tmux_session and not pids:
        # Calculate time since tmux session was created
        session_creation_time = None
        for session in sessions:
            if session.startswith(base_name):
                try:
                    output = subprocess.check_output(['tmux', 'display-message', '-t', session, '-p', '#{session_created}'], 
                                                  stderr=subprocess.DEVNULL).decode().strip()
                    if output.isdigit():
                        session_creation_time = int(output)
                        break
                except:
                    continue
        
        if session_creation_time:
            time_since_creation = current_time - session_creation_time
            creation_time_str = f"{int(time_since_creation//60)}m {int(time_since_creation%60)}s ago"
            timestamp_source = f"tmux_session_created ({creation_time_str})"
        else:
            timestamp_source = "tmux_session_exists"
        
        return {
            'status': 'starting',
            'color': Colors.YELLOW,
            'message': '🔄 Bot is starting up (tmux session exists)',
            'pids': [],
            'memory_mb': 0,
            'uptime': 'N/A',
            'next_action': 'Waiting for process to start',
            'time_remaining': 'N/A',
            'timestamp_source': timestamp_source,
            'action_color': Colors.YELLOW
        }
    
    # Check memory usage
    total_memory = 0
    proc_start = None
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'create_time']):
        try:
            if proc.info['pid'] in pids:
                memory = proc.info['memory_info'].rss
                total_memory += memory
                if proc_start is None:
                    proc_start = proc.info['create_time']
        except:
            continue
    
    memory_mb = total_memory / 1024 / 1024
    uptime = current_time - proc_start if proc_start else 0
    uptime_str = f"{int(uptime//3600)}h {int((uptime%3600)//60)}m {int(uptime%60)}s" if uptime > 0 else "Starting up"
    
    # Determine health status
    if total_memory == 0:
        health_status = 'inactive'
        health_message = f"⚠️ Low memory usage ({memory_mb:.2f} MB) - may be starting up"
    elif memory_mb > 1000:
        health_status = 'memory_leak'
        health_message = f"⚠️ Memory leak detected ({memory_mb:.2f} MB)"
    else:
        health_status = 'healthy'
        health_message = f"✅ Healthy ({memory_mb:.2f} MB)"
    
    # Calculate timing information with better timestamp source detection
    if file_start_time:
        # Use file start time from tmux session
        reference_time = file_start_time
        timestamp_source = f"file_start_time ({datetime.fromtimestamp(file_start_time).strftime('%H:%M:%S')})"
        time_since_reference = current_time - reference_time
    elif proc_start:
        # Use process start time
        reference_time = proc_start
        timestamp_source = f"process_start_time ({datetime.fromtimestamp(proc_start).strftime('%H:%M:%S')})"
        time_since_reference = current_time - reference_time
    else:
        reference_time = current_time
        timestamp_source = "current_time"
        time_since_reference = 0
    
    # Determine next action and time remaining
    timeout_seconds = timeout_minutes * 60
    time_remaining = max(0, timeout_seconds - time_since_reference)
    
    if time_remaining == 0:
        next_action = "Will restart now"
        action_color = Colors.RED
    elif time_remaining <= 60:  # Less than 1 minute
        next_action = f"Will restart in {time_remaining:.0f}s"
        action_color = Colors.YELLOW
    else:
        next_action = f"Will restart in {time_remaining/60:.1f} minutes"
        action_color = Colors.BLUE
    
    # Determine overall status color
    if health_status == 'healthy' and time_remaining > 300:  # More than 5 minutes
        overall_color = Colors.GREEN
    elif health_status == 'healthy' and time_remaining > 60:
        overall_color = Colors.YELLOW
    elif health_status == 'healthy':
        overall_color = Colors.RED
    else:
        overall_color = Colors.RED
    
    return {
        'status': health_status,
        'color': overall_color,
        'message': health_message,
        'pids': pids,
        'memory_mb': memory_mb,
        'uptime': uptime_str,
        'next_action': next_action,
        'time_remaining': f"{time_remaining/60:.1f}m" if time_remaining > 60 else f"{time_remaining:.0f}s",
        'timestamp_source': timestamp_source,
        'action_color': action_color
    }

def display_live_status(interval):
    """Display live status of all systems"""
    clear_screen()
    
    # Get current time
    utc_time, ist_time = get_utc_ist()
    
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*100}")
    print(f"🤖 TMUX CLEANER LIVE MONITORING - Updates every {interval}s")
    print(f"{'='*100}{Colors.RESET}")
    
    print(f"{Colors.WHITE}📅 UTC Time: {utc_time}")
    print(f"🌍 IST Time: {ist_time}")
    print(f"⏰ Next Update: {interval} seconds{Colors.RESET}")
    
    # 1. TMUX Cleaner Status
    print(f"\n{Colors.BOLD}{Colors.PURPLE}🔧 TMUX CLEANER STATUS{Colors.RESET}")
    tmux_status = get_tmux_cleaner_status()
    if tmux_status['running']:
        print(f"{Colors.GREEN}✅ TMUX Cleaner is RUNNING")
        print(f"   PID: {tmux_status['pid']}")
        print(f"   Uptime: {tmux_status['uptime']}")
        print(f"   Memory: {tmux_status['memory_mb']:.2f} MB{Colors.RESET}")
    else:
        print(f"{Colors.RED}❌ TMUX Cleaner is NOT RUNNING{Colors.RESET}")
    
    # 2. System Memory Status
    print(f"\n{Colors.BOLD}{Colors.CYAN}💾 SYSTEM MEMORY STATUS{Colors.RESET}")
    memory_percent = psutil.virtual_memory().percent
    if memory_percent < 70:
        memory_color = Colors.GREEN
        memory_status = "✅ Good"
    elif memory_percent < 90:
        memory_color = Colors.YELLOW
        memory_status = "⚠️ Warning"
    else:
        memory_color = Colors.RED
        memory_status = "❌ Critical"
    
    print(f"{memory_color}{memory_status} Memory Usage: {memory_percent:.1f}%{Colors.RESET}")
    
    # 3. PostgreSQL Status
    print(f"\n{Colors.BOLD}{Colors.BLUE}🐘 POSTGRESQL STATUS{Colors.RESET}")
    if is_db_running():
        db_memory = get_db_memory() / 1024 / 1024
        print(f"{Colors.GREEN}✅ PostgreSQL is RUNNING")
        print(f"   Memory Usage: {db_memory:.2f} MB{Colors.RESET}")
    else:
        print(f"{Colors.RED}❌ PostgreSQL is NOT RUNNING{Colors.RESET}")
    
    # 4. Bot Status Table
    print(f"\n{Colors.BOLD}{Colors.GREEN}🤖 BOT STATUS TABLE{Colors.RESET}")
    
    # Read bot files
    mode = 'MAIN'
    bots_file = MAIN_BOTS_FILE
    if os.path.exists(INSTRUCTOR_FILE):
        with open(INSTRUCTOR_FILE, 'r') as f:
            code = f.read().strip().lower()
            if code == 'backup':
                mode = 'BACKUP'
                bots_file = BACKUP_BOTS_FILE
    
    print(f"{Colors.WHITE}📁 Current Mode: {mode}{Colors.RESET}")
    
    all_bots = read_file_list_with_timeout(bots_file)
    noclean_bots = set(read_file_list(NOCLEANER_FILE))
    
    # Prepare table data
    table_data = []
    running_count = 0
    starting_count = 0
    stopped_count = 0
    
    for bot_info in all_bots:
        if len(bot_info) == 2:
            script_path, timeout_minutes = bot_info
        else:
            script_path = bot_info
            timeout_minutes = 5  # Default timeout
        
        if script_path.startswith('*'):
            continue
            
        # Get detailed status
        status_info = get_detailed_bot_status(script_path, timeout_minutes)
        
        # Count different statuses
        if status_info['status'] == 'healthy':
            running_count += 1
        elif status_info['status'] == 'starting':
            starting_count += 1
        else:
            stopped_count += 1
        
        # Add to table data
        table_data.append({
            'script': os.path.basename(script_path),
            'status': status_info['message'],
            'pids': status_info['pids'] if status_info['pids'] else 'None',
            'memory': f"{status_info['memory_mb']:.2f} MB",
            'uptime': status_info['uptime'],
            'next_action': status_info['next_action'],
            'time_remaining': status_info['time_remaining'],
            'timestamp_source': status_info['timestamp_source'],
            'color': status_info['color']
        })
    
    # Display table header
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'─'*120}")
    print(f"{'Script':<25} {'Status':<30} {'PIDs':<8} {'Memory':<12} {'Uptime':<15} {'Next Action':<20} {'Time Left':<12} {'Timestamp Source':<25}")
    print(f"{'─'*120}{Colors.RESET}")
    
    # Display table rows
    for row in table_data:
        script_col = f"{row['script']:<25}"
        status_col = f"{row['status']:<30}"
        pids_col = f"{row['pids']:<8}" if isinstance(row['pids'], str) else f"{str(row['pids']):<8}"
        memory_col = f"{row['memory']:<12}"
        uptime_col = f"{row['uptime']:<15}"
        next_action_col = f"{row['next_action']:<20}"
        time_remaining_col = f"{row['time_remaining']:<12}"
        timestamp_col = f"{row['timestamp_source']:<25}"
        
        print(f"{row['color']}{script_col} {status_col} {pids_col} {memory_col} {uptime_col} {next_action_col} {time_remaining_col} {timestamp_col}{Colors.RESET}")
    
    # Display table footer
    print(f"{Colors.BOLD}{Colors.CYAN}{'─'*120}{Colors.RESET}")
    
    # 5. Summary
    print(f"\n{Colors.BOLD}{Colors.PURPLE}📊 SUMMARY{Colors.RESET}")
    total_bots = len(all_bots)
    
    print(f"{Colors.WHITE}Total Bots: {total_bots}")
    print(f"{Colors.GREEN}Running: {running_count}")
    print(f"{Colors.YELLOW}Starting: {starting_count}")
    print(f"{Colors.RED}Stopped: {stopped_count}")
    print(f"Mode: {mode}")
    print(f"Memory Threshold: {MAX_MEMORY_PERCENT}%")
    print(f"Monitoring Interval: {interval} seconds{Colors.RESET}")
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*100}")
    print(f"🔄 LIVE MONITORING ACTIVE - Press Ctrl+C to stop")
    print(f"{'='*100}{Colors.RESET}")

def parse_bot_line(line):
    """Parse bot line: path|timeout_minutes"""
    if '|' not in line:
        return None, None
    parts = line.strip().split('|')
    if len(parts) != 2:
        return None, None
    try:
        path = parts[0].strip()
        timeout = int(parts[1].strip())
        return path, timeout
    except ValueError:
        return None, None

def read_file_list_with_timeout(path):
    """Read bot files with timeout information"""
    if not os.path.exists(path):
        return []
    
    bots = []
    timeouts = []  # Collect all valid timeouts
    
    # First pass: collect all valid timeouts
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                script_path, timeout = parse_bot_line(line)
                if script_path and timeout:
                    timeouts.append(timeout)
    
    # Calculate max timeout (default to 5 if no valid timeouts found)
    max_timeout = max(timeouts) if timeouts else 5
    
    # Second pass: assign timeouts to bots
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                script_path, timeout = parse_bot_line(line)
                if script_path and timeout:
                    # File has explicit timeout
                    bots.append((script_path, timeout))
                else:
                    # File has no timeout - use max timeout from other files
                    bots.append((line, max_timeout))
    
    return bots

def get_utc_ist():
    utc_now = datetime.utcnow()
    ist_now = utc_now + timedelta(hours=5, minutes=30)
    return utc_now.strftime('%Y-%m-%d %H:%M:%S'), ist_now.strftime('%Y-%m-%d %H:%M:%S')

def get_session_name(script_path):
    return os.path.splitext(os.path.basename(script_path))[0]

def get_running_tmux_sessions():
    try:
        output = subprocess.check_output(['tmux', 'ls'], stderr=subprocess.DEVNULL).decode()
        return [line.split(':')[0] for line in output.strip().splitlines()]
    except subprocess.CalledProcessError:
        return []

def get_python_pids_for(script_path):
    matches = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if PYTHON_PROCESS_NAME in proc.info['name'] and script_path in ' '.join(proc.info['cmdline']):
                matches.append(proc.info['pid'])
        except:
            continue
    return matches

def get_file_start_time(script_path):
    """Get when the file was started (from tmux session creation time)"""
    base_name = get_session_name(script_path)
    sessions = get_running_tmux_sessions()
    
    for session in sessions:
        if session.startswith(base_name):
            try:
                # Get session creation time
                output = subprocess.check_output(['tmux', 'display-message', '-t', session, '-p', '#{session_created}'], 
                                              stderr=subprocess.DEVNULL).decode().strip()
                if output.isdigit():
                    return int(output)
            except:
                continue
    
    return None

def get_db_memory():
    return sum(proc.info['memory_info'].rss for proc in psutil.process_iter(['name', 'memory_info']) if DB_PROCESS_NAME in proc.info['name'])

def is_db_running():
    return any(DB_PROCESS_NAME in proc.info['name'] for proc in psutil.process_iter(['name']))

def read_file_list(path):
    if not os.path.exists(path):
        return []
    with open(path, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

def live_monitoring_loop(interval):
    """Main live monitoring loop"""
    try:
        while True:
            display_live_status(interval)
            time.sleep(interval)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.BOLD}{Colors.GREEN}✅ Live monitoring stopped by user.{Colors.RESET}")
        print(f"{Colors.WHITE}Thank you for using TMUX Cleaner Live Monitor!{Colors.RESET}\n")

# ---------------- Main Execution ----------------
if __name__ == '__main__':
    try:
        # Get user interval
        interval = get_user_interval()
        
        # Start live monitoring
        live_monitoring_loop(interval)
        
    except Exception as e:
        print(f"\n{Colors.RED}❌ An error occurred: {e}{Colors.RESET}")
        print(f"{Colors.WHITE}Please check your configuration and try again.{Colors.RESET}")
