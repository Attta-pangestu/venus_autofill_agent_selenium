#!/usr/bin/env python3
"""
Test Task Register Automation with Selected Staging Data

This script tests the automated form filling for task register page
using selected data from staging database, following the same flow
as the enhanced user controlled automation system.
"""

import sys
import json
import asyncio
import time
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from run_user_controlled_automation_enhanced import EnhancedUserControlledAutomationSystem

class TaskRegisterAutomationTester:
    """Test class for task register automation with staging data"""
    
    def __init__(self):
        self.automation_system = None
        self.test_data = []
        
    def setup_test_data(self) -> List[Dict]:
        """Setup test data based on user's example structure"""
        test_records = [
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
                "source_record_id": "PTRJ.250300212_20250814",
                "transaction_type": "Normal"  # Added for automation
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
                "shift": "LABOR _SHIFT1",
                "check_in": "07:00",
                "check_out": "17:00",
                "regular_hours": 7.0,
                "overtime_hours": 2.0,
                "total_hours": 9.0,
                "leave_type_code": None,
                "leave_type_description": None,
                "leave_ref_number": None,
                "is_alfa": False,
                "is_on_leave": False,
                "notes": "Test record for maintenance work",
                "status": "staged",
                "source_record_id": "PTRJ.250300213_20250815",
                "transaction_type": "Normal"  # Added for automation
            },
            {
                "employee_name": "CITRA",
                "employee_id": "PTRJ.250300214",
                "ptrj_employee_id": "POM00285",
                "task_code": "(OC7242) QUALITY CONTROL",
                "station_code": "STN-QC (STATION QUALITY CONTROL)",
                "machine_code": "QC00001 (QC EQUIPMENT)",
                "expense_code": "L (LABOUR)",
                "raw_charge_job": "(OC7242) QUALITY CONTROL / STN-QC (STATION QUALITY CONTROL) / QC00001 (QC EQUIPMENT) / L (LABOUR)",
                "id": "405f7b08-3e2b-4cc9-aead-744b3ec495ed",
                "date": "2025-08-16",
                "day_of_week": "",
                "shift": "LABOR _SHIFT2",
                "check_in": "15:00",
                "check_out": "23:00",
                "regular_hours": 7.0,
                "overtime_hours": 1.0,
                "total_hours": 8.0,
                "leave_type_code": None,
                "leave_type_description": None,
                "leave_ref_number": None,
                "is_alfa": False,
                "is_on_leave": False,
                "notes": "Test record for quality control work",
                "status": "staged",
                "source_record_id": "PTRJ.250300214_20250816",
                "transaction_type": "Normal"  # Added for automation
            }
        ]
        
        self.test_data = test_records
        return test_records
    
    async def initialize_system(self) -> bool:
        """Initialize the automation system"""
        try:
            print("\n🚀 ===== TASK REGISTER AUTOMATION TEST INITIALIZATION =====\n")
            
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
            
            # Check current URL to verify we're on the right page
            driver = self.automation_system.processor.browser_manager.get_driver()
            if driver:
                current_url = driver.current_url
                print(f"📍 Current browser URL: {current_url}")
                
                if "frmPrTrxTaskRegisterDet.aspx" in current_url:
                    print("✅ Browser is positioned at task register page")
                else:
                    print(f"⚠️ Browser is not at task register page. Current URL: {current_url}")
                    print("🔄 Attempting to navigate to task register page...")
                    
                    # Try to navigate to task register page
                    try:
                        await self.automation_system.processor.browser_manager.navigate_to_task_register()
                        await asyncio.sleep(3)  # Wait for navigation
                        
                        # Check URL again
                        final_url = driver.current_url
                        print(f"📍 URL after navigation: {final_url}")
                        
                        if "frmPrTrxTaskRegisterDet.aspx" not in final_url:
                            print(f"❌ Failed to navigate to task register page. Final URL: {final_url}")
                            return False
                        
                        print("✅ Successfully navigated to task register page")
                        
                    except Exception as nav_error:
                        print(f"❌ Navigation error: {nav_error}")
                        return False
            
            return True
            
        except Exception as e:
            print(f"❌ System initialization failed: {e}")
            return False
    
    async def test_single_record_processing(self, record: Dict, record_index: int, total_records: int) -> bool:
        """Test processing of a single record"""
        try:
            print(f"\n🎯 ===== TESTING RECORD {record_index}/{total_records} =====\n")
            print(f"👤 Employee: {record['employee_name']} (ID: {record['ptrj_employee_id']})")
            print(f"📅 Date: {record['date']}")
            print(f"💼 Task: {record['task_code']}")
            print(f"⏰ Hours: Regular={record['regular_hours']}, Overtime={record['overtime_hours']}")
            
            # Get driver from automation system
            driver = self.automation_system.processor.browser_manager.get_driver()
            
            if not driver:
                print("❌ No WebDriver available")
                return False
            
            # Process the record using enhanced automation
            success = await self.automation_system.process_single_record_enhanced(
                driver, record, record_index, total_records
            )
            
            if success:
                print(f"✅ Record {record_index} processed successfully")
                print(f"   Employee: {record['employee_name']}")
                print(f"   Status: SUCCESS")
            else:
                print(f"❌ Record {record_index} processing failed")
                print(f"   Employee: {record['employee_name']}")
                print(f"   Status: FAILED")
            
            return success
            
        except Exception as e:
            print(f"❌ Single record processing failed: {e}")
            return False
    
    async def run_automation_test(self) -> bool:
        """Run the complete automation test"""
        try:
            print("\n🧪 ===== STARTING TASK REGISTER AUTOMATION TEST =====\n")
            
            # Setup test data
            test_records = self.setup_test_data()
            total_records = len(test_records)
            
            print(f"📊 Test Data Summary:")
            print(f"   📝 Total Records: {total_records}")
            print(f"   👥 Employees: {', '.join([r['employee_name'] for r in test_records])}")
            print(f"   📅 Date Range: {test_records[0]['date']} - {test_records[-1]['date']}")
            
            # Initialize system
            if not await self.initialize_system():
                print("❌ System initialization failed")
                return False
            
            # Process each record
            successful_records = 0
            failed_records = 0
            
            for i, record in enumerate(test_records, 1):
                print(f"\n⏳ Processing record {i}/{total_records}...")
                
                success = await self.test_single_record_processing(record, i, total_records)
                
                if success:
                    successful_records += 1
                    print(f"✅ Record {i} completed successfully")
                else:
                    failed_records += 1
                    print(f"❌ Record {i} failed")
                
                # Add delay between records
                if i < total_records:
                    print(f"⏸️ Waiting 3 seconds before next record...")
                    await asyncio.sleep(3)
            
            # Final summary
            print(f"\n🎉 ===== AUTOMATION TEST COMPLETED =====\n")
            print(f"📊 FINAL RESULTS:")
            print(f"   ✅ Successful Records: {successful_records}/{total_records}")
            print(f"   ❌ Failed Records: {failed_records}/{total_records}")
            print(f"   📈 Success Rate: {(successful_records/total_records)*100:.1f}%")
            
            if successful_records == total_records:
                print(f"\n🏆 ALL TESTS PASSED! Task register automation is working correctly.")
                return True
            else:
                print(f"\n⚠️ Some tests failed. Please check the logs for details.")
                return False
            
        except Exception as e:
            print(f"❌ Automation test failed: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            if self.automation_system:
                await self.automation_system.cleanup()
                print("✅ Cleanup completed")
        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")

async def main():
    """Main test function"""
    tester = TaskRegisterAutomationTester()
    
    try:
        # Run the automation test
        success = await tester.run_automation_test()
        
        if success:
            print("\n🎯 Task register automation test completed successfully!")
            print("✅ Ready for integration with main web application.")
        else:
            print("\n❌ Task register automation test failed.")
            print("🔧 Please check the logs and fix any issues before integration.")
        
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
    finally:
        # Cleanup
        await tester.cleanup()
        print("\n👋 Test session ended.")

if __name__ == "__main__":
    print("🧪 Task Register Automation Tester")
    print("====================================")
    print("This script tests automated form filling for task register")
    print("using selected staging data with the enhanced automation system.")
    print("\nPress Ctrl+C to stop the test at any time.\n")
    
    # Run the test
    asyncio.run(main())