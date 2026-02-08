#!/usr/bin/env python3
"""
TRADING BOT CPU & RAM MONITOR
Specialized monitor for trading bots showing per-process CPU usage and core distribution
Designed for 16-core systems with real-time bot monitoring
"""

import psutil
import os
import time
import sys
import subprocess
from datetime import datetime
import signal
import threading
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

class TradingBotCPUMonitor:
    def __init__(self):
        self.running = True
        self.refresh_interval = 2  # Default 2 seconds
        self.auto_refresh = True  # Default auto refresh
        self.cpu_history = defaultdict(list)
        self.max_history = 5
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        self.running = False
        os.system('clear')
        print(f"{Colors.GREEN}✅ Trading Bot CPU Monitor stopped{Colors.ENDC}")
        sys.exit(0)
    
    def get_bot_processes(self):
        """Get all trading bot processes"""
        bot_processes = []
        
        # Try to read bot configuration files
        bot_paths = self.read_bot_configs()
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_info', 'status', 'create_time', 'num_threads', 'cpu_affinity']):
            try:
                proc_info = proc.info
                
                # Only Python processes
                if not (proc_info['name'] and 'python' in proc_info['name'].lower()):
                    continue
                
                # Check if it's a trading bot
                is_bot = False
                bot_name = "Unknown"
                cmdline = ' '.join(proc_info['cmdline']) if proc_info['cmdline'] else ''
                
                # Check against known bot paths
                for bot_path in bot_paths:
                    if bot_path in cmdline:
                        is_bot = True
                        bot_name = os.path.basename(bot_path)
                        break
                
                # Also check for common trading bot patterns
                if not is_bot:
                    if any(keyword in cmdline.lower() for keyword in ['trading', 'bot', 'signal', 'pair', 'binance', 'crypto']):
                        is_bot = True
                        # Extract bot name from command line
                        for arg in proc_info['cmdline']:
                            if arg.endswith('.py'):
                                bot_name = os.path.basename(arg)
                                break
                
                if is_bot:
                    # Calculate uptime
                    uptime_seconds = time.time() - proc_info['create_time']
                    
                    # Get memory in MB
                    memory_mb = proc_info['memory_info'].rss / (1024 * 1024)
                    
                    # Store CPU history for trend analysis
                    pid = proc_info['pid']
                    cpu_percent = proc_info['cpu_percent'] or 0
                    self.cpu_history[pid].append(cpu_percent)
                    if len(self.cpu_history[pid]) > self.max_history:
                        self.cpu_history[pid].pop(0)
                    
                    # Calculate CPU trend
                    cpu_trend = self.calculate_trend(self.cpu_history[pid])
                    
                    bot_processes.append({
                        'pid': pid,
                        'name': proc_info['name'],
                        'bot_name': bot_name,
                        'cmdline': cmdline,
                        'cpu_percent': cpu_percent,
                        'memory_mb': memory_mb,
                        'memory_percent': proc_info['memory_info'].rss / psutil.virtual_memory().total * 100,
                        'status': proc_info['status'],
                        'uptime_seconds': uptime_seconds,
                        'threads': proc_info['num_threads'],
                        'cpu_affinity': proc_info['cpu_affinity'],
                        'cpu_trend': cpu_trend
                    })
                
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        return bot_processes
    
    def read_bot_configs(self):
        """Read bot configuration files to identify trading bots"""
        bot_paths = set()
        
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
        
        return list(bot_paths)
    
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
        print(f"{Colors.BOLD}{Colors.WHITE}🤖 TRADING BOT CPU & RAM MONITOR - 16-CORE SYSTEM{Colors.ENDC}")
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
    
    def display_bot_processes(self, bot_processes):
        """Display trading bot processes"""
        if not bot_processes:
            print(f"{Colors.YELLOW}⚠️  No trading bot processes found{Colors.ENDC}")
            return
        
        # Sort by CPU usage (highest first)
        bot_processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        
        # Header
        print(f"{Colors.BOLD}{'PID':<8} {'BOT NAME':<30} {'%CPU':<6} {'%MEM':<6} {'RAM':<8} {'THREADS':<8} {'STATUS':<6} {'UPTIME':<8} {'TREND':<8} {'CORES'}{Colors.ENDC}")
        print("-" * 120)
        
        # Display processes
        for bot in bot_processes:
            # Colors based on usage
            cpu_color = self.get_color(bot['cpu_percent'], [20, 50, 80])
            mem_color = self.get_color(bot['memory_mb'], [500, 1000, 2000])
            status_color = Colors.GREEN if bot['status'] == 'R' else Colors.YELLOW if bot['status'] == 'S' else Colors.RED
            
            # Trend color
            trend_color = Colors.RED if bot['cpu_trend'] == 'rising' else Colors.GREEN if bot['cpu_trend'] == 'falling' else Colors.CYAN
            
            # Format data
            pid = f"{bot['pid']:<8}"
            bot_name = f"{bot['bot_name']:<30}"
            cpu_percent = f"{bot['cpu_percent']:5.1f}%"
            mem_percent = f"{bot['memory_percent']:5.1f}%"
            ram = f"{self.format_memory(bot['memory_mb'] * 1024 * 1024):<8}"
            threads = f"{bot['threads']:<8}"
            status = f"{bot['status']:<6}"
            uptime = f"{self.format_uptime(bot['uptime_seconds']):<8}"
            trend = f"{bot['cpu_trend']:<8}"
            
            # CPU affinity (cores)
            if bot['cpu_affinity']:
                cores = f"{len(bot['cpu_affinity'])} cores"
            else:
                cores = "all cores"
            
            # Display row
            print(f"{pid} {bot_name} {cpu_color}{cpu_percent}{Colors.ENDC} {mem_color}{mem_percent}{Colors.ENDC} {ram} {threads} {status_color}{status}{Colors.ENDC} {uptime} {trend_color}{trend}{Colors.ENDC} {cores}")
    
    def display_core_distribution(self, bot_processes):
        """Display CPU core distribution analysis"""
        if not bot_processes:
            return
        
        print(f"\n{Colors.BOLD}⚡ CPU CORE DISTRIBUTION ANALYSIS:{Colors.ENDC}")
        
        # Analyze core usage
        core_usage = defaultdict(list)
        total_cpu_usage = 0
        
        for bot in bot_processes:
            total_cpu_usage += bot['cpu_percent']
            if bot['cpu_affinity']:
                for core in bot['cpu_affinity']:
                    core_usage[core].append({
                        'bot_name': bot['bot_name'],
                        'cpu_percent': bot['cpu_percent'],
                        'pid': bot['pid']
                    })
        
        # Show core distribution
        if core_usage:
            print("Cores with specific bot assignments:")
            for core in sorted(core_usage.keys()):
                bots_on_core = core_usage[core]
                total_core_cpu = sum(bot['cpu_percent'] for bot in bots_on_core)
                bot_list = ', '.join([f"{bot['bot_name']}({bot['cpu_percent']:.1f}%)" for bot in bots_on_core])
                print(f"  Core {core+1:2d}: {total_core_cpu:5.1f}% total - {bot_list}")
        else:
            print("  All bots can use any core (no specific affinity set)")
        
        print(f"\nTotal Bot CPU Usage: {total_cpu_usage:.1f}%")
        print(f"Average CPU per Bot: {total_cpu_usage/len(bot_processes):.1f}%")
    
    def display_summary(self, bot_processes):
        """Display summary statistics"""
        if not bot_processes:
            return
        
        # Calculate totals
        total_cpu = sum(bot['cpu_percent'] for bot in bot_processes)
        total_memory = sum(bot['memory_mb'] for bot in bot_processes)
        total_threads = sum(bot['threads'] for bot in bot_processes)
        
        # Count by status
        running_count = sum(1 for bot in bot_processes if bot['status'] == 'R')
        sleeping_count = sum(1 for bot in bot_processes if bot['status'] == 'S')
        
        # Count by trend
        rising_count = sum(1 for bot in bot_processes if bot['cpu_trend'] == 'rising')
        falling_count = sum(1 for bot in bot_processes if bot['cpu_trend'] == 'falling')
        stable_count = sum(1 for bot in bot_processes if bot['cpu_trend'] == 'stable')
        
        print(f"\n{Colors.BOLD}📊 BOT SUMMARY:{Colors.ENDC}")
        print(f"Total Trading Bots: {len(bot_processes)}")
        print(f"Total CPU Usage: {total_cpu:.1f}%")
        print(f"Total Memory Usage: {self.format_memory(total_memory * 1024 * 1024)}")
        print(f"Total Threads: {total_threads}")
        print(f"Status - Running: {running_count}, Sleeping: {sleeping_count}")
        print(f"CPU Trends - Rising: {rising_count}, Falling: {falling_count}, Stable: {stable_count}")
        
        # Top consumers
        if bot_processes:
            top_cpu = max(bot_processes, key=lambda x: x['cpu_percent'])
            top_memory = max(bot_processes, key=lambda x: x['memory_mb'])
            
            print(f"\n{Colors.BOLD}🔝 TOP CONSUMERS:{Colors.ENDC}")
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
        print(f"{Colors.GREEN}🚀 Starting Trading Bot CPU & RAM Monitor...{Colors.ENDC}")
        print(f"{Colors.CYAN}This monitor shows CPU and RAM usage for trading bots{Colors.ENDC}")
        
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
                
                # Get and display bot processes
                bot_processes = self.get_bot_processes()
                self.display_bot_processes(bot_processes)
                
                # Display core distribution
                self.display_core_distribution(bot_processes)
                
                # Display summary
                self.display_summary(bot_processes)
                
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
    monitor = TradingBotCPUMonitor()
    monitor.run()

if __name__ == "__main__":
    main()
