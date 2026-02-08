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
    # Use timezone-aware UTC time to avoid deprecation warning
    # Compatible with older Python versions
    try:
        # Try Python 3.11+ method first
        utc_now = datetime.now(datetime.timezone.utc)
    except AttributeError:
        # Fallback for older Python versions
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
            # Use the same timezone-aware approach as get_utc_ist()
            try:
                current_time = datetime.now(datetime.timezone.utc)
            except AttributeError:
                current_time = datetime.utcnow()
            if current_time - log_time <= timedelta(days=7):
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
    subprocess.call(['tmux', 'new-session', '-d', '-s', session_name, f'python3.11 "{script_path}"'])
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

# ---------------- Database Functions ----------------
def is_database_accessible():
    """Check if database is accessible without actually connecting"""
    try:
        # Check if PostgreSQL process is running
        if not is_db_running():
            return False
        
        # Try a quick connection test
        import psycopg2
        conn = psycopg2.connect(**DB_CONFIG)
        conn.close()
        return True
    except ImportError:
        log_event("⚠️ psycopg2 not available - timestamp monitoring disabled")
        return False
    except Exception as e:
        log_event(f"⚠️ Database connection test failed: {e}")
        return False

def get_db_connection():
    """Get database connection only when needed"""
    if not is_database_accessible():
        return None
    
    try:
        import psycopg2
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        log_event(f"⚠️ Database connection failed: {e}")
        return None

def create_tmux_log_table():
    """Verify tmux_log table structure matches expected columns"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cursor:
            # Check if table exists and what columns it has
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'tmux_log'
            """)
            existing_columns = {row[0] for row in cursor.fetchall()}
            
            # Verify we have the expected columns
            expected_columns = {'code', 'last_timestamp', 'alert', 'log'}
            missing_columns = expected_columns - existing_columns
            
            if missing_columns:
                log_event(f"⚠️ Missing columns in tmux_log table: {missing_columns}")
                log_event(f"📊 Available columns: {existing_columns}")
                return False
            else:
                log_event("✅ tmux_log table structure verified - all required columns exist")
                return True
            
    except Exception as e:
        log_event(f"⚠️ Failed to verify tmux_log table structure: {e}")
        return False
    finally:
        conn.close()

def update_tmux_cleaner_status():
    """Update tmux_cleaner status in database every 2 minutes"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cursor:
            # Since code column has no unique constraint, just insert new record
            cursor.execute("""
                INSERT INTO tmux_log (code, last_timestamp, alert, log) 
                VALUES ('tmux_cleaner', NOW(), FALSE, '01/01-01 | 1')
            """)
            conn.commit()
            return True
    except Exception as e:
        log_event(f"⚠️ Failed to update tmux_cleaner status: {e}")
        return False
    finally:
        conn.close()

def get_bot_timestamp_from_db(script_path):
    """Get bot's last timestamp from database"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT last_timestamp FROM tmux_log WHERE code = %s ORDER BY last_timestamp DESC LIMIT 1", (script_path,))
            result = cursor.fetchone()
            return result[0] if result else None
    except Exception as e:
        log_event(f"⚠️ Database query failed for {script_path}: {e}")
        return None
    finally:
        conn.close()

