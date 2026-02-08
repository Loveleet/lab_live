#!/usr/bin/env python3
"""
REAL-TIME CPU & RAM PROCESS MONITOR
Advanced process monitoring tool specifically designed for trading bot management
Shows detailed CPU usage per process, RAM usage, and system-wide statistics
"""

import psutil
import os
import time
import sys
import subprocess
from datetime import datetime
import threading
import signal
import json
from collections import defaultdict

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
    DIM = '\033[2m'

class CPU_RAM_ProcessMonitor:
    def __init__(self):
        self.running = True
        self.sort_key = 'cpu_percent'  # Default sort by CPU
        self.sort_reverse = True  # Descending order
        self.filter_text = ""
        self.selected_pid = None
        self.show_help = False
        self.show_detailed = False
        self.refresh_interval = 2  # seconds
        self.cpu_history = defaultdict(list)  # Store CPU history for each process
        self.max_history = 10  # Keep last 10 readings
        
        # Signal handler for graceful exit
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        self.running = False
        self.cleanup()
        sys.exit(0)
    
    def cleanup(self):
        """Clean up terminal on exit"""
        os.system('clear')
        print(f"{Colors.OKGREEN}✅ CPU & RAM Process Monitor stopped{Colors.ENDC}")
    
    def read_bots_config(self):
        """Read bot paths from various config files"""
        bot_paths = set()
        
        # Try different possible locations
        config_files = [
            '/root/botsBackup.txt',
            '/root/bots.txt',
            '/root/TmuxCleaner/botsBackup.txt',
            '/root/TmuxCleaner/bots.txt',
            'botsBackup.txt',
            'bots.txt'
        ]
        
        for config_file in config_files:
            try:
                if os.path.exists(config_file):
                    with open(config_file, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                # Extract bot path (before any | or space)
                                bot_path = line.split('|')[0].split()[0]
                                if bot_path.endswith('.py'):
                                    bot_paths.add(bot_path)
            except Exception as e:
                continue
        
        # If no config files found, monitor all Python processes
        if not bot_paths:
            print(f"{Colors.WARNING}⚠️ No bot config files found, monitoring all Python processes{Colors.ENDC}")
            return list(bot_paths)
        
        return list(bot_paths)
    
    def get_process_info(self, bot_path=None):
        """Get detailed process information for all processes or specific bot"""
        processes = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_info', 'memory_percent', 'status', 'create_time', 'num_threads', 'cpu_affinity', 'username']):
                try:
                    proc_info = proc.info
                    
                    # Filter for Python processes or specific bot
                    if bot_path:
                        if not (proc_info['cmdline'] and bot_path in ' '.join(proc_info['cmdline'])):
                            continue
                    else:
                        # Only show Python processes
                        if not (proc_info['name'] and 'python' in proc_info['name'].lower()):
                            continue
                    
                    # Get CPU times for more detailed analysis
                    try:
                        cpu_times = proc.cpu_times()
                        cpu_times_info = {
                            'user_time': cpu_times.user,
                            'system_time': cpu_times.system,
                            'children_user': getattr(cpu_times, 'children_user', 0),
                            'children_system': getattr(cpu_times, 'children_system', 0)
                        }
                    except:
                        cpu_times_info = {
                            'user_time': 0,
                            'system_time': 0,
                            'children_user': 0,
                            'children_system': 0
                        }
                    
                    # Get memory info
                    memory_info = proc_info['memory_info']
                    memory_mb = memory_info.rss / (1024 * 1024)
                    memory_vms_mb = memory_info.vms / (1024 * 1024)
                    
                    # Get process uptime
                    uptime_seconds = time.time() - proc_info['create_time']
                    
                    # Store CPU history for trend analysis
                    pid = proc_info['pid']
                    cpu_percent = proc_info['cpu_percent'] or 0
                    self.cpu_history[pid].append(cpu_percent)
                    if len(self.cpu_history[pid]) > self.max_history:
                        self.cpu_history[pid].pop(0)
                    
                    # Calculate CPU trend
                    cpu_trend = self.calculate_trend(self.cpu_history[pid])
                    
                    process_data = {
                        'pid': pid,
                        'name': proc_info['name'],
                        'cmdline': ' '.join(proc_info['cmdline']) if proc_info['cmdline'] else '',
                        'cpu_percent': cpu_percent,
                        'memory_mb': memory_mb,
                        'memory_vms_mb': memory_vms_mb,
                        'memory_percent': proc_info['memory_percent'] or 0,
                        'status': proc_info['status'],
                        'create_time': proc_info['create_time'],
                        'uptime_seconds': uptime_seconds,
                        'num_threads': proc_info['num_threads'],
                        'cpu_affinity': proc_info['cpu_affinity'],
                        'username': proc_info['username'],
                        'cpu_times': cpu_times_info,
                        'cpu_trend': cpu_trend,
                        'bot_path': bot_path if bot_path else self.extract_bot_path(proc_info['cmdline'])
                    }
                    
                    processes.append(process_data)
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                    
        except Exception as e:
            print(f"{Colors.FAIL}❌ Error getting process info: {e}{Colors.ENDC}")
            
        return processes
    
    def extract_bot_path(self, cmdline):
        """Extract bot path from command line"""
        if not cmdline:
            return "Unknown"
        
        cmdline_str = ' '.join(cmdline)
        # Look for .py files in the command line
        for part in cmdline:
            if part.endswith('.py') and 'python' in cmdline_str.lower():
                return part
        return "Unknown"
    
    def calculate_trend(self, cpu_history):
        """Calculate CPU usage trend"""
        if len(cpu_history) < 2:
            return "stable"
        
        recent_avg = sum(cpu_history[-3:]) / min(3, len(cpu_history))
        older_avg = sum(cpu_history[:-3]) / max(1, len(cpu_history) - 3) if len(cpu_history) > 3 else recent_avg
        
        if recent_avg > older_avg * 1.2:
            return "increasing"
        elif recent_avg < older_avg * 0.8:
            return "decreasing"
        else:
            return "stable"
    
    def format_uptime(self, uptime_seconds):
        """Format process uptime"""
        if uptime_seconds < 60:
            return f"{uptime_seconds:.0f}s"
        elif uptime_seconds < 3600:
            return f"{uptime_seconds/60:.0f}m"
        elif uptime_seconds < 86400:
            return f"{uptime_seconds/3600:.0f}h"
        else:
            return f"{uptime_seconds/86400:.0f}d"
    
    def format_memory(self, memory_bytes):
        """Format memory size"""
        if memory_bytes < 1024:
            return f"{memory_bytes:.0f}B"
        elif memory_bytes < 1024**2:
            return f"{memory_bytes/1024:.0f}K"
        elif memory_bytes < 1024**3:
            return f"{memory_bytes/(1024**2):.0f}M"
        else:
            return f"{memory_bytes/(1024**3):.1f}G"
    
    def get_status_color(self, status):
        """Get color for process status"""
        status_map = {
            'R': Colors.OKGREEN,  # Running
            'S': Colors.OKCYAN,   # Sleeping
            'D': Colors.WARNING,  # Uninterruptible
            'Z': Colors.FAIL,     # Zombie
            'T': Colors.FAIL,     # Stopped
            'I': Colors.OKGREEN,  # Idle
        }
        return status_map.get(status[0], Colors.ENDC)
    
    def get_cpu_color(self, cpu_percent):
        """Get color for CPU usage"""
        if cpu_percent > 80:
            return Colors.FAIL
        elif cpu_percent > 50:
            return Colors.WARNING
        elif cpu_percent > 20:
            return Colors.OKGREEN
        else:
            return Colors.OKCYAN
    
    def get_memory_color(self, memory_mb):
        """Get color for memory usage"""
        if memory_mb > 2000:  # > 2GB
            return Colors.FAIL
        elif memory_mb > 1000:  # > 1GB
            return Colors.WARNING
        elif memory_mb > 500:   # > 500MB
            return Colors.OKGREEN
        else:
            return Colors.OKCYAN
    
    def get_trend_color(self, trend):
        """Get color for CPU trend"""
        if trend == "increasing":
            return Colors.FAIL
        elif trend == "decreasing":
            return Colors.OKGREEN
        else:
            return Colors.OKCYAN
    
    def display_system_header(self):
        """Display system-wide CPU and RAM information"""
        # Get system info
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_per_core = psutil.cpu_percent(interval=0.1, percpu=True)
        memory = psutil.virtual_memory()
        load_avg = os.getloadavg()
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        
        print(f"{Colors.BOLD}{Colors.HEADER}{'='*140}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}🖥️  REAL-TIME CPU & RAM PROCESS MONITOR - 16-CORE SYSTEM ANALYSIS{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}{'='*140}{Colors.ENDC}")
        
        # System status
        print(f"{Colors.BOLD}🖥️  SYSTEM OVERVIEW:{Colors.ENDC}")
        print(f"Overall CPU: {self.get_cpu_color(cpu_percent)}[{cpu_percent:5.1f}%]{Colors.ENDC}  "
              f"Memory: {self.get_memory_color(memory.used/(1024**3))}[{memory.percent:5.1f}%]{Colors.ENDC}  "
              f"Load: {load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f}  "
              f"Uptime: {str(uptime).split('.')[0]}")
        
        # Per-core CPU usage
        print(f"\n{Colors.BOLD}⚡ CPU CORE USAGE (16 cores):{Colors.ENDC}")
        core_line = ""
        for i, core_usage in enumerate(cpu_per_core):
            core_color = self.get_cpu_color(core_usage)
            core_line += f"{core_color}[{core_usage:4.1f}%]{Colors.ENDC} "
            if (i + 1) % 8 == 0:  # New line every 8 cores
                print(f"Cores {i-7:2d}-{i+1:2d}: {core_line}")
                core_line = ""
        if core_line:  # Print remaining cores
            print(f"Cores {len(cpu_per_core)-len(cpu_per_core)%8+1:2d}-{len(cpu_per_core):2d}: {core_line}")
        
        # Memory breakdown
        print(f"\n{Colors.BOLD}🧠 MEMORY BREAKDOWN:{Colors.ENDC}")
        print(f"Total: {self.format_memory(memory.total)}  "
              f"Used: {self.format_memory(memory.used)}  "
              f"Free: {self.format_memory(memory.free)}  "
              f"Available: {self.format_memory(memory.available)}  "
              f"Cached: {self.format_memory(memory.cached)}  "
              f"Buffers: {self.format_memory(memory.buffers)}")
        print()
    
    def display_processes(self, processes):
        """Display process list with detailed CPU and RAM info"""
        if not processes:
            print(f"{Colors.WARNING}⚠️  No Python processes found{Colors.ENDC}")
            return
        
        # Sort processes
        if self.sort_key == 'cpu_percent':
            processes.sort(key=lambda x: x['cpu_percent'], reverse=self.sort_reverse)
        elif self.sort_key == 'memory_mb':
            processes.sort(key=lambda x: x['memory_mb'], reverse=self.sort_reverse)
        elif self.sort_key == 'pid':
            processes.sort(key=lambda x: x['pid'], reverse=self.sort_reverse)
        elif self.sort_key == 'uptime':
            processes.sort(key=lambda x: x['uptime_seconds'], reverse=self.sort_reverse)
        elif self.sort_key == 'threads':
            processes.sort(key=lambda x: x['num_threads'], reverse=self.sort_reverse)
        
        # Header
        if self.show_detailed:
            header = f"{Colors.BOLD}{'PID':<8} {'USER':<8} {'%CPU':<6} {'%MEM':<6} {'RSS':<8} {'VMS':<8} {'THREADS':<8} {'STATUS':<6} {'UPTIME':<8} {'TREND':<8} {'BOT PATH'}{Colors.ENDC}"
        else:
            header = f"{Colors.BOLD}{'PID':<8} {'%CPU':<6} {'%MEM':<6} {'RSS':<8} {'THREADS':<8} {'STATUS':<6} {'UPTIME':<8} {'TREND':<8} {'BOT PATH'}{Colors.ENDC}"
        print(header)
        print("-" * 140)
        
        # Display processes
        for i, proc in enumerate(processes):
            # Filter
            if self.filter_text and self.filter_text.lower() not in proc['cmdline'].lower():
                continue
            
            # Selection highlight
            if self.selected_pid == proc['pid']:
                selection_color = Colors.BOLD + Colors.OKBLUE
            else:
                selection_color = ""
            
            # Format data
            pid = f"{proc['pid']:<8}"
            user = f"{proc['username']:<8}" if self.show_detailed else ""
            cpu_percent = f"{proc['cpu_percent']:5.1f}%"
            memory_percent = f"{proc['memory_percent']:5.1f}%"
            rss = f"{self.format_memory(proc['memory_mb'] * 1024 * 1024):<8}"
            vms = f"{self.format_memory(proc['memory_vms_mb'] * 1024 * 1024):<8}" if self.show_detailed else ""
            threads = f"{proc['num_threads']:<8}"
            status = f"{proc['status']:<6}"
            uptime = f"{self.format_uptime(proc['uptime_seconds']):<8}"
            trend = f"{proc['cpu_trend']:<8}"
            bot_path = proc['bot_path'][:50] + "..." if len(proc['bot_path']) > 50 else proc['bot_path']
            
            # Colors
            cpu_color = self.get_cpu_color(proc['cpu_percent'])
            memory_color = self.get_memory_color(proc['memory_mb'])
            status_color = self.get_status_color(proc['status'])
            trend_color = self.get_trend_color(proc['cpu_trend'])
            
            # Display row
            if self.show_detailed:
                row = f"{selection_color}{pid}{Colors.ENDC} {user} {cpu_color}{cpu_percent}{Colors.ENDC} {memory_color}{memory_percent}{Colors.ENDC} {rss} {vms} {threads} {status_color}{status}{Colors.ENDC} {uptime} {trend_color}{trend}{Colors.ENDC} {bot_path}"
            else:
                row = f"{selection_color}{pid}{Colors.ENDC} {cpu_color}{cpu_percent}{Colors.ENDC} {memory_color}{memory_percent}{Colors.ENDC} {rss} {threads} {status_color}{status}{Colors.ENDC} {uptime} {trend_color}{trend}{Colors.ENDC} {bot_path}"
            print(row)
    
    def display_process_details(self, process):
        """Display detailed information for a specific process"""
        if not process:
            return
        
        print(f"\n{Colors.BOLD}🔍 DETAILED PROCESS INFORMATION{Colors.ENDC}")
        print("-" * 80)
        print(f"PID: {process['pid']}")
        print(f"Name: {process['name']}")
        print(f"User: {process['username']}")
        print(f"Command: {process['cmdline']}")
        print(f"Status: {process['status']}")
        print(f"Uptime: {self.format_uptime(process['uptime_seconds'])}")
        print(f"Threads: {process['num_threads']}")
        print(f"CPU Affinity: {process['cpu_affinity']}")
        print(f"CPU Times - User: {process['cpu_times']['user']:.2f}s, System: {process['cpu_times']['system']:.2f}s")
        print(f"Memory - RSS: {self.format_memory(process['memory_mb'] * 1024 * 1024)}, VMS: {self.format_memory(process['memory_vms_mb'] * 1024 * 1024)}")
        print(f"CPU Trend: {process['cpu_trend']}")
        print(f"CPU History: {self.cpu_history[process['pid']]}")
    
    def display_help(self):
        """Display help information"""
        print(f"\n{Colors.BOLD}{Colors.HEADER}📖 CPU & RAM PROCESS MONITOR HELP{Colors.ENDC}")
        print("-" * 80)
        print(f"{Colors.BOLD}Keyboard Shortcuts:{Colors.ENDC}")
        print("h - Show/hide this help")
        print("q - Quit")
        print("r - Refresh now")
        print("c - Sort by CPU usage")
        print("m - Sort by memory usage")
        print("p - Sort by PID")
        print("t - Sort by uptime")
        print("n - Sort by thread count")
        print("d - Toggle detailed view")
        print("f - Filter processes (type to search)")
        print("↑/↓ - Navigate process list")
        print("Enter - Show detailed info for selected process")
        print("k - Kill selected process")
        print("R - Restart selected process")
        print("s - Save current view to file")
        print()
        print(f"{Colors.BOLD}Status Codes:{Colors.ENDC}")
        print("R - Running")
        print("S - Sleeping")
        print("D - Uninterruptible")
        print("Z - Zombie")
        print("T - Stopped")
        print("I - Idle")
        print()
        print(f"{Colors.BOLD}Color Coding:{Colors.ENDC}")
        print("🟢 Green - Normal/Low usage")
        print("🟡 Yellow - Moderate usage")
        print("🔴 Red - High usage")
        print()
        print(f"{Colors.BOLD}CPU Trend:{Colors.ENDC}")
        print("increasing - CPU usage is rising")
        print("decreasing - CPU usage is falling")
        print("stable - CPU usage is steady")
        print()
    
    def get_key(self):
        """Get keyboard input (non-blocking)"""
        import select
        import tty
        import termios
        
        if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
            return sys.stdin.read(1)
        return None
    
    def handle_input(self):
        """Handle keyboard input"""
        key = self.get_key()
        if not key:
            return
        
        if key == 'q':
            self.running = False
        elif key == 'h':
            self.show_help = not self.show_help
        elif key == 'r':
            pass  # Refresh happens automatically
        elif key == 'c':
            self.sort_key = 'cpu_percent'
            self.sort_reverse = not self.sort_reverse
        elif key == 'm':
            self.sort_key = 'memory_mb'
            self.sort_reverse = not self.sort_reverse
        elif key == 'p':
            self.sort_key = 'pid'
            self.sort_reverse = not self.sort_reverse
        elif key == 't':
            self.sort_key = 'uptime'
            self.sort_reverse = not self.sort_reverse
        elif key == 'n':
            self.sort_key = 'threads'
            self.sort_reverse = not self.sort_reverse
        elif key == 'd':
            self.show_detailed = not self.show_detailed
        elif key == 'f':
            self.filter_text = input("Filter: ")
        elif key == '\x1b':  # Escape sequence
            # Handle arrow keys
            next_key = self.get_key()
            if next_key == '[':
                arrow_key = self.get_key()
                if arrow_key == 'A':  # Up arrow
                    pass  # Navigate up
                elif arrow_key == 'B':  # Down arrow
                    pass  # Navigate down
        elif key == '\n':  # Enter
            if self.selected_pid:
                # Find the selected process
                for proc in self.get_process_info():
                    if proc['pid'] == self.selected_pid:
                        self.display_process_details(proc)
                        break
        elif key == 'k':
            if self.selected_pid:
                self.kill_process(self.selected_pid)
        elif key == 'R':
            if self.selected_pid:
                self.restart_process(self.selected_pid)
        elif key == 's':
            self.save_current_view()
    
    def kill_process(self, pid):
        """Kill selected process"""
        try:
            process = psutil.Process(pid)
            process.terminate()
            print(f"{Colors.WARNING}⚠️  Process {pid} terminated{Colors.ENDC}")
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            print(f"{Colors.FAIL}❌ Cannot kill process {pid}: {e}{Colors.ENDC}")
    
    def restart_process(self, pid):
        """Restart selected process"""
        try:
            process = psutil.Process(pid)
            cmdline = process.cmdline()
            process.terminate()
            time.sleep(1)
            # Restart process
            subprocess.Popen(cmdline)
            print(f"{Colors.OKGREEN}✅ Process {pid} restarted{Colors.ENDC}")
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            print(f"{Colors.FAIL}❌ Cannot restart process {pid}: {e}{Colors.ENDC}")
    
    def save_current_view(self):
        """Save current process view to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"process_monitor_{timestamp}.txt"
            
            with open(filename, 'w') as f:
                f.write(f"Process Monitor Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 80 + "\n\n")
                
                # System info
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
                f.write(f"System CPU: {cpu_percent:.1f}%\n")
                f.write(f"System Memory: {memory.percent:.1f}%\n\n")
                
                # Process info
                processes = self.get_process_info()
                processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
                
                f.write("Processes (sorted by CPU):\n")
                f.write("-" * 80 + "\n")
                for proc in processes:
                    f.write(f"PID: {proc['pid']}, CPU: {proc['cpu_percent']:.1f}%, "
                           f"Memory: {proc['memory_mb']:.1f}MB, "
                           f"Status: {proc['status']}, "
                           f"Uptime: {self.format_uptime(proc['uptime_seconds'])}, "
                           f"Bot: {proc['bot_path']}\n")
            
            print(f"{Colors.OKGREEN}✅ Current view saved to {filename}{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.FAIL}❌ Error saving view: {e}{Colors.ENDC}")
    
    def get_refresh_interval(self):
        """Get refresh interval from user input"""
        try:
            user_input = input(f"\n{Colors.OKCYAN}Enter refresh interval in seconds (or press Enter for {self.refresh_interval}s): {Colors.ENDC}").strip()
            if user_input:
                interval = float(user_input)
                if interval > 0:
                    self.refresh_interval = interval
                    print(f"{Colors.OKGREEN}✅ Refresh interval set to {self.refresh_interval} seconds{Colors.ENDC}")
                else:
                    print(f"{Colors.WARNING}⚠️  Invalid interval, using default {self.refresh_interval} seconds{Colors.ENDC}")
            else:
                print(f"{Colors.OKCYAN}Using default refresh interval: {self.refresh_interval} seconds{Colors.ENDC}")
        except ValueError:
            print(f"{Colors.WARNING}⚠️  Invalid input, using default {self.refresh_interval} seconds{Colors.ENDC}")

    def run(self):
        """Main monitoring loop"""
        print(f"{Colors.OKGREEN}🚀 Starting CPU & RAM Process Monitor...{Colors.ENDC}")
        print(f"{Colors.OKCYAN}This monitor shows detailed CPU and RAM usage for all processes{Colors.ENDC}")
        
        # Get refresh interval
        self.get_refresh_interval()
        
        print(f"{Colors.OKCYAN}Press 'h' for help, 'q' to quit{Colors.ENDC}")
        time.sleep(2)
        
        while self.running:
            try:
                # Clear screen
                os.system('clear')
                
                # Display system header
                self.display_system_header()
                
                # Get all Python processes
                processes = self.get_process_info()
                
                # Display processes
                self.display_processes(processes)
                
                # Display help if requested
                if self.show_help:
                    self.display_help()
                
                # Display controls
                print(f"\n{Colors.BOLD}CONTROLS: h=help, q=quit, c=cpu sort, m=memory sort, d=detailed, f=filter, Enter=details, k=kill, R=restart, s=save{Colors.ENDC}")
                
                # Handle input
                self.handle_input()
                
                # Wait for next refresh
                time.sleep(self.refresh_interval)
                
            except KeyboardInterrupt:
                self.running = False
            except Exception as e:
                print(f"{Colors.FAIL}❌ Error: {e}{Colors.ENDC}")
                time.sleep(1)
        
        self.cleanup()

def main():
    """Main function"""
    monitor = CPU_RAM_ProcessMonitor()
    monitor.run()

if __name__ == "__main__":
    main()
