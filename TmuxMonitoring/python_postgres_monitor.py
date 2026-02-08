#!/usr/bin/env python3
"""
PYTHON & POSTGRESQL MONITOR
Shows only Python and PostgreSQL processes
Filtered view for development and database monitoring
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

class PythonPostgresMonitor:
    def __init__(self):
        self.running = True
        self.refresh_interval = 3
        self.auto_refresh = True
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        self.running = False
        os.system('clear')
        print(f"{Colors.GREEN}✅ Python & PostgreSQL Monitor stopped{Colors.ENDC}")
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
        elif 'postgres' in name.lower():
            return "PostgreSQL"
        return name
    
    def get_python_postgres_processes(self):
        """Get only Python and PostgreSQL processes"""
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_info', 'status', 'create_time', 'num_threads', 'cpu_affinity', 'username']):
            try:
                proc_info = proc.info
                
                # Only Python and PostgreSQL processes
                process_name = proc_info['name'].lower()
                if not ('python' in process_name or 'postgres' in process_name):
                    continue
                
                # Calculate uptime
                uptime_seconds = time.time() - proc_info['create_time']
                
                # Get memory in MB
                memory_mb = proc_info['memory_info'].rss / (1024 * 1024)
                
                # Extract process name
                cmdline = ' '.join(proc_info['cmdline']) if proc_info['cmdline'] else 'Unknown'
                display_name = self.extract_process_name(proc_info['name'], cmdline)
                
                process_data = {
                    'pid': proc_info['pid'],
                    'name': proc_info['name'],
                    'display_name': display_name,
                    'cmdline': cmdline,
                    'cpu_percent': proc_info['cpu_percent'] or 0,
                    'memory_mb': memory_mb,
                    'memory_percent': proc_info['memory_info'].rss / psutil.virtual_memory().total * 100,
                    'status': proc_info['status'],
                    'uptime_seconds': uptime_seconds,
                    'threads': proc_info['num_threads'],
                    'cpu_affinity': proc_info['cpu_affinity'],
                    'username': proc_info['username'],
                    'process_type': 'Python' if 'python' in process_name else 'PostgreSQL'
                }
                
                processes.append(process_data)
                
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        return processes
    
    def group_processes_by_name(self, processes):
        """Group processes by name and calculate totals"""
        grouped = defaultdict(list)
        
        for proc in processes:
            grouped[proc['display_name']].append(proc)
        
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
                'pids': [p['pid'] for p in procs],
                'process_type': procs[0]['process_type'] if procs else 'Unknown'
            }
        
        return process_groups
    
    def display_system_header(self):
        """Display system-wide information"""
        # System CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_per_core = psutil.cpu_percent(interval=0.1, percpu=True)
        
        # System Memory
        memory = psutil.virtual_memory()
        
        # Load average
        load_avg = os.getloadavg()
        
        print(f"{Colors.BOLD}{Colors.WHITE}{'='*120}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.WHITE}🐍 PYTHON & POSTGRESQL MONITOR - DEVELOPMENT VIEW{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.WHITE}{'='*120}{Colors.ENDC}")
        
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
    
    def display_processes(self, processes):
        """Display Python and PostgreSQL processes"""
        if not processes:
            print(f"{Colors.YELLOW}⚠️  No Python or PostgreSQL processes found{Colors.ENDC}")
            return
        
        # Sort by CPU usage (highest first)
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        
        # Header with CPU core explanation columns
        print(f"{Colors.BOLD}{'PID':<8} {'TYPE':<10} {'PROCESS NAME':<30} {'%CPU':<6} {'%MEM':<6} {'RAM':<8} {'THREADS':<8} {'STATUS':<6} {'UPTIME':<8} {'CORES':<8} {'CPU%':<6}{Colors.ENDC}")
        print("-" * 120)
        
        # Display processes
        for proc in processes:
            # Colors based on usage
            cpu_color = self.get_color(proc['cpu_percent'], [20, 50, 80])
            mem_color = self.get_color(proc['memory_mb'], [500, 1000, 2000])
            status_color = Colors.GREEN if proc['status'] == 'R' else Colors.YELLOW if proc['status'] == 'S' else Colors.RED
            
            # Type color
            type_color = Colors.CYAN if proc['process_type'] == 'Python' else Colors.BLUE
            
            # Calculate actual CPU core usage (equivalent cores being used)
            cpu_cores_used = proc['cpu_percent'] / 100.0  # Convert percentage to equivalent cores
            cpu_per_core = proc['cpu_percent'] / 16.0  # CPU usage per core on 16-core system
            
            # Format data
            pid = f"{proc['pid']:<8}"
            process_type = f"{proc['process_type']:<10}"
            display_name = f"{proc['display_name']:<30}"
            cpu_percent = f"{proc['cpu_percent']:5.1f}%"
            mem_percent = f"{proc['memory_percent']:5.1f}%"
            ram = f"{self.format_memory(proc['memory_mb'] * 1024 * 1024):<8}"
            threads = f"{proc['threads']:<8}"
            status = f"{proc['status']:<6}"
            uptime = f"{self.format_uptime(proc['uptime_seconds']):<8}"
            cores = f"{cpu_cores_used:<8.2f}"
            cpu_per_core_display = f"{cpu_per_core:5.1f}%"
            
            # Display row
            print(f"{pid} {type_color}{process_type}{Colors.ENDC} {display_name} {cpu_color}{cpu_percent}{Colors.ENDC} {mem_color}{mem_percent}{Colors.ENDC} {ram} {threads} {status_color}{status}{Colors.ENDC} {uptime} {cores} {cpu_per_core_display}")
    
    def display_process_groups(self, process_groups):
        """Display processes grouped by name with totals"""
        if not process_groups:
            print(f"{Colors.YELLOW}⚠️  No process groups found{Colors.ENDC}")
            return
        
        # Sort by total CPU usage (highest first)
        sorted_groups = sorted(process_groups.items(), key=lambda x: x[1]['total_cpu'], reverse=True)
        
        print(f"\n{Colors.BOLD}📊 PROCESSES GROUPED BY NAME (with totals):{Colors.ENDC}")
        print("-" * 120)
        print(f"{Colors.BOLD}{'PROCESS NAME':<30} {'TYPE':<10} {'INSTANCES':<10} {'TOTAL CPU%':<12} {'TOTAL RAM':<12} {'TOTAL THREADS':<15} {'CORES':<8} {'CPU%':<6} {'PIDS'}{Colors.ENDC}")
        print("-" * 120)
        
        for name, group in sorted_groups:
            # Colors based on usage
            cpu_color = self.get_color(group['total_cpu'], [50, 100, 200])
            mem_color = self.get_color(group['total_memory'], [500, 1000, 2000])
            type_color = Colors.CYAN if group['process_type'] == 'Python' else Colors.BLUE
            
            # Calculate actual CPU core usage for the group
            total_cores_used = group['total_cpu'] / 100.0  # Convert percentage to equivalent cores
            cpu_per_core = group['total_cpu'] / 16.0  # CPU usage per core on 16-core system
            
            # Format data
            process_name = f"{name:<30}"
            process_type = f"{group['process_type']:<10}"
            instances = f"{group['count']:<10}"
            total_cpu = f"{group['total_cpu']:10.1f}%"
            total_ram = f"{self.format_memory(group['total_memory'] * 1024 * 1024):<12}"
            total_threads = f"{group['total_threads']:<15}"
            cores = f"{total_cores_used:<8.2f}"
            cpu_per_core_display = f"{cpu_per_core:5.1f}%"
            pids = f"{', '.join(map(str, group['pids'][:5]))}"  # Show first 5 PIDs
            if len(group['pids']) > 5:
                pids += f"... (+{len(group['pids'])-5} more)"
            
            # Display row
            print(f"{process_name} {type_color}{process_type}{Colors.ENDC} {instances} {cpu_color}{total_cpu}{Colors.ENDC} {mem_color}{total_ram}{Colors.ENDC} {total_threads} {cores} {cpu_per_core_display} {pids}")
    
    def display_summary(self, process_groups):
        """Display summary statistics"""
        if not process_groups:
            return
        
        # Calculate totals
        total_cpu = sum(group['total_cpu'] for group in process_groups.values())
        total_memory = sum(group['total_memory'] for group in process_groups.values())
        total_threads = sum(group['total_threads'] for group in process_groups.values())
        
        # Count by type
        python_count = sum(1 for group in process_groups.values() if group['process_type'] == 'Python')
        postgres_count = sum(1 for group in process_groups.values() if group['process_type'] == 'PostgreSQL')
        
        # Count instances
        python_instances = sum(group['count'] for group in process_groups.values() if group['process_type'] == 'Python')
        postgres_instances = sum(group['count'] for group in process_groups.values() if group['process_type'] == 'PostgreSQL')
        
        print(f"\n{Colors.BOLD}📊 PYTHON & POSTGRESQL SUMMARY:{Colors.ENDC}")
        print(f"Total Process Groups: {len(process_groups)}")
        print(f"Total CPU Usage: {total_cpu:.1f}%")
        print(f"Total Memory Usage: {self.format_memory(total_memory * 1024 * 1024)}")
        print(f"Total Threads: {total_threads}")
        print(f"Python Groups: {python_count} ({python_instances} instances)")
        print(f"PostgreSQL Groups: {postgres_count} ({postgres_instances} instances)")
        
        # Top consumers
        if process_groups:
            top_cpu = max(process_groups.values(), key=lambda x: x['total_cpu'])
            top_memory = max(process_groups.values(), key=lambda x: x['total_memory'])
            
            print(f"\n{Colors.BOLD}🔝 TOP CONSUMERS:{Colors.ENDC}")
            print(f"Highest CPU: {top_cpu['processes'][0]['display_name']} ({top_cpu['total_cpu']:.1f}%)")
            print(f"Highest Memory: {top_memory['processes'][0]['display_name']} ({self.format_memory(top_memory['total_memory'] * 1024 * 1024)})")
    
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
        print(f"{Colors.GREEN}🚀 Starting Python & PostgreSQL Monitor...{Colors.ENDC}")
        print(f"{Colors.CYAN}This monitor shows only Python and PostgreSQL processes{Colors.ENDC}")
        
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
                
                # Get Python and PostgreSQL processes
                processes = self.get_python_postgres_processes()
                
                # Display processes
                self.display_processes(processes)
                
                # Group processes by name
                process_groups = self.group_processes_by_name(processes)
                
                # Display process groups
                self.display_process_groups(process_groups)
                
                # Display summary
                self.display_summary(process_groups)
                
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
    monitor = PythonPostgresMonitor()
    monitor.run()

if __name__ == "__main__":
    main()
