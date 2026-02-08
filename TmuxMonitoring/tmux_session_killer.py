#!/usr/bin/env python3
"""
TMUX SESSION KILLER
Kills specific tmux sessions based on bot configuration files
"""

import os
import subprocess
import sys
from datetime import datetime

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

def read_bot_files():
    """Read bot configuration files"""
    # Check which file is active based on instructor.txt
    instructor_file = "/root/TmuxCleaner/instructor.txt"
    bots_file = "/root/TmuxCleaner/bots.txt"
    bots_backup_file = "/root/TmuxCleaner/botsBackup.txt"
    nocleaner_file = "/root/TmuxCleaner/nocleaner.txt"
    
    active_bots = []
    nocleaner_bots = []
    
    try:
        # Read instructor.txt to determine which file to use
        if os.path.exists(instructor_file):
            with open(instructor_file, 'r') as f:
                instructor_content = f.read().strip().lower()
                if 'backup' in instructor_content:
                    active_file = bots_backup_file
                    mode = "BACKUP"
                else:
                    active_file = bots_file
                    mode = "MAIN"
        else:
            active_file = bots_file
            mode = "MAIN"
        
        print(f"{Colors.OKCYAN}📁 Mode: {mode} | Using file: {os.path.basename(active_file)}{Colors.ENDC}")
        
        # Read active bots file
        if os.path.exists(active_file):
            with open(active_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Extract script path (before | if exists)
                        script_path = line.split('|')[0].strip()
                        if script_path:
                            active_bots.append(script_path)
        
        # Read nocleaner file
        if os.path.exists(nocleaner_file):
            with open(nocleaner_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and not line.startswith('*'):
                        # Extract script path (before | if exists)
                        script_path = line.split('|')[0].strip()
                        if script_path:
                            nocleaner_bots.append(script_path)
                            
    except Exception as e:
        print(f"{Colors.FAIL}❌ Error reading bot files: {e}{Colors.ENDC}")
    
    return active_bots, nocleaner_bots

def get_session_name_from_script(script_path):
    """Convert script path to potential tmux session name"""
    script_name = os.path.basename(script_path)
    if script_name.endswith('.py'):
        script_name = script_name[:-3]  # Remove .py
    
    # Get current date for session naming pattern
    today = datetime.now().strftime("%m%d")
    
    # Common session naming patterns
    possible_names = [
        script_name,
        f"{script_name}_{today}_1",
        f"{script_name}_{today}_2",
        f"{script_name}_{today}_3",
        f"{script_name}_1",
        f"{script_name}_2",
        f"{script_name}_3"
    ]
    
    return possible_names

def kill_sessions_by_scripts(scripts, session_type):
    """Kill tmux sessions based on script list"""
    active_sessions = get_active_tmux_sessions()
    killed_sessions = []
    
    print(f"\n{Colors.BOLD}🔍 Looking for {session_type} sessions...{Colors.ENDC}")
    
    for script in scripts:
        possible_names = get_session_name_from_script(script)
        
        for session_name in possible_names:
            if session_name in active_sessions:
                try:
                    print(f"{Colors.WARNING}🔪 Killing session: {session_name}{Colors.ENDC}")
                    subprocess.run(['tmux', 'kill-session', '-t', session_name], 
                                 capture_output=True)
                    killed_sessions.append(session_name)
                except Exception as e:
                    print(f"{Colors.FAIL}❌ Error killing session {session_name}: {e}{Colors.ENDC}")
    
    return killed_sessions

def main():
    print(f"{Colors.BOLD}{Colors.HEADER}🔪 TMUX SESSION KILLER{Colors.ENDC}")
    print("=" * 50)
    
    # Get current active sessions
    active_sessions = get_active_tmux_sessions()
    if not active_sessions:
        print(f"{Colors.WARNING}⚠️  No active tmux sessions found{Colors.ENDC}")
        return
    
    print(f"{Colors.OKCYAN}📋 Active tmux sessions:{Colors.ENDC}")
    for i, session in enumerate(active_sessions, 1):
        print(f"  {i}. {session}")
    
    # Read bot configuration
    active_bots, nocleaner_bots = read_bot_files()
    
    print(f"\n{Colors.BOLD}Select kill option:{Colors.ENDC}")
    print("1. 🔪 Kill Main Bots (bots.txt/botsBackup.txt)")
    print("2. 🔪 Kill Nocleaner Bots only")
    print("3. 🔪 Kill Both (Main + Nocleaner)")
    print("0. 🔙 Cancel")
    
    while True:
        choice = input(f"\n{Colors.BOLD}Enter choice (1-3, 0=cancel): {Colors.ENDC}").strip()
        
        if choice == '0':
            print(f"{Colors.OKGREEN}👋 Cancelled{Colors.ENDC}")
            return
        elif choice == '1':
            if not active_bots:
                print(f"{Colors.WARNING}⚠️  No main bots found in configuration{Colors.ENDC}")
                return
            
            print(f"\n{Colors.BOLD}🔪 Killing Main Bots...{Colors.ENDC}")
            killed = kill_sessions_by_scripts(active_bots, "Main Bot")
            
            if killed:
                print(f"\n{Colors.OKGREEN}✅ Successfully killed {len(killed)} sessions:{Colors.ENDC}")
                for session in killed:
                    print(f"  - {session}")
            else:
                print(f"{Colors.WARNING}⚠️  No main bot sessions found to kill{Colors.ENDC}")
            break
            
        elif choice == '2':
            if not nocleaner_bots:
                print(f"{Colors.WARNING}⚠️  No nocleaner bots found in configuration{Colors.ENDC}")
                return
            
            print(f"\n{Colors.BOLD}🔪 Killing Nocleaner Bots...{Colors.ENDC}")
            killed = kill_sessions_by_scripts(nocleaner_bots, "Nocleaner Bot")
            
            if killed:
                print(f"\n{Colors.OKGREEN}✅ Successfully killed {len(killed)} sessions:{Colors.ENDC}")
                for session in killed:
                    print(f"  - {session}")
            else:
                print(f"{Colors.WARNING}⚠️  No nocleaner bot sessions found to kill{Colors.ENDC}")
            break
            
        elif choice == '3':
            all_bots = active_bots + nocleaner_bots
            if not all_bots:
                print(f"{Colors.WARNING}⚠️  No bots found in configuration{Colors.ENDC}")
                return
            
            print(f"\n{Colors.BOLD}🔪 Killing All Bots...{Colors.ENDC}")
            killed = kill_sessions_by_scripts(all_bots, "All Bot")
            
            if killed:
                print(f"\n{Colors.OKGREEN}✅ Successfully killed {len(killed)} sessions:{Colors.ENDC}")
                for session in killed:
                    print(f"  - {session}")
            else:
                print(f"{Colors.WARNING}⚠️  No bot sessions found to kill{Colors.ENDC}")
            break
            
        else:
            print(f"{Colors.FAIL}❌ Invalid choice. Please enter 1, 2, 3, or 0{Colors.ENDC}")

if __name__ == "__main__":
    main()
