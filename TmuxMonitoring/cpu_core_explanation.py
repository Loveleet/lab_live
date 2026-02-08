#!/usr/bin/env python3
"""
CPU CORE EXPLANATION & ANALYSIS
Explains how CPU percentages work across multiple cores
Shows actual core usage vs total system capacity
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

class CPUCoreExplanation:
    def __init__(self):
        self.running = True
        self.refresh_interval = 3
        self.auto_refresh = True
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        self.running = False
        os.system('clear')
        print(f"{Colors.GREEN}✅ CPU Core Explanation stopped{Colors.ENDC}")
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
    
    def display_cpu_explanation(self):
        """Display explanation of how CPU percentages work"""
        print(f"{Colors.BOLD}{Colors.WHITE}{'='*120}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.WHITE}🧠 CPU PERCENTAGE EXPLANATION - 16-CORE SYSTEM{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.WHITE}{'='*120}{Colors.ENDC}")
        
        print(f"{Colors.BOLD}📚 How CPU Percentages Work:{Colors.ENDC}")
        print()
        print(f"{Colors.CYAN}1. Single Core System:{Colors.ENDC}")
        print(f"   • Maximum CPU usage: 100%")
        print(f"   • Process using 50% = using half of one core")
        print()
        print(f"{Colors.CYAN}2. Multi-Core System (Your 16-core system):{Colors.ENDC}")
        print(f"   • Maximum CPU usage: 1600% (16 cores × 100%)")
        print(f"   • Process using 200% = using 2 cores worth of CPU")
        print(f"   • Process using 800% = using 8 cores worth of CPU")
        print()
        print(f"{Colors.CYAN}3. How Processes Use Multiple Cores:{Colors.ENDC}")
        print(f"   • Multi-threaded processes can run on multiple cores")
        print(f"   • OS scheduler distributes threads across available cores")
        print(f"   • CPU percentage = sum of all cores the process is using")
        print()
        print(f"{Colors.CYAN}4. Examples from Your System:{Colors.ENDC}")
        print(f"   • trading_runner_final.py: 570% = using ~5.7 cores")
        print(f"   • hedge_botmain.py: 133% = using ~1.3 cores")
        print(f"   • Total system usage: 737% = using ~7.4 cores out of 16")
        print()
    
    def display_system_capacity(self):
        """Display system capacity and current usage"""
        # System CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_per_core = psutil.cpu_percent(interval=0.1, percpu=True)
        cpu_count = psutil.cpu_count()
        
        # Calculate actual core usage
        total_core_usage = sum(cpu_per_core)
        max_possible = cpu_count * 100
        actual_cores_used = total_core_usage / 100
        
        print(f"{Colors.BOLD}🖥️  SYSTEM CAPACITY ANALYSIS:{Colors.ENDC}")
        print(f"Total CPU Cores: {cpu_count}")
        print(f"Maximum Possible CPU Usage: {max_possible}%")
        print(f"Current Total CPU Usage: {total_core_usage:.1f}%")
        print(f"Actual Cores Being Used: {actual_cores_used:.1f} out of {cpu_count}")
        print(f"Available Cores: {cpu_count - actual_cores_used:.1f}")
        
        # Per-core breakdown
        print(f"\n{Colors.BOLD}⚡ Per-Core Usage:{Colors.ENDC}")
        for i in range(0, len(cpu_per_core), 8):  # 8 cores per line
            core_line = ""
            for j in range(i, min(i+8, len(cpu_per_core))):
                core_usage = cpu_per_core[j]
                core_color = self.get_color(core_usage, [50, 80, 95])
                core_line += f"{core_color}[{core_usage:4.1f}%]{Colors.ENDC} "
            print(f"Cores {i+1:2d}-{min(i+8, len(cpu_per_core)):2d}: {core_line}")
        print()
    
    def display_process_core_usage(self, process_groups):
        """Display how much of each core each process is using"""
        if not process_groups:
            print(f"{Colors.YELLOW}⚠️  No processes found{Colors.ENDC}")
            return
        
        # Sort by total CPU usage (highest first)
        sorted_groups = sorted(process_groups.items(), key=lambda x: x[1]['total_cpu'], reverse=True)
        
        print(f"{Colors.BOLD}📊 PROCESS CORE USAGE BREAKDOWN:{Colors.ENDC}")
        print("-" * 120)
        print(f"{Colors.BOLD}{'PROCESS NAME':<30} {'INSTANCES':<10} {'TOTAL CPU%':<12} {'EQUIVALENT CORES':<15} {'% OF SYSTEM':<12} {'STATUS'}{Colors.ENDC}")
        print("-" * 120)
        
        total_system_cpu = sum(group['total_cpu'] for group in process_groups.values())
        
        for name, group in sorted_groups:
            # Colors based on usage
            cpu_color = self.get_color(group['total_cpu'], [100, 300, 600])
            
            # Calculate equivalent cores
            equivalent_cores = group['total_cpu'] / 100
            system_percentage = (group['total_cpu'] / total_system_cpu) * 100 if total_system_cpu > 0 else 0
            
            # Format data
            process_name = f"{name:<30}"
            instances = f"{group['count']:<10}"
            total_cpu = f"{group['total_cpu']:10.1f}%"
            equiv_cores = f"{equivalent_cores:13.1f} cores"
            sys_percent = f"{system_percentage:10.1f}%"
            
            # Get status from first process
            status = group['processes'][0]['status'] if group['processes'] else 'unknown'
            
            # Display row
            print(f"{process_name} {instances} {cpu_color}{total_cpu}{Colors.ENDC} {equiv_cores} {sys_percent} {status}")
        
        print("-" * 120)
        print(f"{Colors.BOLD}Total System CPU Usage: {total_system_cpu:.1f}% ({total_system_cpu/100:.1f} cores){Colors.ENDC}")
        print()
    
    def display_core_distribution_analysis(self, process_groups):
        """Display analysis of how cores are distributed"""
        print(f"{Colors.BOLD}🔍 CORE DISTRIBUTION ANALYSIS:{Colors.ENDC}")
        
        total_cpu = sum(group['total_cpu'] for group in process_groups.values())
        cpu_count = psutil.cpu_count()
        max_possible = cpu_count * 100
        
        # Calculate efficiency
        efficiency = (total_cpu / max_possible) * 100
        cores_used = total_cpu / 100
        cores_available = cpu_count - cores_used
        
        print(f"Total CPU Usage: {total_cpu:.1f}%")
        print(f"Maximum Possible: {max_possible}%")
        print(f"System Efficiency: {efficiency:.1f}%")
        print(f"Cores Being Used: {cores_used:.1f}")
        print(f"Cores Available: {cores_available:.1f}")
        
        # Analysis
        if efficiency > 80:
            status = f"{Colors.RED}HIGH LOAD{Colors.ENDC}"
            recommendation = "Consider optimizing processes or adding more cores"
        elif efficiency > 50:
            status = f"{Colors.YELLOW}MODERATE LOAD{Colors.ENDC}"
            recommendation = "System is working well, monitor for spikes"
        else:
            status = f"{Colors.GREEN}LOW LOAD{Colors.ENDC}"
            recommendation = "System has plenty of capacity available"
        
        print(f"\nSystem Status: {status}")
        print(f"Recommendation: {recommendation}")
        print()
    
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
        print(f"{Colors.GREEN}🚀 Starting CPU Core Explanation & Analysis...{Colors.ENDC}")
        print(f"{Colors.CYAN}This tool explains how CPU percentages work across multiple cores{Colors.ENDC}")
        
        # Get refresh interval
        self.get_refresh_interval()
        
        print(f"{Colors.CYAN}Press Ctrl+C to quit{Colors.ENDC}")
        time.sleep(2)
        
        while self.running:
            try:
                # Clear screen
                os.system('clear')
                
                # Display CPU explanation
                self.display_cpu_explanation()
                
                # Display system capacity
                self.display_system_capacity()
                
                # Get all processes
                processes = self.get_all_processes()
                
                # Group processes by name
                process_groups = self.group_processes_by_name(processes)
                
                # Display process core usage
                self.display_process_core_usage(process_groups)
                
                # Display core distribution analysis
                self.display_core_distribution_analysis(process_groups)
                
                # Display timestamp and controls
                print(f"{Colors.DIM}Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}")
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
    monitor = CPUCoreExplanation()
    monitor.run()

if __name__ == "__main__":
    main()
