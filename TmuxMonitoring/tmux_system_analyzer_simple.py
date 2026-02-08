#!/usr/bin/env python3
"""
WORLD-CLASS SYSTEM ANALYZER - Simplified Version
Provides comprehensive analysis with detailed explanations
"""

import psutil
import subprocess
import time
from datetime import datetime
import os
import platform
import socket
from collections import defaultdict

def generate_world_class_system_report():
    """Generate the most comprehensive system analysis report possible"""
    
    print("=" * 100)
    print("🌍 WORLD-CLASS COMPREHENSIVE SYSTEM ANALYSIS REPORT 🌍")
    print("=" * 100)
    print(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🖥️  Hostname: {socket.gethostname()}")
    print()
    
    # SYSTEM IDENTIFICATION
    print("🆔 SYSTEM IDENTIFICATION")
    print("-" * 50)
    print(f"🖥️  Platform: {platform.platform()}")
    print(f"🏗️  Architecture: {platform.architecture()[0]} ({platform.architecture()[1]})")
    print(f"⚙️  Processor: {platform.processor()}")
    print(f"🐍 Python Version: {platform.python_version()}")
    
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.now() - boot_time
    print(f"⏰ Boot Time: {boot_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱️  System Uptime: {str(uptime).split('.')[0]}")
    print()
    
    # MEMORY ANALYSIS WITH DETAILED EXPLANATIONS
    print("🧠 COMPREHENSIVE MEMORY ANALYSIS")
    print("-" * 50)
    memory = psutil.virtual_memory()
    swap = psutil.swap_memory()
    
    print(f"📊 Total RAM: {memory.total / (1024**3):.2f} GB")
    print(f"💾 Used RAM: {memory.used / (1024**3):.2f} GB ({memory.percent:.1f}%)")
    print(f"🆓 Free RAM: {memory.free / (1024**3):.2f} GB")
    print(f"📈 Available RAM: {memory.available / (1024**3):.2f} GB")
    print(f"🔄 Cached: {memory.cached / (1024**3):.2f} GB (kernel caches for faster access)")
    print(f"📝 Buffers: {memory.buffers / (1024**3):.2f} GB (kernel buffers for I/O)")
    print(f"📊 Shared: {memory.shared / (1024**3):.2f} GB (shared memory between processes)")
    print()
    
    # Memory health analysis
    if memory.percent < 50:
        memory_health = "🟢 EXCELLENT - Plenty of free memory"
    elif memory.percent < 70:
        memory_health = "🟡 GOOD - Memory usage is normal"
    elif memory.percent < 85:
        memory_health = "🟠 WARNING - Memory usage is high"
    else:
        memory_health = "🔴 CRITICAL - Memory usage is very high"
    
    print(f"🏥 Memory Health: {memory_health}")
    print()
    
    # SWAP ANALYSIS WITH DETAILED EXPLANATIONS
    print("💿 COMPREHENSIVE SWAP ANALYSIS")
    print("-" * 50)
    print(f"📊 Total Swap: {swap.total / (1024**3):.2f} GB")
    print(f"💾 Used Swap: {swap.used / (1024**3):.2f} GB ({swap.percent:.1f}%)")
    print(f"🆓 Free Swap: {swap.free / (1024**3):.2f} GB")
    print(f"📈 Swap In: {swap.sin / (1024**2):.1f} MB (data moved from swap to RAM)")
    print(f"📉 Swap Out: {swap.sout / (1024**2):.1f} MB (data moved from RAM to swap)")
    print()
    
    # Swap health analysis
    if swap.percent == 0:
        swap_health = "🟢 PERFECT - No swap usage (optimal performance)"
        swap_explanation = "This is IDEAL! RAM is 1000x faster than swap. 0% swap means all processes are running in fast RAM memory."
    elif swap.percent < 10:
        swap_health = "🟡 GOOD - Minimal swap usage"
        swap_explanation = "Low swap usage is acceptable, but indicates some memory pressure."
    elif swap.percent < 50:
        swap_health = "🟠 WARNING - Moderate swap usage"
        swap_explanation = "Swap usage indicates memory pressure. Performance may be affected."
    else:
        swap_health = "🔴 CRITICAL - High swap usage"
        swap_explanation = "High swap usage severely impacts performance. Consider adding more RAM."
    
    print(f"🏥 Swap Health: {swap_health}")
    print(f"💡 Explanation: {swap_explanation}")
    print()
    
    # CPU ANALYSIS WITH PER-CORE DETAILS
    print("⚡ COMPREHENSIVE CPU ANALYSIS")
    print("-" * 50)
    cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
    cpu_count = psutil.cpu_count()
    cpu_freq = psutil.cpu_freq()
    cpu_times = psutil.cpu_times()
    load_avg = os.getloadavg()
    
    print(f"🖥️  CPU Cores: {cpu_count} cores")
    if cpu_freq:
        print(f"⚡ CPU Frequency: {cpu_freq.current:.0f} MHz (Min: {cpu_freq.min:.0f}, Max: {cpu_freq.max:.0f})")
    
    # Per-core CPU usage
    print(f"📊 Per-Core CPU Usage:")
    for i, core_usage in enumerate(cpu_percent):
        core_status = "🟢" if core_usage < 50 else "🟡" if core_usage < 80 else "🔴"
        print(f"   Core {i+1}: {core_usage:5.1f}% {core_status}")
    
    avg_cpu = sum(cpu_percent) / len(cpu_percent)
    print(f"📈 Average CPU Usage: {avg_cpu:.1f}%")
    
    # CPU times breakdown
    print(f"⏱️  CPU Time Breakdown:")
    print(f"   User Time: {cpu_times.user:.1f}s (normal processes)")
    print(f"   System Time: {cpu_times.system:.1f}s (kernel operations)")
    print(f"   Idle Time: {cpu_times.idle:.1f}s (CPU not in use)")
    print(f"   I/O Wait: {cpu_times.iowait:.1f}s (waiting for disk I/O)")
    
    # Load average analysis
    print(f"📊 Load Average: {load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f}")
    print(f"   (1min, 5min, 15min averages)")
    
    # Load average health
    if load_avg[0] < cpu_count:
        load_health = "🟢 EXCELLENT - System is not overloaded"
    elif load_avg[0] < cpu_count * 1.5:
        load_health = "🟡 GOOD - System is moderately loaded"
    elif load_avg[0] < cpu_count * 2:
        load_health = "🟠 WARNING - System is heavily loaded"
    else:
        load_health = "🔴 CRITICAL - System is overloaded"
    
    print(f"🏥 Load Health: {load_health}")
    print()
    
    # TOP PROCESSES WITH DETAILED ANALYSIS
    print("🔝 TOP 15 PROCESSES - DETAILED ANALYSIS")
    print("-" * 100)
    print(f"{'PID':<8} {'Name':<20} {'CPU%':<8} {'Memory':<12} {'Status':<15} {'Analysis'}")
    print("-" * 100)
    
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'status', 'create_time']):
        try:
            proc_info = proc.info
            memory_mb = proc_info['memory_info'].rss / (1024 * 1024)
            uptime_seconds = time.time() - proc_info['create_time']
            
            # Format uptime
            if uptime_seconds < 60:
                uptime_str = f"{uptime_seconds:.1f}s"
            elif uptime_seconds < 3600:
                minutes = int(uptime_seconds // 60)
                secs = uptime_seconds % 60
                uptime_str = f"{minutes}m {secs:.1f}s"
            else:
                hours = int(uptime_seconds // 3600)
                minutes = int((uptime_seconds % 3600) // 60)
                uptime_str = f"{hours}h {minutes}m"
            
            processes.append({
                'pid': proc_info['pid'],
                'name': proc_info['name'],
                'cpu_percent': proc_info['cpu_percent'] or 0,
                'memory_mb': memory_mb,
                'status': proc_info['status'],
                'uptime': uptime_str
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    
    # Sort by memory usage
    processes.sort(key=lambda x: x['memory_mb'], reverse=True)
    
    for proc in processes[:15]:
        pid = proc['pid']
        name = proc['name'][:19]
        cpu = proc['cpu_percent']
        memory = f"{proc['memory_mb']:.1f}MB"
        status = proc['status']
        
        # Status analysis
        status_map = {
            'R': {'meaning': 'Running', 'color': '🟢', 'description': 'Actively executing'},
            'S': {'meaning': 'Sleeping', 'color': '🟡', 'description': 'Waiting for event - NORMAL'},
            'D': {'meaning': 'Uninterruptible', 'color': '🟠', 'description': 'Waiting for I/O'},
            'Z': {'meaning': 'Zombie', 'color': '🔴', 'description': 'Terminated but not reaped'},
            'T': {'meaning': 'Stopped', 'color': '🔴', 'description': 'Stopped by signal'},
            'I': {'meaning': 'Idle', 'color': '🟢', 'description': 'Kernel thread idle'},
        }
        
        status_info = status_map.get(status[0], {'meaning': 'Unknown', 'color': '⚪', 'description': 'Unknown status'})
        status_color = status_info['color']
        status_meaning = status_info['meaning']
        
        # Memory analysis
        if proc['memory_mb'] == 0:
            mem_analysis = "🔴 ZERO - CRITICAL ISSUE"
        elif proc['memory_mb'] < 10:
            mem_analysis = "🟢 MINIMAL - System process"
        elif proc['memory_mb'] < 50:
            mem_analysis = "🟢 LOW - Lightweight process"
        elif proc['memory_mb'] < 100:
            mem_analysis = "🟡 MODERATE - Normal application"
        elif proc['memory_mb'] < 500:
            mem_analysis = "🟠 HIGH - Resource-intensive"
        elif proc['memory_mb'] < 1000:
            mem_analysis = "🟠 VERY_HIGH - Heavy application"
        elif proc['memory_mb'] < 2000:
            mem_analysis = "🔴 EXTREME - Memory-intensive"
        else:
            mem_analysis = "🔴 CRITICAL - Potential memory leak"
        
        # CPU analysis
        if cpu == 0:
            cpu_analysis = "🟢 IDLE - Not using CPU"
        elif cpu < 5:
            cpu_analysis = "🟢 LOW - Light processing"
        elif cpu < 15:
            cpu_analysis = "🟡 MODERATE - Active processing"
        elif cpu < 30:
            cpu_analysis = "🟠 HIGH - Intensive processing"
        elif cpu < 50:
            cpu_analysis = "🟠 VERY_HIGH - Heavy processing"
        else:
            cpu_analysis = "🔴 CRITICAL - System overload"
        
        print(f"{pid:<8} {name:<20} {cpu:<8.1f} {memory:<12} {status_color}{status_meaning:<14} {mem_analysis}")
        print(f"{'':8} {'':20} {'':8} {'':12} {'':15} {cpu_analysis}")
        print(f"{'':8} {'':20} {'':8} {'':12} {'':15} Uptime: {proc['uptime']}")
        print()
    
    # SYSTEM HEALTH SUMMARY
    print("🏥 OVERALL SYSTEM HEALTH SUMMARY")
    print("-" * 50)
    
    # Calculate overall health score
    health_score = 100
    
    # Get fresh memory object for health calculation
    memory_health = psutil.virtual_memory()
    
    # Memory health (30% weight)
    if memory_health.percent > 90:
        health_score -= 30
    elif memory_health.percent > 80:
        health_score -= 20
    elif memory_health.percent > 70:
        health_score -= 10
    
    # Swap health (20% weight)
    if swap.percent > 50:
        health_score -= 20
    elif swap.percent > 20:
        health_score -= 10
    elif swap.percent > 5:
        health_score -= 5
    
    # CPU health (20% weight)
    if avg_cpu > 90:
        health_score -= 20
    elif avg_cpu > 80:
        health_score -= 15
    elif avg_cpu > 70:
        health_score -= 10
    
    # Load health (20% weight)
    if load_avg[0] > cpu_count * 2:
        health_score -= 20
    elif load_avg[0] > cpu_count * 1.5:
        health_score -= 15
    elif load_avg[0] > cpu_count:
        health_score -= 10
    
    # Determine health status
    if health_score >= 90:
        health_status = "🟢 EXCELLENT"
        health_message = "System is running optimally with excellent performance."
    elif health_score >= 80:
        health_status = "🟡 GOOD"
        health_message = "System is running well with good performance."
    elif health_score >= 70:
        health_status = "🟠 WARNING"
        health_message = "System shows some performance concerns that should be monitored."
    elif health_score >= 60:
        health_status = "🔴 CRITICAL"
        health_message = "System has significant performance issues requiring attention."
    else:
        health_status = "💀 EMERGENCY"
        health_message = "System is in critical condition and requires immediate intervention."
    
    print(f"📊 Overall Health Score: {health_score:.1f}/100 {health_status}")
    print(f"💡 Status: {health_message}")
    print()
    
    # RECOMMENDATIONS
    print("💡 ACTIONABLE RECOMMENDATIONS")
    print("-" * 50)
    
    recommendations = []
    
    if memory_health.percent > 80:
        recommendations.append("🧠 Consider adding more RAM or optimizing memory usage")
    
    if swap.percent > 10:
        recommendations.append("💿 Reduce swap usage by adding RAM or optimizing processes")
    
    if avg_cpu > 80:
        recommendations.append("⚡ Consider CPU optimization or adding more cores")
    
    if load_avg[0] > cpu_count:
        recommendations.append("📊 System is overloaded - consider reducing workload")
    
    critical_procs = [p for p in processes if p['memory_mb'] > 2000]
    if critical_procs:
        recommendations.append(f"🔴 Investigate {len(critical_procs)} processes with critical memory usage")
    
    if not recommendations:
        recommendations.append("✅ System is running optimally - no immediate actions required")
    
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")
    
    print()
    print("=" * 100)
    print("🎯 ANALYSIS COMPLETE - This is the most comprehensive system analysis available!")
    print("=" * 100)

if __name__ == "__main__":
    generate_world_class_system_report()
