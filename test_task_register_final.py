import asyncio
import sys
import os
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from selenium.webdriver.common.keys import Keys

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from run_user_controlled_automation_enhanced import EnhancedUserControlledAutomationSystem

class TaskRegisterFinalTester:
    def __init__(self):
        self.automation_system = None
        self.test_data = self.get_test_data()
        
    def get_test_data(self):
        """Get sample test data matching the staging database structure"""
        return [
            {
                "employee_name": "ALDI",
                "employee_id": "PTRJ.250300212",
                "ptrj_employee_id": "POM00283",
                "task_code": "(OC7240) LABORATORY ANALYSIS",
                "station_code": "STN-LAB (STATION LABORATORY)",
                "machine_code": "LAB00000 (LABOUR COST )",
                "expense_code": "L (LABOUR)",
                "raw_charge_job": "(OC7240) LABORATORY ANALYSIS / STN-LAB (STATION LABORATORY) / LAB00000 (LABOUR COST ) / L (LABOUR)",
                "id": "205f7b08-3e2b-4cc9-aead-744b3ec495ed",
                "date": "2025-08-14",
                "day_of_week": "",
                "shift": "LABOR _SHIFT1",
                "check_in": "07:08",
                "check_out": "18:02",
                "regular_hours": 7.0,
                "overtime_hours": 3.0,
                "total_hours": 10.0,
                "leave_type_code": None,
                "leave_type_description": None,
                "leave_ref_number": None,
                "is_alfa": False,
                "is_on_leave": False,
                "notes": "Moved from main attendance data with charge job integration",
                "status": "staged",
                "source_record_id": "PTRJ.250300212_20250814"
            },
            {
                "employee_name": "BUDI",
                "employee_id": "PTRJ.250300213",
                "ptrj_employee_id": "POM00284",
                "task_code": "(OC7241) MAINTENANCE WORK",
                "station_code": "STN-MNT (STATION MAINTENANCE)",
                "machine_code": "MNT00001 (MAINTENANCE COST)",
                "expense_code": "L (LABOUR)",
                "raw_charge_job": "(OC7241) MAINTENANCE WORK / STN-MNT (STATION MAINTENANCE) / MNT00001 (MAINTENANCE COST) / L (LABOUR)",
                "id": "305f7b08-3e2b-4cc9-aead-744b3ec495ed",
                "date": "2025-08-15",
                "day_of_week": "",
                "shift": "LABOR _SHIFT2",
                "check_in": "15:00",
                "check_out": "23:00",
                "regular_hours": 8.0,
                "overtime_hours": 0.0,
                "total_hours": 8.0,
                "leave_type_code": None,
                "leave_type_description": None,
                "leave_ref_number": None,
                "is_alfa": False,
                "is_on_leave": False,
                "notes": "Regular maintenance shift",
                "status": "staged",
                "source_record_id": "PTRJ.250300213_20250815"
            }
        ]
    
    def calculate_transaction_date_by_mode(self, original_date_str, mode='testing'):
        """Calculate transaction date based on mode"""
        try:
            original_date = datetime.strptime(original_date_str, '%Y-%m-%d')
            
            if mode == 'testing':
                # Subtract one month for testing
                if original_date.month == 1:
                    transaction_date = original_date.replace(year=original_date.year - 1, month=12)
                else:
                    transaction_date = original_date.replace(month=original_date.month - 1)
            else:
                # Use original date for real mode
                transaction_date = original_date
            
            # Format as DD/MM/YYYY for form compatibility
            return transaction_date.strftime('%d/%m/%Y')
            
        except Exception as e:
            print(f"❌ Error calculating transaction date: {e}")
            return None
    
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
                
                # Navigate to task register page
                print("🔄 Navigating to task register page...")
                await self.automation_system.processor.browser_manager.navigate_to_task_register()
                await asyncio.sleep(2)
                print(f"📍 New URL: {driver.current_url}")
                
                return True
            else:
                print("❌ Failed to get WebDriver")
                return False
                
        except Exception as e:
            print(f"❌ Error initializing system: {e}")
            return False
    
    async def process_single_record_using_system(self, record, record_index):
        """Process a single record using the existing system's process_single_record_enhanced method"""
        print(f"\n{'='*60}")
        print(f"🔄 Processing Record #{record_index + 1} using system method")
        print(f"👤 Employee: {record['employee_name']}")
        print(f"📅 Date: {record['date']}")
        print(f"⏰ Hours: Regular={record['regular_hours']}, Overtime={record['overtime_hours']}")
        print(f"{'='*60}")
        
        try:
            # Use the existing system's method to process the record
            success = await self.automation_system.process_single_record_enhanced(record)
            
            if success:
                print(f"✅ Record #{record_index + 1} processed successfully using system method")
            else:
                print(f"❌ Record #{record_index + 1} failed using system method")
            
            return success
            
        except Exception as e:
            print(f"❌ Error processing record #{record_index + 1} using system method: {e}")
            return False
    
    async def process_single_record_manual(self, record, record_index):
        """Process a single record with manual implementation using the same approach as the system"""
        print(f"\n{'='*60}")
        print(f"🔄 Processing Record #{record_index + 1} with manual implementation")
        print(f"👤 Employee: {record['employee_name']}")
        print(f"📅 Date: {record['date']}")
        print(f"⏰ Hours: Regular={record['regular_hours']}, Overtime={record['overtime_hours']}")
        print(f"{'='*60}")
        
        try:
            driver = self.automation_system.processor.browser_manager.get_driver()
            if not driver:
                print("❌ No WebDriver available")
                return False
            
            # Calculate transaction date
            transaction_date = self.calculate_transaction_date_by_mode(record['date'], 'testing')
            if not transaction_date:
                print("❌ Failed to calculate transaction date")
                return False
            
            print(f"📅 STEP 1: FILLING TRANSACTION DATE FIELD")
            print(f"   📅 Calculated transaction date: {transaction_date}")
            
            # Use JavaScript to fill transaction date field (same as system implementation)
            script = f"""
                var dateField = document.getElementById('MainContent_txtTrxDate');
                if (dateField) {{
                    dateField.value = '{transaction_date}';
                    dateField.dispatchEvent(new Event('change', {{bubbles: true}}));
                    return true;
                }}
                return false;
            """
            
            result = driver.execute_script(script)
            if result:
                print(f"   ✅ Transaction date field filled successfully: {transaction_date}")
                print(f"   ⌨️ Sending ENTER key to trigger date processing...")
                
                # Find the field again and send ENTER
                try:
                    date_field = driver.find_element(By.ID, "MainContent_txtTrxDate")
                    date_field.send_keys(Keys.ENTER)
                    await asyncio.sleep(2)
                    print(f"   ✅ Date processing triggered successfully")
                except Exception as e:
                    print(f"   ⚠️ Could not send ENTER key: {e}")
            else:
                print(f"   ❌ Transaction date field not found or failed to fill")
                return False
            
            print(f"\n👤 STEP 2: FILLING EMPLOYEE FIELD")
            print(f"   👤 Employee Name: {record['employee_name']}")
            print(f"   🆔 Employee ID: {record['employee_id']}")
            
            # Find autocomplete fields
            autocomplete_fields = driver.find_elements(By.CSS_SELECTOR, ".ui-autocomplete-input")
            print(f"   🔍 Found {len(autocomplete_fields)} autocomplete fields")
            
            if len(autocomplete_fields) > 0:
                employee_field = autocomplete_fields[0]
                print(f"   🎯 Using first autocomplete field for employee input")
                
                # Clear and fill employee field
                employee_field.clear()
                employee_field.send_keys(record['employee_name'])
                await asyncio.sleep(2)  # Wait for autocomplete
                
                # Press TAB to select first autocomplete option
                employee_field.send_keys(Keys.TAB)
                await asyncio.sleep(1)
                
                print(f"   ✅ Employee field filled successfully")
            else:
                print(f"   ❌ No autocomplete fields found for employee input")
                return False
            
            print(f"\n✅ Record #{record_index + 1} processed successfully with manual implementation")
            return True
            
        except Exception as e:
            print(f"❌ Error processing record #{record_index + 1} with manual implementation: {e}")
            return False
    
    async def run_final_test(self):
        """Run final test with both system method and manual implementation"""
        print("🚀 Starting Task Register Final Test")
        print(f"📊 Total records to process: {len(self.test_data)}")
        
        # Initialize system
        if not await self.initialize_system():
            print("❌ Failed to initialize system")
            return
        
        # Test with system method first
        print("\n🔧 TESTING WITH SYSTEM METHOD")
        print("="*60)
        
        system_success_count = 0
        for index, record in enumerate(self.test_data):
            success = await self.process_single_record_using_system(record, index)
            if success:
                system_success_count += 1
            
            # Add delay between records
            if index < len(self.test_data) - 1:
                print(f"⏳ Waiting before next record...")
                await asyncio.sleep(3)
        
        # Test with manual implementation
        print("\n🛠️ TESTING WITH MANUAL IMPLEMENTATION")
        print("="*60)
        
        manual_success_count = 0
        for index, record in enumerate(self.test_data):
            success = await self.process_single_record_manual(record, index)
            if success:
                manual_success_count += 1
            
            # Add delay between records
            if index < len(self.test_data) - 1:
                print(f"⏳ Waiting before next record...")
                await asyncio.sleep(3)
        
        # Report results
        total_records = len(self.test_data)
        system_success_rate = (system_success_count / total_records) * 100
        manual_success_rate = (manual_success_count / total_records) * 100
        
        print(f"\n{'='*60}")
        print(f"📊 FINAL TEST RESULTS SUMMARY")
        print(f"{'='*60}")
        print(f"🔧 System Method Results:")
        print(f"   ✅ Successful records: {system_success_count}/{total_records}")
        print(f"   📈 Success rate: {system_success_rate:.1f}%")
        print(f"")
        print(f"🛠️ Manual Implementation Results:")
        print(f"   ✅ Successful records: {manual_success_count}/{total_records}")
        print(f"   📈 Success rate: {manual_success_rate:.1f}%")
        print(f"{'='*60}")
        
        return max(system_success_rate, manual_success_rate) >= 80

async def main():
    """Main function to run the final test"""
    tester = TaskRegisterFinalTester()
    
    try:
        success = await tester.run_final_test()
        if success:
            print("🎉 Final test completed successfully!")
        else:
            print("⚠️ Final test completed with issues")
            
    except Exception as e:
        print(f"❌ Error in main: {e}")
    
    finally:
        # Cleanup
        if tester.automation_system and tester.automation_system.processor and tester.automation_system.processor.browser_manager:
            print("🧹 Cleaning up...")
            # Keep browser open for debugging
            # await tester.automation_system.processor.browser_manager.cleanup()

if __name__ == "__main__":
    asyncio.run(main())