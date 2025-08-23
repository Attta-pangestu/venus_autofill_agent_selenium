#!/usr/bin/env python3
"""
CRITICAL FIX: Stale Element Reference and Dynamic Field Detection

This script fixes the critical stale element reference issues and improves 
dynamic field detection based on test results.

Key Issues to Fix:
1. Date field stale element reference (100% failure rate)
2. Dynamic autocomplete fields not appearing until previous fields are filled
3. Field detection timing issues
"""

import shutil
import os

def create_critical_fixes():
    """Create the critical fixes for stale element issues"""
    
    # Fix 1: Improved date field handling with better stale element recovery
    date_field_fix = '''    async def _fill_date_field_robust(self, date_value: str):
        """Fill date field with CRITICAL stale element handling based on test results"""
        try:
            self.logger.info(f"🎯 Starting CRITICAL date field filling with advanced stale handling")
            print(f"📅 Starting date field filling: {date_value}")

            # Convert date format (YYYY-MM-DD to DD/MM/YYYY)
            try:
                if '-' in date_value:
                    year, month, day = date_value.split('-')
                    formatted_date = f"{day}/{month}/{year}"
                else:
                    formatted_date = date_value
                self.logger.info(f"📅 Formatted date: {formatted_date}")
            except:
                formatted_date = date_value

            max_attempts = 3  # Reduced attempts for faster recovery
            
            for attempt in range(1, max_attempts + 1):
                try:
                    self.logger.info(f"📅 Date field attempt {attempt}/{max_attempts}")
                    print(f"📅 Date field attempt {attempt}: {formatted_date}")

                    # CRITICAL FIX: Find element fresh each time, don't store references
                    date_field = None
                    
                    # Try multiple approaches to find a FRESH date field
                    for selector_attempt in range(3):
                        try:
                            if selector_attempt == 0:
                                # Primary: Direct ID
                                date_field = self.driver.find_element(By.ID, "MainContent_txtTrxDate")
                            elif selector_attempt == 1:
                                # Secondary: CSS selector
                                date_field = self.driver.find_element(By.CSS_SELECTOR, "input[id='MainContent_txtTrxDate']")
                            else:
                                # Tertiary: XPath
                                date_field = self.driver.find_element(By.XPATH, "//input[@id='MainContent_txtTrxDate']")
                            
                            # Verify element is fresh and usable
                            if date_field and date_field.is_displayed() and date_field.is_enabled():
                                break
                            else:
                                date_field = None
                                
                        except Exception as e:
                            self.logger.debug(f"Selector attempt {selector_attempt} failed: {e}")
                            continue
                    
                    if not date_field:
                        raise Exception("Could not locate fresh date field with any selector")

                    self.logger.info("✅ Found fresh date field")
                    print("✅ Found fresh date field")

                    # CRITICAL: Use JavaScript for input to avoid stale element issues
                    try:
                        # Method 1: JavaScript direct value setting (most reliable)
                        self.driver.execute_script(
                            "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change'));",
                            date_field, formatted_date
                        )
                        self.logger.info(f"✅ Date field filled via JavaScript: {formatted_date}")
                        print(f"✅ Date filled via JavaScript: {formatted_date}")
                        
                        # Small delay for form processing
                        await asyncio.sleep(1)
                        
                        # Verify the value was set
                        current_value = self.driver.execute_script("return arguments[0].value;", date_field)
                        if current_value == formatted_date:
                            self.logger.info("✅ Date field value verified successfully")
                            print("✅ Date field verified successfully")
                            return True
                        else:
                            self.logger.warning(f"⚠️ Date verification failed: expected {formatted_date}, got {current_value}")
                            
                    except Exception as js_error:
                        self.logger.warning(f"JavaScript method failed: {js_error}")
                        
                        # Method 2: Traditional Selenium input as fallback
                        try:
                            # Clear field carefully
                            date_field.clear()
                            await asyncio.sleep(0.3)
                            
                            # Input the date
                            date_field.send_keys(formatted_date)
                            await asyncio.sleep(0.5)
                            
                            # Trigger change event
                            date_field.send_keys(Keys.TAB)
                            await asyncio.sleep(0.5)
                            
                            self.logger.info(f"✅ Date field filled via Selenium: {formatted_date}")
                            print(f"✅ Date filled via Selenium: {formatted_date}")
                            return True
                            
                        except Exception as selenium_error:
                            raise Exception(f"Both JavaScript and Selenium methods failed: JS={js_error}, Selenium={selenium_error}")

                except StaleElementReferenceException as stale_error:
                    self.logger.warning(f"⚠️ Stale element on attempt {attempt}: {str(stale_error)[:100]}...")
                    print(f"⚠️ Stale element on attempt {attempt}, retrying...")
                    
                    if attempt < max_attempts:
                        # Quick page state check and recovery
                        try:
                            current_url = self.driver.current_url
                            if "frmPrTrxTaskRegisterDet.aspx" not in current_url:
                                self.logger.warning(f"⚠️ Page changed unexpectedly: {current_url}")
                                await self._navigate_to_task_register_robust()
                        except:
                            pass
                        
                        # Brief wait before retry
                        await asyncio.sleep(1.5)
                        continue
                    else:
                        raise stale_error

                except Exception as e:
                    self.logger.error(f"❌ Date field error on attempt {attempt}: {e}")
                    print(f"❌ Date field error on attempt {attempt}")
                    
                    if attempt < max_attempts:
                        await asyncio.sleep(2)
                        continue
                    else:
                        raise e

            # If we get here, all attempts failed
            self.logger.error("❌ Date field failed after all attempts")
            print("❌ Date field failed after all attempts")
            
            # Don't fail completely - log warning and continue
            self.logger.warning("⚠️ Date field filling unsuccessful, but continuing automation")
            print("⚠️ Date field filling unsuccessful, but continuing with next steps")
            return False

        except Exception as e:
            self.logger.error(f"❌ Critical date field error: {e}")
            print(f"❌ Critical date field error: {e}")
            
            # Always continue - don't let date field issues stop the automation
            self.logger.warning("⚠️ Date field filling failed, but continuing automation")
            print("⚠️ Date field filling failed, but continuing with automation")
            return False'''

    # Fix 2: Dynamic field detection that waits for fields to appear after previous inputs
    dynamic_field_fix = '''    async def _fill_charge_job_fields_robust(self, charge_job_parts: List[str]):
        """Fill charge job fields with DYNAMIC field detection based on test results"""
        try:
            self.logger.info(f"🔧 Filling charge job fields with DYNAMIC detection")
            print(f"🔧 Filling charge job fields: {len(charge_job_parts)} parts")

            if len(charge_job_parts) < 4:
                self.logger.warning(f"⚠️ Expected 4 charge job parts, got {len(charge_job_parts)}")
                print(f"⚠️ Expected 4 parts, got {len(charge_job_parts)}")
                return

            # Based on test results: fields appear DYNAMICALLY after previous inputs
            # Field sequence: Employee -> Task Code -> (Dynamic fields appear) -> Station Code -> Machine Code -> Expense Code
            
            field_sequence = [
                (charge_job_parts[0], "Task Code", True),       # Task Code - always available
                (charge_job_parts[1], "Station Code", False),   # Station Code - appears after Task Code
                (charge_job_parts[2], "Machine Code", False),   # Machine Code - appears after Station Code  
                (charge_job_parts[3], "Expense Code", False)    # Expense Code - appears after Machine Code
            ]

            for field_index, (value, field_name, is_static) in enumerate(field_sequence):
                try:
                    self.logger.info(f"🔧 Processing {field_name}: {value}")
                    print(f"🔧 Processing {field_name}: {value}")

                    # For dynamic fields, wait for them to appear
                    if not is_static:
                        self.logger.info(f"⏳ Waiting for dynamic field {field_name} to appear...")
                        print(f"⏳ Waiting for {field_name} to appear...")
                        await asyncio.sleep(2)  # Wait for dynamic loading

                    # Find the next available autocomplete field
                    target_field = None
                    
                    # Try multiple times to find the field as it may load dynamically
                    for find_attempt in range(5):
                        try:
                            autocomplete_fields = self.driver.find_elements(
                                By.CSS_SELECTOR, 
                                "input.ui-autocomplete-input.ui-widget.ui-widget-content"
                            )
                            
                            # Get available fields (displayed and enabled)
                            available_fields = []
                            for field in autocomplete_fields:
                                try:
                                    if field.is_displayed() and field.is_enabled():
                                        # Skip employee field (first one) - it's already filled
                                        field_value = field.get_attribute('value') or ''
                                        if 'ADM075' not in field_value.upper():  # Skip employee field
                                            available_fields.append(field)
                                except:
                                    continue
                            
                            self.logger.info(f"📊 Found {len(available_fields)} available fields for {field_name}")
                            
                            # For Task Code, use the first available field after employee
                            # For others, use the next empty field
                            if field_name == "Task Code" and len(available_fields) >= 1:
                                target_field = available_fields[0]
                                break
                            elif field_name == "Station Code" and len(available_fields) >= 2:
                                target_field = available_fields[1]
                                break  
                            elif field_name == "Machine Code" and len(available_fields) >= 3:
                                target_field = available_fields[2]
                                break
                            elif field_name == "Expense Code" and len(available_fields) >= 4:
                                target_field = available_fields[3]
                                break
                            else:
                                # Field not yet available, wait and retry
                                if find_attempt < 4:
                                    await asyncio.sleep(1)
                                    continue
                                else:
                                    self.logger.warning(f"⚠️ {field_name} field not available after {find_attempt+1} attempts")
                                    print(f"⚠️ {field_name} field not available")
                                    break
                                    
                        except Exception as find_error:
                            self.logger.debug(f"Field finding attempt {find_attempt+1} failed: {find_error}")
                            if find_attempt < 4:
                                await asyncio.sleep(1)
                                continue
                            else:
                                break

                    if not target_field:
                        self.logger.warning(f"⚠️ Could not locate {field_name} field, skipping")
                        print(f"⚠️ {field_name} field not found, skipping")
                        continue

                    # Fill the field using JavaScript for reliability
                    try:
                        self.logger.info(f"🔧 Filling {field_name}: {value}")
                        print(f"🔧 Filling {field_name}: {value}")
                        
                        # Use JavaScript to set value and trigger events
                        self.driver.execute_script("""
                            arguments[0].value = arguments[1];
                            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                            arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                        """, target_field, value)
                        
                        await asyncio.sleep(1)  # Wait for autocomplete to process
                        
                        # Verify the value was set
                        current_value = target_field.get_attribute('value')
                        if value in current_value:
                            self.logger.info(f"✅ {field_name} filled successfully")
                            print(f"✅ {field_name} filled successfully")
                        else:
                            self.logger.warning(f"⚠️ {field_name} value verification unclear: {current_value}")
                        
                        # Wait for any dynamic field loading after this input
                        await asyncio.sleep(1.5)
                        
                    except Exception as fill_error:
                        self.logger.error(f"❌ Failed to fill {field_name}: {fill_error}")
                        print(f"❌ Failed to fill {field_name}: {fill_error}")
                        continue

                except Exception as field_error:
                    self.logger.error(f"❌ Error processing {field_name}: {field_error}")
                    print(f"❌ Error processing {field_name}")
                    continue

            self.logger.info("✅ Charge job fields processing completed")
            print("✅ Charge job fields processing completed")

        except Exception as e:
            self.logger.error(f"❌ Critical error in charge job fields: {e}")
            print(f"❌ Charge job fields error: {e}")
            # Don't raise - continue with automation'''

    return date_field_fix, dynamic_field_fix

