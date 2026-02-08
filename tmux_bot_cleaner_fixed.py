#!/usr/bin/env python3
"""
TMUX BOT CLEANER - FIXED VERSION
Fixed database operations to prevent hanging
"""

import os
import subprocess
import time
import psutil
import threading
from datetime import datetime, timedelta

# ---------------- Initialization ----------------
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ---------------- Configuration ----------------
INTERVAL = 30
MAX_MEMORY_PERCENT = 90
DB_LOCK_FILE = "/tmp/db_restart_in_progress"
DB_RESTART_TIMEOUT = 120
DB_PROCESS_NAME = "postgres"
PYTHON_PROCESS_NAME = "python3.11"

# Database configuration
DB_CONFIG = {
    'user': 'postgres',
    'password': 'IndiaNepal1-',
    'host': '150.241.244.23',
    'port': '5432',
    'database': 'labdb2',
    'sslmode': 'require'
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLEANER_DIR = os.path.join(BASE_DIR, "TmuxCleaner")

INSTRUCTOR_FILE = os.path.join(CLEANER_DIR, "instructor.txt")
MAIN_BOTS_FILE = os.path.join(CLEANER_DIR, "bots.txt")
BACKUP_BOTS_FILE = os.path.join(CLEANER_DIR, "botsBackup.txt")
NOCLEANER_FILE = os.path.join(CLEANER_DIR, "nocleaner.txt")
LOG_FILE = os.path.join(CLEANER_DIR, "monitoring.log")

last_mode = None

# ---------------- Logging ----------------
def get_utc_ist():
    try:
        utc_now = datetime.now(datetime.timezone.utc)
    except AttributeError:
        utc_now = datetime.utcnow()
    
    ist_now = utc_now + timedelta(hours=5, minutes=30)
    return utc_now, ist_now

def log_event(message):
    utc_time, ist_time = get_utc_ist()
    utc_str = utc_time.strftime("%Y-%m-%d %H:%M:%S")
    ist_str = ist_time.strftime("%Y-%m-%d %H:%M:%S")
    
    log_entry = f"[UTC: {utc_str} | IST: {ist_str}] {message}\n"
    
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Failed to write to log: {e}")

# ---------------- Database Functions ----------------
def get_db_connection():
    try:
        import psycopg2
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        log_event(f"⚠️ Database connection failed: {e}")
        return None

def is_database_accessible():
    try:
        if not is_db_running():
            return False
        import psycopg2
        conn = psycopg2.connect(**DB_CONFIG)
        conn.close()
        return True
    except ImportError:
        log_event("⚠️ psycopg2 not installed - database features disabled")
        return False
    except Exception as e:
        log_event(f"⚠️ Database connection test failed: {e}")
        return False

def update_tmux_cleaner_status():
    """Update trading_runner_final.py status in database every 2 minutes (for tmux cleaner status)"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cursor:
            # Use UPSERT to avoid duplicate key errors
            cursor.execute("""
                INSERT INTO tmux_log (code, last_timestamp, alert, log) 
                VALUES ('/root/trading_runner_final.py', NOW(), FALSE, '01/01-01 | 1')
                ON CONFLICT (code) 
                DO UPDATE SET 
                    last_timestamp = NOW(),
                    alert = FALSE,
                    log = '01/01-01 | 1'
            """)
            conn.commit()
            return True
    except Exception as e:
        log_event(f"⚠️ Failed to update tmux_cleaner status: {e}")
        return False
    finally:
        conn.close()

# ---------------- Process Management ----------------
def get_python_pids_for(script_path):
    matches = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if PYTHON_PROCESS_NAME in proc.info['name'] and script_path in ' '.join(proc.info['cmdline']):
                matches.append(proc.info['pid'])
        except:
            continue
    return matches

def get_running_tmux_sessions():
    try:
        result = subprocess.run(['tmux', 'list-sessions', '-F', '#{session_name}'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip().split('\n') if result.stdout.strip() else []
        return []
    except Exception as e:
        log_event(f"⚠️ Error getting tmux sessions: {e}")
        return []

def get_session_name(script_path):
    return os.path.splitext(os.path.basename(script_path))[0]

def get_daily_session_name(script_path):
    base_name = get_session_name(script_path)
    today = datetime.now().strftime("%m%d")
    
    existing_sessions = get_running_tmux_sessions()
    today_sessions = [s for s in existing_sessions if s.startswith(f"{base_name}_{today}_")]
    
    max_counter = 0
    for session in today_sessions:
        try:
            parts = session.split('_')
            if len(parts) >= 3:
                counter = int(parts[-1])
                max_counter = max(max_counter, counter)
        except:
            continue
    
    new_counter = max_counter + 1
    return f"{base_name}_{today}_{new_counter}"

def start_tmux_session(session_name, script_path):
    subprocess.call(['tmux', 'new-session', '-d', '-s', session_name, f'python3.11 "{script_path}"'])
    log_event(f"✅ Started tmux session '{session_name}' for {script_path}")

def kill_tmux_session(session):
    subprocess.call(['tmux', 'kill-session', '-t', session])
    log_event(f"❌ Killed tmux session: {session}")

def fix_bot(script_path):
    base_name = get_session_name(script_path)
    sessions = get_running_tmux_sessions()
    pids = get_python_pids_for(script_path)
    
    expected_session = get_daily_session_name(script_path)
    
    if not pids:
        log_event(f"⏳ Fixing bot: {script_path}")
        try:
            for s in sessions:
                if s.startswith(base_name):
                    kill_tmux_session(s)
            start_tmux_session(expected_session, script_path)
            time.sleep(2)
            new_pids = get_python_pids_for(script_path)
            if new_pids:
                log_event(f"✅ Restarted bot: {script_path}, PID: {new_pids}")
        except Exception as e:
            log_event(f"❌ Error fixing bot {script_path}: {e}")

# ---------------- Memory Checks ----------------
def is_memory_high():
    return psutil.virtual_memory().percent >= MAX_MEMORY_PERCENT

def get_total_python_memory():
    return sum(proc.info['memory_info'].rss for proc in psutil.process_iter(['name', 'memory_info', 'cmdline']) if PYTHON_PROCESS_NAME in proc.info['name'])

def get_db_memory():
    return sum(proc.info['memory_info'].rss for proc in psutil.process_iter(['name', 'memory_info']) if DB_PROCESS_NAME in proc.info['name'])

def is_db_running():
    return any(DB_PROCESS_NAME in proc.info['name'] for proc in psutil.process_iter(['name']))

# ---------------- File Reading ----------------
def read_file_list(file_path):
    if not os.path.exists(file_path):
        return []
    
    try:
        with open(file_path, 'r') as f:
            return [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
    except Exception as e:
        log_event(f"⚠️ Error reading {file_path}: {e}")
        return []

# ---------------- Bot Monitoring ----------------
def should_restart_bot_ram_only(script_path):
    """Simple RAM-based monitoring for bots without timeout specification"""
    pids = get_python_pids_for(script_path)
    if not pids:
        log_event(f"🔧 Bot {script_path} not running - will start")
        return True
    
    # Check if bot is running in a tmux session
    base_name = get_session_name(script_path)
    running_sessions = get_running_tmux_sessions()
    bot_in_tmux = any(session.startswith(base_name) for session in running_sessions)
    
    if not bot_in_tmux:
        log_event(f"🔧 Bot {script_path} running but not in tmux session - will restart in tmux")
        return True
    
    # Check memory usage
    total_memory = 0
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info']):
        try:
            if proc.info['pid'] in pids:
                memory = proc.info['memory_info'].rss
                total_memory += memory
        except:
            continue
    
    memory_mb = total_memory / 1024 / 1024
    
    if total_memory == 0:
        log_event(f"⚠️ Bot {script_path} has zero memory usage ({memory_mb:.2f} MB) - will restart")
        return True
    elif memory_mb > 3000:
        log_event(f"🚨 Bot {script_path} memory leak detected ({memory_mb:.2f} MB) - ALARM ONLY (no restart)")
        return False
    
    return False

# ---------------- Main Monitoring Loop ----------------
def monitor_loop():
    global last_mode
    
    log_event("🚀 tmux_bot_cleaner.py started (FIXED VERSION)")
    
    # Start tmux cleaner status update thread
    def update_status_thread():
        while True:
            try:
                if is_database_accessible():
                    update_tmux_cleaner_status()
                else:
                    log_event("⚠️ Database not accessible - skipping status update")
            except Exception as e:
                log_event(f"⚠️ Error in status update thread: {e}")
            time.sleep(120)
    
    threading.Thread(target=update_status_thread, daemon=True).start()
    
    while True:
        try:
            # Determine mode
            mode = 'MAIN'
            bots_file = MAIN_BOTS_FILE
            if os.path.exists(INSTRUCTOR_FILE):
                with open(INSTRUCTOR_FILE, 'r') as f:
                    code = f.read().strip().lower()
                    if code == 'backup':
                        mode = 'BACKUP'
                        bots_file = BACKUP_BOTS_FILE

            all_bots = read_file_list(bots_file)
            noclean_bots = set(read_file_list(NOCLEANER_FILE))
            bot_set = set(all_bots)
            cleanable_bots = list(bot_set - noclean_bots)
            db_monitor = any(line.strip().lower() == '*db' for line in all_bots)

            if last_mode != mode:
                log_event(f"📁 Mode: {mode} | PostgreSQL Monitoring: {'ON' if db_monitor else 'OFF'} | Bot Count: {len(all_bots)}")
                last_mode = mode

            # Handle nocleaner bots
            for path in noclean_bots:
                if not path.startswith('*'):
                    pids = get_python_pids_for(path)
                    if not pids:
                        log_event(f"🔧 Simple monitoring for nocleaner: {path}")
                        fix_bot(path)

            # Handle cleanable bots (RAM-only monitoring)
            ram_only_bots = []
            for script_path in cleanable_bots:
                if script_path.startswith('*'):
                    continue
                if '|' not in script_path:  # No timeout specified
                    ram_only_bots.append(script_path)

            # Process RAM-only bots
            if ram_only_bots:
                log_event(f"🔧 Processing {len(ram_only_bots)} RAM-only bots")
                for script_path in ram_only_bots:
                    if should_restart_bot_ram_only(script_path):
                        fix_bot(script_path)

            # Check memory and handle high RAM situations
            if is_memory_high():
                log_event("🚨 High memory usage detected!")
                py_mem = get_total_python_memory()
                db_mem = get_db_memory()
                log_event(f"📊 Python RAM: {py_mem / 1024 / 1024:.2f} MB | PostgreSQL RAM: {db_mem / 1024 / 1024:.2f} MB")

                if db_monitor and db_mem >= py_mem:
                    log_event("🔄 PostgreSQL using more RAM - restarting PostgreSQL...")
                    subprocess.call(['sudo', 'systemctl', 'restart', 'postgresql'])
                else:
                    log_event("🔧 High memory - restarting Python bots...")
                    for script_path in cleanable_bots:
                        if not script_path.startswith('*'):
                            fix_bot(script_path)

            log_event(f"📊 Monitoring cycle complete - RAM bots: {len(ram_only_bots)}")
            time.sleep(INTERVAL)
            
        except Exception as e:
            log_event(f"❌ Error in main monitoring loop: {e}")
            log_event("🔄 Continuing monitoring loop after error...")
            time.sleep(INTERVAL)

if __name__ == '__main__':
    monitor_loop()
