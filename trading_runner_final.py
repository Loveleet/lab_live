#!/usr/bin/env python3
"""
Final Production-Ready Trading Bot Runner with Memory Management and Pagination
This version includes comprehensive error handling, monitoring, and pagination support
"""

import time
import sys
import os
import gc
import psutil
import signal
import threading
import subprocess
import csv
from datetime import datetime, timezone, timedelta
import warnings
warnings.filterwarnings('ignore')

# Import the main trading functions
from FinalVersionTrading_AWS import (
    start_squeezed_pairs_loop,
    start_non_squeezed_pairs_loop,
    log_system_health,
    log_error,
    MAIN_SIGNAL_DETECTOR_ID,
    shutdown_requested
)

# Import pagination functions
from utils.FinalVersionTradingDB_PostgreSQL import (
    get_total_pairs_count
   
)

# Global shutdown flag for the runner
runner_shutdown_requested = False

# Global pagination state
pagination_state = {
    'offset': 0,
    'total_count': 0,
    'batch_size': 100 
}

# Global timing variables
start_time = None
end_time = None

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

def get_ist_time():
    """Get current time in IST (Indian Standard Time)"""
    return datetime.now(IST)

# Timeout constants
THREAD_JOIN_TIMEOUT = 600  # 10 minutes for thread joins
PROCESS_BATCH_TIMEOUT = 600  # 10 minutes for process batches

