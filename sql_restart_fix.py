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