#!/usr/bin/env python3
"""
TMUX SERVER KILLER
Kills the entire tmux server (all sessions)
"""

import subprocess
import sys

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

def get_active_tmux_sessions():
    """Get list of active tmux sessions"""
    try:
        result = subprocess.run(['tmux', 'list-sessions', '-F', '#{session_name}'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip().split('\n') if result.stdout.strip() else []
        return []
    except Exception as e:
        print(f"{Colors.FAIL}❌ Error getting tmux sessions: {e}{Colors.ENDC}")
        return []

def kill_tmux_server():
    """Kill the entire tmux server"""
    try:
        print(f"{Colors.WARNING}🔪 Killing tmux server...{Colors.ENDC}")
        result = subprocess.run(['tmux', 'kill-server'], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"{Colors.OKGREEN}✅ Tmux server killed successfully{Colors.ENDC}")
            return True
        else:
            print(f"{Colors.FAIL}❌ Failed to kill tmux server: {result.stderr}{Colors.ENDC}")
            return False
    except Exception as e:
        print(f"{Colors.FAIL}❌ Error killing tmux server: {e}{Colors.ENDC}")
        return False

def main():
    print(f"{Colors.BOLD}{Colors.HEADER}💀 TMUX SERVER KILLER{Colors.ENDC}")
    print("=" * 50)
    
    # Check if tmux server is running
    active_sessions = get_active_tmux_sessions()
    
    if not active_sessions:
        print(f"{Colors.WARNING}⚠️  No tmux server running{Colors.ENDC}")
        return
    
    print(f"{Colors.OKCYAN}📋 Active tmux sessions that will be killed:{Colors.ENDC}")
    for i, session in enumerate(active_sessions, 1):
        print(f"  {i}. {session}")
    
    print(f"\n{Colors.FAIL}⚠️  WARNING: This will kill ALL tmux sessions!{Colors.ENDC}")
    print(f"{Colors.BOLD}Are you sure you want to continue?{Colors.ENDC}")
    
    while True:
        choice = input(f"\n{Colors.BOLD}Enter 'yes' to confirm or 'no' to cancel: {Colors.ENDC}").strip().lower()
        
        if choice in ['no', 'n', '0']:
            print(f"{Colors.OKGREEN}👋 Cancelled{Colors.ENDC}")
            return
        elif choice in ['yes', 'y', '1']:
            if kill_tmux_server():
                print(f"\n{Colors.OKGREEN}🎉 All tmux sessions have been terminated{Colors.ENDC}")
                print(f"{Colors.OKCYAN}💡 Tmux server is now completely stopped{Colors.ENDC}")
            break
        else:
            print(f"{Colors.FAIL}❌ Invalid input. Please enter 'yes' or 'no'{Colors.ENDC}")

if __name__ == "__main__":
    main()
