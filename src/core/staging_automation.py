"""
Staging Data Automation Engine
Handles automated data entry for staging records using Selenium
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
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .automation_engine import AutomationEngine
from .browser_manager import BrowserManager

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

class StagingAutomationEngine:
    """Enhanced automation engine for processing staging data"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.browser_manager = None
        self.driver = None
        self.automation_engine = None
        
        # URLs from config
        self.login_url = config.get('urls', {}).get('login', 'http://millwarep3:8004/')
        self.task_register_url = config.get('urls', {}).get('taskRegister', 
            'http://millwarep3:8004/en/PR/trx/frmPrTrxTaskRegisterDet.aspx')
        
        # Credentials
        self.username = config.get('credentials', {}).get('username', 'adm075')
        self.password = config.get('credentials', {}).get('password', 'adm075')
    
    async def initialize(self):
        """Initialize the automation system"""
        try:
            self.logger.info("Initializing Staging Automation Engine")
            
            # Initialize browser manager
            browser_config = self.config.get('browser', {})
            self.browser_manager = BrowserManager(browser_config)
            
            # Create browser driver
            self.driver = self.browser_manager.create_driver()
            
            # Initialize automation engine
            automation_config = self.config.get('automation', {})
            self.automation_engine = AutomationEngine(self.driver, automation_config)
            
            self.logger.info("Staging Automation Engine initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize automation engine: {e}")
            raise
    
    async def process_staging_records(self, records: List[Dict[str, Any]]) -> List[AutomationResult]:
        """Process multiple staging records"""
        results = []
        
        try:
            # Ensure we're logged in
            await self.ensure_logged_in()
            
            for i, record_data in enumerate(records):
                self.logger.info(f"Processing record {i+1}/{len(records)}: {record_data.get('employee_name')}")
                
                # Convert dict to StagingRecord
                record = self._dict_to_staging_record(record_data)
                
                # Process individual record
                result = await self.process_single_record(record)
                results.append(result)
                
                # Add delay between records
                if i < len(records) - 1:  # Don't wait after the last record
                    await asyncio.sleep(2)
            
            self.logger.info(f"Completed processing {len(records)} records")
            return results
            
        except Exception as e:
            self.logger.error(f"Error processing staging records: {e}")
            # Add error result for any unprocessed records
            for record_data in records[len(results):]:
                results.append(AutomationResult(
                    success=False,
                    record_id=record_data.get('id', 'unknown'),
                    message="Processing failed due to system error",
                    error_details=str(e)
                ))
            return results
    
    async def process_single_record(self, record: StagingRecord) -> AutomationResult:
        """Process a single staging record"""
        start_time = time.time()
        
        try:
            self.logger.info(f"Processing record: {record.employee_name} - {record.date}")
            
            # Navigate to task register page
            await self.navigate_to_task_register()
            
            # Fill the form with record data
            await self.fill_task_register_form(record)
            
            # Submit the form (Arrow Down + Enter)
            await self.submit_form()
            
            # Wait for page reload and verify success
            await self.wait_for_form_submission()
            
            processing_time = time.time() - start_time
            
            self.logger.info(f"Successfully processed record {record.id} in {processing_time:.2f}s")
            
            return AutomationResult(
                success=True,
                record_id=record.id,
                message="Record processed successfully",
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Failed to process record {record.id}: {str(e)}"
            self.logger.error(error_msg)
            
            return AutomationResult(
                success=False,
                record_id=record.id,
                message="Processing failed",
                error_details=str(e),
                processing_time=processing_time
            )
    
    async def ensure_logged_in(self):
        """Ensure user is logged in to the system"""
        try:
            current_url = self.driver.current_url
            
            # Check if we need to login
            if 'login' in current_url.lower() or not self.is_logged_in():
                self.logger.info("Performing login...")
                await self.perform_login()
            else:
                self.logger.info("Already logged in")
                
        except Exception as e:
            self.logger.error(f"Login check failed: {e}")
            # Try to login anyway
            await self.perform_login()
    
    def is_logged_in(self) -> bool:
        """Check if user is currently logged in"""
        try:
            # Check for login form elements (if present, we're not logged in)
            username_field = self.driver.find_elements(By.ID, "txtUsername")
            if username_field:
                return False
            
            # Check for navigation elements (if present, we're logged in)
            nav_elements = self.driver.find_elements(By.CSS_SELECTOR, "a.popout.level1.static")
            return len(nav_elements) > 0
            
        except Exception:
            return False
    
    async def perform_login(self):
        """Perform login to the system"""
        try:
            self.logger.info(f"Navigating to login page: {self.login_url}")
            self.driver.get(self.login_url)
            
            # Wait for login form
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "txtUsername"))
            )
            
            # Enter credentials
            username_field.clear()
            username_field.send_keys(self.username)
            
            password_field = self.driver.find_element(By.ID, "txtPassword")
            password_field.clear()
            password_field.send_keys(self.password)
            
            # Click login button
            login_button = self.driver.find_element(By.ID, "btnLogin")
            login_button.click()
            
            # Wait for login to complete
            await asyncio.sleep(2)
            
            # Handle any popups
            await self.handle_login_popups()
            
            self.logger.info("Login completed successfully")
            
        except Exception as e:
            self.logger.error(f"Login failed: {e}")
            raise
    
    async def handle_login_popups(self):
        """Handle any popups that appear after login"""
        try:
            # Wait a bit for popups to appear
            await asyncio.sleep(1)
            
            # Look for common popup elements
            popup_selectors = [
                "#MainContent_mpopLocation_backgroundElement",
                ".ModalPopupBG",
                "[class*='modal']",
                "[class*='popup']"
            ]
            
            ok_button_selectors = [
                "#MainContent_btnOkay",
                "#btnOkay",
                "input[type='button'][value*='OK']",
                "input[type='button'][value*='Ok']",
                ".button"
            ]
            
            # Try to find and dismiss popups
            for ok_selector in ok_button_selectors:
                try:
                    ok_button = self.driver.find_element(By.CSS_SELECTOR, ok_selector)
                    if ok_button.is_displayed():
                        ok_button.click()
                        await asyncio.sleep(1)
                        self.logger.info(f"Dismissed popup using selector: {ok_selector}")
                        break
                except NoSuchElementException:
                    continue
                    
        except Exception as e:
            self.logger.warning(f"Error handling login popups: {e}")
    
    async def navigate_to_task_register(self):
        """Navigate to the task register page"""
        try:
            self.logger.info(f"Navigating to task register: {self.task_register_url}")
            self.driver.get(self.task_register_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "MainContent_txtTrxDate"))
            )
            
            await asyncio.sleep(1)  # Additional stability wait
            
        except Exception as e:
            self.logger.error(f"Failed to navigate to task register: {e}")
            raise
    
    async def fill_task_register_form(self, record: StagingRecord):
        """Fill the task register form with record data"""
        try:
            # 1. Fill transaction date
            await self.fill_date_field(record.date)
            
            # 2. Fill employee name
            await self.fill_employee_field(record.employee_name)
            
            # 3. Parse and fill charge job data
            charge_job_parts = self.parse_charge_job(record.raw_charge_job)
            await self.fill_charge_job_fields(charge_job_parts)
            
            self.logger.info(f"Form filled successfully for record {record.id}")
            
        except Exception as e:
            self.logger.error(f"Failed to fill form for record {record.id}: {e}")
            raise
    
    async def fill_date_field(self, date_str: str):
        """Fill the transaction date field"""
        try:
            # Convert date format if needed (YYYY-MM-DD to DD/MM/YYYY)
            formatted_date = self.format_date_for_input(date_str)
            
            date_field = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.ID, "MainContent_txtTrxDate"))
            )
            
            date_field.clear()
            date_field.send_keys(formatted_date)
            
            # Click elsewhere to trigger page reload
            body = self.driver.find_element(By.TAG_NAME, "body")
            body.click()
            
            # Wait for page reload
            await asyncio.sleep(2)
            
            self.logger.info(f"Date field filled: {formatted_date}")
            
        except Exception as e:
            self.logger.error(f"Failed to fill date field: {e}")
            raise
    
    async def fill_employee_field(self, employee_name: str):
        """Fill the employee autocomplete field"""
        try:
            # Wait for employee autocomplete field
            employee_field = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#MainContent_ddlEmployee + input.ui-autocomplete-input"))
            )
            
            employee_field.clear()
            employee_field.send_keys(employee_name)
            
            # Wait for autocomplete suggestions
            await asyncio.sleep(1)
            
            # Navigate and select
            employee_field.send_keys(Keys.ARROW_DOWN)
            await asyncio.sleep(0.5)
            employee_field.send_keys(Keys.ENTER)
            
            # Wait for page reload
            await asyncio.sleep(2)
            
            self.logger.info(f"Employee field filled: {employee_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to fill employee field: {e}")
            raise
    
    def parse_charge_job(self, raw_charge_job: str) -> List[str]:
        """Parse the raw charge job string into components"""
        try:
            if not raw_charge_job:
                return []
            
            # Split by " / " separator
            parts = [part.strip() for part in raw_charge_job.split(" / ")]
            
            self.logger.info(f"Parsed charge job into {len(parts)} parts: {parts}")
            return parts
            
        except Exception as e:
            self.logger.error(f"Failed to parse charge job: {e}")
            return []
    
    async def fill_charge_job_fields(self, charge_job_parts: List[str]):
        """Fill the charge job fields sequentially"""
        try:
            if not charge_job_parts:
                self.logger.warning("No charge job parts to fill")
                return
            
            # The autocomplete fields appear sequentially as we fill them
            # Start with task code (first part)
            if len(charge_job_parts) > 0:
                await self.fill_autocomplete_field_by_position(1, charge_job_parts[0], "Task Code")
            
            # Station code (second part)
            if len(charge_job_parts) > 1:
                await self.fill_autocomplete_field_by_position(2, charge_job_parts[1], "Station Code")
            
            # Machine code (third part)
            if len(charge_job_parts) > 2:
                await self.fill_autocomplete_field_by_position(3, charge_job_parts[2], "Machine Code")
            
            # Expense code (fourth part)
            if len(charge_job_parts) > 3:
                await self.fill_autocomplete_field_by_position(4, charge_job_parts[3], "Expense Code")
            
        except Exception as e:
            self.logger.error(f"Failed to fill charge job fields: {e}")
            raise
    
    async def fill_autocomplete_field_by_position(self, position: int, value: str, field_name: str):
        """Fill an autocomplete field by its position"""
        try:
            # Wait for the field to appear
            selector = f"input.ui-autocomplete-input:nth-of-type({position + 1})"  # +1 because employee is first
            
            field = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
            
            field.clear()
            field.send_keys(value)
            
            # Wait for autocomplete suggestions
            await asyncio.sleep(1)
            
            # Navigate and select
            field.send_keys(Keys.ARROW_DOWN)
            await asyncio.sleep(0.5)
            field.send_keys(Keys.ENTER)
            
            # Wait for field to be processed
            await asyncio.sleep(1.5)
            
            self.logger.info(f"{field_name} field filled: {value}")
            
        except Exception as e:
            self.logger.error(f"Failed to fill {field_name} field: {e}")
            raise
    
    async def submit_form(self):
        """Submit the form using Arrow Down + Enter"""
        try:
            # Send Arrow Down key
            actions = ActionChains(self.driver)
            actions.send_keys(Keys.ARROW_DOWN).perform()
            await asyncio.sleep(0.5)
            
            # Send Enter key
            actions.send_keys(Keys.ENTER).perform()
            
            self.logger.info("Form submitted with Arrow Down + Enter")
            
        except Exception as e:
            self.logger.error(f"Failed to submit form: {e}")
            raise
    
    async def wait_for_form_submission(self):
        """Wait for form submission to complete"""
        try:
            # Wait for page reload completion
            # We'll use a more sophisticated approach than just time.sleep()
            await self.wait_for_page_stability()
            
            self.logger.info("Form submission completed")
            
        except Exception as e:
            self.logger.error(f"Error waiting for form submission: {e}")
            raise
    
    async def wait_for_page_stability(self, timeout: int = 10):
        """Wait for page to be stable (DOM ready and no pending requests)"""
        try:
            # Wait for document ready state
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # Additional wait for dynamic content
            await asyncio.sleep(1)
            
        except TimeoutException:
            self.logger.warning("Page stability timeout - continuing anyway")
    
    def format_date_for_input(self, date_str: str) -> str:
        """Format date string for input field (convert YYYY-MM-DD to DD/MM/YYYY)"""
        try:
            if '/' in date_str:
                # Already in DD/MM/YYYY format
                return date_str
            
            # Convert from YYYY-MM-DD
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            return date_obj.strftime('%d/%m/%Y')
            
        except ValueError:
            # If parsing fails, return as-is
            self.logger.warning(f"Could not parse date: {date_str}")
            return date_str
    
    def _dict_to_staging_record(self, record_data: Dict[str, Any]) -> StagingRecord:
        """Convert dictionary to StagingRecord object"""
        return StagingRecord(
            id=record_data.get('id', f"{record_data.get('employee_id', 'unknown')}_{record_data.get('date', 'unknown')}"),
            employee_name=record_data.get('employee_name', ''),
            employee_id=record_data.get('employee_id', ''),
            date=record_data.get('date', ''),
            task_code=record_data.get('task_code', ''),
            station_code=record_data.get('station_code', ''),
            raw_charge_job=record_data.get('raw_charge_job', ''),
            status=record_data.get('status', 'staged'),
            hours=record_data.get('hours', 7.0),
            unit=record_data.get('unit', 1.0)
        )
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            if self.browser_manager:
                self.browser_manager.quit_driver()
            self.logger.info("Staging automation engine cleaned up")
        except Exception as e:
            self.logger.warning(f"Error during cleanup: {e}")
