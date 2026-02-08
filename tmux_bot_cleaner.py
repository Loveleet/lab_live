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

# Timer queue management
RESTART_COOLDOWN_MINUTES = 0.5  # 30 seconds instead of 2 minutes
last_restart_time = 0

# Database configuration
DB_CONFIG = {
    'user': 'lab',
    'password': 'IndiaNepal1-',
    'host': '127.0.0.1',
    'port': '5432',
    'database': 'labdb2'
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLEANER_DIR = "/root/TmuxCleaner"

INSTRUCTOR_FILE = os.path.join(CLEANER_DIR, "instructor.txt")
MAIN_BOTS_FILE = os.path.join(CLEANER_DIR, "bots.txt")
BACKUP_BOTS_FILE = os.path.join(CLEANER_DIR, "botsBackup.txt")
NOCLEANER_FILE = os.path.join(CLEANER_DIR, "nocleaner.txt")
LOG_FILE = os.path.join(CLEANER_DIR, "monitoring.log")

last_mode = None

# ---------------- Bot Configuration Parsing ----------------
def parse_bot_configuration(script_path):
    """Parse bot configuration from script path"""
    if '|' not in script_path:
        return script_path.strip(), None, None
    
    parts = script_path.split('|')
    script_file = parts[0].strip()
    
    # Check for uptime timer (R-20 format) at the end
    uptime_minutes = None
    if len(parts) > 1 and parts[-1].strip().startswith('R-'):
        try:
            uptime_minutes = int(parts[-1].strip().replace('R-', ''))
            parts = parts[:-1]  # Remove R- part
        except ValueError:
            return None, None, None
    
    # Handle remaining parts
    if len(parts) == 1:
        # Only script path (with or without R-)
        return script_file, None, uptime_minutes
    elif len(parts) == 2:
        # Format: path|timeout or path|alarmArestart
        timeout_spec = parts[1].strip()
        return script_file, timeout_spec, uptime_minutes
    elif len(parts) == 4:
        # Format: path|alarm|A|restart
        try:
            alarm_minutes = int(parts[1].strip())
            restart_minutes = int(parts[3].strip())
            if parts[2].strip() == 'A':
                timeout_spec = f"{alarm_minutes}A{restart_minutes}"
                return script_file, timeout_spec, uptime_minutes
            else:
                return None, None, None
        except ValueError:
            return None, None, None
    else:
        return None, None, None

def parse_alarm_restart(timeout_spec):
    """Parse alarm and restart minutes from timeout specification"""
    if 'A' in timeout_spec:
        alarm_restart = timeout_spec.split('A')
        if len(alarm_restart) == 2:
            try:
                alarm_minutes = int(alarm_restart[0])
                restart_minutes = int(alarm_restart[1])
                return alarm_minutes, restart_minutes
            except ValueError:
                return None, None
    return None, None

# ---------------- Timer Queue Management ----------------
def get_ready_timer_bots(ram_only_bots, simple_timeout_bots, timestamp_bots):
    """Get all bots that are ready for timer restart with their uptime"""
    ready_bots = []
    
    # Check all bot types for R- timers
    for bot_config in ram_only_bots:
        if isinstance(bot_config, tuple):
            script_path, uptime_minutes = bot_config
            if uptime_minutes:
                uptime_actual = get_uptime_minutes(script_path)
                if uptime_actual and uptime_actual >= uptime_minutes:
                    ready_bots.append((script_path, uptime_actual, uptime_minutes))
    
    for script_path, timeout_minutes, uptime_minutes in simple_timeout_bots:
        if uptime_minutes:
            uptime_actual = get_uptime_minutes(script_path)
            if uptime_actual and uptime_actual >= uptime_minutes:
                ready_bots.append((script_path, uptime_actual, uptime_minutes))
    
    for script_path, alarm_minutes, restart_minutes, uptime_minutes in timestamp_bots:
        if uptime_minutes:
            uptime_actual = get_uptime_minutes(script_path)
            if uptime_actual and uptime_actual >= uptime_minutes:
                ready_bots.append((script_path, uptime_actual, uptime_minutes))
    
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

def can_restart_now():
    """Check if enough time has passed since last restart AND no bot is too new"""
    global last_restart_time
    current_time = time.time()
    time_since_last = (current_time - last_restart_time) / 60  # Convert to minutes
    
    log_event(f"🔍 can_restart_now() called: time_since_last={time_since_last:.1f}m, cooldown={RESTART_COOLDOWN_MINUTES}m")
    
    # Check cooldown between restarts (30 seconds minimum)
    if time_since_last < RESTART_COOLDOWN_MINUTES:
        log_event(f"⏳ Blocking restart: cooldown not met ({time_since_last:.1f}m < {RESTART_COOLDOWN_MINUTES}m)")
        return False
    
    # Check if ANY bot has been running for less than 2 minutes
    # This includes bots that just restarted (0 minutes uptime)
    try:
        with open(BOTS_BACKUP_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Extract script path
                    if '|' in line:
                        script_path = line.split('|')[0].strip()
                    else:
                        script_path = line.strip()
                    
                    # Check if bot is running
                    pids = get_python_pids_for(script_path)
                    if pids:  # Bot is running
                        uptime_minutes = get_uptime_minutes(script_path)
                        log_event(f"🔍 Checking {os.path.basename(script_path)}: PIDs={pids}, Uptime={uptime_minutes:.1f}m")
                        if uptime_minutes is not None and uptime_minutes < 2.0:
                            log_event(f"⏳ Blocking restart: {os.path.basename(script_path)} has been running for {uptime_minutes:.1f}m (< 2m)")
                            return False  # Found a bot running less than 2 minutes
    except Exception as e:
        log_event(f"⚠️ Error checking bot uptimes: {e}")
        pass  # If file read fails, allow restart
    
    return True

def update_last_restart_time():
    """Update the last restart time"""
    global last_restart_time
    last_restart_time = time.time()

def get_timer_queue_info(script_path, ram_only_bots, simple_timeout_bots, timestamp_bots):
    """Get queue position and estimated start time for a bot"""
    ready_bots = get_ready_timer_bots(ram_only_bots, simple_timeout_bots, timestamp_bots)
    
    # Find this bot in the queue
    for i, (bot_path, uptime, timer_minutes) in enumerate(ready_bots):
        if bot_path == script_path:
            if i == 0 and can_restart_now():
                return 0, 0  # W-0, immediate start
            else:
                wait_position = i
                wait_minutes = i * RESTART_COOLDOWN_MINUTES
                return wait_position, wait_minutes
    
    return None, None  # Not in queue

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

def get_daily_session_name(script_path):
    """Generate session name with daily restart counter: botname_MMDD_N"""
    base_name = get_session_name(script_path)
    today = datetime.now().strftime("%m%d")  # MMDD format (e.g., 0904)
    
    # Get all existing sessions for this bot today
    existing_sessions = get_running_tmux_sessions()
    today_sessions = [s for s in existing_sessions if s.startswith(f"{base_name}_{today}_")]
    
    # Find the highest counter for today
    max_counter = 0
    for session in today_sessions:
        try:
            # Extract counter from session name: botname_MMDD_N
            counter_part = session.split('_')[-1]
            counter = int(counter_part)
            max_counter = max(max_counter, counter)
        except (ValueError, IndexError):
            continue
    
    # Next counter is max + 1
    next_counter = max_counter + 1
    session_name = f"{base_name}_{today}_{next_counter}"
    
    log_event(f"📊 Generated session name: {session_name} (restart #{next_counter} today)")
    return session_name

def get_running_tmux_sessions():
    try:
        output = subprocess.check_output(['tmux', 'ls'], stderr=subprocess.DEVNULL).decode()
        return [line.split(':')[0] for line in output.strip().splitlines()]
    except subprocess.CalledProcessError:
        return []

def get_python_pids_for(script_path):
    """Optimized process detection - only check Python processes"""
    matches = []
    try:
        # Use pgrep for much faster process detection
        result = subprocess.run(['pgrep', '-f', f'python.*{script_path}'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            matches = [int(pid.strip()) for pid in result.stdout.split('\n') if pid.strip()]
    except (subprocess.TimeoutExpired, ValueError, subprocess.SubprocessError):
        # Fallback to psutil if pgrep fails
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if PYTHON_PROCESS_NAME in proc.info['name'] and script_path in ' '.join(proc.info['cmdline']):
                    matches.append(proc.info['pid'])
            except:
                continue
    return matches

def start_tmux_session(session_name, script_path):
    """Start tmux session with timeout to prevent hanging"""
    try:
        subprocess.run(['tmux', 'new-session', '-d', '-s', session_name, f'python3.11 "{script_path}"'], 
                     timeout=10, check=True)
        log_event(f"✅ Started tmux session '{session_name}' for {script_path}")
        return True
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
        log_event(f"⚠️ Failed to start tmux session '{session_name}': {e}")
        return False

def kill_tmux_session(session):
    """Kill tmux session with timeout to prevent hanging"""
    try:
        subprocess.run(['tmux', 'kill-session', '-t', session], timeout=5, check=True)
        log_event(f"❌ Killed tmux session: {session}")
        return True
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
        log_event(f"⚠️ Failed to kill tmux session '{session}': {e}")
        return False

def kill_pid(pid):
    """Kill a process and all its children - FAST VERSION"""
    try:
        # Kill child processes first (non-blocking)
        try:
            subprocess.Popen(['pkill', '-P', str(pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass
        
        # Force kill immediately (no graceful termination for speed)
        os.kill(pid, 9)  # SIGKILL
        log_event(f"❌ Killed process PID: {pid}")
        return True
    except ProcessLookupError:
        log_event(f"✅ Process PID {pid} already dead")
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
    """Get database connection with timeout to prevent hanging"""
    if not is_database_accessible():
        return None
    
    try:
        import psycopg2
        # Add connection timeout to prevent hanging
        config_with_timeout = DB_CONFIG.copy()
        config_with_timeout['connect_timeout'] = 5
        return psycopg2.connect(**config_with_timeout)
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
            # Use UPSERT to avoid duplicate key errors
            cursor.execute("""
                INSERT INTO tmux_log (code, last_timestamp, alert, log) 
                VALUES (%s, NOW(), %s, '01/01-01 | 1')
                ON CONFLICT (code) 
                DO UPDATE SET 
                    last_timestamp = NOW(),
                    alert = %s,
                    log = '01/01-01 | 1'
            """, (script_path, alert_status, alert_status))
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
                ON CONFLICT (code) 
                DO UPDATE SET 
                    last_timestamp = NOW(),
                    alert = FALSE,
                    log = %s
            """, (new_log_count, new_log_count))
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

def should_restart_bot_ram_only(script_path, uptime_minutes=None):
    """Simple RAM-based monitoring for bots without timeout specification"""
    pids = get_python_pids_for(script_path)
    if not pids:
        log_event(f"🔧 Bot {script_path} not running - will start")
        return True  # Start if not running
    
    # Check if bot is running in a tmux session
    base_name = get_session_name(script_path)
    running_sessions = get_running_tmux_sessions()
    bot_in_tmux = any(session.startswith(base_name) for session in running_sessions)
    
    if not bot_in_tmux:
        log_event(f"🔧 Bot {script_path} running but not in tmux session - will restart in tmux")
        return True  # Restart in tmux if not in tmux session
    
    # Check uptime timer if specified
    if uptime_minutes:
        process_start_time = get_process_start_time(script_path)
        if process_start_time:
            current_time = time.time()
            uptime_seconds = current_time - process_start_time
            uptime_minutes_actual = uptime_seconds / 60
            
            if uptime_minutes_actual >= uptime_minutes:
                log_event(f"⏰ Bot {script_path} uptime timer reached ({uptime_minutes_actual:.1f}m >= {uptime_minutes}m) - will restart")
                return True
    
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
    elif memory_mb > 3000:  # More than 3GB - memory leak
        # Memory leak detected - log alarm, update database alert, do NOT restart
        # Memory leak detected - update database alert only (no logging to reduce spam)
        
        # Update database alert status if accessible
        if is_database_accessible():
            update_bot_alert(script_path, True)  # Set alert = TRUE
            log_event(f"📊 Database alert updated for {script_path} - Memory leak detected")
        else:
            log_event(f"⚠️ Database not accessible - cannot update alert status for {script_path}")
        
        return False  # Don't restart for memory leaks
    elif memory_mb > 2000:  # More than 2GB - higher memory usage
        # Higher memory usage - log warning, no database alert
        # Higher memory usage detected (no logging to reduce spam)
        return False  # Don't restart for higher memory usage
    elif memory_mb > 1000:  # More than 1GB - high memory usage
        # High memory usage - log info, no action needed
        # High memory usage detected (no logging to reduce spam)
        return False  # Don't restart for high memory usage
    
    # Bot is healthy - clear alerts silently (no logging to reduce spam)
    if script_path not in bot_status or time.time() - bot_status.get(script_path, {}).get('last_health_log', 0) > 300:  # Check every 5 minutes
        if script_path not in bot_status:
            bot_status[script_path] = {}
        bot_status[script_path]['last_health_log'] = time.time()
        
        # Clear alert if bot is healthy (memory < 1GB) - clears ALL types of alerts
        if memory_mb < 1000 and is_database_accessible():
            update_bot_alert(script_path, False)  # Set alert = FALSE
    
    return False  # Bot is healthy

def should_restart_bot_simple(script_path, timeout_minutes, uptime_minutes=None):
    """Simple timeout monitoring for bots with format: path|timeout"""
    current_time = time.time()
    pids = get_python_pids_for(script_path)
    
    if not pids:
        return True  # Start if not running
    
    # Check if bot is running in a tmux session
    base_name = get_session_name(script_path)
    running_sessions = get_running_tmux_sessions()
    bot_in_tmux = any(session.startswith(base_name) for session in running_sessions)
    
    if not bot_in_tmux:
        log_event(f"🔧 Bot {script_path} running but not in tmux session - will restart in tmux")
        return True  # Restart in tmux if not in tmux session
    
    # Check uptime timer if specified
    if uptime_minutes:
        process_start_time = get_process_start_time(script_path)
        if process_start_time:
            uptime_seconds = current_time - process_start_time
            uptime_minutes_actual = uptime_seconds / 60
            
            if uptime_minutes_actual >= uptime_minutes:
                log_event(f"⏰ Bot {script_path} uptime timer reached ({uptime_minutes_actual:.1f}m >= {uptime_minutes}m) - will restart")
                return True
    
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
    
    if total_memory == 0 or memory_mb > 3000:
        # Bot is unhealthy
        if status['last_inactive'] is None:
            # First time detected as unhealthy
            status['last_inactive'] = current_time
            if memory_mb > 3000:
                # Memory leak detected - update database alert
                # Memory leak detected - update database alert only (no logging to reduce spam)
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
        
        # Clear alert if bot is healthy (memory < 1GB and not zero) - clears ALL types of alerts
        if 0 < memory_mb < 1000 and is_database_accessible():
            update_bot_alert(script_path, False)  # Set alert = FALSE
            log_event(f"📊 Database alert cleared for {script_path} - Bot is healthy (clears all alert types, Memory: {memory_mb:.2f} MB)")
        
        return False

def monitor_bot_timestamp(script_path, timeout_minutes, pids, is_nocleaner=False):
    """Monitor bot with timestamp-based logic (wrapper for nocleaner support)"""
    if is_nocleaner:
        # For nocleaner bots, use timeout_minutes as both alarm and restart time
        # This means: if timestamp is older than timeout_minutes, restart immediately
        return should_restart_bot_timestamp(script_path, timeout_minutes, timeout_minutes)
    else:
        # For regular bots, use the existing logic (alarm and restart are the same for now)
        return should_restart_bot_timestamp(script_path, timeout_minutes, timeout_minutes)

def monitor_bot_simple_timeout(script_path, timeout_minutes, pids, is_nocleaner=False):
    """Monitor bot with simple timeout logic (wrapper for nocleaner support)"""
    if is_nocleaner:
        # For nocleaner bots, use simple timeout monitoring
        return should_restart_bot_simple(script_path, timeout_minutes)
    else:
        # For regular bots, use the existing logic
        return should_restart_bot_simple(script_path, timeout_minutes)

def should_restart_bot_timestamp(script_path, alarm_minutes, restart_minutes, uptime_minutes=None):
    """Timestamp-based monitoring for bots with format: path|alarmArestart"""
    current_time = time.time()
    
    # Get process start time (when the actual Python process started)
    process_start_time = get_process_start_time(script_path)
    if not process_start_time:
        # No process running, start immediately
        return True
    
    # Check if bot is running in a tmux session
    base_name = get_session_name(script_path)
    running_sessions = get_running_tmux_sessions()
    bot_in_tmux = any(session.startswith(base_name) for session in running_sessions)
    
    if not bot_in_tmux:
        log_event(f"🔧 Bot {script_path} running but not in tmux session - will restart in tmux")
        return True  # Restart in tmux if not in tmux session
    
    # Check uptime timer if specified
    if uptime_minutes:
        uptime_seconds = current_time - process_start_time
        uptime_minutes_actual = uptime_seconds / 60
        
        if uptime_minutes_actual >= uptime_minutes:
            log_event(f"⏰ Bot {script_path} uptime timer reached ({uptime_minutes_actual:.1f}m >= {uptime_minutes}m) - will restart")
            return True
    
    # Get database timestamp
    db_timestamp = get_bot_timestamp_from_db(script_path)
    
    # Determine which timestamp to use as reference
    if db_timestamp:
        db_timestamp_unix = db_timestamp.timestamp()
        
        # Convert process start time to datetime for proper comparison
        process_datetime = datetime.fromtimestamp(process_start_time)
        
        # Format timestamps for logging (with date)
        process_str = process_datetime.strftime("%m/%d %H:%M:%S")
        db_str = db_timestamp.strftime("%m/%d %H:%M:%S")
        
        # Compare Unix timestamps (handles dates automatically)
        if process_start_time < db_timestamp_unix:
            # Process started BEFORE DB timestamp → Use DATABASE time (DB is newer)
            reference_time = db_timestamp_unix
            timestamp_source = "database_timestamp"
            log_event(f"📊 Using database timestamp for {script_path} (Process: {process_str} < DB: {db_str})")
        else:
            # Process started AFTER DB timestamp → Use PROCESS time (process is newer)
            reference_time = process_start_time
            timestamp_source = "process_start_time"
            log_event(f"📊 Using process start time for {script_path} (Process: {process_str} >= DB: {db_str})")
    else:
        # No database timestamp, use process start time
        reference_time = process_start_time
        timestamp_source = "process_start_time"
        process_str = datetime.fromtimestamp(process_start_time).strftime("%m/%d %H:%M:%S")
        log_event(f"📊 No DB timestamp for {script_path}, using process start time ({process_str})")
    
    # Calculate time since reference
    time_since_reference = current_time - reference_time
    
    # Convert alarm and restart times to seconds
    alarm_seconds = alarm_minutes * 60
    restart_seconds = restart_minutes * 60
    
    # Format reference time for logging
    reference_datetime = datetime.fromtimestamp(reference_time)
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
            
            # Set alert when alarm threshold is exceeded
            if is_database_accessible():
                update_bot_alert(script_path, True)  # Set alert = TRUE
                log_event(f"📊 Database alert updated for {script_path} - Alarm threshold exceeded")
            else:
                log_event(f"⚠️ Database not accessible - cannot update alert status for {script_path}")
            
            return False
    else:
        remaining_alarm = alarm_seconds - time_since_reference
        log_event(f"📊 Bot {script_path} healthy - Next alarm in {remaining_alarm/60:.1f}m (ref: {reference_str}, using {timestamp_source})")
        
        # Clear alert if bot is healthy (within alarm threshold) - clears ALL types of alerts
        if is_database_accessible():
            update_bot_alert(script_path, False)  # Set alert = FALSE
            log_event(f"📊 Database alert cleared for {script_path} - Bot is healthy (clears all alert types, within alarm threshold)")
        
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
    
    # Generate new session name with daily restart counter
    expected_session = get_daily_session_name(script_path)

    if not pids:
        log_event(f"⏳ Fixing bot: {script_path}")
        old_pids = pids
        try:
            # Kill all existing sessions for this bot (both old format and new format)
            for s in sessions:
                if s.startswith(base_name):
                    kill_tmux_session(s)
            start_tmux_session(expected_session, script_path)
            time.sleep(0.5)
            new_pids = get_python_pids_for(script_path)
            
            # Only log restart if we actually got new PIDs
            if new_pids:
                log_event(f"✅ Restarted bot: {script_path}, PID: {new_pids}")
                log_bot_restart(script_path, "Bot not running", old_pids, new_pids)
                
                # Clear alert on successful restart
                if is_database_accessible():
                    update_bot_alert(script_path, False)  # Set alert = FALSE
                    log_event(f"📊 Database alert cleared for {script_path} - Bot restarted successfully")
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
    else:
        # Bot is running but not in tmux - restart it in tmux
        log_event(f"⏳ Fixing bot: {script_path}")
        old_pids = pids
        try:
            # Kill all existing sessions for this bot (both old format and new format)
            for s in sessions:
                if s.startswith(base_name):
                    kill_tmux_session(s)
            
            # Kill the running process
            for pid in pids:
                kill_pid(pid)
            
            # Short wait for processes to terminate
            time.sleep(0.5)
            
            # Start in tmux session immediately
            start_tmux_session(expected_session, script_path)
            time.sleep(0.5)
            new_pids = get_python_pids_for(script_path)
            
            # Only log restart if we actually got new PIDs
            if new_pids:
                log_event(f"✅ Restarted bot: {script_path}, PID: {new_pids}")
                log_bot_restart(script_path, "Bot running but not in tmux", old_pids, new_pids)
                
                # Clear alert on successful restart
                if is_database_accessible():
                    update_bot_alert(script_path, False)  # Set alert = FALSE
                    log_event(f"📊 Database alert cleared for {script_path} - Bot restarted successfully")
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
    last_heartbeat = time.time()

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
        try:
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

            # 1. Handle nocleaner.txt files - TIMESTAMP MONITORING (no RAM monitoring)
            for path in noclean_bots:
                if not path.startswith('*'):
                    pids = get_python_pids_for(path)
                    
                    # Check if file has timeout specification
                    if '|' in path:
                        parts = path.split('|')
                        if len(parts) == 2:
                            script_file = parts[0].strip()
                            timeout_spec = parts[1].strip()
                            
                            if 'A' in timeout_spec:
                                # Timestamp-based monitoring for nocleaner bots
                                timeout_str = timeout_spec.replace('A', '').strip()
                                try:
                                    timeout_minutes = int(timeout_str)
                                    if monitor_bot_timestamp(script_file, timeout_minutes, pids, is_nocleaner=True):
                                        fix_bot(script_file)
                                except ValueError:
                                    log_event(f"⚠️  Invalid timeout format in nocleaner: {timeout_spec}")
                            else:
                                # Simple timeout monitoring for nocleaner bots
                                try:
                                    timeout_minutes = int(timeout_spec)
                                    if monitor_bot_simple_timeout(script_file, timeout_minutes, pids, is_nocleaner=True):
                                        fix_bot(script_file)
                                except ValueError:
                                    log_event(f"⚠️  Invalid timeout format in nocleaner: {timeout_spec}")
                        else:
                            log_event(f"⚠️ Invalid format in nocleaner: {path}")
                    else:
                        # No timeout specified - just start if not running
                        if not pids:
                            log_event(f"🔧 Simple monitoring for nocleaner: {path}")
                            fix_bot(path)

            # 2. Handle cleanable bots (from bots.txt or botsBackup.txt)
            # First, categorize bots by monitoring type to optimize database access
            timestamp_bots = []  # Need database access
            simple_timeout_bots = []  # No database needed
            ram_only_bots = []  # No database needed
        
            for script_path in cleanable_bots:
                if script_path.startswith('*'):
                    continue
                
                # Parse bot configuration using simple, robust logic
                script_file, timeout_spec, uptime_minutes = parse_bot_configuration(script_path)
                
                if script_file is None:
                    log_event(f"⚠️ Invalid format in {script_path}")
                    continue
                
                # Categorize based on configuration
                if uptime_minutes and not timeout_spec:
                    # Format: path|R-20 (uptime timer only)
                    ram_only_bots.append((script_file, uptime_minutes))
                elif timeout_spec and 'A' in timeout_spec:
                    # Format: path|alarmArestart or path|alarm|A|restart - needs database
                    alarm_minutes, restart_minutes = parse_alarm_restart(timeout_spec)
                    if alarm_minutes is not None and restart_minutes is not None:
                        timestamp_bots.append((script_file, alarm_minutes, restart_minutes, uptime_minutes))
                    else:
                        log_event(f"⚠️ Invalid alarm/restart format: {timeout_spec} for {script_file}")
                elif timeout_spec:
                    # Format: path|timeout (e.g., path|5) - no database needed
                    try:
                        timeout_minutes = int(timeout_spec)
                        simple_timeout_bots.append((script_file, timeout_minutes, uptime_minutes))
                    except ValueError:
                        log_event(f"⚠️ Invalid timeout format: {timeout_spec} for {script_file}")
                else:
                    # No timeout specified - no database needed
                    ram_only_bots.append(script_file)
        
            # Process RAM-only bots first (no database access needed)
            if ram_only_bots:
                # Process RAM-only bots (no logging to reduce spam)
                for bot_config in ram_only_bots:
                    if isinstance(bot_config, tuple):
                        script_path, uptime_minutes = bot_config
                        if uptime_minutes:
                            # Timer-based bot - check if running first
                            pids = get_python_pids_for(script_path)
                            if not pids:
                                # Bot not running - start it immediately
                                log_event(f"🔧 Starting R-timer bot: {script_path} (R-{uptime_minutes})")
                                fix_bot(script_path)
                            else:
                                # Bot is running - use queue management
                                queue_position, wait_minutes = get_timer_queue_info(script_path, ram_only_bots, simple_timeout_bots, timestamp_bots)
                                if queue_position == 0 and can_restart_now():
                                    log_event(f"🔄 Timer restart: {script_path} (R-{uptime_minutes})")
                                    fix_bot(script_path)
                                    update_last_restart_time()
                                elif queue_position is not None:
                                    log_event(f"⏳ Bot {script_path} in queue W-{queue_position} (wait: {wait_minutes}m)")
                        else:
                            # Regular RAM monitoring
                            if should_restart_bot_ram_only(script_path, uptime_minutes):
                                fix_bot(script_path)
                    else:
                        # Legacy format (string only)
                        script_path = bot_config
                        if should_restart_bot_ram_only(script_path):
                            fix_bot(script_path)
            
            # Process simple timeout bots (no database access needed)
            if simple_timeout_bots:
                log_event(f"⏰ Processing {len(simple_timeout_bots)} simple timeout bots (no database needed)")
                for bot_config in simple_timeout_bots:
                    if len(bot_config) == 3:
                        script_file, timeout_minutes, uptime_minutes = bot_config
                        if uptime_minutes:
                            # Timer-based bot - use queue management
                            queue_position, wait_minutes = get_timer_queue_info(script_file, ram_only_bots, simple_timeout_bots, timestamp_bots)
                            if queue_position == 0 and can_restart_now():
                                log_event(f"🔄 Timer restart: {script_file} (R-{uptime_minutes})")
                                fix_bot(script_file)
                                update_last_restart_time()
                            elif queue_position is not None:
                                log_event(f"⏳ Bot {script_file} in queue W-{queue_position} (wait: {wait_minutes}m)")
                        else:
                            # Regular timeout monitoring
                            if should_restart_bot_simple(script_file, timeout_minutes, uptime_minutes):
                                fix_bot(script_file)
                    else:
                        script_file, timeout_minutes = bot_config
                        uptime_minutes = None
                        if should_restart_bot_simple(script_file, timeout_minutes, uptime_minutes):
                            fix_bot(script_file)
        
            # Process timestamp bots (only these need database access)
            if timestamp_bots:
                log_event(f"📊 Processing {len(timestamp_bots)} timestamp-based bots (database access required)")
                # Only check database connectivity if we have timestamp-based bots
                if is_database_accessible():
                    # Create table if it doesn't exist (only when needed)
                    create_tmux_log_table()
                    
                    for bot_config in timestamp_bots:
                        if len(bot_config) == 4:
                            script_file, alarm_minutes, restart_minutes, uptime_minutes = bot_config
                            if uptime_minutes:
                                # Timer-based bot - use queue management
                                queue_position, wait_minutes = get_timer_queue_info(script_file, ram_only_bots, simple_timeout_bots, timestamp_bots)
                                if queue_position == 0 and can_restart_now():
                                    log_event(f"🔄 Timer restart: {script_file} (R-{uptime_minutes})")
                                    fix_bot(script_file)
                                    update_last_restart_time()
                                elif queue_position is not None:
                                    log_event(f"⏳ Bot {script_file} in queue W-{queue_position} (wait: {wait_minutes}m)")
                            else:
                                # Regular timestamp monitoring
                                if should_restart_bot_timestamp(script_file, alarm_minutes, restart_minutes, uptime_minutes):
                                    fix_bot(script_file)
                        else:
                            script_file, alarm_minutes, restart_minutes = bot_config
                            uptime_minutes = None
                            if should_restart_bot_timestamp(script_file, alarm_minutes, restart_minutes, uptime_minutes):
                                fix_bot(script_file)
                else:
                    log_event("⚠️ Database not accessible - skipping timestamp-based monitoring")
                    # Fall back to simple monitoring for timestamp bots
                    for bot_config in timestamp_bots:
                        if len(bot_config) == 4:
                            script_file, alarm_minutes, restart_minutes, uptime_minutes = bot_config
                            if uptime_minutes:
                                # Timer-based bot - use queue management
                                queue_position, wait_minutes = get_timer_queue_info(script_file, ram_only_bots, simple_timeout_bots, timestamp_bots)
                                if queue_position == 0 and can_restart_now():
                                    log_event(f"🔄 Timer restart: {script_file} (R-{uptime_minutes})")
                                    fix_bot(script_file)
                                    update_last_restart_time()
                                elif queue_position is not None:
                                    log_event(f"⏳ Bot {script_file} in queue W-{queue_position} (wait: {wait_minutes}m)")
                            else:
                                # Regular simple monitoring
                                if should_restart_bot_simple(script_file, restart_minutes, uptime_minutes):
                                    fix_bot(script_file)
                        else:
                            script_file, alarm_minutes, restart_minutes = bot_config
                            uptime_minutes = None
                            if should_restart_bot_simple(script_file, restart_minutes, uptime_minutes):
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
            
            # Update heartbeat (no logging to reduce spam)
            last_heartbeat = time.time()
            
            time.sleep(INTERVAL)
        except Exception as e:
            log_event(f"❌ Error in main monitoring loop: {e}")
            log_event("🔄 Continuing monitoring loop after error...")
            time.sleep(INTERVAL)  # Wait before retrying

if __name__ == '__main__':
    monitor_loop()


    

    

    