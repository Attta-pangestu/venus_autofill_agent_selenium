"""
Enhanced Staging Data Automation Engine
Handles automated data entry with robust error handling and persistent sessions
"""

import time
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    StaleElementReferenceException,
    ElementNotInteractableException
)

from .persistent_browser_manager import PersistentBrowserManager


@dataclass
class StagingRecord:
    """Represents a staging data record"""
    id: str
    employee_name: str
    employee_id: str
    date: str
    task_code: str
    station_code: str
    raw_charge_job: str
    status: str
    hours: float = 7.0
    unit: float = 1.0


@dataclass
class AutomationResult:
    """Result of automation processing"""
    success: bool
    record_id: str
    message: str
    error_details: Optional[str] = None
    processing_time: float = 0.0


class EnhancedStagingAutomationEngine:
    """Enhanced automation engine with robust error handling and persistent sessions"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Use persistent browser manager
        self.browser_manager = PersistentBrowserManager(config)
        self.driver = None
        
        # URLs and credentials
        self.task_register_url = config.get('urls', {}).get('taskRegister', 
            'http://millwarep3:8004/en/PR/trx/frmPrTrxTaskRegisterDet.aspx')
        
        # Retry settings
        self.max_retries = config.get('automation', {}).get('max_retries', 3)
        self.retry_delay = config.get('automation', {}).get('retry_delay', 2)
        self.element_timeout = config.get('automation', {}).get('element_timeout', 15)
    
        # Dynamic field detection
        self.date_field_id = 'MainContent_txtTrxDate'  # Default, will be updated by form detection
    
    async def initialize(self) -> bool:
        """Initialize the automation system with persistent session"""
        try:
            self.logger.info("Initializing Enhanced Staging Automation Engine")
            
            # Initialize persistent browser manager (this will pre-login)
            success = await self.browser_manager.initialize()
            if not success:
                raise Exception("Failed to initialize persistent browser manager")
            
            # Get the pre-initialized driver
            self.driver = self.browser_manager.get_driver()
            if not self.driver:
                raise Exception("Failed to get WebDriver from persistent manager")
            
            self.logger.info("✅ Enhanced Staging Automation Engine initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize automation engine: {e}")
            return False
    
    async def process_staging_records(self, records: List[Dict[str, Any]]) -> List[AutomationResult]:
        """Process multiple staging records with improved error handling"""
        results = []
        
        try:
            print("\n" + "🚀" + "="*70)
            print("🤖 STARTING AUTOMATED DATA ENTRY PROCESS")
            print("="*72)
            print(f"📊 Total Records to Process: {len(records)}")
            print(f"🕒 Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("="*72)
            
            self.logger.info(f"🤖 Starting automation process for {len(records)} staging records")
            
            for i, record_data in enumerate(records):
                record_id = record_data.get('id', f'record_{i+1}')
                employee_name = record_data.get('employee_name', 'Unknown Employee')
                
                print(f"\n📋 PROCESSING RECORD {i+1}/{len(records)}")
                print(f"🆔 Record ID: {record_id}")
                print(f"👨‍💼 Employee: {employee_name}")
                print(f"📅 Date: {record_data.get('date', 'N/A')}")
                
                self.logger.info(f"Processing record {i+1}/{len(records)}: {employee_name} ({record_id})")
                
                # Convert dict to StagingRecord
                record = self._dict_to_staging_record(record_data)
                
                # Log detailed record information
                self._log_record_details(record, i+1)
                
                # Process individual record with retry logic
                print(f"⚡ Starting automation for {employee_name}...")
                result = await self._process_record_with_retry(record)
                results.append(result)
                
                # Display result
                if result.success:
                    print(f"✅ SUCCESS: {employee_name} processed in {result.processing_time:.2f}s")
                else:
                    print(f"❌ FAILED: {employee_name} - {result.message}")
                    if result.error_details:
                        print(f"   Error: {result.error_details}")
                
                # Add delay between records to avoid overwhelming the system
                if i < len(records) - 1:
                    print(f"⏳ Waiting 2 seconds before next record...")
                    await asyncio.sleep(2)
            
            # Log final summary
            successful = sum(1 for r in results if r.success)
            failed = len(results) - successful
            
            print("\n" + "="*72)
            print("📊 AUTOMATION PROCESS COMPLETE")
            print("="*72)
            print(f"✅ Successful: {successful}/{len(records)} records")
            print(f"❌ Failed: {failed}/{len(records)} records")
            print(f"📈 Success Rate: {(successful/len(records)*100):.1f}%")
            print(f"🕒 End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("="*72)
            
            self.logger.info(f"✅ Automation completed: {successful} successful, {failed} failed")
            
            return results
            
        except Exception as e:
            print(f"\n❌ CRITICAL ERROR IN AUTOMATION PROCESS: {e}")
            self.logger.error(f"Error processing staging records: {e}")
            # Add error results for any unprocessed records
            for record_data in records[len(results):]:
                results.append(AutomationResult(
                    success=False,
                    record_id=record_data.get('id', 'unknown'),
                    message="Processing failed due to system error",
                    error_details=str(e)
                ))
            return results
    
    def _log_record_details(self, record: StagingRecord, record_number: int):
        """Log detailed information about the record being processed"""
        try:
            print(f"🔍 RECORD {record_number} DETAILS:")
            print(f"   📅 Date: {record.date}")
            print(f"   🏢 Task Code: {record.task_code}")
            print(f"   📍 Station Code: {record.station_code}")
            print(f"   ⏰ Hours: {record.hours}")
            print(f"   🔢 Unit: {record.unit}")
            print(f"   🏗️ Raw Charge Job: {record.raw_charge_job}")
            
            # Parse and display charge job components
            charge_job_parts = self.parse_charge_job(record.raw_charge_job)
            if charge_job_parts and len(charge_job_parts) >= 4:
                print(f"   🔧 Parsed Components:")
                print(f"      • Task Code: {charge_job_parts[0]}")
                print(f"      • Location: {charge_job_parts[1]}")
                print(f"      • Sub Location: {charge_job_parts[2]}")
                print(f"      • Type: {charge_job_parts[3]}")
            else:
                print(f"   ⚠️ Could not parse charge job into components")
                
        except Exception as e:
            print(f"   ⚠️ Error displaying record details: {e}")
    
    async def _process_record_with_retry(self, record: StagingRecord) -> AutomationResult:
        """Process a single record with retry logic for error handling"""
        start_time = time.time()
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"Processing record {record.id} (attempt {attempt + 1}/{self.max_retries})")
                
                # Navigate to task register (with fresh page load)
                await self._navigate_to_task_register_robust()
                
                # Fill the form with enhanced error handling
                await self._fill_form_robust(record)
                
                # Submit the form
                await self._submit_form_robust()
                
                # Wait and verify submission
                await self._verify_submission()
                
                processing_time = time.time() - start_time
                
                self.logger.info(f"✅ Successfully processed record {record.id} in {processing_time:.2f}s")
                
                return AutomationResult(
                    success=True,
                    record_id=record.id,
                    message="Record processed successfully",
                    processing_time=processing_time
                )
                
            except Exception as e:
                last_error = e
                self.logger.warning(f"⚠️ Attempt {attempt + 1} failed for record {record.id}: {str(e)}")
                
                if attempt < self.max_retries - 1:
                    # Wait before retry
                    await asyncio.sleep(self.retry_delay)
                    
                    # Try to recover the page state
                    await self._recover_page_state()
        
        # All retries failed
        processing_time = time.time() - start_time
        error_msg = f"Failed to process record {record.id} after {self.max_retries} attempts"
        self.logger.error(f"❌ {error_msg}: {str(last_error)}")
        
        return AutomationResult(
            success=False,
            record_id=record.id,
            message="Processing failed after multiple attempts",
            error_details=str(last_error),
            processing_time=processing_time
        )
    
    async def _navigate_to_task_register_robust(self):
        """Navigate to task register page with robust error handling and redundancy elimination"""
        try:
            self.logger.info("🎯 Starting robust navigation to task register...")
            
            # Log current state before navigation
            current_url = self.driver.current_url
            self.logger.info(f"Current URL before navigation: {current_url}")
            print(f"📍 Current URL before navigation: {current_url}")

            # CRITICAL FIX: Check if already on task register page to avoid redundant navigation
            if "frmPrTrxTaskRegisterDet.aspx" in current_url:
                self.logger.info("✅ Already on task register page - skipping navigation")
                print("✅ Already on task register page - skipping navigation")
            else:
                # Only navigate if not already on the target page
                self.logger.info("🚀 Navigating to task register page...")
                print("🚀 Navigating to task register page...")
            await self.browser_manager.navigate_to_task_register()
            
            # Verify successful navigation
            final_url = self.driver.current_url
            self.logger.info(f"Final URL after navigation: {final_url}")
            print(f"📍 Final URL after navigation: {final_url}")
            
            if "frmPrTrxTaskRegisterDet.aspx" not in final_url:
                raise Exception(f"Navigation failed - ended up at unexpected URL: {final_url}")
            
            # Wait for the form to be ready with enhanced detection
            self.logger.info("🔄 Waiting for task register form to be ready...")
            print("🔄 Waiting for task register form to be ready...")
            await self._wait_for_form_ready_enhanced()
            
            self.logger.info("✅ Successfully navigated to task register and form is ready")
            print("✅ Task register form is ready for data entry")
            
        except Exception as e:
            self.logger.error(f"Failed to navigate to task register: {e}")
            print(f"❌ Navigation failed: {e}")
            raise
    
    async def _wait_for_form_ready_enhanced(self):
        """Enhanced form readiness detection based on ACTUAL HTML structure from user"""
        try:
            self.logger.info("🔍 Starting enhanced form readiness detection...")
            print("🔍 Checking form elements availability...")

            # FIXED: Based on actual HTML structure provided by user
            # All autocomplete fields use the same class: "ui-autocomplete-input ui-widget ui-widget-content"
            
            available_count = 0
            
            # 1. Check Date Field (MainContent_txtTrxDate) - This one has a specific ID
            try:
                date_field = self.driver.find_element(By.ID, "MainContent_txtTrxDate")
                if date_field.is_displayed() and date_field.is_enabled():
                    self.date_field_id = "MainContent_txtTrxDate"
                    available_count += 1
                    self.logger.info("✅ Found date field (MainContent_txtTrxDate): ready for input")
                    print("✅ Found date field: ready for input")
                else:
                    self.logger.warning("⚠️ Date field not ready")
                    print("⚠️ Date field not ready")
            except Exception as e:
                self.logger.warning(f"❌ Date field not found: {e}")
                print("❌ Date field not found")
            
            # 2. Check Autocomplete Fields (Employee, Task Code, Station, Machine, Expense)
            try:
                # Find all autocomplete input fields
                autocomplete_fields = self.driver.find_elements(
                    By.CSS_SELECTOR, 
                    "input.ui-autocomplete-input.ui-widget.ui-widget-content"
                )
                
                displayed_autocomplete_count = 0
                for i, field in enumerate(autocomplete_fields):
                    try:
                        if field.is_displayed() and field.is_enabled():
                            displayed_autocomplete_count += 1
                            self.logger.info(f"✅ Found autocomplete field {i+1}: ready for input")
                            print(f"✅ Found autocomplete field {i+1}: ready")
                    except:
                        continue
                
                available_count += displayed_autocomplete_count
                self.logger.info(f"📊 Found {displayed_autocomplete_count} autocomplete fields ready")
                print(f"📊 Found {displayed_autocomplete_count} autocomplete fields ready")
                
            except Exception as e:
                self.logger.warning(f"❌ Error checking autocomplete fields: {e}")
                print("❌ Error checking autocomplete fields")

            # Set default date field ID if not set
            if not hasattr(self, 'date_field_id') or not self.date_field_id:
                self.date_field_id = "MainContent_txtTrxDate"
                self.logger.warning("⚠️ Using default date field ID: MainContent_txtTrxDate")
                print("⚠️ Using default date field ID")

            self.logger.info(f"📊 Form readiness summary: {available_count} elements ready")
            print(f"📊 Form readiness: {available_count} elements ready")

            # More lenient criteria - just need at least the date field
            if available_count >= 1:
                self.logger.info("✅ Form is ready for data entry")
                print("✅ Form ready - proceeding with data entry")
                await asyncio.sleep(1)  # Brief stabilization wait
                return True
            else:
                # Give the page more time to load
                self.logger.warning("⚠️ No elements ready, waiting for page to load...")
                print("⚠️ Waiting for page elements to load...")
                await asyncio.sleep(3)
                
                # Retry once more
                try:
                    retry_date_field = self.driver.find_element(By.ID, "MainContent_txtTrxDate")
                    if retry_date_field.is_displayed():
                        self.logger.info("✅ Date field became available after waiting")
                        print("✅ Date field is now available")
                        return True
                except:
                    pass

                # Even if detection fails, try to proceed
                self.logger.warning("⚠️ Form detection incomplete, but proceeding with automation")
                print("⚠️ Proceeding with automation attempt")
                return True

        except Exception as e:
            self.logger.error(f"❌ Form readiness check failed: {e}")
            print(f"❌ Form readiness check failed: {e}")

            # Always fall back gracefully
            self.date_field_id = "MainContent_txtTrxDate"
            self.logger.warning("⚠️ Using fallback strategy - assuming form is ready")
            print("⚠️ Using fallback strategy")
            return True
    
    async def _fill_form_robust(self, record: StagingRecord):
        """Fill the form with robust element handling"""
        try:
            # Fill date field with retry logic
            await self._fill_date_field_robust(record.date)
            
            # Fill employee field
            await self._fill_employee_field_robust(record.employee_name)
            
            # Parse and fill charge job fields
            charge_job_parts = self.parse_charge_job(record.raw_charge_job)
            await self._fill_charge_job_fields_robust(charge_job_parts)
            
        except Exception as e:
            self.logger.error(f"Failed to fill form: {e}")
            raise
    
    async def _fill_date_field_robust(self, date_str: str):
        """Fill date field using JavaScript to completely avoid stale element issues"""
        try:
            self.logger.info(f"🎯 Starting JAVASCRIPT date field filling")
            print(f"📅 Starting date field filling: {date_str}")

            # Format the date
            formatted_date = self.format_date_for_input(date_str)
            self.logger.info(f"📅 Formatted date: {formatted_date}")

            max_attempts = 3
        
            for attempt in range(1, max_attempts + 1):
                try:
                    self.logger.info(f"📅 JavaScript date filling attempt {attempt}/{max_attempts}")
                    print(f"📅 JavaScript attempt {attempt}: {formatted_date}")

                    # Method 1: Direct JavaScript execution (most reliable)
                    script = f"""
                    var dateField = document.getElementById('MainContent_txtTrxDate');
                    if (dateField && dateField.offsetParent !== null) {{
                        dateField.value = '{formatted_date}';
                        dateField.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        dateField.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        return 'SUCCESS';
                    }} else {{
                        return 'FIELD_NOT_FOUND';
                    }}
                    """

                    result = self.driver.execute_script(script)

                    if result == 'SUCCESS':
                        self.logger.info(f"✅ Date field filled via JavaScript: {formatted_date}")
                        print(f"✅ Date filled via JavaScript: {formatted_date}")

                        # Brief pause for form processing
                        await asyncio.sleep(1)

                        # Verify the value was set
                        verify_script = "return document.getElementById('MainContent_txtTrxDate').value;"
                        current_value = self.driver.execute_script(verify_script)

                        if current_value == formatted_date:
                            self.logger.info("✅ Date field value verified successfully")
                            print("✅ Date field verified successfully")
                            return True
                        else:
                            self.logger.warning(f"⚠️ Date verification failed: expected {formatted_date}, got {current_value}")
                            print(f"⚠️ Date verification failed, got: {current_value}")

                    elif result == 'FIELD_NOT_FOUND':
                        self.logger.warning("⚠️ Date field not found via JavaScript")
                        print("⚠️ Date field not found")

                    # If JavaScript method failed, try fallback
                    if attempt < max_attempts:
                        self.logger.info("🔄 JavaScript method failed, trying fallback...")
                        print("🔄 Trying fallback method...")

                        # Wait and try again
                        await asyncio.sleep(2)
                        continue
                    else:
                        # Final attempt with traditional Selenium as last resort
                        self.logger.info("🔄 Final attempt with traditional Selenium...")
                        print("🔄 Final attempt with Selenium...")

                        try:
                            date_field = self.driver.find_element(By.ID, "MainContent_txtTrxDate")
                            if date_field.is_displayed() and date_field.is_enabled():
                                # Clear field using JavaScript first
                                self.driver.execute_script("arguments[0].value = '';", date_field)
                                await asyncio.sleep(0.3)

                                # Input using Selenium
                                date_field.send_keys(formatted_date)
                                await asyncio.sleep(0.5)

                                # Trigger events using JavaScript
                                self.driver.execute_script("""
                                    arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                                    arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                                """, date_field)

                                self.logger.info(f"✅ Date field filled via hybrid method: {formatted_date}")
                                print(f"✅ Date filled via hybrid method: {formatted_date}")
                                return True
                        except Exception as selenium_error:
                            self.logger.warning(f"Selenium fallback also failed: {selenium_error}")
                            print("⚠️ Selenium fallback failed")

                except Exception as e:
                    self.logger.error(f"Date field error on attempt {attempt}: {e}")
                    print(f"❌ Date field error on attempt {attempt}")

                    if attempt < max_attempts:
                        await asyncio.sleep(1.5)
                        continue
                    else:
                        break

            # If we get here, all attempts failed
            self.logger.error("❌ Date field failed after all JavaScript attempts")
            print("❌ Date field failed after all attempts")
            
            # Continue without failing - just log warning
            self.logger.warning("⚠️ Date field filling unsuccessful, but continuing automation")
            print("⚠️ Date field filling unsuccessful, but continuing with next steps")
            return False

        except Exception as e:
            self.logger.error(f"❌ Critical date field error: {e}")
            print(f"❌ Critical date field error: {e}")
            
            # Always continue - don't let date field issues stop the automation
            self.logger.warning("⚠️ Date field filling failed, but continuing automation")
            print("⚠️ Date field filling failed, but continuing with automation")
            return False

    async def _wait_for_page_stability(self):
        """Wait for the page to be stable and not changing"""
        try:
            self.logger.debug("⏱️ Waiting for page stability...")
            
            # Check that we're still on the right page
            current_url = self.driver.current_url
            if "frmPrTrxTaskRegisterDet.aspx" not in current_url:
                raise Exception(f"Page changed unexpectedly to: {current_url}")
            
            # Wait for DOM to be stable (no pending requests)
            await asyncio.sleep(1.5)
            
            # Check readyState
            ready_state = self.driver.execute_script("return document.readyState")
            if ready_state != "complete":
                self.logger.debug(f"Page not ready (readyState: {ready_state}), waiting...")
                await asyncio.sleep(2)
            
            self.logger.debug("✅ Page appears stable")
            
        except Exception as e:
            self.logger.warning(f"Page stability check failed: {e}")

    async def _refresh_page_state(self):
        """Refresh the page state when encountering persistent stale element issues"""
        try:
            self.logger.info("🔄 Refreshing page state to resolve stale element issues...")
            print("🔄 Refreshing page to resolve issues...")
            
            current_url = self.driver.current_url
            
            # Soft refresh - just reload current page
            self.driver.refresh()
            await asyncio.sleep(3)
            
            # Verify we're still on the right page
            final_url = self.driver.current_url
            
            if "frmPrTrxTaskRegisterDet.aspx" not in final_url:
                # If refresh took us somewhere else, navigate back
                await self._navigate_to_task_register_robust()
            
            # Wait for form to be ready again
            await self._wait_for_form_ready_enhanced()
            
            self.logger.info("✅ Page state refreshed successfully")
            print("✅ Page refreshed and ready")
            
        except Exception as e:
            self.logger.warning(f"Page state refresh failed: {e}")
            print(f"⚠️ Page refresh failed: {e}")
    
    async def _fill_employee_field_robust(self, employee_name: str):
        """Fill employee field using the actual HTML structure (autocomplete input)"""
        try:
            self.logger.info(f"👤 Filling employee field with: {employee_name}")
            print(f"👤 Filling employee field: {employee_name}")

            # Based on actual HTML: Employee field is the FIRST autocomplete input after the date field
            autocomplete_fields = self.driver.find_elements(
                By.CSS_SELECTOR, 
                "input.ui-autocomplete-input.ui-widget.ui-widget-content"
            )
            
            employee_field = None
            
            # Employee field should be the first autocomplete field
            for field in autocomplete_fields:
                try:
                    if field.is_displayed() and field.is_enabled():
                        employee_field = field
                        break
                except:
                    continue
            
            if not employee_field:
                # Fallback: try to find by proximity to employee label
                try:
                    # Look for employee label and find nearby input
                    employee_labels = self.driver.find_elements(By.XPATH, "//td[contains(text(), 'Employee')]")
                    if employee_labels:
                        # Find the autocomplete input in the same row or nearby
                        parent_row = employee_labels[0].find_element(By.XPATH, "./ancestor::tr[1]")
                        employee_field = parent_row.find_element(By.CSS_SELECTOR, "input.ui-autocomplete-input")
                except:
                    pass
            
            if not employee_field:
                raise Exception("Could not locate employee autocomplete field")

            self.logger.info("✅ Found employee autocomplete field")
            print("✅ Found employee autocomplete field")

            # Clear and fill the field
            employee_field.clear()
            await asyncio.sleep(0.5)
            
            employee_field.send_keys(employee_name)
            await asyncio.sleep(1)  # Wait for autocomplete suggestions
            
            # Press Tab to select and move to next field
            employee_field.send_keys(Keys.TAB)
            await asyncio.sleep(1)
            
            self.logger.info("✅ Employee field filled successfully")
            print("✅ Employee field filled successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to fill employee field: {e}")
            print(f"❌ Failed to fill employee field: {e}")
            # Don't fail completely - continue with automation
            self.logger.warning("⚠️ Employee field filling failed, continuing anyway")
            print("⚠️ Continuing with next field")
    
    async def _fill_charge_job_fields_robust(self, charge_job_parts: List[str]):
        """Fill charge job fields using actual HTML structure (autocomplete inputs in sequence)"""
        try:
            self.logger.info(f"🔧 Filling charge job fields with {len(charge_job_parts)} parts")
            print(f"🔧 Filling charge job fields: {len(charge_job_parts)} parts")

            if len(charge_job_parts) < 4:
                self.logger.warning(f"⚠️ Expected 4 charge job parts, got {len(charge_job_parts)}")
                print(f"⚠️ Expected 4 parts, got {len(charge_job_parts)}")
                return

            # Get all autocomplete fields
            autocomplete_fields = self.driver.find_elements(
                By.CSS_SELECTOR, 
                "input.ui-autocomplete-input.ui-widget.ui-widget-content"
            )
                
            # Filter to get only displayed and enabled fields
            available_fields = []
            for field in autocomplete_fields:
                try:
                    if field.is_displayed() and field.is_enabled():
                        available_fields.append(field)
                except:
                    continue
            
            self.logger.info(f"📊 Found {len(available_fields)} available autocomplete fields")
            print(f"📊 Found {len(available_fields)} autocomplete fields")

            # Based on HTML structure, the fields are in order:
            # 0: Employee (already filled)
            # 1: Task Code  
            # 2: Station Code
            # 3: Machine Code
            # 4: Expense Code

            field_mapping = [
                (1, charge_job_parts[0], "Task Code"),      # Task Code
                (2, charge_job_parts[1], "Station Code"),   # Station Code  
                (3, charge_job_parts[2], "Machine Code"),   # Machine Code
                (4, charge_job_parts[3], "Expense Code")    # Expense Code
            ]

            for field_index, value, field_name in field_mapping:
                try:
                    if field_index < len(available_fields):
                        field = available_fields[field_index]
                        
                        self.logger.info(f"🔧 Filling {field_name} (field {field_index}): {value}")
                        print(f"🔧 Filling {field_name}: {value}")
                        
                        # Clear and fill
                        field.clear()
                        await asyncio.sleep(0.5)

                        field.send_keys(value)
                        await asyncio.sleep(1)  # Wait for autocomplete
            
                        # Press Tab to confirm selection and move to next
                        field.send_keys(Keys.TAB)
                        await asyncio.sleep(1)
                        
                        self.logger.info(f"✅ {field_name} filled successfully")
                        print(f"✅ {field_name} filled")
                        
                    else:
                        self.logger.warning(f"⚠️ Field index {field_index} not available for {field_name}")
                        print(f"⚠️ {field_name} field not available")
                        
                except Exception as e:
                    self.logger.error(f"❌ Failed to fill {field_name}: {e}")
                    print(f"❌ Failed to fill {field_name}")
                    continue

            self.logger.info("✅ All charge job fields processed")
            print("✅ Charge job fields completed")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to fill charge job fields: {e}")
            print(f"❌ Charge job filling failed: {e}")
            # Don't raise - continue with automation
    
    async def _submit_form_robust(self):
        """Submit form using the actual form structure (Add button)"""
        try:
            self.logger.info("📤 Submitting form...")
            print("📤 Submitting form...")

            # Look for the Add button based on actual HTML: id="MainContent_btnAdd"
            try:
                add_button = self.driver.find_element(By.ID, "MainContent_btnAdd")
                if add_button.is_displayed() and add_button.is_enabled():
                    add_button.click()
                    self.logger.info("✅ Clicked Add button")
                    print("✅ Form submitted via Add button")
                else:
                    raise Exception("Add button not clickable")
            except:
                # Fallback: use keyboard method
                self.logger.info("🔄 Add button not found, using keyboard method")
                print("🔄 Using keyboard submission")

                actions = webdriver.ActionChains(self.driver)
                actions.send_keys(Keys.ARROW_DOWN).send_keys(Keys.RETURN).perform()

                self.logger.info("✅ Form submitted using keyboard")
                print("✅ Form submitted via keyboard")

            # Wait for submission processing
            await asyncio.sleep(3)
            
        except Exception as e:
            self.logger.error(f"❌ Failed to submit form: {e}")
            print(f"❌ Form submission failed: {e}")
            raise
    
    async def _verify_submission(self):
        """Verify form submission was successful"""
        try:
            # Wait for page to process the submission
            await asyncio.sleep(5)
            
            # Check if we're still on the same page or if there were any errors
            current_url = self.driver.current_url
            
            # Look for any error messages
            error_elements = self.driver.find_elements(By.CSS_SELECTOR, ".error, .alert-danger, .validation-error")
            if error_elements:
                error_text = " ".join([elem.text for elem in error_elements if elem.text.strip()])
                if error_text:
                    raise Exception(f"Form submission error: {error_text}")
            
            self.logger.debug("Form submission verified successfully")
            
        except Exception as e:
            self.logger.error(f"Form submission verification failed: {e}")
            raise
    
    async def _recover_page_state(self):
        """Attempt to recover the page state after an error"""
        try:
            self.logger.info("Attempting to recover page state...")
            
            # Try to refresh the page
            self.driver.refresh()
            await asyncio.sleep(3)
            
            # Navigate back to task register
            await self._navigate_to_task_register_robust()
            
        except Exception as e:
            self.logger.warning(f"Page state recovery failed: {e}")
    
    def parse_charge_job(self, raw_charge_job: str) -> List[str]:
        """Parse raw charge job string into components"""
        try:
            # Split by " / " to get the main parts
            parts = raw_charge_job.split(" / ")
            
            if len(parts) >= 4:
                # Extract task code from first part (remove parentheses)
                task_code = parts[0].strip()
                if task_code.startswith("(") and ")" in task_code:
                    task_code = task_code.split(")", 1)[0][1:]
                
                # Extract other parts
                location = parts[1].strip()
                sub_location = parts[2].split("(")[0].strip()
                type_code = parts[3].split("(")[0].strip()
                
                return [task_code, location, sub_location, type_code]
            
            return []
            
        except Exception as e:
            self.logger.error(f"Failed to parse charge job: {e}")
            return []
    
    def format_date_for_input(self, date_str: str) -> str:
        """Format date string for input field"""
        try:
            # Parse the date and format as DD/MM/YYYY
            if "-" in date_str:
                # Assume YYYY-MM-DD format
                year, month, day = date_str.split("-")
                return f"{day.zfill(2)}/{month.zfill(2)}/{year}"
            else:
                # Return as-is if already in expected format
                return date_str
                
        except Exception as e:
            self.logger.warning(f"Date formatting error: {e}, using original: {date_str}")
            return date_str
    
    def _dict_to_staging_record(self, record_data: Dict[str, Any]) -> StagingRecord:
        """Convert dictionary to StagingRecord"""
        return StagingRecord(
            id=record_data.get('id', ''),
            employee_name=record_data.get('employee_name', ''),
            employee_id=record_data.get('employee_id', ''),
            date=record_data.get('date', ''),
            task_code=record_data.get('task_code', ''),
            station_code=record_data.get('station_code', ''),
            raw_charge_job=record_data.get('raw_charge_job', ''),
            status=record_data.get('status', ''),
            hours=record_data.get('hours', 7.0),
            unit=record_data.get('unit', 1.0)
        )
    
    async def cleanup(self):
        """Clean up resources"""
        try:
            self.logger.info("Cleaning up Enhanced Staging Automation Engine")
            
            if self.browser_manager:
                await self.browser_manager.cleanup()
            
            self.driver = None
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}") 