"""
Millware Integration Test - Selenium AutoFill
Tests the smart flow selection and Millware system integration
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.browser_manager import BrowserManager
from core.automation_engine import AutomationEngine
from main import SeleniumAutoFillApp


async def test_login_detection():
    """Test login status detection on Millware system"""
    
    browser_manager = BrowserManager({
        'headless': False,
        'window_size': (1280, 720),
        'disable_notifications': True
    })
    
    try:
        driver = browser_manager.create_driver()
        automation_engine = AutomationEngine(driver, {'event_delay': 0.5})
        
        # Create app instance for testing login detection
        app = SeleniumAutoFillApp()
        app.driver = driver
        app.browser_manager = browser_manager
        app.automation_engine = automation_engine
        
        # Show automation badge
        automation_engine.visual_feedback.show_automation_badge()
        
        print("🔍 Testing Login Status Detection on Millware System")
        print("=" * 60)
        
        # Navigate to Millware login page
        millware_url = "http://millwarep3.rebinmas.com:8003/"
        print(f"🌐 Navigating to: {millware_url}")
        driver.get(millware_url)
        
        await asyncio.sleep(3)  # Wait for page to load
        
        # Test login detection
        status = await app.check_login_status()
        
        print(f"\n📊 Detection Results:")
        print(f"   📍 Current URL: {status['current_url']}")
        print(f"   📋 Page Title: {status['page_title']}")
        print(f"   🔍 Detected State: {status['detected_state']}")
        print(f"   👤 Login Status: {'✅ Logged In' if status['is_logged_in'] else '❌ Not Logged In'}")
        print(f"   💡 Recommended Flow: {status['recommended_flow']}")
        
        # Test different scenarios
        scenarios = [
            {
                'name': 'Login Page Detection',
                'description': 'Testing detection on login page'
            }
        ]
        
        print(f"\n🧪 Test Scenarios:")
        for i, scenario in enumerate(scenarios, 1):
            print(f"   {i}. {scenario['name']}: {scenario['description']}")
        
        # Check for specific elements
        print(f"\n🔍 Element Detection:")
        
        # Check for login form elements
        try:
            username_field = driver.find_element(By.CSS_SELECTOR, "#txtUsername")
            print(f"   ✅ Username field found: {username_field.is_displayed()}")
        except:
            print(f"   ❌ Username field not found")
        
        try:
            password_field = driver.find_element(By.CSS_SELECTOR, "#txtPassword")
            print(f"   ✅ Password field found: {password_field.is_displayed()}")
        except:
            print(f"   ❌ Password field not found")
        
        try:
            login_button = driver.find_element(By.CSS_SELECTOR, "#btnLogin")
            print(f"   ✅ Login button found: {login_button.is_displayed()}")
        except:
            print(f"   ❌ Login button not found")
        
        # Check for navigation elements (if logged in)
        try:
            nav_elements = driver.find_elements(By.CSS_SELECTOR, "a.popout.level1.static")
            if nav_elements:
                print(f"   ✅ Navigation menu found: {len(nav_elements)} items")
            else:
                print(f"   ❌ Navigation menu not found")
        except:
            print(f"   ❌ Navigation menu not found")
        
        await asyncio.sleep(5)  # Keep browser open for manual inspection
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        browser_manager.quit_driver()


async def test_smart_flow_selection():
    """Test the smart flow selection feature"""
    
    print("🧠 Testing Smart Flow Selection")
    print("This test will create an app instance and test the smart flow logic")
    
    app = SeleniumAutoFillApp()
    
    try:
        await app.initialize()
        
        print("✅ App initialized successfully")
        print("🔍 Testing smart flow selection logic...")
        
        # Test the smart flow selection
        await app.smart_flow_selection()
        
    except Exception as e:
        print(f"❌ Error during smart flow test: {e}")
    
    finally:
        await app.cleanup()


async def test_flow_files():
    """Test loading and validating the flow files"""
    
    print("📁 Testing Flow File Loading")
    print("=" * 50)
    
    flows_dir = Path(__file__).parent.parent / "flows"
    
    # Test pre-login flow
    pre_login_file = flows_dir / "pre_login_flow.json"
    post_login_file = flows_dir / "post_login_flow.json"
    
    import json
    
    try:
        if pre_login_file.exists():
            with open(pre_login_file, 'r') as f:
                pre_flow = json.load(f)
            
            print(f"✅ Pre-login flow loaded successfully")
            print(f"   📁 File: {pre_login_file}")
            print(f"   📋 Name: {pre_flow['name']}")
            print(f"   📝 Description: {pre_flow['description']}")
            print(f"   🔢 Events: {len(pre_flow['events'])}")
            print(f"   🔗 Variables: {list(pre_flow['variables'].keys())}")
            
            # Check for required events
            event_types = [event.get('type') for event in pre_flow['events']]
            required_types = ['navigate', 'input', 'click', 'popup_handler']
            
            print(f"   📊 Event types: {set(event_types)}")
            
            for req_type in required_types:
                if req_type in event_types:
                    print(f"   ✅ Required event type '{req_type}' found")
                else:
                    print(f"   ❌ Required event type '{req_type}' missing")
        else:
            print(f"❌ Pre-login flow file not found: {pre_login_file}")
        
        if post_login_file.exists():
            with open(post_login_file, 'r') as f:
                post_flow = json.load(f)
            
            print(f"\n✅ Post-login flow loaded successfully")
            print(f"   📁 File: {post_login_file}")
            print(f"   📋 Name: {post_flow['name']}")
            print(f"   📝 Description: {post_flow['description']}")
            print(f"   🔢 Events: {len(post_flow['events'])}")
            print(f"   🔗 Variables: {list(post_flow['variables'].keys())}")
            
            # Check for required events
            event_types = [event.get('type') for event in post_flow['events']]
            required_types = ['navigate', 'input', 'keyboard', 'prevent_redirect']
            
            print(f"   📊 Event types: {set(event_types)}")
            
            for req_type in required_types:
                if req_type in event_types:
                    print(f"   ✅ Required event type '{req_type}' found")
                else:
                    print(f"   ❌ Required event type '{req_type}' missing")
        else:
            print(f"❌ Post-login flow file not found: {post_login_file}")
            
    except Exception as e:
        print(f"❌ Error loading flow files: {e}")


async def main():
    """Main test function"""
    print("🤖 Millware Integration Test Suite")
    print("=" * 50)
    
    tests = [
        ("Login Status Detection", test_login_detection),
        ("Smart Flow Selection", test_smart_flow_selection),
        ("Flow Files Validation", test_flow_files)
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
    # Add missing import
    from selenium.webdriver.common.by import By
    asyncio.run(main()) 