#!/usr/bin/env python3
"""
WebDriver Responsiveness Fix for Venus AutoFill
Provides enhanced element interaction methods to fix automation unresponsiveness
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException


class WebDriverResponsivenessFix:
    """Enhanced WebDriver interaction methods with better responsiveness"""
    
    def __init__(self, driver, logger=None):
        self.driver = driver
        self.logger = logger or logging.getLogger(__name__)
        self.wait = WebDriverWait(driver, 15)  # Increased timeout
        
    async def diagnose_page_elements(self) -> Dict[str, Any]:
        """Comprehensive page element diagnosis"""
        diagnosis = {
            'autocomplete_fields': [],
            'radio_buttons': [],
            'input_fields': [],
            'buttons': [],
            'page_ready': False,
            'issues': []
        }
        
        try:
            print("🔍 DIAGNOSING PAGE ELEMENTS...")
            
            # Check page load status
            page_state = self.driver.execute_script("return document.readyState")
            diagnosis['page_ready'] = page_state == "complete"
            print(f"  📄 Page state: {page_state}")
            
            # Analyze autocomplete fields
            autocomplete_fields = self.driver.find_elements(By.CSS_SELECTOR, ".ui-autocomplete-input")
            diagnosis['autocomplete_fields'] = [
                {
                    'index': i,
                    'id': field.get_attribute('id'),
                    'displayed': field.is_displayed(),
                    'enabled': field.is_enabled(),
                    'value': field.get_attribute('value')
                }
                for i, field in enumerate(autocomplete_fields)
            ]
            print(f"  📋 Autocomplete fields: {len(autocomplete_fields)}")
            
            # Analyze key input fields
            key_field_ids = ['MainContent_txtTrxDate', 'MainContent_txtHours']
            for field_id in key_field_ids:
                try:
                    field = self.driver.find_element(By.ID, field_id)
                    field_info = {
                        'id': field_id,
                        'displayed': field.is_displayed(),
                        'enabled': field.is_enabled(),
                        'value': field.get_attribute('value')
                    }
                    diagnosis['input_fields'].append(field_info)
                    status = "✅" if field_info['displayed'] and field_info['enabled'] else "❌"
                    print(f"    {status} {field_id}")
                except NoSuchElementException:
                    diagnosis['issues'].append(f"Missing field: {field_id}")
                    print(f"    ❌ {field_id}: NOT FOUND")
            
            # Analyze radio buttons
            radio_buttons = self.driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
            diagnosis['radio_buttons'] = [
                {
                    'id': btn.get_attribute('id'),
                    'value': btn.get_attribute('value'),
                    'checked': btn.is_selected(),
                    'displayed': btn.is_displayed(),
                    'enabled': btn.is_enabled()
                }
                for btn in radio_buttons
            ]
            print(f"  🔘 Radio buttons: {len(radio_buttons)}")
            
            # Analyze buttons
            add_buttons = self.driver.find_elements(By.CSS_SELECTOR, "input[value='Add']")
            diagnosis['buttons'] = [
                {
                    'type': 'Add',
                    'displayed': btn.is_displayed(),
                    'enabled': btn.is_enabled()
                }
                for btn in add_buttons
            ]
            print(f"  🔳 Add buttons: {len(add_buttons)}")
            
            print(f"  📊 Diagnosis complete - {len(diagnosis['issues'])} issues found")
            
        except Exception as e:
            diagnosis['issues'].append(f"Diagnosis error: {e}")
            print(f"  ❌ Diagnosis error: {e}")
        
        return diagnosis
    
    async def safe_javascript_fill(self, field_id: str, value: str, field_name: str = None) -> bool:
        """Fill field using JavaScript for maximum reliability"""
        field_name = field_name or field_id
        
        try:
            # Escape value for JavaScript
            escaped_value = str(value).replace("'", "\\'")
            
            script = f"""
                var field = document.getElementById('{field_id}');
                if (field) {{
                    field.value = '{escaped_value}';
                    field.dispatchEvent(new Event('change', {{bubbles: true}}));
                    field.dispatchEvent(new Event('blur', {{bubbles: true}}));
                    return field.value;
                }}
                return null;
            """
            
            result = self.driver.execute_script(script)
            
            if result is not None:
                self.logger.info(f"✅ {field_name}: JavaScript fill successful - '{result}'")
                print(f"    ✅ {field_name}: '{result}'")
                return True
            else:
                self.logger.error(f"❌ {field_name}: Field not found")
                print(f"    ❌ {field_name}: Field not found")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ {field_name}: JavaScript fill error: {e}")
            print(f"    ❌ {field_name}: Error - {e}")
            return False
    
    async def safe_radio_button_select(self, radio_id: str, radio_name: str = None) -> bool:
        """Select radio button with enhanced reliability"""
        radio_name = radio_name or radio_id
        
        try:
            # Method 1: JavaScript selection
            script = f"""
                var radio = document.getElementById('{radio_id}');
                if (radio) {{
                    radio.checked = true;
                    radio.click();
                    radio.dispatchEvent(new Event('change', {{bubbles: true}}));
                    return radio.checked;
                }}
                return false;
            """
            
            result = self.driver.execute_script(script)
            
            if result:
                self.logger.info(f"✅ {radio_name}: JavaScript selection successful")
                print(f"    ✅ {radio_name}: Selected")
                return True
            
            # Method 2: Selenium click as fallback
            try:
                radio_element = self.wait.until(EC.element_to_be_clickable((By.ID, radio_id)))
                radio_element.click()
                
                if radio_element.is_selected():
                    self.logger.info(f"✅ {radio_name}: Selenium click successful")
                    print(f"    ✅ {radio_name}: Selected (fallback)")
                    return True
                    
            except Exception as selenium_error:
                self.logger.warning(f"⚠️ {radio_name}: Selenium fallback failed: {selenium_error}")
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ {radio_name}: Radio selection error: {e}")
            print(f"    ❌ {radio_name}: Error - {e}")
            return False
    
    async def enhanced_autocomplete_input(self, field_index: int, target_value: str, field_name: str = "field") -> bool:
        """Enhanced autocomplete input with comprehensive error handling"""
        try:
            self.logger.info(f"🔄 Starting enhanced autocomplete for {field_name}: '{target_value}'")
            print(f"    🔄 {field_name}: Enhanced autocomplete starting")
            
            # Find autocomplete fields
            autocomplete_fields = self.driver.find_elements(By.CSS_SELECTOR, ".ui-autocomplete-input")
            
            if field_index >= len(autocomplete_fields):
                print(f"    ❌ {field_name}: Field index {field_index} not available (only {len(autocomplete_fields)} fields)")
                return False
            
            field = autocomplete_fields[field_index]
            
            # Enhanced field preparation
            print(f"    🔧 {field_name}: Preparing field...")
            
            # Scroll into view
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", field)
            await asyncio.sleep(0.5)
            
            # Focus field
            field.click()
            await asyncio.sleep(0.3)
            
            # Enhanced clearing
            field.clear()
            await asyncio.sleep(0.2)
            
            # Alternative clearing methods
            for clear_method in [
                lambda: field.send_keys(Keys.CONTROL + "a"),
                lambda: field.send_keys(Keys.DELETE),
                lambda: field.send_keys(Keys.BACKSPACE * 20)
            ]:
                try:
                    clear_method()
                    await asyncio.sleep(0.1)
                except:
                    continue
            
            print(f"    ✅ {field_name}: Field prepared and cleared")
            
            # Enhanced typing with progress tracking
            typed_chars = ""
            for i, char in enumerate(target_value):
                try:
                    typed_chars += char
                    field.send_keys(char)
                    
                    if i % 3 == 0:  # Progress update every 3 characters
                        print(f"      📝 Progress: '{typed_chars}' ({i+1}/{len(target_value)})")
                    
                    await asyncio.sleep(0.35)  # Longer wait for autocomplete response
                    
                    # Check for dropdown after sufficient typing
                    if i >= 2:  # After 3+ characters
                        dropdown_success = await self.check_and_handle_dropdown(field, field_name, typed_chars)
                        if dropdown_success:
                            return True
                
                except Exception as char_error:
                    self.logger.warning(f"⚠️ {field_name}: Char input error at position {i}: {char_error}")
                    continue
            
            print(f"    🔄 {field_name}: Finished typing, applying selection methods...")
            
            # Enhanced selection methods
            selection_methods = [
                {
                    'name': 'Arrow Down + Enter',
                    'action': lambda: (
                        field.send_keys(Keys.ARROW_DOWN),
                        asyncio.sleep(0.6),
                        field.send_keys(Keys.ENTER)
                    )
                },
                {
                    'name': 'Tab Selection',
                    'action': lambda: field.send_keys(Keys.TAB)
                },
                {
                    'name': 'Click Away and Back',
                    'action': lambda: (
                        self.driver.execute_script("document.body.click();"),
                        asyncio.sleep(0.3),
                        field.click()
                    )
                }
            ]
            
            for method in selection_methods:
                try:
                    print(f"      🔄 Trying: {method['name']}")
                    
                    if callable(method['action']):
                        await method['action']()
                    else:
                        # Handle tuple actions
                        for action in method['action']:
                            if callable(action):
                                await action() if asyncio.iscoroutinefunction(action) else action()
                    
                    await asyncio.sleep(1)
                    
                    # Verify selection
                    final_value = field.get_attribute('value')
                    if final_value and len(final_value) > len(typed_chars) * 0.7:
                        print(f"      ✅ {field_name}: {method['name']} successful - '{final_value}'")
                        return True
                
                except Exception as method_error:
                    print(f"      ⚠️ {method['name']} failed: {method_error}")
                    continue
            
            # Final verification
            final_value = field.get_attribute('value')
            success = final_value and len(final_value) > 0
            
            if success:
                print(f"    ✅ {field_name}: Final value - '{final_value}'")
            else:
                print(f"    ❌ {field_name}: No value set after all attempts")
            
            return success
        
        except Exception as e:
            self.logger.error(f"❌ Enhanced autocomplete failed for {field_name}: {e}")
            print(f"    ❌ {field_name}: Critical error - {e}")
            return False
    
    async def check_and_handle_dropdown(self, field, field_name: str, typed_text: str) -> bool:
        """Check for autocomplete dropdown and handle selection"""
        try:
            # Look for dropdown options
            dropdown_options = self.driver.find_elements(By.CSS_SELECTOR, ".ui-autocomplete .ui-menu-item")
            visible_options = [opt for opt in dropdown_options if opt.is_displayed()]
            
            if not visible_options:
                return False
            
            print(f"      🔍 {field_name}: Found {len(visible_options)} dropdown options")
            
            if len(visible_options) == 1:
                # Single option - select it immediately
                option_text = visible_options[0].text
                print(f"      ✅ {field_name}: Single option '{option_text}' - selecting...")
                
                # Multiple selection methods for single option
                selection_success = False
                
                # Method 1: Arrow down + Enter
                try:
                    field.send_keys(Keys.ARROW_DOWN)
                    await asyncio.sleep(0.4)
                    field.send_keys(Keys.ENTER)
                    await asyncio.sleep(0.5)
                    selection_success = True
                except Exception as method1_error:
                    print(f"        ⚠️ Arrow+Enter failed: {method1_error}")
                
                # Method 2: Direct click on option
                if not selection_success:
                    try:
                        visible_options[0].click()
                        await asyncio.sleep(0.5)
                        selection_success = True
                    except Exception as method2_error:
                        print(f"        ⚠️ Direct click failed: {method2_error}")
                
                # Verify selection
                if selection_success:
                    final_value = field.get_attribute('value')
                    print(f"      ✅ {field_name}: Selection completed - '{final_value}'")
                    return True
            
            elif len(visible_options) > 1:
                # Multiple options - continue typing for more specificity
                print(f"      🔄 {field_name}: {len(visible_options)} options, need more specificity")
                return False
            
        except Exception as dropdown_error:
            # Dropdown handling failed - not critical
            return False
        
        return False
    
    async def safe_button_click(self, button_selector: str, button_name: str = "button") -> bool:
        """Safe button clicking with multiple strategies"""
        try:
            print(f"    🔄 {button_name}: Searching for button...")
            
            # Find button with multiple strategies
            button = None
            strategies = [
                (By.CSS_SELECTOR, button_selector),
                (By.XPATH, f"//input[@value='{button_selector.replace('input[value=\'', '').replace('\']', '')}']"),
                (By.XPATH, f"//button[text()='{button_name}']")
            ]
            
            for strategy in strategies:
                try:
                    buttons = self.driver.find_elements(*strategy)
                    for btn in buttons:
                        if btn.is_displayed() and btn.is_enabled():
                            button = btn
                            break
                    if button:
                        break
                except Exception as strategy_error:
                    continue
            
            if not button:
                print(f"    ❌ {button_name}: Button not found with any strategy")
                return False
            
            print(f"    ✅ {button_name}: Button found")
            
            # Multiple clicking methods
            click_methods = [
                {
                    'name': 'JavaScript Click',
                    'action': lambda: self.driver.execute_script("arguments[0].click();", button)
                },
                {
                    'name': 'Selenium Click',
                    'action': lambda: button.click()
                },
                {
                    'name': 'Send Keys Enter',
                    'action': lambda: button.send_keys(Keys.ENTER)
                }
            ]
            
            for method in click_methods:
                try:
                    print(f"      🔄 Trying: {method['name']}")
                    method['action']()
                    await asyncio.sleep(1)
                    
                    print(f"      ✅ {button_name}: {method['name']} successful")
                    return True
                
                except Exception as method_error:
                    print(f"      ⚠️ {method['name']} failed: {method_error}")
                    continue
            
            print(f"    ❌ {button_name}: All click methods failed")
            return False
        
        except Exception as e:
            print(f"    ❌ {button_name}: Critical click error - {e}")
            return False
    
    async def verify_form_reset(self, timeout: int = 5) -> bool:
        """Verify that form has been reset after submission"""
        try:
            await asyncio.sleep(2)  # Wait for form processing
            
            # Check if hours field is cleared
            try:
                hours_field = self.driver.find_element(By.ID, "MainContent_txtHours")
                hours_value = hours_field.get_attribute('value')
                
                if hours_value in ['', '0', '0.0']:
                    print(f"    ✅ Form reset verified - hours field cleared")
                    return True
                else:
                    print(f"    ℹ️ Form may not be fully reset - hours: '{hours_value}'")
                    return False
            except Exception as verify_error:
                print(f"    ℹ️ Could not verify form reset: {verify_error}")
                return False
        
        except Exception as e:
            print(f"    ⚠️ Form reset verification error: {e}")
            return False


# Integration example for existing automation system
class AutomationEnhancer:
    """Helper class to enhance existing automation with responsiveness fixes"""
    
    def __init__(self, automation_system):
        self.automation_system = automation_system
        self.responsiveness_fix = None
    
    def enhance_system(self):
        """Enhance existing automation system with responsiveness fixes"""
        try:
            # Get driver from existing system
            driver = self.automation_system.processor.browser_manager.get_driver()
            
            # Initialize responsiveness fix
            self.responsiveness_fix = WebDriverResponsivenessFix(driver, self.automation_system.logger)
            
            # Replace existing methods with enhanced versions
            self.automation_system.enhanced_element_interaction = self.responsiveness_fix
            
            print("✅ Automation system enhanced with responsiveness fixes")
            return True
            
        except Exception as e:
            print(f"❌ Failed to enhance automation system: {e}")
            return False
    
    async def enhanced_record_processing(self, driver, entry: Dict, record_index: int, total_records: int = 1) -> bool:
        """Enhanced record processing using responsiveness fixes"""
        if not self.responsiveness_fix:
            print("❌ Responsiveness fix not initialized")
            return False
        
        try:
            # Extract record data
            employee_name = entry.get('employee_name', 'Unknown')
            date_value = entry.get('date', '')
            transaction_type = entry.get('transaction_type', 'Normal')
            calculated_hours = entry.get('hours', 0)
            raw_charge_job = entry.get('raw_charge_job', '')
            
            print(f"\n🔧 ENHANCED PROCESSING: Record {record_index}/{total_records}")
            print(f"👤 Employee: {employee_name}")
            print(f"📅 Date: {date_value} | 🔘 Type: {transaction_type} | ⏰ Hours: {calculated_hours}")
            
            # Diagnose page before processing
            await self.responsiveness_fix.diagnose_page_elements()
            
            # Step 1: Transaction Date
            print("  📅 Step 1: Transaction Date")
            formatted_date = self.automation_system.processor.format_date(date_value)
            success = await self.responsiveness_fix.safe_javascript_fill(
                'MainContent_txtTrxDate', formatted_date, 'Transaction Date'
            )
            
            if success:
                # Trigger date processing
                try:
                    date_field = driver.find_element(By.ID, "MainContent_txtTrxDate")
                    date_field.send_keys(Keys.ENTER)
                    await asyncio.sleep(2)
                except:
                    pass
            else:
                print("    ❌ Date field failed - stopping")
                return False
            
            # Step 2: Employee Field
            print("  👤 Step 2: Employee Field")
            success = await self.responsiveness_fix.enhanced_autocomplete_input(
                0, employee_name, "Employee"
            )
            
            if not success:
                print("    ❌ Employee field failed - stopping")
                return False
            
            # Step 3: Transaction Type
            print("  🔘 Step 3: Transaction Type")
            radio_id = 'MainContent_rblOT_0' if transaction_type.lower() == 'normal' else 'MainContent_rblOT_1'
            success = await self.responsiveness_fix.safe_radio_button_select(radio_id, transaction_type)
            
            # Step 4: Charge Job Components
            if raw_charge_job:
                print("  🔧 Step 4: Charge Job Components")
                charge_components = self.automation_system.processor.parse_raw_charge_job(raw_charge_job)
                
                if charge_components and len(charge_components) >= 4:
                    successful_components = 0
                    for i, component in enumerate(charge_components[:4]):
                        if component and component.strip():
                            field_index = i + 1  # Skip employee field
                            field_name = ["Task Code", "Station Code", "Machine Code", "Expense Code"][i]
                            
                            success = await self.responsiveness_fix.enhanced_autocomplete_input(
                                field_index, component, field_name
                            )
                            
                            if success:
                                successful_components += 1
                            
                            await asyncio.sleep(0.5)
                    
                    print(f"    📊 Charge components: {successful_components}/{len(charge_components)} filled")
            
            # Step 5: Hours Field
            print("  ⏰ Step 5: Hours Field")
            await self.responsiveness_fix.safe_javascript_fill(
                'MainContent_txtHours', str(calculated_hours), 'Hours'
            )
            
            # Step 6: Add Button
            print("  🔳 Step 6: Add Button")
            success = await self.responsiveness_fix.safe_button_click(
                "input[value='Add']", "Add Button"
            )
            
            if success:
                # Verify form reset
                await self.responsiveness_fix.verify_form_reset()
                print("  ✅ Record processing completed successfully")
                return True
            else:
                print("  ❌ Add button failed")
                return False
        
        except Exception as e:
            print(f"  ❌ Enhanced processing error: {e}")
            return False


# Usage example:
"""
# To integrate with existing system:

# 1. Import this module
from webdriver_responsiveness_fix import AutomationEnhancer

# 2. Enhance your existing automation system
enhancer = AutomationEnhancer(your_automation_system)
enhancer.enhance_system()

# 3. Use enhanced processing method
success = await enhancer.enhanced_record_processing(driver, record_data, 1, 1)
"""

if __name__ == "__main__":
    print("🔧 WebDriver Responsiveness Fix Module")
    print("This module provides enhanced WebDriver interaction methods.")
    print("Import and integrate with your existing automation system.") 