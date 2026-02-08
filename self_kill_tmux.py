#!/usr/bin/env python3
"""
Self-killing tmux script
Prints hello 5 times, then shows session name, counts down, and kills itself
"""

import os
import subprocess
import sys
import time

def get_current_tmux_session():
    """Get the current tmux session name"""
    try:
        # Method 1: Use tmux command to get current session (most reliable)
        result = subprocess.run(['tmux', 'display-message', '-p', '#S'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            session_name = result.stdout.strip()
            print(f"🔍 Detected session from tmux command: {session_name}")
            return session_name
        
        # Method 2: Try to get from TMUX environment variable (fallback)
        tmux_session = os.environ.get('TMUX')
        if tmux_session:
            # TMUX format: /tmp/tmux-1000/default,123456,0
            # Extract session name (default)
            session_name = tmux_session.split(',')[0].split('/')[-1]
            print(f"🔍 Detected session from TMUX env: {session_name}")
            return session_name
            
        return None
    except Exception as e:
        print(f"❌ Error getting session name: {e}")
        return None

def kill_tmux_session(session_name):
    """Kill the specified tmux session"""
    try:
        result = subprocess.run(['tmux', 'kill-session', '-t', session_name], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Successfully killed tmux session: {session_name}")
            return True
        else:
            print(f"❌ Failed to kill tmux session: {session_name}")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error killing tmux session: {e}")
        return False

def main():
    print("🚀 Starting self-kill sequence...")
    
    # Print "hello" 5 times with 5-second intervals
    for i in range(5):
        print(f"Hello {i+1}/5")
        if i < 4:  # Don't sleep after the last hello
            time.sleep(5)
    
    # Get current session name
    session_name = get_current_tmux_session()
    
    if not session_name:
        print("❌ Not running in a tmux session or cannot detect session name")
        sys.exit(1)
    
    print(f"\n📋 Current tmux session: {session_name}")
    time.sleep(5)
    
    # Countdown and kill
    print(f"\n💀 Killing session '{session_name}' in:")
    for count in range(5, 0, -1):
        print(f"   {count}...")
        time.sleep(1)
    
    print(f"\n🔥 KILLING SESSION: {session_name}")
    if kill_tmux_session(session_name):
        print("🎯 Session killed successfully!")
    else:
        print("💥 Failed to kill session")
        sys.exit(1)

if __name__ == "__main__":
    main()
