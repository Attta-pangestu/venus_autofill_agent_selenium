#!/usr/bin/env python3
"""
Debug script to check transaction date field availability
This script will check if MainContent_txtTrxDate field exists on the task register page
"""

import asyncio
import sys
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from run_user_controlled_automation_enhanced import EnhancedUserControlledAutomationSystem

class TransactionDateFieldDebugger:
    def __init__(self):
        self.automation_system = None
    
    async def initialize_system(self) -> bool:
        """Initialize the automation system"""
        try:
            print("\n🚀 ===== TRANSACTION DATE FIELD DEBUGGER =====\n")
            
            # Initialize automation system
            self.automation_system = EnhancedUserControlledAutomationSystem()
            
            # Initialize browser system
            print("📱 Initializing browser system...")
            browser_success = await self.automation_system.initialize_browser_system()
            
            if not browser_success:
                print("❌ Failed to initialize browser system")
                return False
            
            print("✅ Browser system initialized successfully")
            
            # Verify WebDriver connection
            print("🔗 Verifying WebDriver connection...")
            connection_ok = self.automation_system._verify_webdriver_connection()
            
            if not connection_ok:
                print("❌ WebDriver connection verification failed")
                return False
            
            print("✅ WebDriver connection verified successfully")
            return True
            
        except Exception as e:
            print(f"❌ System initialization failed: {e}")
            return False
    
    async def debug_transaction_date_field(self) -> bool:
        """Debug transaction date field availability"""
        try:
            driver = self.automation_system.processor.browser_manager.get_driver()
            
            if not driver:
                print("❌ No WebDriver available")
                return False
            
            # Check current URL
            current_url = driver.current_url
            print(f"\n📍 Current URL: {current_url}")
            
            # Navigate to task register if not already there
            if "frmPrTrxTaskRegisterDet.aspx" not in current_url:
                print("🔄 Navigating to task register page...")
                await self.automation_system.processor.browser_manager.navigate_to_task_register()
                await asyncio.sleep(3)
                
                final_url = driver.current_url
                print(f"📍 URL after navigation: {final_url}")
            
            # Check page title
            page_title = driver.title
            print(f"📄 Page Title: {page_title}")
            
            # Check if transaction date field exists
            print("\n🔍 Checking transaction date field...")
            
            # Method 1: Direct find by ID
            try:
                trx_date_field = driver.find_element(By.ID, "MainContent_txtTrxDate")
                print(f"✅ Transaction date field found by ID: {trx_date_field.tag_name}")
                print(f"   📝 Field type: {trx_date_field.get_attribute('type')}")
                print(f"   👁️ Field visible: {trx_date_field.is_displayed()}")
                print(f"   ✏️ Field enabled: {trx_date_field.is_enabled()}")
                print(f"   📏 Field size: {trx_date_field.size}")
                print(f"   📍 Field location: {trx_date_field.location}")
            except Exception as e:
                print(f"❌ Transaction date field NOT found by ID: {e}")
            
            # Method 2: Find by name attribute
            try:
                trx_date_field_name = driver.find_element(By.NAME, "ctl00$MainContent$txtTrxDate")
                print(f"✅ Transaction date field found by NAME: {trx_date_field_name.tag_name}")
            except Exception as e:
                print(f"❌ Transaction date field NOT found by NAME: {e}")
            
            # Method 3: Find by CSS selector
            try:
                trx_date_field_css = driver.find_element(By.CSS_SELECTOR, "input[id='MainContent_txtTrxDate']")
                print(f"✅ Transaction date field found by CSS: {trx_date_field_css.tag_name}")
            except Exception as e:
                print(f"❌ Transaction date field NOT found by CSS: {e}")
            
            # Method 4: Find all input fields and check
            print("\n🔍 Checking all input fields on page...")
            all_inputs = driver.find_elements(By.TAG_NAME, "input")
            print(f"📊 Total input fields found: {len(all_inputs)}")
            
            date_related_fields = []
            for i, input_field in enumerate(all_inputs):
                field_id = input_field.get_attribute('id') or 'No ID'
                field_name = input_field.get_attribute('name') or 'No Name'
                field_type = input_field.get_attribute('type') or 'No Type'
                
                if 'date' in field_id.lower() or 'date' in field_name.lower() or 'trx' in field_id.lower():
                    date_related_fields.append({
                        'index': i,
                        'id': field_id,
                        'name': field_name,
                        'type': field_type
                    })
            
            if date_related_fields:
                print(f"\n📅 Date-related fields found ({len(date_related_fields)}):")
                for field in date_related_fields:
                    print(f"   [{field['index']}] ID: {field['id']}, Name: {field['name']}, Type: {field['type']}")
            else:
                print("❌ No date-related fields found")
            
            # Method 5: Check page source for the field
            print("\n🔍 Checking page source for transaction date field...")
            page_source = driver.page_source
            
            if "MainContent_txtTrxDate" in page_source:
                print("✅ MainContent_txtTrxDate found in page source")
                
                # Extract the relevant HTML snippet
                import re
                pattern = r'<input[^>]*id=["\']MainContent_txtTrxDate["\'][^>]*>'
                match = re.search(pattern, page_source, re.IGNORECASE)
                if match:
                    print(f"   📝 HTML: {match.group()}")
            else:
                print("❌ MainContent_txtTrxDate NOT found in page source")
            
            # Method 6: Wait for element to be present
            print("\n⏳ Waiting for transaction date field to be present...")
            try:
                wait = WebDriverWait(driver, 10)
                trx_field_wait = wait.until(
                    EC.presence_of_element_located((By.ID, "MainContent_txtTrxDate"))
                )
                print(f"✅ Transaction date field found with WebDriverWait")
            except Exception as e:
                print(f"❌ Transaction date field NOT found with WebDriverWait: {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ Debug failed: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            if self.automation_system and self.automation_system.processor:
                await self.automation_system.processor.cleanup()
                print("\n🧹 Cleanup completed")
        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")

async def main():
    """Main function"""
    debugger = TransactionDateFieldDebugger()
    
    try:
        # Initialize system
        if not await debugger.initialize_system():
            print("❌ Failed to initialize system")
            return
        
        # Debug transaction date field
        await debugger.debug_transaction_date_field()
        
    except Exception as e:
        print(f"❌ Main execution failed: {e}")
    
    finally:
        # Cleanup
        await debugger.cleanup()

if __name__ == "__main__":
    asyncio.run(main())