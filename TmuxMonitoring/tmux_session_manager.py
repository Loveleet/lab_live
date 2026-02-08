#!/usr/bin/env python3
"""
TMUX Session Manager
Interactive tool to list, attach to, and delete tmux sessions
Shows session processes and provides keyboard-based options
"""

import os
import sys
import time
import psutil
import subprocess
from typing import Dict, List, Tuple, Optional

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def get_tmux_sessions():
    """Get list of active tmux sessions"""
    try:
        result = subprocess.run(['tmux', 'list-sessions'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            sessions = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    # Parse session info: session_name: 1 windows (created ...)
                    parts = line.split(':')
                    if len(parts) >= 2:
                        session_name = parts[0].strip()
                        session_info = ':'.join(parts[1:]).strip()
                        sessions.append({
                            'name': session_name,
                            'info': session_info,
                            'line': line.strip()
                        })
            return sessions
        else:
            return []
    except Exception as e:
        print(f"{Colors.FAIL}Error getting tmux sessions: {e}{Colors.ENDC}")
        return []

def get_session_processes(session_name):
    """Get processes running in a tmux session"""
    try:
        # Get tmux session PID
        result = subprocess.run(['tmux', 'list-panes', '-t', session_name, '-F', '#{pane_pid}'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            pids = []
            for pid_str in result.stdout.strip().split('\n'):
                if pid_str.strip():
                    try:
                        pid = int(pid_str.strip())
                        pids.append(pid)
                    except ValueError:
                        continue
            
            # Get process details for each PID
            processes = []
            for pid in pids:
                try:
                    proc = psutil.Process(pid)
                    processes.append({
                        'pid': pid,
                        'name': proc.name(),
                        'cmdline': ' '.join(proc.cmdline()),
                        'memory_mb': proc.memory_info().rss / 1024 / 1024,
                        'cpu_percent': proc.cpu_percent(),
                        'status': proc.status(),
                        'create_time': proc.create_time()
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return processes
        else:
            return []
    except Exception as e:
        print(f"{Colors.WARNING}Error getting processes for session {session_name}: {e}{Colors.ENDC}")
        return []

def format_uptime(create_time):
    """Format process uptime"""
    try:
        uptime_seconds = time.time() - create_time
        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    except:
        return "N/A"

def get_smart_filename(session_name, max_length=25):
    """Get smart filename display with first 4 and last 4 letters before date/count suffix"""
    name = session_name
    
    # Remove .py extension if present
    if name.endswith('.py'):
        name = name[:-3]
    
    # Remove date/count suffix pattern like "_0904_1", "_1205_2", etc.
    import re
    # Pattern to match _MMDD_N at the end
    date_count_pattern = r'_\d{4}_\d+$'
    name = re.sub(date_count_pattern, '', name)
    
    # If name is short enough, return as is
    if len(name) <= max_length:
        return name
    
    # Extract first 4 and last 4 characters
    if len(name) <= 8:
        # If name is 8 chars or less, just return it
        return name
    
    first_part = name[:4]
    last_part = name[-4:]
    
    # Calculate available space for middle part
    available_space = max_length - 8  # 4 for first + 4 for last
    if available_space > 0:
        # Add some middle characters if there's space
        middle_chars = min(available_space - 3, len(name) - 8)  # -3 for "..."
        if middle_chars > 0:
            middle_part = name[4:4+middle_chars]
            return f"{first_part}{middle_part}...{last_part}"
        else:
            return f"{first_part}...{last_part}"
    else:
        return f"{first_part}...{last_part}"

def get_session_status(processes):
    """Get session status based on processes"""
    if not processes:
        return "STOPPED", Colors.FAIL
    
    # Check if any process is actually running (not just shell)
    active_processes = []
    for proc in processes:
        if 'python' in proc['name'].lower() or 'bot' in proc['cmdline'].lower():
            active_processes.append(proc)
    
    if not active_processes:
        return "SHELL_ONLY", Colors.WARNING
    
    # Check memory usage
    total_memory = sum(proc['memory_mb'] for proc in active_processes)
    if total_memory > 3000:
        return "HIGH_MEM", Colors.FAIL
    elif total_memory > 1000:
        return "NORMAL", Colors.OKGREEN
    else:
        return "LOW_MEM", Colors.OKCYAN

def display_sessions_table(sessions):
    """Display tmux sessions in table format like monitoring tool"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}🖥️  TMUX SESSION MANAGER{Colors.ENDC}")
    print("=" * 120)
    
    if not sessions:
        print(f"{Colors.WARNING}No active tmux sessions found.{Colors.ENDC}")
        return
    
    # Prepare session data
    session_data = []
    for i, session in enumerate(sessions, 1):
        session_name = session['name']
        processes = get_session_processes(session_name)
        
        # Get main process info
        main_process = None
        total_memory = 0
        total_cpu = 0
        main_uptime = "N/A"
        
        if processes:
            # Find the main Python process
            for proc in processes:
                if 'python' in proc['name'].lower():
                    main_process = proc
                    break
            
            # If no Python process, use the first process
            if not main_process:
                main_process = processes[0]
            
            total_memory = sum(proc['memory_mb'] for proc in processes)
            total_cpu = sum(proc['cpu_percent'] for proc in processes)
            main_uptime = format_uptime(main_process['create_time'])
        
        status, status_color = get_session_status(processes)
        short_name = get_smart_filename(session_name, 22)
        
        # Create display name with serial number
        display_name = f"{i:2d}. {short_name}"
        
        session_data.append({
            'num': i,
            'display_name': display_name,
            'short_name': short_name,
            'full_name': session_name,
            'status': status,
            'status_color': status_color,
            'pid': main_process['pid'] if main_process else 'N/A',
            'memory': f"{total_memory:.1f} MB",
            'cpu': f"{total_cpu:.1f}%",
            'uptime': main_uptime,
            'process_count': len(processes)
        })
    
    # Display table
    print(f"{Colors.BOLD}Session Name{' ' * 12}Status{' ' * 8}PID{' ' * 8}Memory{' ' * 8}CPU{' ' * 8}Uptime{' ' * 8}Processes{Colors.ENDC}")
    print("-" * 125)
    
    for session in session_data:
        print(f"{session['display_name']:<25} "
              f"{session['status_color']}{session['status']:<12}{Colors.ENDC} "
              f"{session['pid']:<10} "
              f"{session['memory']:<12} "
              f"{session['cpu']:<10} "
              f"{session['uptime']:<12} "
              f"{session['process_count']}")
    
    print("-" * 120)
    
    # Show actions
    print(f"\n{Colors.BOLD}Commands:{Colors.ENDC}")
    print(f"{Colors.OKGREEN}[a1-a{session_data[-1]['num']}] Attach{Colors.ENDC} | "
          f"{Colors.OKBLUE}[c1-c{session_data[-1]['num']}] Copy command{Colors.ENDC} | "
          f"{Colors.OKBLUE}[cc] All commands{Colors.ENDC} | "
          f"{Colors.FAIL}[d1-d{session_data[-1]['num']}] Delete{Colors.ENDC} | "
          f"{Colors.OKCYAN}[r1-r{session_data[-1]['num']}] Refresh{Colors.ENDC} | "
          f"{Colors.WARNING}[0] Back to main{Colors.ENDC} | "
          f"{Colors.WARNING}[q] Quit{Colors.ENDC}")

def display_detailed_processes(sessions):
    """Display detailed process information in a second table if needed"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}📋 DETAILED PROCESS INFORMATION{Colors.ENDC}")
    print("=" * 120)
    
    for i, session in enumerate(sessions, 1):
        session_name = session['name']
        processes = get_session_processes(session_name)
        
        if processes:
            short_name = get_smart_filename(session_name, 22)
            print(f"\n{Colors.BOLD}{Colors.OKBLUE}📺 {i:2d}. {short_name} (Session {i}){Colors.ENDC}")
            
            print(f"{Colors.BOLD}PID{' ' * 8}Process{' ' * 8}Memory{' ' * 8}CPU{' ' * 8}Uptime{' ' * 8}Command{Colors.ENDC}")
            print("-" * 120)
            
            for proc in processes:
                uptime = format_uptime(proc['create_time'])
                cmdline = proc['cmdline']
                if len(cmdline) > 40:
                    cmdline = cmdline[:37] + "..."
                
                print(f"{proc['pid']:<10} "
                      f"{proc['name']:<12} "
                      f"{proc['memory_mb']:.1f} MB{' ' * 4} "
                      f"{proc['cpu_percent']:.1f}%{' ' * 4} "
                      f"{uptime:<12} "
                      f"{cmdline}")
            
            print("-" * 120)

# Removed old get_input function - now using get_unified_input()

def copy_attach_command(session_name):
    """Show tmux attach command with spaces for easy copying"""
    command = f"tmux attach -t {session_name}"
    
    # Show command with spaces above and below for easy copying
    print()  # Space above
    print(f"{Colors.BOLD}{command}{Colors.ENDC}")
    print()  # Space below

def show_all_commands_table(sessions):
    """Show table with all tmux attach commands"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}📋 ALL TMUX ATTACH COMMANDS{Colors.ENDC}")
    print("=" * 100)
    
    # Header
    print(f"{Colors.BOLD}Serial{' ' * 4}Session Name{' ' * 15}Command to Copy{Colors.ENDC}")
    print("-" * 100)
    
    for i, session in enumerate(sessions, 1):
        session_name = session['name']
        command = f"tmux attach -t {session_name}"
        short_name = get_smart_filename(session_name, 25)
        
        print(f"{i:2d}.{' ' * 6}{short_name:<25} {Colors.BOLD}{command}{Colors.ENDC}")
    
    print("=" * 100)
    print(f"{Colors.OKCYAN}💡 Copy any command above{Colors.ENDC}")
    print()  # Extra space for easy copying

def get_unified_input():
    """Get unified command input"""
    return input(f"{Colors.BOLD}Command (c1, a1, d1, r1, 0=back, q=quit): {Colors.ENDC}").strip()

def attach_to_session(session_name):
    """Attach to a tmux session directly in current terminal"""
    try:
        print(f"{Colors.OKGREEN}🔗 Attaching to session: {session_name}{Colors.ENDC}")
        print(f"{Colors.OKCYAN}💡 Tip: Use 'Ctrl+B, D' to detach from session{Colors.ENDC}")
        print(f"{Colors.WARNING}⚠️  This will attach in the current terminal{Colors.ENDC}")
        
        # Directly attach in current terminal
        result = subprocess.run(['tmux', 'attach', '-t', session_name])
        
        # After detaching, automatically return to main menu
        print(f"{Colors.OKGREEN}✅ Detached from session. Returning to main menu...{Colors.ENDC}")
        time.sleep(1)  # Brief pause to show the message
        
    except Exception as e:
        print(f"{Colors.FAIL}❌ Error attaching to session {session_name}: {e}{Colors.ENDC}")
        print(f"{Colors.OKCYAN}💡 Manual command: tmux attach -t {session_name}{Colors.ENDC}")

def delete_session(session_name):
    """Delete a tmux session"""
    try:
        print(f"{Colors.WARNING}⚠️  Deleting session: {session_name}{Colors.ENDC}")
        
        # Kill the session
        result = subprocess.run(['tmux', 'kill-session', '-t', session_name], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print(f"{Colors.OKGREEN}✅ Session {session_name} deleted successfully{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}❌ Error deleting session {session_name}: {result.stderr}{Colors.ENDC}")
            
    except Exception as e:
        print(f"{Colors.FAIL}❌ Error deleting session {session_name}: {e}{Colors.ENDC}")

def refresh_sessions():
    """Refresh and display sessions"""
    print(f"{Colors.OKCYAN}🔄 Refreshing sessions...{Colors.ENDC}")
    sessions = get_tmux_sessions()
    display_sessions_table(sessions)
    return sessions

def main():
    """Main function"""
    print(f"{Colors.BOLD}{Colors.HEADER}🚀 TMUX SESSION MANAGER{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Interactive tmux session management with process monitoring{Colors.ENDC}")
    
    while True:
        # Get current sessions
        sessions = get_tmux_sessions()
        
        if not sessions:
            print(f"\n{Colors.WARNING}No active tmux sessions found.{Colors.ENDC}")
            print(f"{Colors.OKCYAN}Create a session with: tmux new-session -s session_name{Colors.ENDC}")
            break
        
        # Display sessions in table format
        display_sessions_table(sessions)
        
        # Get user action
        action = get_unified_input()
        
        if action.lower() == 'q':
            print(f"{Colors.OKGREEN}👋 Goodbye!{Colors.ENDC}")
            break
        elif action == '0':
            # Back to main menu (already in main menu, just continue)
            continue
        elif action.lower() == 'cc':
            # Show all commands table and enter continuous copy mode
            show_all_commands_table(sessions)
            # Enter continuous copy mode
            while True:
                next_action = get_unified_input()
                if next_action.lower() == 'q':
                    print(f"{Colors.OKGREEN}👋 Goodbye!{Colors.ENDC}")
                    return  # Exit completely
                elif next_action == '0':
                    break  # Exit copy mode, return to main menu
                elif next_action.lower() == 'cc':
                    show_all_commands_table(sessions)
                elif next_action.lower().startswith('c'):
                    try:
                        next_session_num = int(next_action[1:]) - 1
                        if 0 <= next_session_num < len(sessions):
                            next_session_name = sessions[next_session_num]['name']
                            copy_attach_command(next_session_name)
                        else:
                            print(f"{Colors.FAIL}❌ Invalid session number{Colors.ENDC}")
                    except ValueError:
                        print(f"{Colors.FAIL}❌ Invalid action format. Use c1, c2, etc.{Colors.ENDC}")
                elif next_action.lower().startswith('a'):
                    try:
                        next_session_num = int(next_action[1:]) - 1
                        if 0 <= next_session_num < len(sessions):
                            next_session_name = sessions[next_session_num]['name']
                            attach_to_session(next_session_name)
                            break  # Exit copy mode after attach
                        else:
                            print(f"{Colors.FAIL}❌ Invalid session number{Colors.ENDC}")
                    except ValueError:
                        print(f"{Colors.FAIL}❌ Invalid action format. Use a1, a2, etc.{Colors.ENDC}")
                elif next_action.lower().startswith('d'):
                    try:
                        next_session_num = int(next_action[1:]) - 1
                        if 0 <= next_session_num < len(sessions):
                            next_session_name = sessions[next_session_num]['name']
                            delete_session(next_session_name)
                            time.sleep(1)
                            break  # Exit copy mode after delete
                        else:
                            print(f"{Colors.FAIL}❌ Invalid session number{Colors.ENDC}")
                    except ValueError:
                        print(f"{Colors.FAIL}❌ Invalid action format. Use d1, d2, etc.{Colors.ENDC}")
                elif next_action.lower().startswith('r'):
                    sessions = refresh_sessions()
                else:
                    print(f"{Colors.WARNING}❌ Invalid action. Use c1-c10, cc, a1-a10, d1-d10, r1-r10, 0=back, or q=quit{Colors.ENDC}")
        elif action.lower().startswith('c'):
            # Copy attach command - enter continuous copy mode
            try:
                session_num = int(action[1:]) - 1
                if 0 <= session_num < len(sessions):
                    session_name = sessions[session_num]['name']
                    copy_attach_command(session_name)
                    # Enter continuous copy mode
                    while True:
                        next_action = get_unified_input()
                        if next_action.lower() == 'q':
                            print(f"{Colors.OKGREEN}👋 Goodbye!{Colors.ENDC}")
                            return  # Exit completely
                        elif next_action == '0':
                            break  # Exit copy mode, return to main menu
                        elif next_action.lower() == 'cc':
                            show_all_commands_table(sessions)
                        elif next_action.lower().startswith('c'):
                            try:
                                next_session_num = int(next_action[1:]) - 1
                                if 0 <= next_session_num < len(sessions):
                                    next_session_name = sessions[next_session_num]['name']
                                    copy_attach_command(next_session_name)
                                else:
                                    print(f"{Colors.FAIL}❌ Invalid session number{Colors.ENDC}")
                            except ValueError:
                                print(f"{Colors.FAIL}❌ Invalid action format. Use c1, c2, etc.{Colors.ENDC}")
                        elif next_action.lower().startswith('a'):
                            try:
                                next_session_num = int(next_action[1:]) - 1
                                if 0 <= next_session_num < len(sessions):
                                    next_session_name = sessions[next_session_num]['name']
                                    attach_to_session(next_session_name)
                                    break  # Exit copy mode after attach
                                else:
                                    print(f"{Colors.FAIL}❌ Invalid session number{Colors.ENDC}")
                            except ValueError:
                                print(f"{Colors.FAIL}❌ Invalid action format. Use a1, a2, etc.{Colors.ENDC}")
                        elif next_action.lower().startswith('d'):
                            try:
                                next_session_num = int(next_action[1:]) - 1
                                if 0 <= next_session_num < len(sessions):
                                    next_session_name = sessions[next_session_num]['name']
                                    delete_session(next_session_name)
                                    time.sleep(1)
                                    break  # Exit copy mode after delete
                                else:
                                    print(f"{Colors.FAIL}❌ Invalid session number{Colors.ENDC}")
                            except ValueError:
                                print(f"{Colors.FAIL}❌ Invalid action format. Use d1, d2, etc.{Colors.ENDC}")
                        elif next_action.lower().startswith('r'):
                            sessions = refresh_sessions()
                        else:
                            print(f"{Colors.WARNING}❌ Invalid action. Use c1-c10, cc, a1-a10, d1-d10, r1-r10, 0=back, or q=quit{Colors.ENDC}")
                else:
                    print(f"{Colors.FAIL}❌ Invalid session number{Colors.ENDC}")
            except ValueError:
                print(f"{Colors.FAIL}❌ Invalid action format. Use c1, c2, etc.{Colors.ENDC}")
        elif action.lower().startswith('a'):
            # Attach to session
            try:
                session_num = int(action[1:]) - 1
                if 0 <= session_num < len(sessions):
                    session_name = sessions[session_num]['name']
                    attach_to_session(session_name)
                    # Don't break - return to main menu after detaching
                else:
                    print(f"{Colors.FAIL}❌ Invalid session number{Colors.ENDC}")
            except ValueError:
                print(f"{Colors.FAIL}❌ Invalid action format. Use a1, a2, etc.{Colors.ENDC}")
        elif action.lower().startswith('d'):
            # Delete session
            try:
                session_num = int(action[1:]) - 1
                if 0 <= session_num < len(sessions):
                    session_name = sessions[session_num]['name']
                    delete_session(session_name)
                    time.sleep(1)  # Brief pause to show result
                else:
                    print(f"{Colors.FAIL}❌ Invalid session number{Colors.ENDC}")
            except ValueError:
                print(f"{Colors.FAIL}❌ Invalid action format. Use d1, d2, etc.{Colors.ENDC}")
        elif action.lower().startswith('r'):
            # Refresh sessions
            sessions = refresh_sessions()
        else:
            print(f"{Colors.WARNING}❌ Invalid action. Use c1-c10, cc, a1-a10, d1-d10, r1-r10, 0=back, or q=quit{Colors.ENDC}")
        
        print()  # Add spacing

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.OKGREEN}👋 Goodbye!{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.FAIL}❌ Unexpected error: {e}{Colors.ENDC}")