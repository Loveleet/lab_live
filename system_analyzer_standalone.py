#!/usr/bin/env python3
"""
Standalone System Analyzer
A comprehensive system analysis tool that provides detailed explanations
of system performance, processes, and resources - similar to htop but with explanations.
"""

import psutil
import subprocess
import json
import time
from datetime import datetime
import os
import sys

def get_system_overview():
    """Get comprehensive system overview with detailed explanations"""
    
    # Basic system info
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.now() - boot_time
    
    # Memory analysis
    memory = psutil.virtual_memory()
    swap = psutil.swap_memory()
    
    # CPU analysis
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count()
    cpu_freq = psutil.cpu_freq()
    
    # Disk analysis
    disk = psutil.disk_usage('/')
    
    # Load average
    load_avg = os.getloadavg()
    
    return {
        'boot_time': boot_time,
        'uptime': uptime,
        'memory': memory,
        'swap': swap,
        'cpu_percent': cpu_percent,
        'cpu_count': cpu_count,
        'cpu_freq': cpu_freq,
        'disk': disk,
        'load_avg': load_avg
    }

def get_detailed_process_analysis():
    """Get detailed analysis of running processes"""
    
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info', 'status', 'create_time', 'cmdline']):
        try:
            proc_info = proc.info
            proc_info['memory_mb'] = proc_info['memory_info'].rss / 1024 / 1024 if proc_info['memory_info'] else 0
            proc_info['uptime'] = time.time() - proc_info['create_time'] if proc_info['create_time'] else 0
            processes.append(proc_info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    # Sort by memory usage
    processes.sort(key=lambda x: x['memory_mb'], reverse=True)
    
    return processes[:20]  # Top 20 processes

def analyze_process_status(status):
    """Analyze process status and provide explanation"""
    
    status_explanations = {
        'R': '🟢 RUNNING - Process is actively executing',
        'S': '🟡 SLEEPING - Process waiting for an event (normal)',
        'D': '🔴 UNINTERRUPTIBLE SLEEP - Process waiting for I/O (can be problematic)',
        'Z': '💀 ZOMBIE - Process terminated but not cleaned up (problematic)',
        'T': '⏸️ STOPPED - Process suspended by signal (can be resumed)',
        'I': '💤 IDLE - Process waiting for I/O (normal)',
        'W': '⏳ WAITING - Process waiting for page fault (normal)',
        'L': '🔒 LOCKED - Process has pages locked in memory',
        'X': '❌ DEAD - Process is dead (should not appear)'
    }
    
    return status_explanations.get(status, f'❓ UNKNOWN - Status: {status}')

def analyze_memory_usage(memory_mb):
    """Analyze memory usage and provide explanation"""
    
    if memory_mb < 10:
        return "🟢 LOW - Normal memory usage"
    elif memory_mb < 100:
        return "🟡 MODERATE - Moderate memory usage"
    elif memory_mb < 500:
        return "🟠 HIGH - High memory usage, monitor closely"
    elif memory_mb < 1000:
        return "🔴 VERY HIGH - Very high memory usage, potential memory leak"
    else:
        return "🚨 CRITICAL - Critical memory usage, likely memory leak"

def analyze_cpu_usage(cpu_percent):
    """Analyze CPU usage and provide explanation"""
    
    if cpu_percent < 10:
        return "🟢 LOW - Normal CPU usage"
    elif cpu_percent < 50:
        return "🟡 MODERATE - Moderate CPU usage"
    elif cpu_percent < 80:
        return "🟠 HIGH - High CPU usage, monitor closely"
    else:
        return "🔴 CRITICAL - Critical CPU usage, system may be overloaded"

def get_system_health_score():
    """Calculate overall system health score"""
    
    memory = psutil.virtual_memory()
    swap = psutil.swap_memory()
    cpu_percent = psutil.cpu_percent(interval=1)
    
    # Health scoring (0-100, higher is better)
    memory_score = max(0, 100 - memory.percent)
    swap_score = 100 if swap.percent == 0 else max(0, 100 - swap.percent)
    cpu_score = max(0, 100 - cpu_percent)
    
    overall_score = (memory_score + swap_score + cpu_score) / 3
    
    if overall_score >= 80:
        health_status = "🟢 EXCELLENT"
    elif overall_score >= 60:
        health_status = "🟡 GOOD"
    elif overall_score >= 40:
        health_status = "🟠 FAIR"
    else:
        health_status = "🔴 POOR"
    
    return {
        'score': overall_score,
        'status': health_status,
        'memory_score': memory_score,
        'swap_score': swap_score,
        'cpu_score': cpu_score
    }

def get_network_analysis():
    """Get network interface analysis"""
    
    net_io = psutil.net_io_counters()
    net_connections = psutil.net_connections()
    
    return {
        'net_io': net_io,
        'net_connections': len(net_connections)
    }

def get_disk_io_analysis():
    """Get disk I/O analysis"""
    
    disk_io = psutil.disk_io_counters()
    return disk_io

def generate_system_report():
    """Generate comprehensive system analysis report"""
    
    print("=" * 80)
    print("🔍 COMPREHENSIVE SYSTEM ANALYSIS REPORT")
    print("=" * 80)
    print(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # System Overview
    overview = get_system_overview()
    
    print("🖥️  SYSTEM OVERVIEW")
    print("-" * 40)
    print(f"⏰ Boot Time: {overview['boot_time'].strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱️  Uptime: {str(overview['uptime']).split('.')[0]}")
    print(f"🖥️  CPU Cores: {overview['cpu_count']} cores")
    if overview['cpu_freq']:
        print(f"⚡ CPU Frequency: {overview['cpu_freq'].current:.0f} MHz")
    print()
    
    # Memory Analysis
    print("🧠 MEMORY ANALYSIS")
    print("-" * 40)
    memory = overview['memory']
    swap = overview['swap']
    
    print(f"📊 Total RAM: {memory.total / (1024**3):.1f} GB")
    print(f"💾 Used RAM: {memory.used / (1024**3):.1f} GB ({memory.percent:.1f}%)")
    print(f"🆓 Free RAM: {memory.free / (1024**3):.1f} GB")
    print(f"📈 Available RAM: {memory.available / (1024**3):.1f} GB")
    print(f"🔄 Cached: {memory.cached / (1024**3):.1f} GB")
    print(f"📝 Buffers: {memory.buffers / (1024**3):.1f} GB")
    print()
    
    print(f"💿 Total Swap: {swap.total / (1024**3):.1f} GB")
    print(f"📊 Used Swap: {swap.used / (1024**3):.1f} GB ({swap.percent:.1f}%)")
    print(f"🆓 Free Swap: {swap.free / (1024**3):.1f} GB")
    print()
    
    # CPU Analysis
    print("⚡ CPU ANALYSIS")
    print("-" * 40)
    print(f"📊 CPU Usage: {overview['cpu_percent']:.1f}%")
    print(f"📈 Load Average: {overview['load_avg'][0]:.2f}, {overview['load_avg'][1]:.2f}, {overview['load_avg'][2]:.2f}")
    print("   (1min, 5min, 15min averages)")
    print()
    
    # Disk Analysis
    print("💾 DISK ANALYSIS")
    print("-" * 40)
    disk = overview['disk']
    print(f"📊 Total Disk: {disk.total / (1024**3):.1f} GB")
    print(f"💾 Used Disk: {disk.used / (1024**3):.1f} GB ({disk.percent:.1f}%)")
    print(f"🆓 Free Disk: {disk.free / (1024**3):.1f} GB")
    print()
    
    # System Health Score
    health = get_system_health_score()
    print("🏥 SYSTEM HEALTH SCORE")
    print("-" * 40)
    print(f"📊 Overall Score: {health['score']:.1f}/100 {health['status']}")
    print(f"🧠 Memory Score: {health['memory_score']:.1f}/100")
    print(f"💿 Swap Score: {health['swap_score']:.1f}/100")
    print(f"⚡ CPU Score: {health['cpu_score']:.1f}/100")
    print()
    
    # Top Processes Analysis
    print("🔝 TOP PROCESSES ANALYSIS")
    print("-" * 40)
    processes = get_detailed_process_analysis()
    
    print(f"{'PID':<8} {'Name':<20} {'CPU%':<8} {'Memory':<12} {'Status':<15} {'Analysis'}")
    print("-" * 80)
    
    for proc in processes[:10]:
        pid = proc['pid']
        name = proc['name'][:19]
        cpu = proc['cpu_percent'] or 0
        memory = f"{proc['memory_mb']:.1f}MB"
        status = proc['status']
        
        # Analysis
        status_analysis = analyze_process_status(status)
        memory_analysis = analyze_memory_usage(proc['memory_mb'])
        cpu_analysis = analyze_cpu_usage(cpu)
        
        print(f"{pid:<8} {name:<20} {cpu:<8.1f} {memory:<12} {status:<15} {status_analysis}")
        print(f"{'':8} {'':20} {'':8} {'':12} {'':15} {memory_analysis}")
        print(f"{'':8} {'':20} {'':8} {'':12} {'':15} {cpu_analysis}")
        print()
    
    # Network Analysis
    print("🌐 NETWORK ANALYSIS")
    print("-" * 40)
    network = get_network_analysis()
    net_io = network['net_io']
    
    print(f"📤 Bytes Sent: {net_io.bytes_sent / (1024**2):.1f} MB")
    print(f"📥 Bytes Received: {net_io.bytes_recv / (1024**2):.1f} MB")
    print(f"📤 Packets Sent: {net_io.packets_sent:,}")
    print(f"📥 Packets Received: {net_io.packets_recv:,}")
    print(f"🔗 Active Connections: {network['net_connections']}")
    print()
    
    # Disk I/O Analysis
    print("💾 DISK I/O ANALYSIS")
    print("-" * 40)
    disk_io = get_disk_io_analysis()
    
    print(f"📖 Read Count: {disk_io.read_count:,}")
    print(f"📝 Write Count: {disk_io.write_count:,}")
    print(f"📖 Read Bytes: {disk_io.read_bytes / (1024**2):.1f} MB")
    print(f"📝 Write Bytes: {disk_io.write_bytes / (1024**2):.1f} MB")
    print()
    
    # Recommendations
    print("💡 RECOMMENDATIONS")
    print("-" * 40)
    
    if health['score'] < 60:
        print("⚠️  System health is below optimal. Consider:")
        if health['memory_score'] < 60:
            print("   - Monitor memory usage and restart high-memory processes")
        if health['cpu_score'] < 60:
            print("   - Check for CPU-intensive processes")
        if health['swap_score'] < 60:
            print("   - Swap usage detected, consider increasing RAM or optimizing processes")
    else:
        print("✅ System is running well!")
    
    print()
    print("=" * 80)
    print("📋 Report completed.")
    print("=" * 80)

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("System Analyzer - Comprehensive System Status Report")
        print("Usage: python3 system_analyzer_standalone.py")
        print("This tool provides detailed analysis of system performance, processes, and resources")
        print("with explanations of what each metric means.")
        return
    
    generate_system_report()

if __name__ == "__main__":
    main()
