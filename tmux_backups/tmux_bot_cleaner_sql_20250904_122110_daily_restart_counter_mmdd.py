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
MAX_MEMORY_PERCENT = 45
SQL_LOCK_FILE = "/tmp/sql_restart_in_progress"
SQL_RESTART_TIMEOUT = 120
SQL_PROCESS_NAME = "sqlservr"
PYTHON_PROCESS_NAME = "python3"

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
    utc_now = datetime.utcnow()
    ist_now = utc_now + timedelta(hours=5, minutes=30)
    return utc_now.strftime('%Y-%m-%d %H:%M:%S'), ist_now.strftime('%Y-%m-%d %H:%M:%S')

def log_event(message):
    utc_time, ist_time = get_utc_ist()
    line = f"[UTC: {utc_time} | IST: {ist_time}] {message}"
    if os.isatty(1):
        print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')
    trim_old_logs()

def trim_old_logs():
    if not os.path.exists(LOG_FILE):
        return
    with open(LOG_FILE, 'r') as f:
        lines = f.readlines()
    new_lines = []
    for line in lines:
        try:
            timestamp_str = line.split('UTC: ')[1].split(' |')[0]
            log_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            if datetime.utcnow() - log_time <= timedelta(days=7):
                new_lines.append(line)
        except:
            new_lines.append(line)
    with open(LOG_FILE, 'w') as f:
        f.writelines(new_lines)

