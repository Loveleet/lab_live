st9988ar
#!/usr/bin/env python3
"""
Test script for Queue Management System
This script tests the queue management logic without running the full cleaner
"""

import os
import sys
import time
import datetime

# Add the current directory to the path so we can import from tmux_bot_cleaner
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tmux_bot_cleaner import calculate_restart_queue, get_process_start_time, RESTART_INTERVAL

def test_queue_management():
    """Test the queue management system with mock data"""
    print("🧪 Testing Queue Management System")
    print("=" * 50)
    
    # Test scenario 1: Multiple bots with same uptime timer
    print("\n📋 Test Scenario 1: Multiple bots with R-10 timers")
    print("Expected: First bot no delay, subsequent bots get +3m delays")
    
    # Mock current time
    current_time = time.time()
    
    # Create mock bots with same start time (simulating simultaneous start)
    mock_bots = [
        ("/root/bot1.py", 10),  # 10 minute uptime timer
        ("/root/bot2.py", 10),  # 10 minute uptime timer  
        ("/root/bot3.py", 10),  # 10 minute uptime timer
    ]
    
    # Mock process start times (all started at same time)
    start_time = current_time - 300  # 5 minutes ago
    
    # Override get_process_start_time for testing
    original_func = get_process_start_time
    
    def mock_get_process_start_time(script_path):
        return start_time
    
    # Temporarily replace the function
    import tmux_bot_cleaner
    tmux_bot_cleaner.get_process_start_time = mock_get_process_start_time
    
    try:
        # Calculate restart queue
        queue_results = calculate_restart_queue(mock_bots)
        
        print(f"\n📊 Queue Results:")
        for i, result in enumerate(queue_results):
            delay_str = f"+{result['delay_minutes']}m" if result['delay_minutes'] > 0 else "no delay"
            original_restart = datetime.datetime.fromtimestamp(result['original_restart_time']).strftime("%H:%M:%S")
            adjusted_restart = datetime.datetime.fromtimestamp(result['adjusted_restart_time']).strftime("%H:%M:%S")
            
            print(f"  {i+1}. {os.path.basename(result['script_path'])}:")
            print(f"     Original restart: {original_restart}")
            print(f"     Adjusted restart: {adjusted_restart}")
            print(f"     Delay: {delay_str}")
        
        # Verify expected behavior
        print(f"\n✅ Verification:")
        if queue_results[0]['delay_minutes'] == 0:
            print("  ✓ First bot has no delay (highest priority)")
        else:
            print("  ✗ First bot should have no delay")
            
        if queue_results[1]['delay_minutes'] == 3:
            print("  ✓ Second bot has 3-minute delay")
        else:
            print(f"  ✗ Second bot should have 3-minute delay, got {queue_results[1]['delay_minutes']}")
            
        if queue_results[2]['delay_minutes'] == 6:
            print("  ✓ Third bot has 6-minute delay")
        else:
            print(f"  ✗ Third bot should have 6-minute delay, got {queue_results[2]['delay_minutes']}")
    
    finally:
        # Restore original function
        tmux_bot_cleaner.get_process_start_time = original_func
    
    # Test scenario 2: Bots with different start times
    print(f"\n📋 Test Scenario 2: Bots with different start times")
    print("Expected: No delays needed when start times are different")
    
    def mock_get_process_start_time_different(script_path):
        # Different start times for each bot
        if "bot1" in script_path:
            return start_time  # 5 minutes ago
        elif "bot2" in script_path:
            return start_time + 600  # 5 minutes later (10 minutes ago)
        else:
            return start_time + 1200  # 10 minutes later (15 minutes ago)
    
    tmux_bot_cleaner.get_process_start_time = mock_get_process_start_time_different
    
    try:
        queue_results = calculate_restart_queue(mock_bots)
        
        print(f"\n📊 Queue Results:")
        for i, result in enumerate(queue_results):
            delay_str = f"+{result['delay_minutes']}m" if result['delay_minutes'] > 0 else "no delay"
            original_restart = datetime.datetime.fromtimestamp(result['original_restart_time']).strftime("%H:%M:%S")
            adjusted_restart = datetime.datetime.fromtimestamp(result['adjusted_restart_time']).strftime("%H:%M:%S")
            
            print(f"  {i+1}. {os.path.basename(result['script_path'])}:")
            print(f"     Original restart: {original_restart}")
            print(f"     Adjusted restart: {adjusted_restart}")
            print(f"     Delay: {delay_str}")
        
        # Verify no delays needed
        print(f"\n✅ Verification:")
        all_no_delay = all(result['delay_minutes'] == 0 for result in queue_results)
        if all_no_delay:
            print("  ✓ All bots have no delays (different start times)")
        else:
            print("  ✗ Some bots have delays when they shouldn't")
    
    finally:
        # Restore original function
        tmux_bot_cleaner.get_process_start_time = original_func
    
    print(f"\n🎯 Queue Management Test Complete!")
    print(f"📋 RESTART_INTERVAL: {RESTART_INTERVAL} minutes")
    print(f"💡 This ensures minimum {RESTART_INTERVAL} minute gap between bot restarts")

if __name__ == "__main__":
    test_queue_management()

