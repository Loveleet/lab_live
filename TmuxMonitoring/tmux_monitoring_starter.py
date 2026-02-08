#!/usr/bin/env python3
"""
TMUX MONITORING STARTER
Starts the tmux monitoring session with the bot cleaner
"""

import subprocess
import sys
import os

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

def check_monitoring_session():
    """Check if monitoring session already exists"""
    try:
        result = subprocess.run(['tmux', 'has-session', '-t', 'monitoring'], 
                              capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"{Colors.FAIL}❌ Error checking monitoring session: {e}{Colors.ENDC}")
        return False

def get_monitoring_session_info():
    """Get information about the monitoring session"""
    try:
        # Check if session exists and get its status
        result = subprocess.run(['tmux', 'list-sessions', '-F', '#{session_name}:#{session_attached}'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            sessions = result.stdout.strip().split('\n') if result.stdout.strip() else []
            for session in sessions:
                if session.startswith('monitoring:'):
                    attached = session.split(':')[1]
                    return True, attached == '1'
        
        return False, False
    except Exception as e:
        print(f"{Colors.FAIL}❌ Error getting monitoring session info: {e}{Colors.ENDC}")
        return False, False

def start_monitoring_session():
    """Start the monitoring session with tmux bot cleaner"""
    try:
        # Check if tmux_bot_cleaner.py exists
        cleaner_path = "/root/tmux_bot_cleaner.py"
        if not os.path.exists(cleaner_path):
            print(f"{Colors.FAIL}❌ tmux_bot_cleaner.py not found at {cleaner_path}{Colors.ENDC}")
            return False
        
        print(f"{Colors.OKCYAN}🚀 Starting monitoring session...{Colors.ENDC}")
        
        # Create new tmux session named 'monitoring'
        result = subprocess.run(['tmux', 'new-session', '-d', '-s', 'monitoring'], 
                              capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"{Colors.FAIL}❌ Failed to create monitoring session: {result.stderr}{Colors.ENDC}")
            return False
        
        # Send the command to run the bot cleaner
        cmd = f"python3.11 {cleaner_path}"
        result = subprocess.run(['tmux', 'send-keys', '-t', 'monitoring', cmd, 'Enter'], 
                              capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"{Colors.FAIL}❌ Failed to start bot cleaner: {result.stderr}{Colors.ENDC}")
            return False
        
        print(f"{Colors.OKGREEN}✅ Monitoring session started successfully{Colors.ENDC}")
        print(f"{Colors.OKCYAN}📋 Session name: monitoring{Colors.ENDC}")
        print(f"{Colors.OKCYAN}🔧 Running: {cmd}{Colors.ENDC}")
        print(f"\n{Colors.BOLD}To attach to the monitoring session:{Colors.ENDC}")
        print(f"{Colors.OKBLUE}  tmux attach -t monitoring{Colors.ENDC}")
        
        return True
        
    except Exception as e:
        print(f"{Colors.FAIL}❌ Error starting monitoring session: {e}{Colors.ENDC}")
        return False

def main():
    print(f"{Colors.BOLD}{Colors.HEADER}🚀 TMUX MONITORING STARTER{Colors.ENDC}")
    print("=" * 50)
    
    # Check if monitoring session already exists
    session_exists, is_attached = get_monitoring_session_info()
    
    if session_exists:
        if is_attached:
            print(f"{Colors.WARNING}⚠️  Monitoring session is already running and attached{Colors.ENDC}")
        else:
            print(f"{Colors.WARNING}⚠️  Monitoring session is already running (detached){Colors.ENDC}")
        
        print(f"\n{Colors.BOLD}Options:{Colors.ENDC}")
        print("1. 🔗 Attach to existing session")
        print("2. 🔄 Kill and restart session")
        print("0. 🔙 Cancel")
        
        while True:
            choice = input(f"\n{Colors.BOLD}Enter choice (1-2, 0=cancel): {Colors.ENDC}").strip()
            
            if choice == '0':
                print(f"{Colors.OKGREEN}👋 Cancelled{Colors.ENDC}")
                return
            elif choice == '1':
                print(f"{Colors.OKCYAN}🔗 Attaching to monitoring session...{Colors.ENDC}")
                try:
                    subprocess.run(['tmux', 'attach', '-t', 'monitoring'])
                except KeyboardInterrupt:
                    print(f"\n{Colors.OKGREEN}👋 Detached from monitoring session{Colors.ENDC}")
                return
            elif choice == '2':
                print(f"{Colors.WARNING}🔪 Killing existing monitoring session...{Colors.ENDC}")
                try:
                    subprocess.run(['tmux', 'kill-session', '-t', 'monitoring'], 
                                 capture_output=True)
                    print(f"{Colors.OKGREEN}✅ Existing session killed{Colors.ENDC}")
                    break
                except Exception as e:
                    print(f"{Colors.FAIL}❌ Error killing session: {e}{Colors.ENDC}")
                    return
            else:
                print(f"{Colors.FAIL}❌ Invalid choice. Please enter 1, 2, or 0{Colors.ENDC}")
    
    # Start new monitoring session
    if start_monitoring_session():
        print(f"\n{Colors.BOLD}🎉 Monitoring session is now running!{Colors.ENDC}")
        print(f"{Colors.OKCYAN}💡 The tmux bot cleaner is monitoring your bots{Colors.ENDC}")
    else:
        print(f"\n{Colors.FAIL}❌ Failed to start monitoring session{Colors.ENDC}")

if __name__ == "__main__":
    main()