# ---------------- Utilities ----------------
def read_file_list(path):
    if not os.path.exists(path):
        return []
    with open(path, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

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

def start_tmux_session(session_name, script_path):
    subprocess.call(['tmux', 'new-session', '-d', '-s', session_name, f'python3 "{script_path}"'])
    log_event(f"✅ Started tmux session '{session_name}' for {script_path}")

def kill_tmux_session(session):
    subprocess.call(['tmux', 'kill-session', '-t', session])
    log_event(f"❌ Killed tmux session: {session}")

def kill_pid(pid):
    try:
        os.kill(pid, 9)
        log_event(f"❌ Killed process PID: {pid}")
        return True
    except Exception as e:
        log_event(f"⚠️ Failed to kill PID {pid}: {e}")
        return False

# ---------------- Memory Checks ----------------
def is_memory_high():
    return psutil.virtual_memory().percent >= MAX_MEMORY_PERCENT

def get_total_python_memory():
    return sum(proc.info['memory_info'].rss for proc in psutil.process_iter(['name', 'memory_info', 'cmdline']) if PYTHON_PROCESS_NAME in proc.info['name'])

def get_sql_memory():
    return sum(proc.info['memory_info'].rss for proc in psutil.process_iter(['name', 'memory_info']) if SQL_PROCESS_NAME in proc.info['name'])

def is_sql_running():
    return any(SQL_PROCESS_NAME in proc.info['name'] for proc in psutil.process_iter(['name']))

# ---------------- Lock Handling ----------------
def lock_restart():
    with open(SQL_LOCK_FILE, 'w') as f:
        f.write(str(time.time()))
    log_event("🔐 SQL restart lock created")

def is_restart_pending():
    if not os.path.exists(SQL_LOCK_FILE):
        return False
    try:
        with open(SQL_LOCK_FILE, 'r') as f:
            timestamp = float(f.read().strip())
        return (time.time() - timestamp) < SQL_RESTART_TIMEOUT
    except:
        return False

def unlock_restart():
    if os.path.exists(SQL_LOCK_FILE):
        os.remove(SQL_LOCK_FILE)
        log_event("🔓 SQL restart lock removed")

# ---------------- Bot Handlers ----------------
def fix_bot(script_path):
    base_name = get_session_name(script_path)
    sessions = get_running_tmux_sessions()
    pids = get_python_pids_for(script_path)
    expected_session = f"{base_name}1" if f"{base_name}1" not in sessions else f"{base_name}2"

    if not pids:
        log_event(f"⏳ Fixing bot: {script_path}")
        for s in sessions:
            if s.startswith(base_name):
                kill_tmux_session(s)
        start_tmux_session(expected_session, script_path)
        time.sleep(2)
        new_pids = get_python_pids_for(script_path)
        log_event(f"✅ Restarted bot: {script_path}, PID: {new_pids}")

def fix_all_bots(bot_list):
    for script in bot_list:
        if not script.startswith('*'):
            fix_bot(script)

def kill_all_bots(bot_list):
    for script in bot_list:
        for pid in get_python_pids_for(script):
            kill_pid(pid)
        base_name = get_session_name(script)
        for session in get_running_tmux_sessions():
            if session.startswith(base_name):
                kill_tmux_session(session)
    log_event("🧹 All bots cleaned and killed")

# ---------------- SQL Restart Logic (Fixed) ----------------
def restart_sql_thread(cleanable_bots):
    lock_restart()
    
    # Step 1: Restart SQL server
    log_event("🔄 Step 1: Restarting SQL server...")
    subprocess.call(['sudo', 'systemctl', 'restart', 'mssql-server'])
    
    # Wait 60 seconds and check if SQL is running
    log_event("⏳ Waiting 60 seconds to check if SQL restarted...")
    time.sleep(60)
    
    if is_sql_running():
        log_event("✅ SQL restarted successfully after Step 1.")
        unlock_restart()
        return
    
    # Step 2: Kill Python bots to free RAM
    log_event("⚠️ SQL still not up after 60s. Releasing RAM by killing Python bots...")
    kill_all_bots(cleanable_bots)
    
    # Wait 60 seconds and check again
    log_event("⏳ Waiting 60 seconds after killing bots to check SQL...")
    time.sleep(60)
    
    if is_sql_running():
        log_event("✅ SQL came back after Step 2 (killing bots).")
        unlock_restart()
        return
    
    # Step 3: Kill SQL process forcibly and restart
    log_event("🔥 SQL still down. Forcing SQL kill and restart...")
    subprocess.call(['sudo', 'pkill', '-9', SQL_PROCESS_NAME])
    time.sleep(5)
    subprocess.call(['sudo', 'systemctl', 'restart', 'mssql-server'])
    
    # Wait 90 seconds and check again
    log_event("⏳ Waiting 90 seconds after forced SQL restart...")
    time.sleep(90)
    
    if is_sql_running():
        log_event("✅ SQL came back after Step 3 (forced restart).")
        unlock_restart()
        return
    
    # Step 4: Final resort - reboot system
    log_event("💣 SQL restart failed again. Rebooting system...")
    unlock_restart()
    subprocess.call(['sudo', 'reboot'])

# ---------------- Monitoring ----------------
def monitor_loop():
    global last_mode, cleanable_bots

    log_event("🚀 tmux_bot_cleaner.py started")

    while True:
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
        sql_monitor = any(line.strip().lower() == '*sql' for line in all_bots)

        if last_mode != mode:
            log_event(f"📁 Mode: {mode} | SQL Monitoring: {'ON' if sql_monitor else 'OFF'} | Bot Count: {len(all_bots)}")
            last_mode = mode

        if not is_memory_high():
            fix_all_bots(all_bots)
        else:
            log_event("🚨 High memory usage detected!")
            py_mem = get_total_python_memory()
            sql_mem = get_sql_memory()
            log_event(f"📊 Python RAM: {py_mem / 1024 / 1024:.2f} MB | SQL RAM: {sql_mem / 1024 / 1024:.2f} MB")

            if sql_monitor and sql_mem >= py_mem:
                if not is_restart_pending():
                    threading.Thread(target=restart_sql_thread, args=(cleanable_bots,)).start()
                else:
                    log_event("⏳ SQL restart already in progress. Skipping.")
            else:
                log_event("🔧 Restarting Python bots consuming RAM...")
                kill_all_bots(cleanable_bots)
                time.sleep(2)
                fix_all_bots(cleanable_bots)

        fix_all_bots(noclean_bots)
        time.sleep(INTERVAL)

if __name__ == '__main__':
    monitor_loop() 