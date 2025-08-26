#!/usr/bin/env python3
"""
WebDriver Connection Test Script

This script tests the WebDriver connection fix to ensure proper communication
between the web UI and WebDriver when processing selected records.
"""

import sys
import asyncio
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from run_user_controlled_automation_enhanced import EnhancedUserControlledAutomationSystem

def test_webdriver_connection():
    """
    Test WebDriver connection and refresh functionality
    """
    print("🧪 TESTING WEBDRIVER CONNECTION FIX")
    print("="*50)
    
    # Initialize the system
    system = EnhancedUserControlledAutomationSystem()
    
    print("\n1️⃣ Testing initial state...")
    connection_status = system._verify_webdriver_connection()
    print(f"   Initial connection status: {'✅ Connected' if connection_status else '❌ Not Connected'}")
    
    print("\n2️⃣ Initializing browser system...")
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        success = loop.run_until_complete(system.initialize_browser_system())
        print(f"   Browser initialization: {'✅ Success' if success else '❌ Failed'}")
        
        if success:
            print("\n3️⃣ Testing connection after initialization...")
            connection_status = system._verify_webdriver_connection()
            print(f"   Post-init connection status: {'✅ Connected' if connection_status else '❌ Not Connected'}")
            
            if connection_status:
                print("\n4️⃣ Testing WebDriver refresh functionality...")
                driver = system.processor.browser_manager.get_driver()
                if driver:
                    try:
                        print(f"   Current URL before refresh: {driver.current_url}")
                        driver.refresh()
                        time.sleep(2)  # Wait for refresh to complete
                        print(f"   Current URL after refresh: {driver.current_url}")
                        print(f"   Page title: {driver.title}")
                        print("   ✅ WebDriver refresh test successful!")
                        
                        # Test responsiveness after refresh
                        is_alive = system.processor.browser_manager.is_driver_alive()
                        print(f"   Driver responsiveness: {'✅ Responsive' if is_alive else '❌ Unresponsive'}")
                        
                    except Exception as e:
                        print(f"   ❌ WebDriver refresh test failed: {e}")
                else:
                    print("   ❌ Could not get driver instance")
            else:
                print("   ❌ Connection verification failed - cannot test refresh")
        else:
            print("   ❌ Browser initialization failed - cannot proceed with tests")
            
    except Exception as e:
        print(f"   ❌ Test failed with error: {e}")
    finally:
        loop.close()
    
    print("\n🏁 CONNECTION TEST COMPLETED")
    print("="*50)
    
    # Provide guidance based on results
    if connection_status:
        print("\n✅ RESULT: WebDriver connection is working properly!")
        print("   The fix should resolve the UI ↔ WebDriver communication issue.")
        print("   When you click 'Process Selected', the browser should refresh successfully.")
    else:
        print("\n❌ RESULT: WebDriver connection issues detected.")
        print("   Troubleshooting steps:")
        print("   1. Ensure Chrome browser is installed and updated")
        print("   2. Check if ChromeDriver is compatible with your Chrome version")
        print("   3. Verify network connectivity to millwarep3:8004")
        print("   4. Try restarting the application")

if __name__ == "__main__":
    test_webdriver_connection()