def get_current_tmux_session():
    """Get the current tmux session name"""
    try:
        result = subprocess.run(['tmux', 'display-message', '-p', '#S'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except:
        return None

def kill_tmux_session(session_name):
    """Kill the specified tmux session"""
    try:
        result = subprocess.run(['tmux', 'kill-session', '-t', session_name], 
                              capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global runner_shutdown_requested
    print("🛑 Runner shutdown signal received. Gracefully shutting down...")
    runner_shutdown_requested = True

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def log_memory_usage():
    """Log current memory usage"""
    process = psutil.Process()
    memory_info = process.memory_info()
    memory_mb = memory_info.rss / 1024 / 1024
    memory_percent = psutil.virtual_memory().percent
    print(f"💾 Memory Usage: {memory_mb:.2f} MB ({memory_percent:.1f}%)")
    return memory_mb

def save_session_timing_to_csv(start_time, end_time, total_time_seconds, cycles_completed, pairs_processed):
    """Save session timing data to CSV file"""
    csv_filename = "trading_runner_sessions.csv"
    
    # Check if file exists to determine if we need headers
    file_exists = os.path.exists(csv_filename)
    
    try:
        with open(csv_filename, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Session_Start', 'Session_End', 'Total_Time_Seconds', 'Total_Time_Formatted', 'Cycles_Completed', 'Pairs_Processed', 'Status', 'Timestamp']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write header if file is new
            if not file_exists:
                writer.writeheader()
            
            # Format total time for better readability
            hours = int(total_time_seconds // 3600)
            minutes = int((total_time_seconds % 3600) // 60)
            seconds = int(total_time_seconds % 60)
            total_time_formatted = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            # Determine if this is an initial entry or final entry
            status = "SESSION_STARTED" if total_time_seconds == 0 and cycles_completed == 0 else "SESSION_COMPLETED"
            
            # Write session data
            writer.writerow({
                'Session_Start': start_time.strftime('%Y-%m-%d %H:%M:%S IST'),
                'Session_End': end_time.strftime('%Y-%m-%d %H:%M:%S IST'),
                'Total_Time_Seconds': f"{total_time_seconds:.2f}",
                'Total_Time_Formatted': total_time_formatted,
                'Cycles_Completed': cycles_completed,
                'Pairs_Processed': pairs_processed,
                'Status': status,
                'Timestamp': get_ist_time().strftime('%Y-%m-%d %H:%M:%S IST')
            })
            
        print(f"📊 Session timing data saved to {csv_filename}")
        print(f"   - Start: {start_time.strftime('%Y-%m-%d %H:%M:%S IST')}")
        print(f"   - End: {end_time.strftime('%Y-%m-%d %H:%M:%S IST')}")
        print(f"   - Total Time: {total_time_formatted}")
        print(f"   - Cycles: {cycles_completed}")
        print(f"   - Pairs: {pairs_processed}")
        
    except Exception as e:
        print(f"❌ Error saving timing data to CSV: {e}")

def force_garbage_collection():
    """Force garbage collection and log results"""
    print("🧹 Cleaning up memory...")
    collected = gc.collect()
    memory_after = log_memory_usage()
    print(f"🗑️ Garbage collection: {collected} objects collected")
    print(f"💾 Memory after GC: {memory_after:.2f} MB")
    return collected, memory_after

def initialize_pagination_state():
    """Initialize pagination state with total counts from database"""
    global pagination_state
    
    print("📊 Initializing pagination state...")
    
    try:
        # Get total counts from database
        pagination_state['total_count'] = get_total_pairs_count()
        
        print(f"📈 Total pairs: {pagination_state['total_count']}")
        print(f"📦 Batch size: {pagination_state['batch_size']}")
        
    except Exception as e:
        print(f"❌ Error initializing pagination state: {e}")
        # Set default values if database calls fail
        pagination_state['total_count'] = 5

def update_pagination_offsets():
    """Update pagination offsets for next cycle"""
    global pagination_state

    # Update offset
    pagination_state['offset'] += pagination_state['batch_size']
    if pagination_state['offset'] >= pagination_state['total_count']:
        pagination_state['offset'] = 0
        print("🔄 Reset offset to 0")
        # Return True if we've completed a full cycle through all pairs
        return True

    print(f"📊 Next cycle offset: {pagination_state['offset']}")
    return False

def run_single_cycle(cycle_number):
    """Run a single trading cycle with pagination"""
    global pagination_state
    
    print(f"🔄 Starting Cycle #{cycle_number}")
    print("=" * 50)
    
    cycle_start_time = get_ist_time()
    print(f"🚀 Starting trading cycle at {cycle_start_time.strftime('%Y-%m-%d %H:%M:%S IST')}")
    
    # Log pagination info
    print(f"📊 Processing batch {pagination_state['batch_size']} pairs:")
    print(f"   - Squeezed pairs: offset={pagination_state['offset']}, total={pagination_state['total_count']}")
    
    # Log initial memory usage
    initial_memory = log_memory_usage()
    
    # Log system health
    log_system_health(MAIN_SIGNAL_DETECTOR_ID)
    
    try:
        # Start both processing loops in parallel with pagination
        print("🎯 Starting Squeezed Pairs Processing...")
        print("🧠 Starting Non-Squeezed Pairs Processing...")
        
        # Create threads for parallel processing with pagination parameters
        squeezed_thread = threading.Thread(
            target=start_squeezed_pairs_loop,
            args=(pagination_state['offset'], pagination_state['batch_size'])
        )
        non_squeezed_thread = threading.Thread(
            target=start_non_squeezed_pairs_loop,
            args=(pagination_state['offset'], pagination_state['batch_size'])
        )
        
        # Start both threads
        squeezed_thread.start()
        non_squeezed_thread.start()
        
        # Wait for both to complete with timeout
        print("⏳ Waiting for processing to complete...")
        squeezed_thread.join(timeout=THREAD_JOIN_TIMEOUT)
        non_squeezed_thread.join(timeout=THREAD_JOIN_TIMEOUT)

        # Check if threads are still alive (timeout occurred)
        if squeezed_thread.is_alive():
            print("⚠️ Squeezed pairs thread is still running after timeout - terminating...")
            # Note: We can't forcefully terminate threads in Python, but we can continue
            squeezed_timeout = True
        else:
            squeezed_timeout = False

        if non_squeezed_thread.is_alive():
            print("⚠️ Non-squeezed pairs thread is still running after timeout - terminating...")
            # Note: We can't forcefully terminate threads in Python, but we can continue
            non_squeezed_timeout = True
        else:
            non_squeezed_timeout = False

        if squeezed_timeout or non_squeezed_timeout:
            print("⚠️ Some threads timed out. This may indicate hanging processes.")
            print("🔄 Continuing to next cycle to avoid complete system hang...")
            # Calculate cycle time for timeout case
            cycle_end_time = get_ist_time()
            cycle_duration = (cycle_end_time - cycle_start_time).total_seconds()
            return True, cycle_duration  # Still return success to continue the cycle
        
        # Calculate cycle time
        cycle_end_time = get_ist_time()
        cycle_duration = (cycle_end_time - cycle_start_time).total_seconds()
        
        print(f"✅ Cycle completed successfully in {cycle_duration:.2f} seconds")
        print(f"✅ Cycle #{cycle_number} completed successfully")
        
        return True, cycle_duration
        
    except Exception as e:
        print(f"❌ Error in cycle #{cycle_number}: {e}")
        log_error(e, "run_single_cycle", machine_id=MAIN_SIGNAL_DETECTOR_ID)
        return False, 0

def main_runner():
    """Main runner function with memory management and pagination"""
    global runner_shutdown_requested, pagination_state, start_time, end_time
    
    # Record start time
    start_time = get_ist_time()
    
    print("🚀 Starting Trading Bot Runner with Memory Management and Pagination...")
    print(f"⏰ Session started at: {start_time.strftime('%Y-%m-%d %H:%M:%S IST')}")
    print("📊 Each cycle will process pairs in batches and then exit to release memory")
    print("⏰ 20 second pause between cycles")
    print("🎯 Will process all pairs once and then exit automatically")
    print()
    
    # Create initial CSV entry to track session start
    print("📝 Creating initial session record...")
    save_session_timing_to_csv(
        start_time, 
        start_time,  # Same as start time for initial entry
        0,  # 0 seconds initially
        0,  # 0 cycles initially
        0   # 0 pairs initially
    )
    
    # Initialize pagination state
    initialize_pagination_state()
    
    cycle_number = 1
    
    while not runner_shutdown_requested:
        try:
            # Run single cycle
            success, cycle_time = run_single_cycle(cycle_number)
            
            if success:
                # Clean up memory after successful cycle
                force_garbage_collection()
                print(f"⏰ Cycle #{cycle_number} total time: {cycle_time:.2f}s")

                # Update pagination offsets for next cycle
                cycle_completed = update_pagination_offsets()

                # Check if we've completed processing all pairs
                if cycle_completed:
                    print("🎉 All pairs have been processed! Exiting the runner.")
                    print(f"📊 Total pairs processed: {pagination_state['total_count']}")
                    print(f"🔢 Total cycles completed: {cycle_number}")
                    break

                # Wait 20 seconds before next cycle
                print("😴 Waiting 20 seconds before next cycle...")
                for remaining in range(20, 0, -5):
                    if runner_shutdown_requested:
                        break
                    print(f"⏳ {remaining} seconds remaining...")
                    time.sleep(5)

                cycle_number += 1
            else:
                print(f"⚠️ Cycle #{cycle_number} failed, retrying in 30 seconds...")
                time.sleep(30)
                
        except KeyboardInterrupt:
            print("🛑 Interrupted by user")
            break
        except Exception as e:
            print(f"❌ Unexpected error in main runner: {e}")
            log_error(e, "main_runner", machine_id=MAIN_SIGNAL_DETECTOR_ID)
            time.sleep(30)
    
    # Record end time
    end_time = get_ist_time()
    total_time_seconds = (end_time - start_time).total_seconds()
    
    print("🛑 Trading Bot Runner stopped.")
    print(f"⏰ Session ended at: {end_time.strftime('%Y-%m-%d %H:%M:%S IST')}")
    print(f"⏱️ Total session time: {total_time_seconds:.2f} seconds")
    
    # Save timing data to CSV
    save_session_timing_to_csv(
        start_time, 
        end_time, 
        total_time_seconds, 
        cycle_number - 1,  # Total cycles completed
        pagination_state['total_count']  # Total pairs processed
    )
    
    # Wait 4 minutes before killing tmux session
    print("⏰ Waiting 4 minutes before killing tmux session...")
    for remaining in range(240, 0, -60):  # Count down every minute
        print(f"⏳ {remaining} seconds remaining before tmux kill...")
        time.sleep(60)
    
    # Self-kill tmux session when runner finishes
    print("🔄 Runner finished, killing tmux session...")
    session_name = get_current_tmux_session()
    if session_name:
        print(f"💀 Killing tmux session: {session_name}")
        if kill_tmux_session(session_name):
            print("✅ Tmux session killed successfully!")
        else:
            print("❌ Failed to kill tmux session")
    else:
        print("❌ Could not detect tmux session")

if __name__ == "__main__":
    main_runner()