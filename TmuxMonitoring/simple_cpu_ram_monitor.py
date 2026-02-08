#!/usr/bin/env python3
"""
SIMPLE CPU & RAM MONITOR FOR TRADING BOTS
Lightweight real-time monitor showing CPU and RAM usage per process
Optimized for 16-core systems with trading bot management
"""

import psutil
import os
import time
import sys
from datetime import datetime
import signal

class Colors:
    """ANSI color codes"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ENDC = '\033[0m'

class SimpleCPURAMMonitor:
    def __init__(self):
        self.running = True
        self.refresh_interval = 3  # Default 3 seconds
        self.auto_refresh = True  # Default auto refresh
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        self.running = False
        os.system('clear')
        print(f"{Colors.GREEN}✅ Monitor stopped{Colors.ENDC}")
        sys.exit(0)
    
    def get_color(self, value, thresholds):
        """Get color based on value and thresholds"""
        if value >= thresholds[2]:
            return Colors.RED
        elif value >= thresholds[1]:
            return Colors.YELLOW
        else:
            return Colors.GREEN
    
    def format_memory(self, bytes_val):
        """Format memory in MB or GB"""
        mb = bytes_val / (1024 * 1024)
        if mb >= 1024:
            return f"{mb/1024:.1f}G"
        else:
            return f"{mb:.0f}M"
    
    def format_uptime(self, seconds):
        """Format uptime"""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            return f"{seconds/60:.0f}m"
        else:
            return f"{seconds/3600:.0f}h"
    
    def get_python_processes(self):
        """Get all Python processes with detailed info"""
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_info', 'status', 'create_time', 'num_threads']):
            try:
                proc_info = proc.info
                
                # Only Python processes
                if not (proc_info['name'] and 'python' in proc_info['name'].lower()):
                    continue
                
                # Get command line
                cmdline = ' '.join(proc_info['cmdline']) if proc_info['cmdline'] else 'Unknown'
                
                # Extract bot name from command line
                bot_name = "Unknown"
                if proc_info['cmdline']:
                    for arg in proc_info['cmdline']:
                        if arg.endswith('.py'):
                            bot_name = os.path.basename(arg)
                            break
                
                # Calculate uptime
                uptime_seconds = time.time() - proc_info['create_time']
                
                # Get memory in MB
                memory_mb = proc_info['memory_info'].rss / (1024 * 1024)
                
                processes.append({
                    'pid': proc_info['pid'],
                    'name': proc_info['name'],
                    'bot_name': bot_name,
                    'cmdline': cmdline,
                    'cpu_percent': proc_info['cpu_percent'] or 0,
                    'memory_mb': memory_mb,
                    'memory_percent': proc_info['memory_info'].rss / psutil.virtual_memory().total * 100,
                    'status': proc_info['status'],
                    'uptime_seconds': uptime_seconds,
                    'threads': proc_info['num_threads']
                })
                
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        return processes
    
    def display_system_info(self):
        """Display system-wide CPU and RAM information"""
        # System CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_per_core = psutil.cpu_percent(interval=0.1, percpu=True)
        
        # System Memory
        memory = psutil.virtual_memory()
        
        # Load average
        load_avg = os.getloadavg()
        
        print(f"{Colors.BOLD}{Colors.WHITE}{'='*100}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.WHITE}🖥️  CPU & RAM MONITOR - 16-CORE TRADING BOT SYSTEM{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.WHITE}{'='*100}{Colors.ENDC}")
        
        # Overall system status
        cpu_color = self.get_color(cpu_percent, [50, 80, 95])
        mem_color = self.get_color(memory.percent, [70, 85, 95])
        
        print(f"{Colors.BOLD}SYSTEM STATUS:{Colors.ENDC}")
        print(f"Overall CPU: {cpu_color}{cpu_percent:5.1f}%{Colors.ENDC}  "
              f"Memory: {mem_color}{memory.percent:5.1f}%{Colors.ENDC}  "
              f"Load: {load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f}")
        
        # Per-core CPU usage (16 cores)
        print(f"\n{Colors.BOLD}CPU CORES (16 cores):{Colors.ENDC}")
        for i in range(0, len(cpu_per_core), 8):  # 8 cores per line
            core_line = ""
            for j in range(i, min(i+8, len(cpu_per_core))):
                core_usage = cpu_per_core[j]
                core_color = self.get_color(core_usage, [50, 80, 95])
                core_line += f"{core_color}[{core_usage:4.1f}%]{Colors.ENDC} "
            print(f"Cores {i+1:2d}-{min(i+8, len(cpu_per_core)):2d}: {core_line}")
        
        # Memory breakdown
        print(f"\n{Colors.BOLD}MEMORY:{Colors.ENDC}")
        print(f"Total: {self.format_memory(memory.total)}  "
              f"Used: {self.format_memory(memory.used)}  "
              f"Free: {self.format_memory(memory.free)}  "
              f"Available: {self.format_memory(memory.available)}")
        print()
    
    def display_processes(self, processes):
        """Display process list"""
        if not processes:
            print(f"{Colors.YELLOW}⚠️  No Python processes found{Colors.ENDC}")
            return
        
        # Sort by CPU usage (highest first)
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        
        # Header
        print(f"{Colors.BOLD}{'PID':<8} {'BOT NAME':<25} {'%CPU':<6} {'%MEM':<6} {'RAM':<8} {'THREADS':<8} {'STATUS':<6} {'UPTIME':<8} {'COMMAND'}{Colors.ENDC}")
        print("-" * 100)
        
        # Display processes
        for proc in processes:
            # Colors based on usage
            cpu_color = self.get_color(proc['cpu_percent'], [20, 50, 80])
            mem_color = self.get_color(proc['memory_mb'], [500, 1000, 2000])
            status_color = Colors.GREEN if proc['status'] == 'R' else Colors.YELLOW if proc['status'] == 'S' else Colors.RED
            
            # Format data
            pid = f"{proc['pid']:<8}"
            bot_name = f"{proc['bot_name']:<25}"
            cpu_percent = f"{proc['cpu_percent']:5.1f}%"
            mem_percent = f"{proc['memory_percent']:5.1f}%"
            ram = f"{self.format_memory(proc['memory_mb'] * 1024 * 1024):<8}"
            threads = f"{proc['threads']:<8}"
            status = f"{proc['status']:<6}"
            uptime = f"{self.format_uptime(proc['uptime_seconds']):<8}"
            command = proc['cmdline'][:30] + "..." if len(proc['cmdline']) > 30 else proc['cmdline']
            
            # Display row
            print(f"{pid} {bot_name} {cpu_color}{cpu_percent}{Colors.ENDC} {mem_color}{mem_percent}{Colors.ENDC} {ram} {threads} {status_color}{status}{Colors.ENDC} {uptime} {command}")
    
    def display_summary(self, processes):
        """Display summary statistics"""
        if not processes:
            return
        
        # Calculate totals
        total_cpu = sum(proc['cpu_percent'] for proc in processes)
        total_memory = sum(proc['memory_mb'] for proc in processes)
        total_threads = sum(proc['threads'] for proc in processes)
        
        # Count by status
        running_count = sum(1 for proc in processes if proc['status'] == 'R')
        sleeping_count = sum(1 for proc in processes if proc['status'] == 'S')
        
        print(f"\n{Colors.BOLD}SUMMARY:{Colors.ENDC}")
        print(f"Total Python Processes: {len(processes)}")
        print(f"Total CPU Usage: {total_cpu:.1f}%")
        print(f"Total Memory Usage: {self.format_memory(total_memory * 1024 * 1024)}")
        print(f"Total Threads: {total_threads}")
        print(f"Running: {running_count}, Sleeping: {sleeping_count}")
        
        # Top consumers
        if processes:
            top_cpu = max(processes, key=lambda x: x['cpu_percent'])
            top_memory = max(processes, key=lambda x: x['memory_mb'])
            
            print(f"\n{Colors.BOLD}TOP CONSUMERS:{Colors.ENDC}")
            print(f"Highest CPU: {top_cpu['bot_name']} ({top_cpu['cpu_percent']:.1f}%)")
            print(f"Highest Memory: {top_memory['bot_name']} ({self.format_memory(top_memory['memory_mb'] * 1024 * 1024)})")
    
    def get_refresh_interval(self):
        """Get refresh interval from user input"""
        try:
            user_input = input(f"\n{Colors.CYAN}Enter refresh interval in seconds (or press Enter for manual refresh): {Colors.ENDC}").strip()
            if user_input:
                interval = float(user_input)
                if interval > 0:
                    self.refresh_interval = interval
                    self.auto_refresh = True
                    print(f"{Colors.GREEN}✅ Auto-refresh set to {self.refresh_interval} seconds{Colors.ENDC}")
                else:
                    print(f"{Colors.YELLOW}⚠️  Invalid interval, using manual refresh{Colors.ENDC}")
                    self.auto_refresh = False
            else:
                self.auto_refresh = False
                print(f"{Colors.CYAN}Manual refresh mode - press Enter to refresh{Colors.ENDC}")
        except ValueError:
            print(f"{Colors.YELLOW}⚠️  Invalid input, using manual refresh{Colors.ENDC}")
            self.auto_refresh = False

    def run(self):
        """Main monitoring loop"""
        print(f"{Colors.GREEN}🚀 Starting Simple CPU & RAM Monitor...{Colors.ENDC}")
        print(f"{Colors.CYAN}This monitor shows CPU and RAM usage for all processes{Colors.ENDC}")
        
        # Get refresh interval
        self.get_refresh_interval()
        
        print(f"{Colors.CYAN}Press Ctrl+C to quit{Colors.ENDC}")
        time.sleep(2)
        
        while self.running:
            try:
                # Clear screen
                os.system('clear')
                
                # Display system info
                self.display_system_info()
                
                # Get and display processes
                processes = self.get_python_processes()
                self.display_processes(processes)
                
                # Display summary
                self.display_summary(processes)
                
                # Display timestamp and controls
                print(f"\n{Colors.DIM}Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}")
                if self.auto_refresh:
                    print(f"{Colors.DIM}Auto-refresh every {self.refresh_interval}s | Press Ctrl+C to quit{Colors.ENDC}")
                    # Wait for next refresh
                    time.sleep(self.refresh_interval)
                else:
                    print(f"{Colors.DIM}Manual refresh mode | Press Enter to refresh, Ctrl+C to quit{Colors.ENDC}")
                    # Wait for user to press Enter
                    input()
                
            except KeyboardInterrupt:
                self.running = False
            except Exception as e:
                print(f"{Colors.RED}❌ Error: {e}{Colors.ENDC}")
                time.sleep(1)
        
        self.signal_handler(None, None)

def main():
    """Main function"""
    monitor = SimpleCPURAMMonitor()
    monitor.run()

if __name__ == "__main__":
    main()
