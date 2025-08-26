#!/usr/bin/env python3
"""
Test Method Integration

This script tests that the new process_staging_data_array method
has been successfully integrated into the EnhancedUserControlledAutomationSystem class.
"""

import sys
import inspect
from pathlib import Path
from typing import Dict, List, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from run_user_controlled_automation_enhanced import EnhancedUserControlledAutomationSystem

def test_method_integration():
    """Test that the new methods are properly integrated"""
    print("🧪 Testing Method Integration")
    print("=" * 50)
    
    try:
        # Create instance without initialization
        print("📦 Creating EnhancedUserControlledAutomationSystem instance...")
        system = EnhancedUserControlledAutomationSystem()
        
        # Check if the new method exists
        print("🔍 Checking for process_staging_data_array method...")
        has_main_method = hasattr(system, 'process_staging_data_array')
        print(f"   process_staging_data_array: {'✅ EXISTS' if has_main_method else '❌ MISSING'}")
        
        # Check if the helper method exists
        print("🔍 Checking for _process_record_manual_implementation method...")
        has_helper_method = hasattr(system, '_process_record_manual_implementation')
        print(f"   _process_record_manual_implementation: {'✅ EXISTS' if has_helper_method else '❌ MISSING'}")
        
        # Check method signatures
        if has_main_method:
            print("📋 Analyzing process_staging_data_array method signature...")
            method = getattr(system, 'process_staging_data_array')
            sig = inspect.signature(method)
            print(f"   Signature: {sig}")
            print(f"   Is async: {'✅ YES' if inspect.iscoroutinefunction(method) else '❌ NO'}")
            
            # Check parameters
            params = list(sig.parameters.keys())
            expected_params = ['staging_data_array', 'automation_mode']
            has_correct_params = all(param in params for param in expected_params)
            print(f"   Has correct parameters: {'✅ YES' if has_correct_params else '❌ NO'}")
            print(f"   Parameters: {params}")
        
        if has_helper_method:
            print("📋 Analyzing _process_record_manual_implementation method signature...")
            helper_method = getattr(system, '_process_record_manual_implementation')
            helper_sig = inspect.signature(helper_method)
            print(f"   Signature: {helper_sig}")
            print(f"   Is async: {'✅ YES' if inspect.iscoroutinefunction(helper_method) else '❌ NO'}")
        
        # Check if methods are callable
        print("🔧 Checking if methods are callable...")
        main_callable = callable(getattr(system, 'process_staging_data_array', None))
        helper_callable = callable(getattr(system, '_process_record_manual_implementation', None))
        print(f"   process_staging_data_array callable: {'✅ YES' if main_callable else '❌ NO'}")
        print(f"   _process_record_manual_implementation callable: {'✅ YES' if helper_callable else '❌ NO'}")
        
        # Overall integration status
        integration_success = has_main_method and has_helper_method and main_callable and helper_callable
        
        print("\n" + "=" * 50)
        print(f"🎯 INTEGRATION TEST RESULTS:")
        print(f"   Status: {'✅ SUCCESS' if integration_success else '❌ FAILED'}")
        print(f"   Main Method: {'✅ INTEGRATED' if has_main_method else '❌ MISSING'}")
        print(f"   Helper Method: {'✅ INTEGRATED' if has_helper_method else '❌ MISSING'}")
        print(f"   Methods Callable: {'✅ YES' if main_callable and helper_callable else '❌ NO'}")
        print("=" * 50)
        
        return integration_success
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def test_class_structure():
    """Test the overall class structure"""
    print("\n🏗️ Testing Class Structure")
    print("=" * 50)
    
    try:
        # Get all methods of the class
        methods = [method for method in dir(EnhancedUserControlledAutomationSystem) 
                  if not method.startswith('__')]
        
        print(f"📊 Total methods in class: {len(methods)}")
        
        # Look for our new methods
        new_methods = [method for method in methods 
                      if 'process_staging_data_array' in method or 
                         '_process_record_manual_implementation' in method]
        
        print(f"🆕 New methods found: {len(new_methods)}")
        for method in new_methods:
            print(f"   - {method}")
        
        # Check for related methods
        related_methods = [method for method in methods 
                          if 'process' in method.lower() or 'staging' in method.lower()]
        
        print(f"🔗 Related processing methods: {len(related_methods)}")
        for method in related_methods:
            print(f"   - {method}")
        
        return len(new_methods) >= 2
        
    except Exception as e:
        print(f"❌ Class structure test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Method Integration Test Suite")
    print("=" * 80)
    
    # Run integration test
    integration_success = test_method_integration()
    
    # Run class structure test
    structure_success = test_class_structure()
    
    # Overall result
    overall_success = integration_success and structure_success
    
    print(f"\n🎯 FINAL RESULTS:")
    print(f"   Integration Test: {'✅ PASSED' if integration_success else '❌ FAILED'}")
    print(f"   Structure Test: {'✅ PASSED' if structure_success else '❌ FAILED'}")
    print(f"   Overall Status: {'✅ SUCCESS' if overall_success else '❌ FAILED'}")
    print("=" * 80)
    
    if overall_success:
        print("\n🎉 All tests passed! The methods have been successfully integrated.")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the integration.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)