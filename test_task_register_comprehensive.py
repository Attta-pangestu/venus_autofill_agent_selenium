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

class TaskRegisterComprehensiveTester:
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
    
    async def fill_transaction_date_field(self, driver, date_value):
        """Fill transaction date field with retry mechanism"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"📅 Attempting to fill transaction date (attempt {attempt + 1}/{max_retries}): {date_value}")
                
                # Find the transaction date field
                date_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "MainContent_txtTrxDate"))
                )
                
                # Clear and fill using JavaScript
                driver.execute_script(
                    "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change'));",
                    date_field, date_value
                )
                
                # Send ENTER to trigger date processing
                date_field.send_keys(Keys.ENTER)
                await asyncio.sleep(1)
                
                # Verify the value was set
                current_value = date_field.get_attribute('value')
                print(f"✅ Transaction date field filled: {current_value}")
                return True
                
            except StaleElementReferenceException:
                print(f"⚠️ Stale element reference on attempt {attempt + 1}, retrying...")
                await asyncio.sleep(1)
                continue
            except Exception as e:
                print(f"❌ Error filling transaction date (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    return False
                await asyncio.sleep(1)
        
        return False
    
    async def fill_employee_field(self, driver, employee_name):
        """Fill employee field using autocomplete"""
        try:
            print(f"👤 Filling employee field: {employee_name}")
            
            # Find employee field
            employee_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "MainContent_txtEmployee"))
            )
            
            # Clear and type employee name
            employee_field.clear()
            employee_field.send_keys(employee_name)
            await asyncio.sleep(2)  # Wait for autocomplete
            
            # Press TAB to select first autocomplete option
            employee_field.send_keys(Keys.TAB)
            await asyncio.sleep(1)
            
            print(f"✅ Employee field filled: {employee_name}")
            return True
            
        except Exception as e:
            print(f"❌ Error filling employee field: {e}")
            return False
    
    async def fill_task_fields(self, driver, record):
        """Fill task-related fields"""
        try:
            print(f"📋 Filling task fields...")
            
            # Fill task code if available
            if record.get('task_code'):
                task_field = driver.find_element(By.ID, "MainContent_txtTask")
                task_field.clear()
                task_field.send_keys(record['task_code'])
                await asyncio.sleep(1)
            
            # Fill hours fields
            if record.get('regular_hours'):
                regular_hours_field = driver.find_element(By.ID, "MainContent_txtRegularHours")
                regular_hours_field.clear()
                regular_hours_field.send_keys(str(record['regular_hours']))
                await asyncio.sleep(0.5)
            
            if record.get('overtime_hours'):
                overtime_hours_field = driver.find_element(By.ID, "MainContent_txtOvertimeHours")
                overtime_hours_field.clear()
                overtime_hours_field.send_keys(str(record['overtime_hours']))
                await asyncio.sleep(0.5)
            
            print(f"✅ Task fields filled successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error filling task fields: {e}")
            return False
    
    async def process_single_record(self, record, record_index):
        """Process a single record for form filling"""
        print(f"\n{'='*60}")
        print(f"🔄 Processing Record #{record_index + 1}")
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
            
            # Fill transaction date field
            if not await self.fill_transaction_date_field(driver, transaction_date):
                print("❌ Failed to fill transaction date field")
                return False
            
            # Fill employee field
            if not await self.fill_employee_field(driver, record['employee_name']):
                print("❌ Failed to fill employee field")
                return False
            
            # Fill task fields
            if not await self.fill_task_fields(driver, record):
                print("❌ Failed to fill task fields")
                return False
            
            print(f"✅ Record #{record_index + 1} processed successfully")
            
            # Wait before processing next record
            await asyncio.sleep(3)
            return True
            
        except Exception as e:
            print(f"❌ Error processing record #{record_index + 1}: {e}")
            return False
    
    async def run_comprehensive_test(self):
        """Run comprehensive test with multiple records"""
        print("🚀 Starting Task Register Comprehensive Test")
        print(f"📊 Total records to process: {len(self.test_data)}")
        
        # Initialize system
        if not await self.initialize_system():
            print("❌ Failed to initialize system")
            return
        
        # Process each record
        success_count = 0
        total_records = len(self.test_data)
        
        for index, record in enumerate(self.test_data):
            success = await self.process_single_record(record, index)
            if success:
                success_count += 1
            
            # Add delay between records
            if index < total_records - 1:
                print(f"⏳ Waiting before next record...")
                await asyncio.sleep(2)
        
        # Report results
        success_rate = (success_count / total_records) * 100
        print(f"\n{'='*60}")
        print(f"📊 TEST RESULTS SUMMARY")
        print(f"{'='*60}")
        print(f"✅ Successful records: {success_count}/{total_records}")
        print(f"📈 Success rate: {success_rate:.1f}%")
        print(f"{'='*60}")
        
        return success_rate >= 80  # Consider 80% success rate as acceptable

async def main():
    """Main function to run the comprehensive test"""
    tester = TaskRegisterComprehensiveTester()
    
    try:
        success = await tester.run_comprehensive_test()
        if success:
            print("🎉 Comprehensive test completed successfully!")
        else:
            print("⚠️ Comprehensive test completed with issues")
            
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