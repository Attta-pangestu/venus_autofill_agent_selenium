"""
Chrome Extension Flows Example - Selenium AutoFill
Demonstrates the converted Chrome extension flows with keyboard interactions and popup handling
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.browser_manager import BrowserManager
from core.automation_engine import AutomationEngine


async def test_keyboard_events():
    """Test keyboard event functionality"""
    
    browser_manager = BrowserManager({
        'headless': False,
        'window_size': (1280, 720),
        'disable_notifications': True
    })
    
    try:
        driver = browser_manager.create_driver()
        automation_engine = AutomationEngine(driver, {'event_delay': 0.5})
        
        # Show automation badge
        automation_engine.visual_feedback.show_automation_badge()
        
        # Test keyboard events on a simple form
        keyboard_test_flow = [
            {
                "type": "navigate",
                "url": "https://httpbin.org/forms/post",
                "description": "Navigate to test form"
            },
            {
                "type": "input",
                "selector": "input[name='custname']",
                "value": "Test User",
                "description": "Enter name"
            },
            {
                "type": "keyboard",
                "selector": "input[name='custname']",
                "key": "Tab",
                "description": "Tab to next field",
                "waitAfterKey": 500
            },
            {
                "type": "input",
                "selector": "input[name='custtel']",
                "value": "555-1234",
                "description": "Enter phone"
            },
            {
                "type": "keyboard",
                "selector": "input[name='custtel']",
                "key": "ArrowDown",
                "description": "Test arrow key",
                "waitAfterKey": 300
            },
            {
                "type": "keyboard",
                "selector": "input[name='custtel']",
                "key": "Enter",
                "description": "Test Enter key",
                "preventDefault": True,
                "waitAfterKey": 500
            }
        ]
        
        print("🎹 Testing keyboard events...")
        
        result = await automation_engine.execute_automation_flow(keyboard_test_flow)
        
        if result.success:
            print("✅ Keyboard events test completed successfully!")
            automation_engine.visual_feedback.show_success_notification("Keyboard test successful!")
        else:
            print("❌ Keyboard events test failed!")
            automation_engine.visual_feedback.show_error_notification("Keyboard test failed!")
        
        await asyncio.sleep(3)
        
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        browser_manager.quit_driver()


async def test_prevent_redirect():
    """Test prevent redirect functionality"""
    
    browser_manager = BrowserManager()
    
    try:
        driver = browser_manager.create_driver()
        automation_engine = AutomationEngine(driver, {})
        
        # Test redirect prevention
        redirect_test_flow = [
            {
                "type": "navigate",
                "url": "https://httpbin.org/html",
                "description": "Navigate to test page"
            },
            {
                "type": "prevent_redirect",
                "timeout": 5000,
                "description": "Set up redirect prevention",
                "blockMethods": [
                    "location.href",
                    "location.assign",
                    "location.replace"
                ],
                "allowManualNavigation": False
            },
            {
                "type": "wait",
                "duration": 2000,
                "description": "Wait with redirect prevention active"
            }
        ]
        
        print("🚫 Testing redirect prevention...")
        
        result = await automation_engine.execute_automation_flow(redirect_test_flow)
        
        if result.success:
            print("✅ Redirect prevention test completed!")
            automation_engine.visual_feedback.show_success_notification("Redirect prevention test successful!")
        else:
            print("❌ Redirect prevention test failed!")
            automation_engine.visual_feedback.show_error_notification("Redirect prevention test failed!")
        
        await asyncio.sleep(2)
        
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        browser_manager.quit_driver()


async def test_chrome_extension_flows():
    """Test the actual converted Chrome extension flows"""
    
    print("🔧 Testing Chrome Extension Converted Flows")
    print("Note: These flows are designed for the specific Millware system")
    print("They may not work without access to the actual system.")
    
    # Load flow files
    flows_dir = Path(__file__).parent.parent / "flows"
    
    try:
        # Load pre-login flow
        pre_login_file = flows_dir / "pre_login_flow.json"
        post_login_file = flows_dir / "post_login_flow.json"
        
        if pre_login_file.exists() and post_login_file.exists():
            print(f"✅ Found flow files:")
            print(f"   - {pre_login_file}")
            print(f"   - {post_login_file}")
            
            # Read flow contents to show structure
            import json
            
            with open(pre_login_file, 'r') as f:
                pre_flow = json.load(f)
            
            with open(post_login_file, 'r') as f:
                post_flow = json.load(f)
            
            print(f"\n📋 Pre-login flow: {pre_flow['name']}")
            print(f"   Description: {pre_flow['description']}")
            print(f"   Events: {len(pre_flow['events'])}")
            print(f"   Variables: {list(pre_flow['variables'].keys())}")
            
            print(f"\n📋 Post-login flow: {post_flow['name']}")
            print(f"   Description: {post_flow['description']}")
            print(f"   Events: {len(post_flow['events'])}")
            print(f"   Variables: {list(post_flow['variables'].keys())}")
            
            print("\n🔍 Event types in flows:")
            all_event_types = set()
            for event in pre_flow['events'] + post_flow['events']:
                all_event_types.add(event.get('type', 'unknown'))
            
            for event_type in sorted(all_event_types):
                print(f"   - {event_type}")
            
        else:
            print(f"❌ Flow files not found in {flows_dir}")
            
    except Exception as e:
        print(f"Error reading flow files: {e}")


async def main():
    """Main function to run tests"""
    print("🤖 Chrome Extension Flows Test Suite")
    print("=" * 50)
    
    tests = [
        ("Keyboard Events", test_keyboard_events),
        ("Prevent Redirect", test_prevent_redirect),
        ("Chrome Extension Flows Analysis", test_chrome_extension_flows)
    ]
    
    for i, (name, func) in enumerate(tests, 1):
        print(f"{i}. {name}")
    
    print("0. Exit")
    print("-" * 50)
    
    choice = input("Select a test to run (0-3): ").strip()
    
    if choice == "0":
        print("👋 Goodbye!")
        return
    
    try:
        test_index = int(choice) - 1
        if 0 <= test_index < len(tests):
            name, func = tests[test_index]
            print(f"\n🚀 Running {name} test...")
            await func()
        else:
            print("❌ Invalid choice!")
    except ValueError:
        print("❌ Please enter a valid number!")
    except Exception as e:
        print(f"❌ Error running test: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 