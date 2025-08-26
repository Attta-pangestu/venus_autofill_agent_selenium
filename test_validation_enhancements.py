#!/usr/bin/env python3
"""
Test script to verify validation enhancements in EnhancedUserControlledAutomationSystem
Tests input validation, error handling, and robustness improvements
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import List, Dict, Any

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class ValidationEnhancementTest:
    """Test class for validation enhancements"""
    
    def __init__(self):
        self.test_results = []
        self.system = None
        
    def log_test_result(self, test_name: str, passed: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        result = f"{status}: {test_name}"
        if message:
            result += f" - {message}"
        print(result)
        self.test_results.append((test_name, passed, message))
        
    def create_test_data(self) -> Dict[str, List[Dict]]:
        """Create various test data scenarios"""
        return {
            'valid_data': [
                {'employee_name': 'John Doe', 'date': '2024-01-15'},
                {'employee_name': 'Jane Smith', 'date': '2024-01-16'}
            ],
            'invalid_empty_array': [],
            'invalid_not_list': {'employee_name': 'John', 'date': '2024-01-15'},
            'invalid_record_structure': [
                'not_a_dict',
                {'employee_name': 'John'}, # missing date
                {'date': '2024-01-15'}, # missing employee_name
                {'employee_name': '', 'date': '2024-01-15'}, # empty employee_name
                {'employee_name': 'John', 'date': ''}, # empty date
                {'employee_name': 'John', 'date': 'invalid-date'}, # invalid date format
            ],
            'mixed_valid_invalid': [
                {'employee_name': 'Valid User', 'date': '2024-01-15'},
                {'employee_name': '', 'date': '2024-01-16'}, # invalid
                {'employee_name': 'Another Valid', 'date': '2024-01-17'}
            ]
        }
        
    async def test_input_validation(self):
        """Test input validation methods"""
        print("\n🔍 Testing Input Validation...")
        
        try:
            from run_user_controlled_automation_enhanced import EnhancedUserControlledAutomationSystem
            system = EnhancedUserControlledAutomationSystem()
            
            test_data = self.create_test_data()
            
            # Test 1: Valid data should pass validation
            errors = system._validate_staging_records(test_data['valid_data'])
            self.log_test_result(
                "Valid data validation", 
                len(errors) == 0,
                f"Expected 0 errors, got {len(errors)}: {errors}"
            )
            
            # Test 2: Invalid record structure should fail validation
            errors = system._validate_staging_records(test_data['invalid_record_structure'])
            self.log_test_result(
                "Invalid record structure validation", 
                len(errors) > 0,
                f"Expected errors, got {len(errors)} validation errors"
            )
            
            # Test 3: Mixed valid/invalid should identify invalid records
            errors = system._validate_staging_records(test_data['mixed_valid_invalid'])
            self.log_test_result(
                "Mixed valid/invalid validation", 
                len(errors) == 1,  # Only one invalid record
                f"Expected 1 error, got {len(errors)}: {errors}"
            )
            
        except Exception as e:
            self.log_test_result("Input validation test setup", False, f"Setup failed: {e}")
            
    async def test_automation_mode_validation(self):
        """Test automation mode validation"""
        print("\n🔍 Testing Automation Mode Validation...")
        
        try:
            from run_user_controlled_automation_enhanced import EnhancedUserControlledAutomationSystem
            system = EnhancedUserControlledAutomationSystem()
            
            test_data = self.create_test_data()['valid_data']
            
            # Test valid modes
            valid_modes = ['testing', 'real']
            for mode in valid_modes:
                try:
                    # This should not raise an exception during validation
                    result = await system.process_staging_data_array(test_data, mode)
                    # We expect it to fail due to no browser, but validation should pass
                    self.log_test_result(
                        f"Automation mode '{mode}' validation", 
                        'error' in result and 'browser' in result.get('error', '').lower(),
                        f"Mode validation passed, failed at browser initialization as expected"
                    )
                except Exception as e:
                    if 'invalid automation mode' in str(e).lower():
                        self.log_test_result(f"Automation mode '{mode}' validation", False, f"Valid mode rejected: {e}")
                    else:
                        self.log_test_result(f"Automation mode '{mode}' validation", True, f"Mode validation passed, other error: {e}")
            
            # Test invalid mode
            try:
                result = await system.process_staging_data_array(test_data, 'invalid_mode')
                self.log_test_result(
                    "Invalid automation mode rejection", 
                    'error' in result and 'automation mode' in result.get('error', '').lower(),
                    f"Invalid mode properly rejected"
                )
            except Exception as e:
                self.log_test_result(
                    "Invalid automation mode rejection", 
                    'automation mode' in str(e).lower(),
                    f"Invalid mode rejected with exception: {e}"
                )
                
        except Exception as e:
            self.log_test_result("Automation mode validation test setup", False, f"Setup failed: {e}")
            
    async def test_error_handling_robustness(self):
        """Test error handling robustness"""
        print("\n🔍 Testing Error Handling Robustness...")
        
        try:
            from run_user_controlled_automation_enhanced import EnhancedUserControlledAutomationSystem
            system = EnhancedUserControlledAutomationSystem()
            
            test_data = self.create_test_data()
            
            # Test 1: Empty array handling
            result = await system.process_staging_data_array(test_data['invalid_empty_array'])
            self.log_test_result(
                "Empty array handling", 
                'error' in result and 'empty' in result.get('error', '').lower(),
                f"Empty array properly handled: {result.get('error', '')}"
            )
            
            # Test 2: Non-list input handling
            result = await system.process_staging_data_array(test_data['invalid_not_list'])
            self.log_test_result(
                "Non-list input handling", 
                'error' in result and ('list' in result.get('error', '').lower() or 'type' in result.get('error', '').lower()),
                f"Non-list input properly handled: {result.get('error', '')}"
            )
            
            # Test 3: Invalid record structure handling
            result = await system.process_staging_data_array(test_data['invalid_record_structure'])
            self.log_test_result(
                "Invalid record structure handling", 
                'error' in result and 'validation' in result.get('error', '').lower(),
                f"Invalid records properly handled: {result.get('error', '')}"
            )
            
        except Exception as e:
            self.log_test_result("Error handling robustness test setup", False, f"Setup failed: {e}")
            
    async def test_helper_methods_existence(self):
        """Test that all validation helper methods exist and are callable"""
        print("\n🔍 Testing Helper Methods Existence...")
        
        try:
            from run_user_controlled_automation_enhanced import EnhancedUserControlledAutomationSystem
            system = EnhancedUserControlledAutomationSystem()
            
            helper_methods = [
                '_validate_staging_records',
                '_get_validated_driver', 
                '_ensure_task_register_page',
                '_process_records_with_validation',
                '_create_success_result',
                '_create_error_result'
            ]
            
            for method_name in helper_methods:
                has_method = hasattr(system, method_name)
                is_callable = callable(getattr(system, method_name, None)) if has_method else False
                
                self.log_test_result(
                    f"Helper method '{method_name}' exists and callable", 
                    has_method and is_callable,
                    f"Method exists: {has_method}, Callable: {is_callable}"
                )
                
        except Exception as e:
            self.log_test_result("Helper methods existence test setup", False, f"Setup failed: {e}")
            
    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*80)
        print("🧪 VALIDATION ENHANCEMENT TEST SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for _, passed, _ in self.test_results if passed)
        failed_tests = total_tests - passed_tests
        
        print(f"\n📊 Overall Results:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   📈 Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for test_name, passed, message in self.test_results:
                if not passed:
                    print(f"   • {test_name}: {message}")
        
        print(f"\n🎯 Validation Enhancement Status: {'✅ READY' if failed_tests == 0 else '⚠️ NEEDS ATTENTION'}")
        print("="*80)
        
    async def run_all_tests(self):
        """Run all validation enhancement tests"""
        print("🚀 Starting Validation Enhancement Tests...")
        print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run all test categories
        await self.test_input_validation()
        await self.test_automation_mode_validation() 
        await self.test_error_handling_robustness()
        await self.test_helper_methods_existence()
        
        # Print final summary
        self.print_test_summary()
        
        return len([r for r in self.test_results if not r[1]]) == 0  # Return True if all tests passed

async def main():
    """Main test execution function"""
    test_runner = ValidationEnhancementTest()
    
    try:
        success = await test_runner.run_all_tests()
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n⚠️ Test execution interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        return 1
    finally:
        print(f"\n⏰ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)