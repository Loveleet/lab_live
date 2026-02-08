#!/usr/bin/env python3
"""
HTOP-STYLE BOT MONITOR
Interactive real-time monitoring of all bots from botsBackup.txt
Shows complete process details: CPU cores, memory, threads, and everything else
"""

import psutil
import os
import time
import sys
import subprocess
from datetime import datetime
import threading
import signal

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

class HtopStyleBotMonitor:
    def __init__(self):
        self.running = True
        self.sort_key = 'cpu'  # Default sort by CPU
        self.sort_reverse = True  # Descending order
        self.filter_text = ""
        self.selected_pid = None
        self.show_help = False
        self.show_threads = False
        self.show_cores = False
        self.refresh_interval = 2  # seconds
        
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
        print(f"{Colors.OKGREEN}✅ HTOP-style bot monitor stopped{Colors.ENDC}")
    
    def read_bots_backup_file(self):
        """Read bot paths from botsBackup.txt"""
        try:
            with open('/root/botsBackup.txt', 'r') as f:
                bots = []
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Extract bot path (before any | or space)
                        bot_path = line.split('|')[0].split()[0]
                        if bot_path.endswith('.py'):
                            bots.append(bot_path)
                return bots
        except FileNotFoundError:
            print(f"{Colors.FAIL}❌ botsBackup.txt not found{Colors.ENDC}")
            return []
        except Exception as e:
            print(f"{Colors.FAIL}❌ Error reading botsBackup.txt: {e}{Colors.ENDC}")
            return []
    
    def get_process_info(self, bot_path):
        """Get detailed process information for a bot"""
        try:
            # Find process by command line
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_info', 'memory_percent', 'status', 'create_time', 'num_threads', 'cpu_affinity']):
                try:
                    proc_info = proc.info
                    if proc_info['cmdline'] and bot_path in ' '.join(proc_info['cmdline']):
                        return {
                            'pid': proc_info['pid'],
                            'name': proc_info['name'],
                            'cmdline': ' '.join(proc_info['cmdline']),
                            'cpu_percent': proc_info['cpu_percent'] or 0,
                            'memory_info': proc_info['memory_info'],
                            'memory_percent': proc_info['memory_percent'] or 0,
                            'status': proc_info['status'],
                            'create_time': proc_info['create_time'],
                            'num_threads': proc_info['num_threads'],
                            'cpu_affinity': proc_info['cpu_affinity'],
                            'bot_path': bot_path
                        }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return None
        except Exception as e:
            return None
    
    def get_thread_info(self, pid):
        """Get detailed thread information for a process"""
        try:
            process = psutil.Process(pid)
            threads = process.threads()
            return threads
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return []
    
    def get_core_usage(self, pid):
        """Get CPU core usage for a process"""
        try:
            process = psutil.Process(pid)
            # Get CPU affinity
            affinity = process.cpu_affinity()
            return affinity
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return []
    
    def format_uptime(self, create_time):
        """Format process uptime"""
        uptime_seconds = time.time() - create_time
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
            return f"{memory_bytes}B"
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
    
    def get_memory_color(self, memory_percent):
        """Get color for memory usage"""
        if memory_percent > 5:
            return Colors.FAIL
        elif memory_percent > 2:
            return Colors.WARNING
        elif memory_percent > 1:
            return Colors.OKGREEN
        else:
            return Colors.OKCYAN
    
    def display_header(self):
        """Display system header"""
        # Get system info
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        load_avg = os.getloadavg()
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        
        print(f"{Colors.BOLD}{Colors.HEADER}{'='*120}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}🤖 HTOP-STYLE BOT MONITOR - REAL-TIME PROCESS MONITORING{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}{'='*120}{Colors.ENDC}")
        
        # System status
        print(f"{Colors.BOLD}🖥️  SYSTEM STATUS:{Colors.ENDC}")
        print(f"CPU: {self.get_cpu_color(cpu_percent)}[{cpu_percent:5.1f}%]{Colors.ENDC}  "
              f"Memory: {self.get_memory_color(memory.percent)}[{memory.percent:5.1f}%]{Colors.ENDC}  "
              f"Load: {load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f}  "
              f"Uptime: {str(uptime).split('.')[0]}")
        print()
    
    def display_processes(self, processes):
        """Display process list in htop style"""
        if not processes:
            print(f"{Colors.WARNING}⚠️  No bot processes found{Colors.ENDC}")
            return
        
        # Header
        header = f"{Colors.BOLD}{'PID':<8} {'USER':<8} {'%CPU':<6} {'%MEM':<6} {'VSZ':<8} {'RSS':<8} {'TTY':<8} {'STAT':<6} {'START':<8} {'TIME':<8} {'COMMAND'}{Colors.ENDC}"
        print(header)
        print("-" * 120)
        
        # Sort processes
        if self.sort_key == 'cpu':
            processes.sort(key=lambda x: x['cpu_percent'], reverse=self.sort_reverse)
        elif self.sort_key == 'memory':
            processes.sort(key=lambda x: x['memory_percent'], reverse=self.sort_reverse)
        elif self.sort_key == 'pid':
            processes.sort(key=lambda x: x['pid'], reverse=self.sort_reverse)
        elif self.sort_key == 'time':
            processes.sort(key=lambda x: x['create_time'], reverse=self.sort_reverse)
        
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
            user = "root    "  # Most bots run as root
            cpu_percent = f"{proc['cpu_percent']:5.1f}%"
            memory_percent = f"{proc['memory_percent']:5.1f}%"
            vsz = f"{self.format_memory(proc['memory_info'].vms):<8}"
            rss = f"{self.format_memory(proc['memory_info'].rss):<8}"
            tty = "pts/??  "  # We don't track TTY for bots
            stat = f"{proc['status']:<6}"
            start = f"{self.format_uptime(proc['create_time']):<8}"
            time_used = "00:00:00"  # We don't track CPU time
            command = proc['cmdline'][:50] + "..." if len(proc['cmdline']) > 50 else proc['cmdline']
            
            # Colors
            cpu_color = self.get_cpu_color(proc['cpu_percent'])
            memory_color = self.get_memory_color(proc['memory_percent'])
            status_color = self.get_status_color(proc['status'])
            
            # Display row
            row = f"{selection_color}{pid}{Colors.ENDC} {user} {cpu_color}{cpu_percent}{Colors.ENDC} {memory_color}{memory_percent}{Colors.ENDC} {vsz} {rss} {tty} {status_color}{stat}{Colors.ENDC} {start} {time_used} {command}"
            print(row)
    
    def display_threads(self, pid):
        """Display thread information for selected process"""
        threads = self.get_thread_info(pid)
        if not threads:
            print(f"{Colors.WARNING}⚠️  No thread information available{Colors.ENDC}")
            return
        
        print(f"\n{Colors.BOLD}🧵 THREAD INFORMATION (PID: {pid}){Colors.ENDC}")
        print("-" * 80)
        print(f"{Colors.BOLD}{'TID':<8} {'CPU%':<6} {'STATUS':<10} {'FUNCTION'}{Colors.ENDC}")
        print("-" * 80)
        
        for i, thread in enumerate(threads[:20]):  # Show first 20 threads
            tid = f"{thread.id:<8}"
            cpu_percent = f"{thread.cpu_percent or 0:5.1f}%"
            status = f"{thread.status:<10}"
            function = f"Thread-{i+1}"
            
            cpu_color = self.get_cpu_color(thread.cpu_percent or 0)
            status_color = self.get_status_color(thread.status)
            
            row = f"{tid} {cpu_color}{cpu_percent}{Colors.ENDC} {status_color}{status}{Colors.ENDC} {function}"
            print(row)
        
        if len(threads) > 20:
            print(f"... and {len(threads) - 20} more threads")
    
    def display_cores(self, pid):
        """Display CPU core usage for selected process"""
        cores = self.get_core_usage(pid)
        if not cores:
            print(f"{Colors.WARNING}⚠️  No core affinity information available{Colors.ENDC}")
            return
        
        print(f"\n{Colors.BOLD}⚡ CPU CORE USAGE (PID: {pid}){Colors.ENDC}")
        print("-" * 80)
        print(f"CPU Affinity: {cores}")
        print(f"Available Cores: {psutil.cpu_count()}")
        print(f"Cores Used: {len(cores)}/{psutil.cpu_count()}")
        
        # Show per-core usage
        cpu_percent = psutil.cpu_percent(interval=0.1, percpu=True)
        print(f"\n{Colors.BOLD}Per-Core CPU Usage:{Colors.ENDC}")
        for i, core_usage in enumerate(cpu_percent):
            core_color = self.get_cpu_color(core_usage)
            if i in cores:
                marker = "🔴"  # Bot can use this core
            else:
                marker = "⚪"  # Bot cannot use this core
            print(f"Core {i+1}: {core_color}[{core_usage:5.1f}%]{Colors.ENDC} {marker}")
    
    def display_help(self):
        """Display help information"""
        print(f"\n{Colors.BOLD}{Colors.HEADER}📖 HTOP-STYLE BOT MONITOR HELP{Colors.ENDC}")
        print("-" * 60)
        print(f"{Colors.BOLD}Keyboard Shortcuts:{Colors.ENDC}")
        print("h - Show/hide this help")
        print("q - Quit")
        print("r - Refresh now")
        print("s - Sort by CPU usage")
        print("m - Sort by memory usage")
        print("p - Sort by PID")
        print("t - Sort by time")
        print("f - Filter processes (type to search)")
        print("↑/↓ - Navigate process list")
        print("Enter - Show thread details for selected process")
        print("c - Show CPU core usage for selected process")
        print("k - Kill selected process")
        print("R - Restart selected process")
        print("F1 - Toggle thread view")
        print("F2 - Toggle core view")
        print("F3 - Toggle help")
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
        elif key == 's':
            self.sort_key = 'cpu'
            self.sort_reverse = not self.sort_reverse
        elif key == 'm':
            self.sort_key = 'memory'
            self.sort_reverse = not self.sort_reverse
        elif key == 'p':
            self.sort_key = 'pid'
            self.sort_reverse = not self.sort_reverse
        elif key == 't':
            self.sort_key = 'time'
            self.sort_reverse = not self.sort_reverse
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
                self.show_threads = True
        elif key == 'c':
            if self.selected_pid:
                self.show_cores = True
        elif key == 'k':
            if self.selected_pid:
                self.kill_process(self.selected_pid)
        elif key == 'R':
            if self.selected_pid:
                self.restart_process(self.selected_pid)
    
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
    
    def run(self):
        """Main monitoring loop"""
        print(f"{Colors.OKGREEN}🚀 Starting HTOP-style bot monitor...{Colors.ENDC}")
        print(f"{Colors.OKCYAN}Press 'h' for help, 'q' to quit{Colors.ENDC}")
        time.sleep(2)
        
        while self.running:
            try:
                # Clear screen
                os.system('clear')
                
                # Display header
                self.display_header()
                
                # Get bot processes
                bot_paths = self.read_bots_backup_file()
                processes = []
                for bot_path in bot_paths:
                    proc_info = self.get_process_info(bot_path)
                    if proc_info:
                        processes.append(proc_info)
                
                # Display processes
                self.display_processes(processes)
                
                # Display additional info if selected
                if self.show_threads and self.selected_pid:
                    self.display_threads(self.selected_pid)
                
                if self.show_cores and self.selected_pid:
                    self.display_cores(self.selected_pid)
                
                # Display help if requested
                if self.show_help:
                    self.display_help()
                
                # Display controls
                print(f"\n{Colors.BOLD}CONTROLS: h=help, q=quit, s=sort, f=filter, ↑↓=navigate, Enter=threads, c=cores, k=kill, R=restart{Colors.ENDC}")
                
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
    monitor = HtopStyleBotMonitor()
    monitor.run()

if __name__ == "__main__":
    main()