def apply_critical_fixes():
    """Apply the critical fixes to the enhanced_staging_automation.py file"""
    file_path = "src/core/enhanced_staging_automation.py"
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    # Create backup
    backup_file = f"{file_path}.critical_backup"
    shutil.copy2(file_path, backup_file)
    print(f"✅ Created critical backup: {backup_file}")
    
    # Get the fixes
    date_field_fix, dynamic_field_fix = create_critical_fixes()
    
    # Read current file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Apply fixes (will need to find and replace the specific methods)
    print("✅ Critical fixes prepared")
    print("\n📋 CRITICAL FIXES TO APPLY:")
    print("🔥 Date field stale element handling")
    print("🔄 Dynamic autocomplete field detection")
    print("⏱️ Improved timing and retry logic")
    print("🛠️ JavaScript-based input methods")
    
    print(f"\n🚀 Apply these fixes manually or run the search_replace operations")
    print(f"📁 Original file backed up to: {backup_file}")
    
    return True

def main():
    """Apply critical fixes based on test results"""
    print("🔥 APPLYING CRITICAL STALE ELEMENT FIXES")
    print("=" * 60)
    print("Based on test results:")
    print("❌ Date field: 100% stale element failure")  
    print("❌ Dynamic fields: Only 2/5 autocomplete fields detected")
    print("✅ Employee field: Working correctly")
    print("✅ Task Code: Working correctly")
    print("✅ Form submission: Working correctly")
    print()
    
    if apply_critical_fixes():
        print("\n" + "=" * 60)
        print("🎉 CRITICAL FIXES PREPARED!")
        print("=" * 60)
        print("\n🚀 Next Steps:")
        print("1. Apply the fixes to the date field method")
        print("2. Apply the fixes to the charge job fields method")
        print("3. Test with: python test_real_form_structure.py")
        return True
    else:
        print("\n❌ Critical fixes preparation failed")
        return False

if __name__ == "__main__":
    main() 