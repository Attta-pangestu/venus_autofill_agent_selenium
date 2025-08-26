#!/usr/bin/env python3
"""
Test Integrated Staging Data Processor

This script tests the newly integrated process_staging_data_array method
in the EnhancedUserControlledAutomationSystem class to ensure it works
correctly with the main application.
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

class IntegratedStagingProcessorTest:
    """Test class for integrated staging data processor"""
    
    def __init__(self):
        self.automation_system = None
        self.test_data = [
            {
                'id': 1,
                'employee_name': 'ABDUL AZIZ',
                'employee_id': 'EMP001',
                'ptrj_employee_id': 'PTRJ001',
                'date': '2025-01-15',
                'task_code': 'TSK001',
                'station_code': 'ST001',
                'raw_charge_job': 'Normal Work',
                'transaction_type': 'Normal',
                'total_hours': 7.0
            },
            {
                'id': 2,
                'employee_name': 'AHMAD FAUZI',
                'employee_id': 'EMP002',
                'ptrj_employee_id': 'PTRJ002',
                'date': '2025-01-15',
                'task_code': 'TSK002',
                'station_code': 'ST002',
                'raw_charge_job': 'Maintenance',
                'transaction_type': 'Normal',
                'total_hours': 7.0
            }
        ]
    
    async def initialize_system(self):
        """Initialize the automation system"""
        try:
            print("🚀 Initializing Enhanced User Controlled Automation System...")
            
            self.automation_system = EnhancedUserControlledAutomationSystem()
            
            # Initialize browser system
            print("🌐 Initializing browser system...")
            await self.automation_system.initialize_browser_system()
            
            print("✅ System initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ System initialization failed: {e}")
            return False
    
    async def test_process_staging_data_array(self, automation_mode: str = 'testing'):
        """Test the process_staging_data_array method"""
        try:
            print(f"\n🧪 Testing process_staging_data_array method...")
            print(f"📋 Test data: {len(self.test_data)} records")
            print(f"🎯 Automation mode: {automation_mode}")
            
            # Process the staging data array
            start_time = time.time()
            result = await self.automation_system.process_staging_data_array(
                self.test_data, 
                automation_mode
            )
            processing_time = time.time() - start_time
            
            # Display results
            print(f"\n📊 PROCESSING RESULTS:")
            print(f"   📈 Total Records: {result['total_records']}")
            print(f"   ✅ Successful: {result['successful_records']}")
            print(f"   ❌ Failed: {result['failed_records']}")
            print(f"   📊 Success Rate: {result['success_rate']:.1f}%")
            print(f"   ⏱️ Total Time: {result['total_processing_time']:.2f}s")
            print(f"   🎯 Mode: {result['automation_mode']}")
            
            if 'error' in result:
                print(f"   ⚠️ Error: {result['error']}")
            
            # Display individual record results
            print(f"\n📋 INDIVIDUAL RECORD RESULTS:")
            for record_result in result['processing_results']:
                status_icon = "✅" if record_result['status'] == 'success' else "❌"
                print(f"   {status_icon} Record {record_result['record_index']}: {record_result['employee_name']} - {record_result['status']} ({record_result['processing_time']:.2f}s)")
                if 'error' in record_result:
                    print(f"      Error: {record_result['error']}")
            
            return result
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return None
    
    async def test_both_modes(self):
        """Test both testing and real modes"""
        try:
            print(f"\n🔄 Testing both automation modes...")
            
            # Test testing mode
            print(f"\n=== TESTING MODE ===")
            testing_result = await self.test_process_staging_data_array('testing')
            
            # Small delay between tests
            await asyncio.sleep(3)
            
            # Test real mode
            print(f"\n=== REAL MODE ===")
            real_result = await self.test_process_staging_data_array('real')
            
            # Compare results
            print(f"\n📊 MODE COMPARISON:")
            if testing_result and real_result:
                print(f"   Testing Mode Success Rate: {testing_result['success_rate']:.1f}%")
                print(f"   Real Mode Success Rate: {real_result['success_rate']:.1f}%")
                print(f"   Testing Mode Time: {testing_result['total_processing_time']:.2f}s")
                print(f"   Real Mode Time: {real_result['total_processing_time']:.2f}s")
            
            return testing_result, real_result
            
        except Exception as e:
            print(f"❌ Mode comparison test failed: {e}")
            return None, None
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            if self.automation_system:
                await self.automation_system.cleanup()
            print("🧹 Cleanup completed")
        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")
    
    async def run_comprehensive_test(self):
        """Run comprehensive test of the integrated system"""
        try:
            print("🚀 Starting Comprehensive Integrated Staging Processor Test")
            print("=" * 80)
            
            # Initialize system
            if not await self.initialize_system():
                return False
            
            # Test both modes
            testing_result, real_result = await self.test_both_modes()
            
            # Calculate overall success
            overall_success = False
            if testing_result and real_result:
                testing_success = testing_result['success_rate'] > 0
                real_success = real_result['success_rate'] > 0
                overall_success = testing_success and real_success
            
            print(f"\n" + "=" * 80)
            print(f"🎯 COMPREHENSIVE TEST RESULTS:")
            print(f"   Integration Status: {'✅ SUCCESS' if overall_success else '❌ FAILED'}")
            print(f"   Method Available: {'✅ YES' if hasattr(self.automation_system, 'process_staging_data_array') else '❌ NO'}")
            print(f"   Browser Integration: {'✅ WORKING' if self.automation_system.is_browser_ready else '❌ FAILED'}")
            
            if testing_result:
                print(f"   Testing Mode: {'✅ WORKING' if testing_result['success_rate'] > 0 else '❌ FAILED'}")
            if real_result:
                print(f"   Real Mode: {'✅ WORKING' if real_result['success_rate'] > 0 else '❌ FAILED'}")
            
            print("=" * 80)
            
            return overall_success
            
        except Exception as e:
            print(f"❌ Comprehensive test failed: {e}")
            return False
        finally:
            await self.cleanup()

async def main():
    """Main test function"""
    test = IntegratedStagingProcessorTest()
    
    try:
        success = await test.run_comprehensive_test()
        
        if success:
            print(f"\n🎉 All tests passed! The integrated staging processor is working correctly.")
            return 0
        else:
            print(f"\n❌ Some tests failed. Please check the integration.")
            return 1
            
    except KeyboardInterrupt:
        print(f"\n🛑 Test interrupted by user")
        await test.cleanup()
        return 1
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        await test.cleanup()
        return 1

if __name__ == "__main__":
    print("🧪 Integrated Staging Processor Test")
    exit_code = asyncio.run(main())
    sys.exit(exit_code)