def update_bot_alert(script_path, alert_status):
    """Update bot alert status in database"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cursor:
            # Since code column has no unique constraint, just insert new record
            cursor.execute("""
                INSERT INTO tmux_log (code, last_timestamp, alert, log) 
                VALUES (%s, NOW(), %s, '01/01-01 | 1')
            """, (script_path, alert_status))
            conn.commit()
            return True
    except Exception as e:
        log_event(f"⚠️ Failed to update bot alert for {script_path}: {e}")
        return False
    finally:
        conn.close()

def get_log_count():
    """Get current log count from database"""
    conn = get_db_connection()
    if not conn:
        return "01/01-01 | 1"
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT log FROM tmux_log ORDER BY last_timestamp DESC LIMIT 1")
            result = cursor.fetchone()
            return result[0] if result else "01/01-01 | 1"
    except Exception as e:
        log_event(f"⚠️ Failed to get log count: {e}")
        return "01/01-01 | 1"
    finally:
        conn.close()

def update_log_count():
    """Update log count in database"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        current_count = get_log_count()
        today = datetime.now().strftime("%d/%m")
        
        # Parse current count
        if " | " in current_count:
            date_part, count_part = current_count.split(" | ")
            if date_part == today:
                # Same day, increment count
                new_count = int(count_part) + 1
            else:
                # New day, reset count
                new_count = 1
        else:
            new_count = 1
        
        new_log_count = f"{today}-{new_count:02d} | {new_count}"
        
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO tmux_log (code, last_timestamp, alert, log) 
                VALUES ('log_counter', NOW(), FALSE, %s)
            """, (new_log_count,))
            conn.commit()
            
        log_event(f"📊 Log count updated: {new_log_count}")
        return True
    except Exception as e:
        log_event(f"⚠️ Failed to update log count: {e}")
        return False
    finally:
        conn.close()

def get_process_start_time(script_path):
    """Get the actual process start time (not tmux session time)"""
    pids = get_python_pids_for(script_path)
    if not pids:
        return None
    
    # Get the earliest process start time
    earliest_start = None
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
        try:
            if proc.info['pid'] in pids:
                start_time = proc.info['create_time']
                if earliest_start is None or start_time < earliest_start:
                    earliest_start = start_time
        except:
            continue
    
    return earliest_start

# ---------------- Bot Status Tracking ----------------
bot_status = {}  # Track each bot's status and last inactive time

def should_restart_bot_ram_only(script_path):
    """Simple RAM-based monitoring for bots without timeout specification"""
    pids = get_python_pids_for(script_path)
    if not pids:
        log_event(f"🔧 Bot {script_path} not running - will start")
        return True  # Start if not running
    
    # Check memory usage for this specific script
    total_memory = 0
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info']):
        try:
            if proc.info['pid'] in pids:
                memory = proc.info['memory_info'].rss
                total_memory += memory
        except:
            continue
    
    memory_mb = total_memory / 1024 / 1024
    
    # Only restart if memory usage is zero (process not working)
    if total_memory == 0:
        log_event(f"⚠️ Bot {script_path} has zero memory usage ({memory_mb:.2f} MB) - will restart")
        return True
    elif memory_mb > 1000:  # More than 1GB - potential memory leak
        # Memory leak detected - log alarm, update database alert, do NOT restart
        log_event(f"🚨 Bot {script_path} memory leak detected ({memory_mb:.2f} MB) - ALARM ONLY (no restart)")
        
        # Update database alert status if accessible
        if is_database_accessible():
            update_bot_alert(script_path, True)  # Set alert = TRUE
            log_event(f"📊 Database alert updated for {script_path} - Memory leak detected")
        else:
            log_event(f"⚠️ Database not accessible - cannot update alert status for {script_path}")
        
        return False  # Don't restart for memory leaks
    
    # Bot is healthy - log this occasionally but don't restart
    if script_path not in bot_status or time.time() - bot_status.get(script_path, {}).get('last_health_log', 0) > 300:  # Log health every 5 minutes
        log_event(f"✅ Bot {script_path} healthy - Memory: {memory_mb:.2f} MB, PIDs: {pids}")
        if script_path not in bot_status:
            bot_status[script_path] = {}
        bot_status[script_path]['last_health_log'] = time.time()
    
    return False  # Bot is healthy

def should_restart_bot_simple(script_path, timeout_minutes):
    """Simple timeout monitoring for bots with format: path|timeout"""
    current_time = time.time()
    pids = get_python_pids_for(script_path)
    
    if not pids:
        return True  # Start if not running
    
    # Initialize bot status if not exists
    if script_path not in bot_status:
        bot_status[script_path] = {
            'last_active': current_time,
            'last_inactive': None,
            'timeout_minutes': timeout_minutes
        }
        return False
    
    status = bot_status[script_path]
    
    # Check if bot is healthy
    total_memory = 0
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info']):
        try:
            if proc.info['pid'] in pids:
                memory = proc.info['memory_info'].rss
                total_memory += memory
        except:
            continue
    
    memory_mb = total_memory / 1024 / 1024
    
    if total_memory == 0 or memory_mb > 1000:
        # Bot is unhealthy
        if status['last_inactive'] is None:
            # First time detected as unhealthy
            status['last_inactive'] = current_time
            if memory_mb > 1000:
                # Memory leak detected - update database alert
                log_event(f"🚨 Bot {script_path} memory leak detected ({memory_mb:.2f} MB) - ALARM ONLY (no restart)")
                if is_database_accessible():
                    update_bot_alert(script_path, True)  # Set alert = TRUE
                    log_event(f"📊 Database alert updated for {script_path} - Memory leak detected")
                else:
                    log_event(f"⚠️ Database not accessible - cannot update alert status for {script_path}")
            else:
                log_event(f"⚠️ Bot {script_path} detected as unhealthy: Memory {memory_mb:.2f} MB")
            return False
        
        # Calculate how long it's been unhealthy
        unhealthy_duration = current_time - status['last_inactive']
        timeout_seconds = timeout_minutes * 60
        
        if unhealthy_duration >= timeout_seconds:
            log_event(f"🚨 Bot {script_path} unhealthy for {timeout_minutes} minutes. Restarting...")
            return True
        else:
            remaining = timeout_seconds - unhealthy_duration
            log_event(f"⏳ Bot {script_path} still unhealthy. Restart in {remaining/60:.1f} minutes")
            return False
    else:
        # Bot is healthy, update status
        status['last_active'] = current_time
        status['last_inactive'] = None
        return False

def should_restart_bot_timestamp(script_path, alarm_minutes, restart_minutes):
    """Timestamp-based monitoring for bots with format: path|alarmArestart"""
    current_time = time.time()
    
    # Get process start time (when the actual Python process started)
    process_start_time = get_process_start_time(script_path)
    if not process_start_time:
        # No process running, start immediately
        return True
    
    # Get database timestamp
    db_timestamp = get_bot_timestamp_from_db(script_path)
    
    # Determine which timestamp to use as reference
    if db_timestamp:
        db_timestamp_unix = db_timestamp.timestamp()
        
        # Convert process start time to datetime for proper comparison
        process_datetime = datetime.datetime.fromtimestamp(process_start_time)
        
        # Format timestamps for logging (with date)
        process_str = process_datetime.strftime("%m/%d %H:%M:%S")
        db_str = db_timestamp.strftime("%m/%d %H:%M:%S")
        
        # Compare Unix timestamps (handles dates automatically)
        if process_start_time < db_timestamp_unix:
            # Process started BEFORE DB timestamp → Use PROCESS time (file started time)
            reference_time = process_start_time
            timestamp_source = "process_start_time"
            log_event(f"📊 Using process start time for {script_path} (Process: {process_str} < DB: {db_str})")
        else:
            # Process started AFTER DB timestamp → Use DATABASE time
            reference_time = db_timestamp_unix
            timestamp_source = "database_timestamp"
            log_event(f"📊 Using database timestamp for {script_path} (Process: {process_str} >= DB: {db_str})")
    else:
        # No database timestamp, use process start time
        reference_time = process_start_time
        timestamp_source = "process_start_time"
        process_str = datetime.datetime.fromtimestamp(process_start_time).strftime("%m/%d %H:%M:%S")
        log_event(f"📊 No DB timestamp for {script_path}, using process start time ({process_str})")
    
    # Calculate time since reference
    time_since_reference = current_time - reference_time
    
    # Convert alarm and restart times to seconds
    alarm_seconds = alarm_minutes * 60
    restart_seconds = restart_minutes * 60
    
    # Format reference time for logging
    reference_datetime = datetime.datetime.fromtimestamp(reference_time)
    reference_str = reference_datetime.strftime("%m/%d %H:%M:%S")
    
    # Check if we should give alarm (first threshold)
    if time_since_reference >= alarm_seconds:
        # Check if we should restart (second threshold)
        if time_since_reference >= restart_seconds:
            log_event(f"🚨 Bot {script_path} exceeded restart threshold ({restart_minutes}m) - Restarting (ref: {reference_str})")
            return True
        else:
            remaining_restart = restart_seconds - time_since_reference
            log_event(f"⚠️ Bot {script_path} exceeded alarm threshold ({alarm_minutes}m) - Restart in {remaining_restart/60:.1f}m (ref: {reference_str})")
            return False
    else:
        remaining_alarm = alarm_seconds - time_since_reference
        log_event(f"📊 Bot {script_path} healthy - Next alarm in {remaining_alarm/60:.1f}m (ref: {reference_str}, using {timestamp_source})")
        return False

# ---------------- Bot Restart Logging ----------------
BOT_RESTART_LOG_FILE = os.path.join(CLEANER_DIR, "bot_restarts.log")

def log_bot_restart(script_path, reason, old_pids, new_pids):
    """Log bot restart events to separate file with clear formatting"""
    utc_time, ist_time = get_utc_ist()
    
    # Create detailed restart log entry
    restart_log = f"""
{'='*80}
🤖 BOT RESTART EVENT
{'='*80}
📅 UTC Time: {utc_time}
🌍 IST Time: {ist_time}
📁 Bot File: {script_path}
🚨 Restart Reason: {reason}
🔄 Old PIDs: {old_pids if old_pids else 'None'}
✅ New PIDs: {new_pids if new_pids else 'None'}
{'='*80}
"""
    
    # Write to bot restart log file
    with open(BOT_RESTART_LOG_FILE, 'a') as f:
        f.write(restart_log)
    
    # Also log to main monitoring log
    log_event(f"🤖 Bot restart logged to: {BOT_RESTART_LOG_FILE}")
    
    # Update log count in database only if accessible
    if is_database_accessible():
        update_log_count()
    else:
        log_event("⚠️ Database not accessible - skipping log count update")

# ---------------- Bot Handlers ----------------
def fix_bot(script_path):
    base_name = get_session_name(script_path)
    sessions = get_running_tmux_sessions()
    pids = get_python_pids_for(script_path)
    expected_session = f"{base_name}1" if f"{base_name}1" not in sessions else f"{base_name}2"

    if not pids:
        log_event(f"⏳ Fixing bot: {script_path}")
        old_pids = pids
        try:
            for s in sessions:
                if s.startswith(base_name):
                    kill_tmux_session(s)
            start_tmux_session(expected_session, script_path)
            time.sleep(2)
            new_pids = get_python_pids_for(script_path)
            
            # Only log restart if we actually got new PIDs
            if new_pids:
                log_event(f"✅ Restarted bot: {script_path}, PID: {new_pids}")
                log_bot_restart(script_path, "Bot not running", old_pids, new_pids)
            else:
                log_event(f"⚠️ Failed to restart bot: {script_path} - no PIDs found")
                # Update database alert for restart failure
                if is_database_accessible():
                    update_bot_alert(script_path, True)  # Set alert = TRUE
                    log_event(f"📊 Database alert updated for {script_path} - Restart failed")
                else:
                    log_event(f"⚠️ Database not accessible - cannot update alert status for {script_path}")
        except Exception as e:
            log_event(f"🚨 Unexpected error restarting bot {script_path}: {e}")
            # Update database alert for unexpected error
            if is_database_accessible():
                update_bot_alert(script_path, True)  # Set alert = TRUE
                log_event(f"📊 Database alert updated for {script_path} - Unexpected error: {e}")
            else:
                log_event(f"⚠️ Database not accessible - cannot update alert status for {script_path}")

def fix_all_bots(bot_list):
    for script in bot_list:
        if not script.startswith('*'):
            fix_bot(script)

def kill_all_bots(bot_list):
    for script in bot_list:
        try:
            for pid in get_python_pids_for(script):
                kill_pid(pid)
            base_name = get_session_name(script)
            for session in get_running_tmux_sessions():
                if session.startswith(base_name):
                    kill_tmux_session(session)
        except Exception as e:
            log_event(f"🚨 Unexpected error killing bot {script}: {e}")
            # Update database alert for unexpected error
            if is_database_accessible():
                update_bot_alert(script, True)  # Set alert = TRUE
                log_event(f"📊 Database alert updated for {script} - Kill error: {e}")
            else:
                log_event(f"⚠️ Database not accessible - cannot update alert status for {script}")
    log_event("🧹 All bots cleaned and killed")

# ---------------- Memory Checks ----------------
def is_memory_high():
    return psutil.virtual_memory().percent >= MAX_MEMORY_PERCENT

def get_total_python_memory():
    return sum(proc.info['memory_info'].rss for proc in psutil.process_iter(['name', 'memory_info', 'cmdline']) if PYTHON_PROCESS_NAME in proc.info['name'])

def get_db_memory():
    return sum(proc.info['memory_info'].rss for proc in psutil.process_iter(['name', 'memory_info']) if DB_PROCESS_NAME in proc.info['name'])

def is_db_running():
    return any(DB_PROCESS_NAME in proc.info['name'] for proc in psutil.process_iter(['name']))

# ---------------- Lock Handling ----------------
def lock_restart():
    with open(DB_LOCK_FILE, 'w') as f:
        f.write(str(time.time()))
    log_event("🔐 PostgreSQL restart lock created")

def is_restart_pending():
    if not os.path.exists(DB_LOCK_FILE):
        return False
    try:
        with open(DB_LOCK_FILE, 'r') as f:
            timestamp = float(f.read().strip())
        return (time.time() - timestamp) < DB_RESTART_TIMEOUT
    except:
        return False

def unlock_restart():
    if os.path.exists(DB_LOCK_FILE):
        os.remove(DB_LOCK_FILE)
        log_event("🔓 PostgreSQL restart lock removed")

# ---------------- PostgreSQL Restart Logic ----------------
def restart_db_thread(cleanable_bots):
    lock_restart()
    
    # Step 1: Restart PostgreSQL server
    log_event("🔄 Step 1: Restarting PostgreSQL server...")
    subprocess.call(['sudo', 'systemctl', 'restart', 'postgresql'])
    
    # Wait 60 seconds and check if PostgreSQL is running
    log_event("⏳ Waiting 60 seconds to check if PostgreSQL restarted...")
    time.sleep(60)
    
    if is_db_running():
        log_event("✅ PostgreSQL restarted successfully after Step 1.")
        unlock_restart()
        return
    
    # Step 2: Kill Python bots to free RAM
    log_event("⚠️ PostgreSQL still not up after 60s. Releasing RAM by killing Python bots...")
    kill_all_bots(cleanable_bots)
    
    # Wait 60 seconds and check again
    log_event("⏳ Waiting 60 seconds after killing bots to check PostgreSQL...")
    time.sleep(60)
    
    if is_db_running():
        log_event("✅ PostgreSQL came back after Step 2 (killing bots).")
        unlock_restart()
        return
    
    # Step 3: Kill PostgreSQL process forcibly and restart
    log_event("🔥 PostgreSQL still down. Forcing PostgreSQL kill and restart...")
    subprocess.call(['sudo', 'pkill', '-9', DB_PROCESS_NAME])
    time.sleep(5)
    subprocess.call(['sudo', 'systemctl', 'restart', 'postgresql'])
    
    # Wait 90 seconds and check again
    log_event("⏳ Waiting 90 seconds after forced PostgreSQL restart...")
    time.sleep(90)
    
    if is_db_running():
        log_event("✅ PostgreSQL came back after Step 3 (forced restart).")
        unlock_restart()
        return
    
    # Step 4: Final resort - reboot system
    log_event("💣 PostgreSQL restart failed again. Rebooting system...")
    unlock_restart()
    subprocess.call(['sudo', 'reboot'])

# ---------------- Monitoring ----------------
def monitor_loop():
    global last_mode, cleanable_bots

    log_event("🚀 tmux_bot_cleaner_postgrey.py started (with intelligent file type monitoring)")
    
    # Check database accessibility at startup
    if is_database_accessible():
        log_event("✅ Database connection test successful")
        # Initialize database table only if we have timestamp-based bots
        # This will be checked in the main loop
    else:
        log_event("⚠️ Database not accessible - timestamp monitoring will be disabled")
    
    # Start tmux cleaner status update thread (only if database is accessible)
    def update_status_thread():
        while True:
            if is_database_accessible():
                update_tmux_cleaner_status()
            else:
                log_event("⚠️ Database not accessible - skipping status update")
            time.sleep(120)  # Update every 2 minutes
    
    threading.Thread(target=update_status_thread, daemon=True).start()

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
        db_monitor = any(line.strip().lower() == '*db' for line in all_bots)

        if last_mode != mode:
            log_event(f"📁 Mode: {mode} | PostgreSQL Monitoring: {'ON' if db_monitor else 'OFF'} | Bot Count: {len(all_bots)}")
            last_mode = mode

        # 1. Handle nocleaner.txt files - NO MONITORING, just start if not running
        for path in noclean_bots:
            if not path.startswith('*'):
                pids = get_python_pids_for(path)
                if not pids:
                    log_event(f"🔧 Simple monitoring for: {path}")
                    fix_bot(path)  # Just start if not running, no monitoring

        # 2. Handle cleanable bots (from bots.txt or botsBackup.txt)
        # First, categorize bots by monitoring type to optimize database access
        timestamp_bots = []  # Need database access
        simple_timeout_bots = []  # No database needed
        ram_only_bots = []  # No database needed
        
        for script_path in cleanable_bots:
            if script_path.startswith('*'):
                continue
                
            # Check if file has timeout specification
            if '|' in script_path:
                parts = script_path.split('|')
                if len(parts) == 2:
                    script_file = parts[0].strip()
                    timeout_spec = parts[1].strip()
                    
                    if 'A' in timeout_spec:
                        # Format: path|alarmArestart (e.g., path|5A10) - needs database
                        alarm_restart = timeout_spec.split('A')
                        if len(alarm_restart) == 2:
                            try:
                                alarm_minutes = int(alarm_restart[0])
                                restart_minutes = int(alarm_restart[1])
                                timestamp_bots.append((script_file, alarm_minutes, restart_minutes))
                            except ValueError:
                                log_event(f"⚠️ Invalid timeout format: {timeout_spec} for {script_file}")
                    else:
                        # Format: path|timeout (e.g., path|5) - no database needed
                        try:
                            timeout_minutes = int(timeout_spec)
                            simple_timeout_bots.append((script_file, timeout_minutes))
                        except ValueError:
                            log_event(f"⚠️ Invalid timeout format: {timeout_spec} for {script_file}")
                else:
                    log_event(f"⚠️ Invalid format in {script_path}")
            else:
                # No timeout specified - no database needed
                ram_only_bots.append(script_path)
        
        # Process RAM-only bots first (no database access needed)
        if ram_only_bots:
            log_event(f"🔧 Processing {len(ram_only_bots)} RAM-only bots (no database needed)")
            for script_path in ram_only_bots:
                if should_restart_bot_ram_only(script_path):
                    fix_bot(script_path)
        
        # Process simple timeout bots (no database access needed)
        if simple_timeout_bots:
            log_event(f"⏰ Processing {len(simple_timeout_bots)} simple timeout bots (no database needed)")
            for script_file, timeout_minutes in simple_timeout_bots:
                if should_restart_bot_simple(script_file, timeout_minutes):
                    fix_bot(script_file)
        
        # Process timestamp bots (only these need database access)
        if timestamp_bots:
            log_event(f"📊 Processing {len(timestamp_bots)} timestamp-based bots (database access required)")
            # Only check database connectivity if we have timestamp-based bots
            if is_database_accessible():
                # Create table if it doesn't exist (only when needed)
                create_tmux_log_table()
                
                for script_file, alarm_minutes, restart_minutes in timestamp_bots:
                    if should_restart_bot_timestamp(script_file, alarm_minutes, restart_minutes):
                        fix_bot(script_file)
            else:
                log_event("⚠️ Database not accessible - skipping timestamp-based monitoring")
                # Fall back to simple monitoring for timestamp bots
                for script_file, alarm_minutes, restart_minutes in timestamp_bots:
                    if should_restart_bot_simple(script_file, restart_minutes):
                        fix_bot(script_file)

        # 3. Check memory and handle high RAM situations
        if is_memory_high():
            log_event("🚨 High memory usage detected!")
            py_mem = get_total_python_memory()
            db_mem = get_db_memory()
            log_event(f"📊 Python RAM: {py_mem / 1024 / 1024:.2f} MB | PostgreSQL RAM: {db_mem / 1024 / 1024:.2f} MB")

            if db_monitor and db_mem >= py_mem:
                if not is_restart_pending():
                    threading.Thread(target=restart_db_thread, args=(cleanable_bots,)).start()
                else:
                    log_event("⏳ PostgreSQL restart already in progress. Skipping.")
            else:
                log_event("🔧 High memory - restarting Python bots...")
                kill_all_bots(cleanable_bots)
                time.sleep(2)
                # Restart all cleanable bots for memory issues
                for script_path in cleanable_bots:
                    if not script_path.startswith('*'):
                        fix_bot(script_path)
        
        # Log monitoring cycle summary only when there's activity or status changes
        current_status = f"{len(ram_only_bots)}_{len(simple_timeout_bots)}_{len(timestamp_bots)}"
        if not hasattr(monitor_loop, 'last_status') or monitor_loop.last_status != current_status:
            log_event(f"📊 Monitoring cycle complete - RAM bots: {len(ram_only_bots)}, Timeout bots: {len(simple_timeout_bots)}, Timestamp bots: {len(timestamp_bots)}")
            monitor_loop.last_status = current_status
        elif any([ram_only_bots, simple_timeout_bots, timestamp_bots]):
            # Only log every 10 minutes if there are bots to monitor
            if not hasattr(monitor_loop, 'last_summary_log') or time.time() - monitor_loop.last_summary_log > 600:
                log_event(f"📊 Monitoring cycle complete - RAM bots: {len(ram_only_bots)}, Timeout bots: {len(simple_timeout_bots)}, Timestamp bots: {len(timestamp_bots)}")
                monitor_loop.last_summary_log = time.time()
        
        time.sleep(INTERVAL)

if __name__ == '__main__':
    monitor_loop()


    

    

    