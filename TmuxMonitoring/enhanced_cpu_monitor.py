#!/usr/bin/env python3
"""
ENHANCED CPU & RAM MONITOR
Shows which processes are using which CPU cores with detailed analysis
Supports custom refresh intervals and comprehensive process tracking
"""

import psutil
import os
import time
import sys
import signal
from datetime import datetime
from collections import defaultdict

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
    DIM = '\033[2m'

class EnhancedCPUMonitor:
    def __init__(self):
        self.running = True
        self.refresh_interval = 3  # Default 3 seconds
        self.cpu_history = defaultdict(list)
        self.max_history = 5
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        self.running = False
        os.system('clear')
        print(f"{Colors.GREEN}✅ Enhanced CPU Monitor stopped{Colors.ENDC}")
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
    
    def get_all_processes(self):
        """Get all processes with detailed CPU and core information"""
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_info', 'status', 'create_time', 'num_threads', 'cpu_affinity', 'username']):
            try:
                proc_info = proc.info
                
                # Calculate uptime
                uptime_seconds = time.time() - proc_info['create_time']
                
                # Get memory in MB
                memory_mb = proc_info['memory_info'].rss / (1024 * 1024)
                
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
                
                # Store CPU history for trend analysis
                pid = proc_info['pid']
                cpu_percent = proc_info['cpu_percent'] or 0
                self.cpu_history[pid].append(cpu_percent)
                if len(self.cpu_history[pid]) > self.max_history:
                    self.cpu_history[pid].pop(0)
                
                # Calculate CPU trend
                cpu_trend = self.calculate_trend(self.cpu_history[pid])
                
                # Extract process name
                cmdline = ' '.join(proc_info['cmdline']) if proc_info['cmdline'] else 'Unknown'
                process_name = self.extract_process_name(proc_info['name'], cmdline)
                
                process_data = {
                    'pid': pid,
                    'name': proc_info['name'],
                    'process_name': process_name,
                    'cmdline': cmdline,
                    'cpu_percent': cpu_percent,
                    'memory_mb': memory_mb,
                    'memory_percent': proc_info['memory_info'].rss / psutil.virtual_memory().total * 100,
                    'status': proc_info['status'],
                    'uptime_seconds': uptime_seconds,
                    'threads': proc_info['num_threads'],
                    'cpu_affinity': proc_info['cpu_affinity'],
                    'username': proc_info['username'],
                    'cpu_times': cpu_times_info,
                    'cpu_trend': cpu_trend
                }
                
                processes.append(process_data)
                
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        return processes
    
    def extract_process_name(self, name, cmdline):
        """Extract meaningful process name"""
        if 'python' in name.lower():
            # Try to extract script name from command line
            if cmdline and cmdline != 'Unknown':
                parts = cmdline.split()
                for part in parts:
                    if part.endswith('.py'):
                        return os.path.basename(part)
            return f"python ({name})"
        return name
    
    def calculate_trend(self, cpu_history):
        """Calculate CPU usage trend"""
        if len(cpu_history) < 2:
            return "stable"
        
        recent_avg = sum(cpu_history[-2:]) / 2
        older_avg = sum(cpu_history[:-2]) / max(1, len(cpu_history) - 2) if len(cpu_history) > 2 else recent_avg
        
        if recent_avg > older_avg * 1.3:
            return "rising"
        elif recent_avg < older_avg * 0.7:
            return "falling"
        else:
            return "stable"
    
    def display_system_header(self):
        """Display system-wide information"""
        # System CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_per_core = psutil.cpu_percent(interval=0.1, percpu=True)
        
        # System Memory
        memory = psutil.virtual_memory()
        
        # Load average
        load_avg = os.getloadavg()
        
        print(f"{Colors.BOLD}{Colors.WHITE}{'='*140}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.WHITE}🖥️  ENHANCED CPU & RAM MONITOR - DETAILED CORE ANALYSIS{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.WHITE}{'='*140}{Colors.ENDC}")
        
        # Overall system status
        cpu_color = self.get_color(cpu_percent, [50, 80, 95])
        mem_color = self.get_color(memory.percent, [70, 85, 95])
        
        print(f"{Colors.BOLD}🖥️  SYSTEM STATUS:{Colors.ENDC}")
        print(f"Overall CPU: {cpu_color}{cpu_percent:5.1f}%{Colors.ENDC}  "
              f"Memory: {mem_color}{memory.percent:5.1f}%{Colors.ENDC}  "
              f"Load: {load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f}")
        
        # Per-core CPU usage (16 cores)
        print(f"\n{Colors.BOLD}⚡ CPU CORES (16 cores):{Colors.ENDC}")
        for i in range(0, len(cpu_per_core), 8):  # 8 cores per line
            core_line = ""
            for j in range(i, min(i+8, len(cpu_per_core))):
                core_usage = cpu_per_core[j]
                core_color = self.get_color(core_usage, [50, 80, 95])
                core_line += f"{core_color}[{core_usage:4.1f}%]{Colors.ENDC} "
            print(f"Cores {i+1:2d}-{min(i+8, len(cpu_per_core)):2d}: {core_line}")
        
        # Memory breakdown
        print(f"\n{Colors.BOLD}🧠 MEMORY:{Colors.ENDC}")
        print(f"Total: {self.format_memory(memory.total)}  "
              f"Used: {self.format_memory(memory.used)}  "
              f"Free: {self.format_memory(memory.free)}  "
              f"Available: {self.format_memory(memory.available)}")
        print()
    
    def display_top_processes(self, processes):
        """Display top processes by CPU usage"""
        if not processes:
            print(f"{Colors.YELLOW}⚠️  No processes found{Colors.ENDC}")
            return
        
        # Sort by CPU usage (highest first)
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        
        # Show top 20 processes
        top_processes = processes[:20]
        
        # Header
        print(f"{Colors.BOLD}{'PID':<8} {'PROCESS':<25} {'%CPU':<6} {'%MEM':<6} {'RAM':<8} {'THREADS':<8} {'STATUS':<6} {'UPTIME':<8} {'TREND':<8} {'CORES'}{Colors.ENDC}")
        print("-" * 140)
        
        # Display processes
        for proc in top_processes:
            # Colors based on usage
            cpu_color = self.get_color(proc['cpu_percent'], [20, 50, 80])
            mem_color = self.get_color(proc['memory_mb'], [500, 1000, 2000])
            status_color = Colors.GREEN if proc['status'] == 'R' else Colors.YELLOW if proc['status'] == 'S' else Colors.RED
            
            # Trend color
            trend_color = Colors.RED if proc['cpu_trend'] == 'rising' else Colors.GREEN if proc['cpu_trend'] == 'falling' else Colors.CYAN
            
            # Format data
            pid = f"{proc['pid']:<8}"
            process_name = f"{proc['process_name']:<25}"
            cpu_percent = f"{proc['cpu_percent']:5.1f}%"
            mem_percent = f"{proc['memory_percent']:5.1f}%"
            ram = f"{self.format_memory(proc['memory_mb'] * 1024 * 1024):<8}"
            threads = f"{proc['threads']:<8}"
            status = f"{proc['status']:<6}"
            uptime = f"{self.format_uptime(proc['uptime_seconds']):<8}"
            trend = f"{proc['cpu_trend']:<8}"
            
            # CPU affinity (cores)
            if proc['cpu_affinity']:
                cores = f"{len(proc['cpu_affinity'])} cores"
            else:
                cores = "all cores"
            
            # Display row
            print(f"{pid} {process_name} {cpu_color}{cpu_percent}{Colors.ENDC} {mem_color}{mem_percent}{Colors.ENDC} {ram} {threads} {status_color}{status}{Colors.ENDC} {uptime} {trend_color}{trend}{Colors.ENDC} {cores}")
    
    def display_core_analysis(self, processes):
        """Display detailed core usage analysis"""
        print(f"\n{Colors.BOLD}⚡ DETAILED CORE USAGE ANALYSIS:{Colors.ENDC}")
        
        # Analyze core usage
        core_usage = defaultdict(list)
        total_cpu_usage = 0
        
        for proc in processes:
            total_cpu_usage += proc['cpu_percent']
            if proc['cpu_affinity']:
                for core in proc['cpu_affinity']:
                    core_usage[core].append({
                        'process_name': proc['process_name'],
                        'cpu_percent': proc['cpu_percent'],
                        'pid': proc['pid']
                    })
        
        # Show core distribution
        if core_usage:
            print("Cores with specific process assignments:")
            for core in sorted(core_usage.keys()):
                procs_on_core = core_usage[core]
                total_core_cpu = sum(proc['cpu_percent'] for proc in procs_on_core)
                proc_list = ', '.join([f"{proc['process_name']}({proc['cpu_percent']:.1f}%)" for proc in procs_on_core])
                print(f"  Core {core+1:2d}: {total_core_cpu:5.1f}% total - {proc_list}")
        else:
            print("  All processes can use any core (no specific affinity set)")
        
        print(f"\nTotal Process CPU Usage: {total_cpu_usage:.1f}%")
        print(f"Average CPU per Process: {total_cpu_usage/len(processes):.1f}%")
    
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
        
        # Count by trend
        rising_count = sum(1 for proc in processes if proc['cpu_trend'] == 'rising')
        falling_count = sum(1 for proc in processes if proc['cpu_trend'] == 'falling')
        stable_count = sum(1 for proc in processes if proc['cpu_trend'] == 'stable')
        
        # Top consumers
        top_cpu = max(processes, key=lambda x: x['cpu_percent'])
        top_memory = max(processes, key=lambda x: x['memory_mb'])
        
        print(f"\n{Colors.BOLD}📊 SYSTEM SUMMARY:{Colors.ENDC}")
        print(f"Total Processes: {len(processes)}")
        print(f"Total CPU Usage: {total_cpu:.1f}%")
        print(f"Total Memory Usage: {self.format_memory(total_memory * 1024 * 1024)}")
        print(f"Total Threads: {total_threads}")
        print(f"Status - Running: {running_count}, Sleeping: {sleeping_count}")
        print(f"CPU Trends - Rising: {rising_count}, Falling: {falling_count}, Stable: {stable_count}")
        
        print(f"\n{Colors.BOLD}🔝 TOP CONSUMERS:{Colors.ENDC}")
        print(f"Highest CPU: {top_cpu['process_name']} ({top_cpu['cpu_percent']:.1f}%)")
        print(f"Highest Memory: {top_memory['process_name']} ({self.format_memory(top_memory['memory_mb'] * 1024 * 1024)})")
    
    def get_refresh_interval(self):
        """Get refresh interval from user input"""
        try:
            user_input = input(f"\n{Colors.CYAN}Enter refresh interval in seconds (or press Enter for {self.refresh_interval}s): {Colors.ENDC}").strip()
            if user_input:
                interval = float(user_input)
                if interval > 0:
                    self.refresh_interval = interval
                    print(f"{Colors.GREEN}✅ Refresh interval set to {self.refresh_interval} seconds{Colors.ENDC}")
                else:
                    print(f"{Colors.YELLOW}⚠️  Invalid interval, using default {self.refresh_interval} seconds{Colors.ENDC}")
            else:
                print(f"{Colors.CYAN}Using default refresh interval: {self.refresh_interval} seconds{Colors.ENDC}")
        except ValueError:
            print(f"{Colors.YELLOW}⚠️  Invalid input, using default {self.refresh_interval} seconds{Colors.ENDC}")
    
    def run(self):
        """Main monitoring loop"""
        print(f"{Colors.GREEN}🚀 Starting Enhanced CPU & RAM Monitor...{Colors.ENDC}")
        print(f"{Colors.CYAN}This monitor shows which processes are using which CPU cores{Colors.ENDC}")
        
        # Get refresh interval
        self.get_refresh_interval()
        
        print(f"{Colors.CYAN}Press Ctrl+C to quit{Colors.ENDC}")
        time.sleep(2)
        
        while self.running:
            try:
                # Clear screen
                os.system('clear')
                
                # Display system header
                self.display_system_header()
                
                # Get all processes
                processes = self.get_all_processes()
                
                # Display top processes
                self.display_top_processes(processes)
                
                # Display core analysis
                self.display_core_analysis(processes)
                
                # Display summary
                self.display_summary(processes)
                
                # Display timestamp and controls
                print(f"\n{Colors.DIM}Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}")
                print(f"{Colors.DIM}Refresh interval: {self.refresh_interval}s | Press Ctrl+C to quit{Colors.ENDC}")
                
                # Wait for next refresh
                time.sleep(self.refresh_interval)
                
            except KeyboardInterrupt:
                self.running = False
            except Exception as e:
                print(f"{Colors.RED}❌ Error: {e}{Colors.ENDC}")
                time.sleep(1)
        
        self.signal_handler(None, None)

def main():
    """Main function"""
    monitor = EnhancedCPUMonitor()
    monitor.run()

if __name__ == "__main__":
    main()
