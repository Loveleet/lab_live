#!/usr/bin/env python3
"""
CPU USAGE LOGGER
Tracks highest CPU usage per process and saves logs with timestamps
Updates only when CPU usage increases from previous record
"""

import psutil
import os
import time
import sys
import signal
import json
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

class CPUUsageLogger:
    def __init__(self):
        self.running = True
        self.refresh_interval = 3
        self.auto_refresh = True
        self.log_file = "/root/TmuxMonitoring/cpu_usage_log.json"
        self.csv_file = "/root/TmuxMonitoring/cpu_usage_log.csv"
        self.highest_cpu_records = {}
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        self.running = False
        os.system('clear')
        print(f"{Colors.GREEN}✅ CPU Usage Logger stopped{Colors.ENDC}")
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
    
    def get_python_postgres_processes(self):
        """Get only Python and PostgreSQL processes with detailed information"""
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
                    'process_name': display_name,
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
    
    def load_existing_records(self):
        """Load existing CPU usage records from file"""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r') as f:
                    self.highest_cpu_records = json.load(f)
                print(f"{Colors.GREEN}✅ Loaded {len(self.highest_cpu_records)} existing records{Colors.ENDC}")
            except Exception as e:
                print(f"{Colors.YELLOW}⚠️  Error loading existing records: {e}{Colors.ENDC}")
                self.highest_cpu_records = {}
        else:
            self.highest_cpu_records = {}
            print(f"{Colors.CYAN}📝 Starting fresh - no existing records found{Colors.ENDC}")
    
    def save_records(self):
        """Save CPU usage records to file"""
        try:
            with open(self.log_file, 'w') as f:
                json.dump(self.highest_cpu_records, f, indent=2)
        except Exception as e:
            print(f"{Colors.RED}❌ Error saving records: {e}{Colors.ENDC}")
    
    def update_csv_log_all(self):
        """Update CSV log file with all current highest records"""
        try:
            # Write header and all current records
            with open(self.csv_file, 'w') as f:
                f.write("timestamp,process_name,pid,cpu_percent,memory_mb,memory_percent,status,threads,uptime_seconds,username,cmdline\n")
                
                # Write all current highest records
                for process_name, record in self.highest_cpu_records.items():
                    f.write(f"{record['timestamp']},{process_name},{record['pid']},{record['cpu_percent']},{record['memory_mb']},{record['memory_percent']},{record['status']},{record['threads']},{record['uptime_seconds']},{record['username']},{record['cmdline']}\n")
        except Exception as e:
            print(f"{Colors.RED}❌ Error updating CSV log: {e}{Colors.ENDC}")
    
    def update_csv_log(self, process_name, record):
        """Update CSV log file with new record (legacy method - now handled by update_csv_log_all)"""
        pass  # This method is now handled by update_csv_log_all
    
    def check_and_update_records(self, processes):
        """Check processes and update records if CPU usage is higher"""
        updates_made = 0
        
        for proc in processes:
            process_name = proc['process_name']
            current_cpu = proc['cpu_percent']
            
            # Create record for this process
            record = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'pid': proc['pid'],
                'cpu_percent': current_cpu,
                'memory_mb': proc['memory_mb'],
                'memory_percent': proc['memory_percent'],
                'status': proc['status'],
                'threads': proc['threads'],
                'uptime_seconds': proc['uptime_seconds'],
                'username': proc['username'],
                'cmdline': proc['cmdline'],
                'cpu_affinity': proc['cpu_affinity']
            }
            
            # Check if this is a new record or higher CPU usage
            if process_name not in self.highest_cpu_records:
                # New process
                self.highest_cpu_records[process_name] = record
                updates_made += 1
                print(f"{Colors.GREEN}🆕 New process recorded: {process_name} - {current_cpu:.1f}% CPU{Colors.ENDC}")
            else:
                # Existing process - check if CPU usage is higher
                existing_cpu = self.highest_cpu_records[process_name]['cpu_percent']
                if current_cpu > existing_cpu:
                    self.highest_cpu_records[process_name] = record
                    updates_made += 1
                    print(f"{Colors.YELLOW}📈 CPU usage increased: {process_name} - {existing_cpu:.1f}% → {current_cpu:.1f}% CPU{Colors.ENDC}")
        
        if updates_made > 0:
            self.save_records()
            self.update_csv_log_all()  # Update CSV with all current records
            print(f"{Colors.CYAN}💾 Saved {updates_made} updates to log files{Colors.ENDC}")
        
        return updates_made
    
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
        print(f"{Colors.BOLD}{Colors.WHITE}📊 CPU USAGE LOGGER - TRACKING HIGHEST CPU USAGE{Colors.ENDC}")
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
    
    def display_current_processes(self, processes):
        """Display current Python and PostgreSQL processes"""
        if not processes:
            print(f"{Colors.YELLOW}⚠️  No Python or PostgreSQL processes found{Colors.ENDC}")
            return
        
        # Sort by CPU usage (highest first)
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        
        # Show all processes (since we're filtering to only Python/PostgreSQL)
        top_processes = processes
        
        # Header with CPU core explanation columns
        print(f"{Colors.BOLD}📊 CURRENT PYTHON & POSTGRESQL PROCESSES:{Colors.ENDC}")
        print("-" * 120)
        print(f"{Colors.BOLD}{'PID':<8} {'PROCESS NAME':<30} {'%CPU':<6} {'%MEM':<6} {'RAM':<8} {'THREADS':<8} {'STATUS':<6} {'UPTIME':<8} {'CORES':<8} {'CPU%':<6}{Colors.ENDC}")
        print("-" * 120)
        
        # Display processes
        for proc in top_processes:
            # Colors based on usage
            cpu_color = self.get_color(proc['cpu_percent'], [20, 50, 80])
            mem_color = self.get_color(proc['memory_mb'], [500, 1000, 2000])
            status_color = Colors.GREEN if proc['status'] == 'R' else Colors.YELLOW if proc['status'] == 'S' else Colors.RED
            
            # Calculate actual CPU core usage (equivalent cores being used)
            cpu_cores_used = proc['cpu_percent'] / 100.0  # Convert percentage to equivalent cores
            cpu_per_core = proc['cpu_percent'] / 16.0  # CPU usage per core on 16-core system
            
            # Format data
            pid = f"{proc['pid']:<8}"
            process_name = f"{proc['process_name']:<30}"
            cpu_percent = f"{proc['cpu_percent']:5.1f}%"
            mem_percent = f"{proc['memory_percent']:5.1f}%"
            ram = f"{self.format_memory(proc['memory_mb'] * 1024 * 1024):<8}"
            threads = f"{proc['threads']:<8}"
            status = f"{proc['status']:<6}"
            uptime = f"{self.format_uptime(proc['uptime_seconds']):<8}"
            cores = f"{cpu_cores_used:<8.2f}"
            cpu_per_core_display = f"{cpu_per_core:5.1f}%"
            
            # Display row
            print(f"{pid} {process_name} {cpu_color}{cpu_percent}{Colors.ENDC} {mem_color}{mem_percent}{Colors.ENDC} {ram} {threads} {status_color}{status}{Colors.ENDC} {uptime} {cores} {cpu_per_core_display}")
    
    def display_highest_records(self):
        """Display highest CPU usage records in interactive table format"""
        if not self.highest_cpu_records:
            print(f"{Colors.YELLOW}⚠️  No records found yet{Colors.ENDC}")
            return
        
        # Sort by CPU usage (highest first)
        sorted_records = sorted(self.highest_cpu_records.items(), key=lambda x: x[1]['cpu_percent'], reverse=True)
        
        print(f"\n{Colors.BOLD}🏆 HIGHEST CPU USAGE RECORDS (One Entry Per Process):{Colors.ENDC}")
        print("=" * 140)
        print(f"{Colors.BOLD}{'#':<3} {'PROCESS NAME':<35} {'HIGHEST CPU%':<12} {'RECORDED AT':<20} {'PID':<8} {'MEMORY':<8} {'THREADS':<8} {'CORES':<8} {'CPU%':<6} {'STATUS':<8}{Colors.ENDC}")
        print("=" * 140)
        
        # Display records with numbering
        for i, (process_name, record) in enumerate(sorted_records, 1):
            # Colors based on usage
            cpu_color = self.get_color(record['cpu_percent'], [50, 100, 200])
            mem_color = self.get_color(record['memory_mb'], [500, 1000, 2000])
            status_color = Colors.GREEN if record['status'] == 'R' else Colors.YELLOW if record['status'] == 'S' else Colors.RED
            
            # Calculate actual CPU core usage for the record
            cpu_cores_used = record['cpu_percent'] / 100.0  # Convert percentage to equivalent cores
            cpu_per_core = record['cpu_percent'] / 16.0  # CPU usage per core on 16-core system
            
            # Format data
            number = f"{i:<3}"
            process_name_display = f"{process_name:<35}"
            highest_cpu = f"{record['cpu_percent']:10.1f}%"
            recorded_at = f"{record['timestamp']:<20}"
            pid = f"{record['pid']:<8}"
            memory = f"{self.format_memory(record['memory_mb'] * 1024 * 1024):<8}"
            threads = f"{record['threads']:<8}"
            cores = f"{cpu_cores_used:<8.2f}"
            cpu_per_core_display = f"{cpu_per_core:5.1f}%"
            status = f"{record['status']:<8}"
            
            # Display row with alternating background for better readability
            if i % 2 == 0:
                print(f"{Colors.DIM}{number} {process_name_display} {cpu_color}{highest_cpu}{Colors.ENDC}{Colors.DIM} {recorded_at} {pid} {mem_color}{memory}{Colors.ENDC}{Colors.DIM} {threads} {cores} {cpu_per_core_display} {status_color}{status}{Colors.ENDC}{Colors.DIM}{Colors.ENDC}")
            else:
                print(f"{number} {process_name_display} {cpu_color}{highest_cpu}{Colors.ENDC} {recorded_at} {pid} {mem_color}{memory}{Colors.ENDC} {threads} {cores} {cpu_per_core_display} {status_color}{status}{Colors.ENDC}")
        
        print("=" * 140)
        
        # Display summary statistics
        total_processes = len(sorted_records)
        total_cpu = sum(record['cpu_percent'] for record in self.highest_cpu_records.values())
        avg_cpu = total_cpu / total_processes if total_processes > 0 else 0
        
        print(f"{Colors.BOLD}📊 SUMMARY:{Colors.ENDC}")
        print(f"Total Processes Tracked: {total_processes}")
        print(f"Total CPU Usage: {total_cpu:.1f}%")
        print(f"Average CPU per Process: {avg_cpu:.1f}%")
        
        # Top 3 consumers
        if len(sorted_records) >= 3:
            print(f"\n{Colors.BOLD}🔝 TOP 3 CPU CONSUMERS:{Colors.ENDC}")
            for i in range(min(3, len(sorted_records))):
                name, record = sorted_records[i]
                cpu_color = self.get_color(record['cpu_percent'], [50, 100, 200])
                print(f"{i+1}. {name}: {cpu_color}{record['cpu_percent']:.1f}%{Colors.ENDC} CPU (Recorded: {record['timestamp']})")
    
    def display_log_summary(self):
        """Display log file summary"""
        print(f"\n{Colors.BOLD}📁 LOG FILES:{Colors.ENDC}")
        print(f"JSON Log: {self.log_file}")
        print(f"CSV Log: {self.csv_file}")
        print(f"Total Unique Processes: {len(self.highest_cpu_records)}")
        print(f"CSV Entries: {len(self.highest_cpu_records)} (one per process)")
        
        # Show file sizes
        try:
            if os.path.exists(self.log_file):
                json_size = os.path.getsize(self.log_file)
                print(f"JSON File Size: {json_size} bytes")
            if os.path.exists(self.csv_file):
                csv_size = os.path.getsize(self.csv_file)
                print(f"CSV File Size: {csv_size} bytes")
        except:
            pass
    
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
        print(f"{Colors.GREEN}🚀 Starting CPU Usage Logger...{Colors.ENDC}")
        print(f"{Colors.CYAN}This logger tracks highest CPU usage per process and saves logs{Colors.ENDC}")
        
        # Load existing records
        self.load_existing_records()
        
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
                
                # Get Python and PostgreSQL processes only
                processes = self.get_python_postgres_processes()
                
                # Display current processes
                self.display_current_processes(processes)
                
                # Check and update records
                updates_made = self.check_and_update_records(processes)
                
                # Display highest records
                self.display_highest_records()
                
                # Display log summary
                self.display_log_summary()
                
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
    logger = CPUUsageLogger()
    logger.run()

if __name__ == "__main__":
    main()
