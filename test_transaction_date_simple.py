import asyncio
import sys
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from run_user_controlled_automation_enhanced import EnhancedUserControlledAutomationSystem

class SimpleTransactionDateTester:
    def __init__(self):
        self.automation_system = None
        
    def calculate_transaction_date_by_mode(self, original_date_str: str, mode: str = 'testing') -> str:
        """Calculate transaction date based on automation mode"""
        try:
            from datetime import datetime
            from dateutil.relativedelta import relativedelta
            
            # Parse original date
            original_date = None
            if '/' in original_date_str and len(original_date_str.split('/')) == 3:
                try:
                    original_date = datetime.strptime(original_date_str, "%d/%m/%Y")
                except:
                    original_date = datetime.strptime(original_date_str, "%Y-%m-%d")
            else:
                original_date = datetime.strptime(original_date_str, "%Y-%m-%d")
            
            if mode == 'testing':
                # Testing mode: Kurangi 1 bulan dari tanggal original absen
                trx_date = original_date - relativedelta(months=1)
                formatted_date = trx_date.strftime("%d/%m/%Y")
                return formatted_date
            else:
                # Real mode: Gunakan tanggal original dari data absen
                formatted_date = original_date.strftime("%d/%m/%Y")
                return formatted_date
                
        except Exception as e:
            print(f"❌ Error calculating transaction date: {e}")
            try:
                if '/' in original_date_str:
                    return original_date_str
                else:
                    date_obj = datetime.strptime(original_date_str, "%Y-%m-%d")
                    return date_obj.strftime("%d/%m/%Y")
            except:
                return original_date_str
    
    async def initialize_system(self):
        """Initialize the automation system"""
        try:
            print("🚀 Initializing Enhanced User Controlled Automation System...")
            self.automation_system = EnhancedUserControlledAutomationSystem()
            
            # Initialize browser system
            print("🌐 Initializing browser system...")
            await self.automation_system.initialize_browser_system()
            
            # Verify WebDriver connection
            driver = self.automation_system.processor.browser_manager.get_driver()
            if driver:
                print(f"✅ WebDriver connection verified")
                print(f"📍 Current URL: {driver.current_url}")
                
                # Check if we're on the task register page
                if 'frmPrTrxTaskRegisterDet.aspx' not in driver.current_url:
                    print("⚠️ Not on task register page, attempting navigation...")
                    driver.get('http://millwarep3.rebinmas.com:8004/en/PR/trx/frmPrTrxTaskRegisterDet.aspx')
                    await asyncio.sleep(3)
                    print(f"📍 New URL: {driver.current_url}")
                
                return True
            else:
                print("❌ Failed to get WebDriver")
                return False
                
        except Exception as e:
            print(f"❌ Error initializing system: {e}")
            return False
    
    async def test_transaction_date_filling(self):
        """Test transaction date field filling with different approaches"""
        try:
            driver = self.automation_system.processor.browser_manager.get_driver()
            if not driver:
                print("❌ No WebDriver available")
                return False
            
            # Test data
            test_date = "2025-08-14"
            formatted_date = self.calculate_transaction_date_by_mode(test_date, 'testing')
            
            print(f"\n🧪 TESTING TRANSACTION DATE FILLING")
            print(f"📅 Original Date: {test_date}")
            print(f"📅 Formatted Date: {formatted_date}")
            print(f"🎯 Target Field: MainContent_txtTrxDate")
            
            # Method 1: JavaScript direct value assignment
            print(f"\n🔧 Method 1: JavaScript direct value assignment")
            script1 = f"""
                var dateField = document.getElementById('MainContent_txtTrxDate');
                if (dateField) {{
                    console.log('Field found:', dateField);
                    dateField.value = '{formatted_date}';
                    dateField.dispatchEvent(new Event('change', {{bubbles: true}}));
                    return {{success: true, value: dateField.value}};
                }}
                return {{success: false, error: 'Field not found'}};
            """
            
            result1 = driver.execute_script(script1)
            print(f"   Result: {result1}")
            
            await asyncio.sleep(2)
            
            # Method 2: Clear field first, then set value
            print(f"\n🔧 Method 2: Clear field first, then set value")
            script2 = f"""
                var dateField = document.getElementById('MainContent_txtTrxDate');
                if (dateField) {{
                    dateField.value = '';
                    dateField.focus();
                    dateField.value = '{formatted_date}';
                    dateField.blur();
                    dateField.dispatchEvent(new Event('input', {{bubbles: true}}));
                    dateField.dispatchEvent(new Event('change', {{bubbles: true}}));
                    return {{success: true, value: dateField.value}};
                }}
                return {{success: false, error: 'Field not found'}};
            """
            
            result2 = driver.execute_script(script2)
            print(f"   Result: {result2}")
            
            await asyncio.sleep(2)
            
            # Method 3: Using Selenium WebElement
            print(f"\n🔧 Method 3: Using Selenium WebElement")
            try:
                from selenium.webdriver.common.by import By
                from selenium.webdriver.common.keys import Keys
                
                date_field = driver.find_element(By.ID, "MainContent_txtTrxDate")
                date_field.clear()
                date_field.send_keys(formatted_date)
                date_field.send_keys(Keys.TAB)
                
                current_value = date_field.get_attribute('value')
                print(f"   Result: {{success: True, value: '{current_value}'}}")
                
            except Exception as e:
                print(f"   Result: {{success: False, error: '{e}'}}")
            
            await asyncio.sleep(2)
            
            # Method 4: Check final field value
            print(f"\n🔍 Final field value check")
            final_script = """
                var dateField = document.getElementById('MainContent_txtTrxDate');
                if (dateField) {
                    return {success: true, value: dateField.value, visible: dateField.offsetParent !== null};
                }
                return {success: false, error: 'Field not found'};
            """
            
            final_result = driver.execute_script(final_script)
            print(f"   Final Result: {final_result}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error testing transaction date filling: {e}")
            return False
    
    async def run_test(self):
        """Run the complete test"""
        try:
            print("🧪 ===== SIMPLE TRANSACTION DATE FILLING TEST =====")
            
            # Initialize system
            if not await self.initialize_system():
                print("❌ Failed to initialize system")
                return
            
            # Test transaction date filling
            await self.test_transaction_date_filling()
            
            print("\n✅ Test completed")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
        finally:
            # Cleanup
            if self.automation_system and self.automation_system.processor and self.automation_system.processor.browser_manager:
                print("🧹 Cleaning up...")
                # Don't close browser for debugging
                # await self.automation_system.processor.browser_manager.cleanup()

async def main():
    tester = SimpleTransactionDateTester()
    await tester.run_test()

if __name__ == "__main__":
    asyncio.run(main())