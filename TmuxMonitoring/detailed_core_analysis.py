#!/usr/bin/env python3
"""
DETAILED CORE ANALYSIS REPORT
Shows which processes are using which CPU cores with detailed breakdown
Groups processes by name and shows total CPU usage per process
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
    DIM = '\033[2m'
    ENDC = '\033[0m'

class DetailedCoreAnalysis:
    def __init__(self):
        self.running = True
        self.refresh_interval = 3
        self.auto_refresh = True
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        self.running = False
        os.system('clear')
        print(f"{Colors.GREEN}✅ Detailed Core Analysis stopped{Colors.ENDC}")
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
    
    def extract_process_name(self, name, cmdline):
        """Extract meaningful process name"""
        if 'python' in name.lower():
            if cmdline and cmdline != 'Unknown':
                parts = cmdline.split()
                for part in parts:
                    if part.endswith('.py'):
                        return os.path.basename(part)
            return f"python ({name})"
        return name
    
    def get_all_processes(self):
        """Get all processes with detailed information"""
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_info', 'status', 'create_time', 'num_threads', 'cpu_affinity', 'username']):
            try:
                proc_info = proc.info
                
                # Calculate uptime
                uptime_seconds = time.time() - proc_info['create_time']
                
                # Get memory in MB
                memory_mb = proc_info['memory_info'].rss / (1024 * 1024)
                
                # Extract process name
                cmdline = ' '.join(proc_info['cmdline']) if proc_info['cmdline'] else 'Unknown'
                process_name = self.extract_process_name(proc_info['name'], cmdline)
                
                process_data = {
                    'pid': proc_info['pid'],
                    'name': proc_info['name'],
                    'process_name': process_name,
                    'cmdline': cmdline,
                    'cpu_percent': proc_info['cpu_percent'] or 0,
                    'memory_mb': memory_mb,
                    'memory_percent': proc_info['memory_info'].rss / psutil.virtual_memory().total * 100,
                    'status': proc_info['status'],
                    'uptime_seconds': uptime_seconds,
                    'threads': proc_info['num_threads'],
                    'cpu_affinity': proc_info['cpu_affinity'],
                    'username': proc_info['username']
                }
                
                processes.append(process_data)
                
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        return processes
    
    def group_processes_by_name(self, processes):
        """Group processes by name and calculate totals"""
        grouped = defaultdict(list)
        
        for proc in processes:
            grouped[proc['process_name']].append(proc)
        
        # Calculate totals for each group
        process_groups = {}
        for name, procs in grouped.items():
            total_cpu = sum(p['cpu_percent'] for p in procs)
            total_memory = sum(p['memory_mb'] for p in procs)
            total_threads = sum(p['threads'] for p in procs)
            
            process_groups[name] = {
                'processes': procs,
                'total_cpu': total_cpu,
                'total_memory': total_memory,
                'total_threads': total_threads,
                'count': len(procs),
                'pids': [p['pid'] for p in procs]
            }
        
        return process_groups
    
    def analyze_core_usage(self, processes):
        """Analyze which processes are using which cores"""
        core_usage = defaultdict(list)
        
        for proc in processes:
            if proc['cpu_affinity']:
                # Process has specific core affinity
                for core in proc['cpu_affinity']:
                    core_usage[core].append({
                        'process_name': proc['process_name'],
                        'pid': proc['pid'],
                        'cpu_percent': proc['cpu_percent'],
                        'threads': proc['threads'],
                        'status': proc['status']
                    })
            else:
                # Process can use any core (no specific affinity)
                core_usage['any'].append({
                    'process_name': proc['process_name'],
                    'pid': proc['pid'],
                    'cpu_percent': proc['cpu_percent'],
                    'threads': proc['threads'],
                    'status': proc['status']
                })
        
        return core_usage
    
    def display_system_header(self):
        """Display system-wide information"""
        # System CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_per_core = psutil.cpu_percent(interval=0.1, percpu=True)
        
        # System Memory
        memory = psutil.virtual_memory()
        
        # Load average
        load_avg = os.getloadavg()
        
        print(f"{Colors.BOLD}{Colors.WHITE}{'='*150}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.WHITE}🖥️  DETAILED CORE ANALYSIS REPORT - 16-CORE SYSTEM{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.WHITE}{'='*150}{Colors.ENDC}")
        
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
    
    def display_process_groups(self, process_groups):
        """Display processes grouped by name with totals"""
        if not process_groups:
            print(f"{Colors.YELLOW}⚠️  No processes found{Colors.ENDC}")
            return
        
        # Sort by total CPU usage (highest first)
        sorted_groups = sorted(process_groups.items(), key=lambda x: x[1]['total_cpu'], reverse=True)
        
        print(f"{Colors.BOLD}📊 PROCESSES GROUPED BY NAME (with totals):{Colors.ENDC}")
        print("-" * 150)
        print(f"{Colors.BOLD}{'PROCESS NAME':<30} {'INSTANCES':<10} {'TOTAL CPU%':<12} {'TOTAL RAM':<12} {'TOTAL THREADS':<15} {'PIDS'}{Colors.ENDC}")
        print("-" * 150)
        
        for name, group in sorted_groups:
            # Colors based on usage
            cpu_color = self.get_color(group['total_cpu'], [50, 100, 200])
            mem_color = self.get_color(group['total_memory'], [500, 1000, 2000])
            
            # Format data
            process_name = f"{name:<30}"
            instances = f"{group['count']:<10}"
            total_cpu = f"{group['total_cpu']:10.1f}%"
            total_ram = f"{self.format_memory(group['total_memory'] * 1024 * 1024):<12}"
            total_threads = f"{group['total_threads']:<15}"
            pids = f"{', '.join(map(str, group['pids'][:5]))}"  # Show first 5 PIDs
            if len(group['pids']) > 5:
                pids += f"... (+{len(group['pids'])-5} more)"
            
            # Display row
            print(f"{process_name} {instances} {cpu_color}{total_cpu}{Colors.ENDC} {mem_color}{total_ram}{Colors.ENDC} {total_threads} {pids}")
    
    def display_detailed_core_analysis(self, core_usage):
        """Display detailed core usage analysis"""
        print(f"\n{Colors.BOLD}⚡ DETAILED CORE USAGE ANALYSIS:{Colors.ENDC}")
        print("-" * 150)
        
        # Show cores with specific assignments
        if 'any' in core_usage:
            any_core_procs = core_usage['any']
            total_any_cpu = sum(proc['cpu_percent'] for proc in any_core_procs)
            print(f"{Colors.BOLD}Processes that can use ANY core (no specific affinity):{Colors.ENDC}")
            print(f"Total CPU usage: {total_any_cpu:.1f}%")
            for proc in any_core_procs[:10]:  # Show first 10
                print(f"  {proc['process_name']} (PID: {proc['pid']}) - {proc['cpu_percent']:.1f}% CPU, {proc['threads']} threads, {proc['status']}")
            if len(any_core_procs) > 10:
                print(f"  ... and {len(any_core_procs) - 10} more processes")
            print()
        
        # Show cores with specific assignments
        specific_cores = {k: v for k, v in core_usage.items() if k != 'any'}
        if specific_cores:
            print(f"{Colors.BOLD}Cores with specific process assignments:{Colors.ENDC}")
            for core in sorted(specific_cores.keys()):
                procs_on_core = core_usage[core]
                total_core_cpu = sum(proc['cpu_percent'] for proc in procs_on_core)
                
                print(f"\n{Colors.BOLD}Core {core+1:2d}:{Colors.ENDC} Total CPU: {total_core_cpu:.1f}%")
                for proc in procs_on_core:
                    print(f"  {proc['process_name']} (PID: {proc['pid']}) - {proc['cpu_percent']:.1f}% CPU, {proc['threads']} threads, {proc['status']}")
        else:
            print(f"{Colors.YELLOW}No processes have specific core affinity set{Colors.ENDC}")
    
    def display_core_distribution_summary(self, core_usage, process_groups):
        """Display summary of core distribution"""
        print(f"\n{Colors.BOLD}📈 CORE DISTRIBUTION SUMMARY:{Colors.ENDC}")
        print("-" * 100)
        
        # Calculate total CPU usage
        total_cpu_usage = sum(group['total_cpu'] for group in process_groups.values())
        
        # Count processes by affinity
        any_core_count = len(core_usage.get('any', []))
        specific_core_count = sum(len(procs) for core, procs in core_usage.items() if core != 'any')
        
        print(f"Total System CPU Usage: {total_cpu_usage:.1f}%")
        print(f"Processes with no core affinity: {any_core_count}")
        print(f"Processes with specific core affinity: {specific_core_count}")
        
        # Show top CPU consumers
        sorted_groups = sorted(process_groups.items(), key=lambda x: x[1]['total_cpu'], reverse=True)
        print(f"\n{Colors.BOLD}Top 5 CPU Consumers:{Colors.ENDC}")
        for i, (name, group) in enumerate(sorted_groups[:5], 1):
            cpu_color = self.get_color(group['total_cpu'], [50, 100, 200])
            print(f"{i}. {name}: {cpu_color}{group['total_cpu']:.1f}%{Colors.ENDC} CPU ({group['count']} instances)")
    
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
        print(f"{Colors.GREEN}🚀 Starting Detailed Core Analysis Report...{Colors.ENDC}")
        print(f"{Colors.CYAN}This report shows which processes use which cores with detailed breakdown{Colors.ENDC}")
        
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
                
                # Group processes by name
                process_groups = self.group_processes_by_name(processes)
                
                # Display process groups
                self.display_process_groups(process_groups)
                
                # Analyze core usage
                core_usage = self.analyze_core_usage(processes)
                
                # Display detailed core analysis
                self.display_detailed_core_analysis(core_usage)
                
                # Display summary
                self.display_core_distribution_summary(core_usage, process_groups)
                
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
    monitor = DetailedCoreAnalysis()
    monitor.run()

if __name__ == "__main__":
    main()
