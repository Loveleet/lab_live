#!/usr/bin/env python3
"""
CPU & RAM MONITOR LAUNCHER
Easy launcher for different monitoring tools
"""

import os
import sys
import subprocess
from datetime import datetime

class Colors:
    """ANSI color codes"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    ENDC = '\033[0m'

def display_menu():
    """Display the main menu"""
    print(f"{Colors.BOLD}{Colors.WHITE}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.WHITE}🖥️  CPU & RAM MONITOR LAUNCHER{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.WHITE}{'='*60}{Colors.ENDC}")
    print()
    print(f"{Colors.BOLD}Available Monitors:{Colors.ENDC}")
    print()
    print(f"{Colors.CYAN}1.{Colors.ENDC} Simple CPU & RAM Monitor")
    print(f"   - Lightweight, easy to use")
    print(f"   - Shows all Python processes")
    print(f"   - Perfect for quick monitoring")
    print()
    print(f"{Colors.CYAN}2.{Colors.ENDC} Trading Bot CPU Monitor")
    print(f"   - Specialized for trading bots")
    print(f"   - Shows CPU core distribution")
    print(f"   - Tracks bot-specific metrics")
    print()
    print(f"{Colors.CYAN}3.{Colors.ENDC} Advanced CPU & RAM Monitor")
    print(f"   - Full-featured with interactive controls")
    print(f"   - Detailed process information")
    print(f"   - Advanced filtering and sorting")
    print()
    print(f"{Colors.CYAN}4.{Colors.ENDC} System Analyzer")
    print(f"   - Comprehensive system analysis")
    print(f"   - One-time detailed report")
    print(f"   - Performance recommendations")
    print()
    print(f"{Colors.CYAN}5.{Colors.ENDC} HTOP-Style Monitor")
    print(f"   - Interactive process manager")
    print(f"   - Real-time updates")
    print(f"   - Process control features")
    print()
    print(f"{Colors.CYAN}6.{Colors.ENDC} CPU Core Explanation")
    print(f"   - Explains how CPU percentages work")
    print(f"   - Shows core usage breakdown")
    print(f"   - System capacity analysis")
    print()
    print(f"{Colors.CYAN}7.{Colors.ENDC} Python & PostgreSQL Monitor")
    print(f"   - Shows only Python and PostgreSQL processes")
    print(f"   - Filtered view for development")
    print()
    print(f"{Colors.CYAN}8.{Colors.ENDC} CPU Usage Logger")
    print(f"   - Tracks highest CPU usage per process")
    print(f"   - Saves logs with timestamps")
    print(f"   - Updates only when CPU usage increases")
    print()
    print(f"{Colors.CYAN}0.{Colors.ENDC} Exit")
    print()

def run_monitor(choice):
    """Run the selected monitor"""
    monitors = {
        '1': 'simple_cpu_ram_monitor.py',
        '2': 'trading_bot_cpu_monitor.py',
        '3': 'cpu_ram_process_monitor.py',
        '4': 'tmux_system_analyzer_simple.py',
        '5': 'tmux_htop_style_monitor.py',
        '6': 'cpu_core_explanation.py',
        '7': 'python_postgres_monitor.py',
        '8': 'cpu_usage_logger.py'
    }
    
    if choice in monitors:
        script_name = monitors[choice]
        script_path = os.path.join(os.path.dirname(__file__), script_name)
        
        if os.path.exists(script_path):
            print(f"{Colors.GREEN}🚀 Launching {script_name}...{Colors.ENDC}")
            print(f"{Colors.CYAN}Press Ctrl+C to return to this menu{Colors.ENDC}")
            print()
            
            try:
                # Run the monitor
                subprocess.run([sys.executable, script_path])
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}⚠️  Monitor stopped by user{Colors.ENDC}")
            except Exception as e:
                print(f"{Colors.RED}❌ Error running monitor: {e}{Colors.ENDC}")
        else:
            print(f"{Colors.RED}❌ Monitor script not found: {script_path}{Colors.ENDC}")
    else:
        print(f"{Colors.RED}❌ Invalid choice: {choice}{Colors.ENDC}")

def main():
    """Main function"""
    while True:
        try:
            # Clear screen
            os.system('clear')
            
            # Display menu
            display_menu()
            
            # Get user choice
            choice = input(f"{Colors.BOLD}Enter your choice (0-8): {Colors.ENDC}").strip()
            
            if choice == '0':
                print(f"{Colors.GREEN}👋 Goodbye!{Colors.ENDC}")
                break
            elif choice in ['1', '2', '3', '4', '5', '6', '7', '8']:
                run_monitor(choice)
                input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.ENDC}")
            else:
                print(f"{Colors.RED}❌ Invalid choice. Please enter 0-8.{Colors.ENDC}")
                input(f"{Colors.CYAN}Press Enter to continue...{Colors.ENDC}")
                
        except KeyboardInterrupt:
            print(f"\n{Colors.GREEN}👋 Goodbye!{Colors.ENDC}")
            break
        except Exception as e:
            print(f"{Colors.RED}❌ Error: {e}{Colors.ENDC}")
            input(f"{Colors.CYAN}Press Enter to continue...{Colors.ENDC}")

if __name__ == "__main__":
    main()
