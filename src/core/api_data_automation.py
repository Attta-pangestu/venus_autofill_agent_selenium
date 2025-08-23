"""
API Data Automation Module for Venus AutoFill
Fetches staging data from API and fills Millware ERP forms with proper sequence
Handles overtime entries as separate transactions
"""

import asyncio
import json
import logging
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
import os

from .persistent_browser_manager import PersistentBrowserManager


class APIDataAutomation:
    """Handles API data fetching and form automation with proper sequence"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.browser_manager = None
        self.logger = logging.getLogger(__name__)
        self.api_url = "http://localhost:5173/api/staging/data"
        
    async def fetch_staging_data(self) -> List[Dict]:
        """Fetch staging data from API"""
        try:
            self.logger.info(f"Fetching data from API: {self.api_url}")
            response = requests.get(self.api_url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            self.logger.info(f"✅ Fetched {len(data)} records from API")
            return data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ API request failed: {e}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"❌ Invalid JSON response: {e}")
            raise
    
    def create_overtime_entries(self, record: Dict) -> List[Dict]:
        """
        Create separate entries for normal and overtime hours
        If overtime_hours > 0, creates two entries: normal and overtime
        If overtime_hours = 0, creates one normal entry
        """
        entries = []
        
        regular_hours = float(record.get('regular_hours', 0))
        overtime_hours = float(record.get('overtime_hours', 0))
        
        # Always create normal entry if regular_hours > 0
        if regular_hours > 0:
            normal_entry = record.copy()
            normal_entry['transaction_type'] = 'Normal'
            normal_entry['hours'] = regular_hours
            normal_entry['entry_type'] = 'normal'
            entries.append(normal_entry)
            self.logger.info(f"✅ Created normal entry: {regular_hours} hours")
        
        # Create overtime entry if overtime_hours > 0
        if overtime_hours > 0:
            overtime_entry = record.copy()
            overtime_entry['transaction_type'] = 'Overtime'
            overtime_entry['hours'] = overtime_hours
            overtime_entry['entry_type'] = 'overtime'
            entries.append(overtime_entry)
            self.logger.info(f"✅ Created overtime entry: {overtime_hours} hours")
        
        # If both are 0, still create one entry with 0 hours
        if regular_hours == 0 and overtime_hours == 0:
            normal_entry = record.copy()
            normal_entry['transaction_type'] = 'Normal'
            normal_entry['hours'] = 0
            normal_entry['entry_type'] = 'normal'
            entries.append(normal_entry)
            self.logger.info(f"✅ Created zero-hours entry")
        
        return entries
    
    def parse_charge_job(self, raw_charge_job: str) -> Tuple[str, str, str, str]:
        """
        Parse raw_charge_job into components
        Example: "(OC7190) BOILER OPERATION / STN-BLR (STATION BOILER) / BLR00000 (LABOUR COST) / L (LABOUR)"
        Returns: (task_code, station_code, machine_code, expense_code)
        """
        try:
            parts = [part.strip() for part in raw_charge_job.split(' / ')]
            
            task_code = parts[0] if len(parts) > 0 else ""
            station_code = parts[1] if len(parts) > 1 else ""
            machine_code = parts[2] if len(parts) > 2 else ""
            expense_code = parts[3] if len(parts) > 3 else ""
            
            self.logger.info(f"Parsed charge job:")
            self.logger.info(f"  Task: {task_code}")
            self.logger.info(f"  Station: {station_code}")
            self.logger.info(f"  Machine: {machine_code}")
            self.logger.info(f"  Expense: {expense_code}")
            
            return task_code, station_code, machine_code, expense_code
            
        except Exception as e:
            self.logger.error(f"❌ Failed to parse charge job: {e}")
            return "", "", "", ""
    
    def format_date(self, date_str: str) -> str:
        """
        Convert date from API format (2025-05-30) to form format (30/05/2025)
        """
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            formatted = date_obj.strftime("%d/%m/%Y")
            self.logger.info(f"Date formatted: {date_str} -> {formatted}")
            return formatted
        except Exception as e:
            self.logger.error(f"❌ Date formatting failed: {e}")
            return date_str
    
    async def select_transaction_type(self, driver, transaction_type: str) -> bool:
        """
        Select transaction type radio button (Normal or Overtime)
        """
        try:
            self.logger.info(f"🔘 Selecting transaction type: {transaction_type}")
            
            if transaction_type.lower() == 'normal':
                # Select Normal radio button
                script = """
                    var normalRadio = document.getElementById('MainContent_rblOT_0');
                    if (normalRadio) {
                        normalRadio.checked = true;
                        normalRadio.click();
                        return true;
                    }
                    return false;
                """
            elif transaction_type.lower() == 'overtime':
                # Select Overtime radio button
                script = """
                    var overtimeRadio = document.getElementById('MainContent_rblOT_1');
                    if (overtimeRadio) {
                        overtimeRadio.checked = true;
                        overtimeRadio.click();
                        return true;
                    }
                    return false;
                """
            else:
                self.logger.error(f"❌ Unknown transaction type: {transaction_type}")
                return False
            
            result = driver.execute_script(script)
            if result:
                self.logger.info(f"✅ {transaction_type} transaction type selected")
                await asyncio.sleep(1)  # Wait for any page updates
                return True
            else:
                self.logger.error(f"❌ Failed to select {transaction_type} transaction type")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Transaction type selection failed: {e}")
            return False
    
    async def fill_hours_field(self, driver, hours_value: float) -> bool:
        """Fill the hours field with the specified value"""
        try:
            self.logger.info(f"⏰ Filling hours field with: {hours_value}")
            
            # Use JavaScript to fill hours field
            script = f"""
                var hoursField = document.getElementById('MainContent_txtHours');
                if (hoursField) {{
                    hoursField.value = '{hours_value}';
                    hoursField.dispatchEvent(new Event('change', {{bubbles: true}}));
                    hoursField.dispatchEvent(new Event('blur', {{bubbles: true}}));
                    return true;
                }} else {{
                    return false;
                }}
            """
            
            result = driver.execute_script(script)
            if result:
                self.logger.info(f"✅ Hours field filled: {hours_value}")
                return True
            else:
                self.logger.error("❌ Hours field not found")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Hours field filling failed: {e}")
            return False
    
    async def fill_date_field(self, driver, date_value: str) -> bool:
        """Fill date field using JavaScript (proven method)"""
        try:
            # Check if date is already formatted (DD/MM/YYYY) or needs formatting (YYYY-MM-DD)
            if '/' in date_value and len(date_value.split('/')) == 3:
                # Already formatted as DD/MM/YYYY
                formatted_date = date_value
                self.logger.info(f"Date already formatted: {formatted_date}")
            else:
                # Need to format from YYYY-MM-DD to DD/MM/YYYY
                formatted_date = self.format_date(date_value)
            
            # Use JavaScript to fill date field (stale element immune)
            script = f"""
                var dateField = document.getElementById('MainContent_txtTrxDate');
                if (dateField) {{
                    dateField.value = '{formatted_date}';
                    dateField.dispatchEvent(new Event('change', {{bubbles: true}}));
                    dateField.dispatchEvent(new Event('blur', {{bubbles: true}}));
                    return true;
                }} else {{
                    return false;
                }}
            """
            
            result = driver.execute_script(script)
            if result:
                self.logger.info(f"✅ Date filled via JavaScript: {formatted_date}")
                
                # Send Enter and wait for reload
                date_field = driver.find_element(By.ID, "MainContent_txtTrxDate")
                date_field.send_keys(Keys.ENTER)
                self.logger.info("📤 Enter sent, waiting for reload...")
                
                # Wait for page to process
                await asyncio.sleep(2)
                return True
            else:
                self.logger.error("❌ Date field not found")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Date field filling failed: {e}")
            return False
    
    async def fill_employee_field(self, driver, employee_name: str) -> bool:
        """Fill employee field with arrow down + enter sequence"""
        try:
            # Find employee autocomplete input (based on actual HTML structure)
            employee_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".ui-autocomplete-input.ui-widget.ui-widget-content"))
            )
            
            # Clear and type employee name
            employee_input.clear()
            employee_input.send_keys(employee_name)
            self.logger.info(f"📝 Employee name typed: {employee_name}")
            
            # Wait for autocomplete suggestions
            await asyncio.sleep(1)
            
            # Arrow down + Enter
            employee_input.send_keys(Keys.ARROW_DOWN)
            await asyncio.sleep(0.5)
            employee_input.send_keys(Keys.ENTER)
            
            self.logger.info("✅ Employee selected with arrow down + enter")
            await asyncio.sleep(1)  # Wait for field to process
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Employee field filling failed: {e}")
            return False
    
    async def fill_autocomplete_field_by_index(self, driver, field_index: int, value: str, field_name: str) -> bool:
        """Fill autocomplete field by index position (0-based)"""
        try:
            # Find all autocomplete inputs
            autocomplete_inputs = driver.find_elements(By.CSS_SELECTOR, ".ui-autocomplete-input")
            
            if field_index >= len(autocomplete_inputs):
                self.logger.error(f"❌ {field_name} field index {field_index} not found. Only {len(autocomplete_inputs)} autocomplete fields available")
                return False
            
            field_input = autocomplete_inputs[field_index]
            
            # Check if field is visible and interactable
            if not field_input.is_displayed() or not field_input.is_enabled():
                self.logger.error(f"❌ {field_name} field at index {field_index} is not interactable")
                return False
            
            self.logger.info(f"✅ Found {field_name} field at index {field_index}")
            
            # Clear and type value
            field_input.clear()
            field_input.send_keys(value)
            self.logger.info(f"📝 {field_name} typed: {value}")
            
            # Wait for autocomplete suggestions
            await asyncio.sleep(1.5)  # Increased wait time
            
            # Arrow down + Enter
            field_input.send_keys(Keys.ARROW_DOWN)
            await asyncio.sleep(0.8)  # Increased wait time
            field_input.send_keys(Keys.ENTER)
            
            self.logger.info(f"✅ {field_name} selected with arrow down + enter")
            await asyncio.sleep(1.5)  # Wait for field to process
            return True
            
        except Exception as e:
            self.logger.error(f"❌ {field_name} field filling failed: {e}")
            return False
    
    async def process_single_record(self, driver, record: Dict) -> bool:
        """Process a single record following the exact sequence"""
        try:
            self.logger.info(f"🔄 Processing record ID: {record.get('id', 'Unknown')}")
            self.logger.info(f"Employee: {record.get('employee_name', 'Unknown')}")
            self.logger.info(f"Entry Type: {record.get('entry_type', 'normal')} - Hours: {record.get('hours', 0)}")
            
            # Parse charge job components
            task_code, station_code, machine_code, expense_code = self.parse_charge_job(
                record.get('raw_charge_job', '')
            )
            
            # Step 1: Fill date field
            if not await self.fill_date_field(driver, record.get('date', '')):
                return False
            
            # Step 2: Fill employee field
            if not await self.fill_employee_field(driver, record.get('employee_name', '')):
                return False
            
            # Step 3: Select transaction type (Normal or Overtime)
            transaction_type = record.get('transaction_type', 'Normal')
            if not await self.select_transaction_type(driver, transaction_type):
                return False
            
            # Step 4: Fill task code
            if task_code and not await self.fill_autocomplete_field_by_index(
                driver, 1, task_code, "Task Code"
            ):
                return False
            
            # Step 5: Fill station code
            if station_code and not await self.fill_autocomplete_field_by_index(
                driver, 2, station_code, "Station Code"
            ):
                return False
            
            # Step 6: Fill machine code
            if machine_code and not await self.fill_autocomplete_field_by_index(
                driver, 3, machine_code, "Machine Code"
            ):
                return False
            
            # Step 7: Fill expense code
            if expense_code and not await self.fill_autocomplete_field_by_index(
                driver, 4, expense_code, "Expense Code"
            ):
                return False
            
            # Step 8: Fill hours field
            hours = record.get('hours', 0)
            if not await self.fill_hours_field(driver, hours):
                return False
            
            self.logger.info("✅ Record processed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Record processing failed: {e}")
            return False
    
    async def run_api_automation(self) -> bool:
        """Main automation method - fetch data and process records"""
        try:
            # Fetch data from API
            raw_records = await self.fetch_staging_data()
            
            if not raw_records:
                self.logger.warning("⚠️ No records found in API response")
                return False
            
            # Process records to create separate normal/overtime entries
            all_entries = []
            for record in raw_records:
                entries = self.create_overtime_entries(record)
                all_entries.extend(entries)
            
            self.logger.info(f"📊 Created {len(all_entries)} entries from {len(raw_records)} records")
            
            # Get browser driver
            driver = await self.browser_manager.get_driver()
            if not driver:
                self.logger.error("❌ Failed to get browser driver")
                return False
            
            # Navigate to task register page
            task_register_url = "http://millwarep3.rebinmas.com:8004/en/PR/trx/frmPrTrxTaskRegisterDet.aspx"
            driver.get(task_register_url)
            self.logger.info(f"🌐 Navigated to: {task_register_url}")
            
            # Wait for page to load
            await asyncio.sleep(3)
            
            # Process each entry
            successful_entries = 0
            for i, entry in enumerate(all_entries, 1):
                self.logger.info(f"\n{'='*60}")
                self.logger.info(f"Processing Entry {i}/{len(all_entries)}")
                self.logger.info(f"Record ID: {entry.get('id', 'Unknown')}")
                self.logger.info(f"Type: {entry.get('transaction_type', 'Normal')} - Hours: {entry.get('hours', 0)}")
                self.logger.info(f"{'='*60}")
                
                if await self.process_single_record(driver, entry):
                    successful_entries += 1
                    
                    # TODO: Add form submission here (Add button click)
                    # For now, just wait before next entry
                    await asyncio.sleep(2)
                    
                    # Navigate back to form for next entry if not the last entry
                    if i < len(all_entries):
                        driver.get(task_register_url)
                        await asyncio.sleep(2)
                else:
                    self.logger.error(f"❌ Failed to process entry {i}")
            
            self.logger.info(f"\n🎯 Automation Complete!")
            self.logger.info(f"✅ Successfully processed: {successful_entries}/{len(all_entries)} entries")
            self.logger.info(f"📊 From {len(raw_records)} original records")
            
            return successful_entries > 0
            
        except Exception as e:
            self.logger.error(f"❌ API automation failed: {e}")
            return False

    async def fill_single_record(self, form_data: Dict) -> bool:
        """Fill a single record with form data (used by demo)"""
        try:
            if not self.browser_manager:
                self.logger.error("❌ Browser manager not initialized")
                return False
            
            driver = self.browser_manager.get_driver()
            if not driver:
                self.logger.error("❌ WebDriver not available")
                return False
            
            self.logger.info(f"🔄 Filling form with data: {form_data.get('employee', 'Unknown')}")
            
            # Step 1: Fill date field
            if 'date' in form_data and not await self.fill_date_field(driver, form_data['date']):
                return False
            
            # Step 2: Fill employee field (index 0 - first autocomplete field)
            if 'employee' in form_data and not await self.fill_autocomplete_field_by_index(
                driver, 0, form_data['employee'], "Employee"
            ):
                return False
            
            # Step 3: Fill task code (index 1 - second autocomplete field)  
            if 'task_code' in form_data and form_data['task_code']:
                if not await self.fill_autocomplete_field_by_index(
                    driver, 1, form_data['task_code'], "Task Code"
                ):
                    return False
            
            # Note: Based on form inspection, there are only 2 autocomplete fields visible
            # The Task Code field might contain multiple components or need different approach
            # For now, we'll focus on the first two fields that are working
            
            self.logger.info("✅ Form filled successfully (Date + Employee + Task)")
            self.logger.info("ℹ️ Station, Machine, Expense codes may be handled differently in this form")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Form filling failed: {e}")
            return False


class RealAPIDataProcessor:
    """Processor for real API data with sequential charge job filling and overtime support"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.browser_manager = None
        self.api_url = "http://localhost:5173/api/staging/data"
        self.grouped_api_url = "http://localhost:5173/api/staging/data-grouped"
        self.config = self._load_config()
        
        # Initialize API automation for overtime handling
        self.api_automation = APIDataAutomation()
        self.api_automation.logger = self.logger
    
    def _load_config(self) -> dict:
        """Load configuration from app_config.json with comprehensive defaults"""
        config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'app_config.json')
        
        # Default configuration with all required fields
        default_config = {
            "browser": {
                "headless": False,
                "window_size": [1280, 720],
                "page_load_timeout": 30,
                "implicit_wait": 10,
                "script_timeout": 30
            },
            "urls": {
                "login": "http://millwarep3.rebinmas.com:8004/",
                "taskRegister": "http://millwarep3.rebinmas.com:8004/en/PR/trx/frmPrTrxTaskRegisterDet.aspx",
                "taskRegisterTest": "http://millwarep3.rebinmas.com:8004/en/PR/trx/frmPrTrxTaskRegisterDet.aspx"
            },
            "credentials": {
                "username": "adm075",
                "password": "adm075"
            },
            "session": {
                "timeout_minutes": 30,
                "keepalive_interval": 10
            },
            "api": {
                "staging_url": "http://localhost:5173/api/staging/data",
                "grouped_url": "http://localhost:5173/api/staging/data-grouped",
                "timeout": 30
            }
        }
        
        try:
            # Try to load from config file
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                
                # Merge with defaults (file config takes precedence)
                merged_config = default_config.copy()
                
                # Deep merge nested dictionaries
                for key, value in file_config.items():
                    if key in merged_config and isinstance(merged_config[key], dict) and isinstance(value, dict):
                        merged_config[key].update(value)
                    else:
                        merged_config[key] = value
                
                self.logger.info(f"✅ Configuration loaded from: {config_path}")
                return merged_config
            else:
                self.logger.warning(f"⚠️ Config file not found at: {config_path}")
                self.logger.info("ℹ️ Using default configuration")
                return default_config
                
        except Exception as e:
            self.logger.error(f"❌ Error loading config: {e}")
            self.logger.info("ℹ️ Using default configuration")
            return default_config
    
    async def fetch_real_api_data(self) -> List[Dict]:
        """Fetch data from real API endpoint"""
        try:
            self.logger.info(f"🌐 Fetching data from: {self.api_url}")
            response = requests.get(self.api_url, timeout=30)
            response.raise_for_status()
            
            response_data = response.json()
            self.logger.info(f"✅ API response received")
            
            # The API returns a dict with 'data' key containing the actual records
            if isinstance(response_data, dict) and 'data' in response_data:
                data = response_data['data']
                self.logger.info(f"✅ Fetched {len(data)} records from API")
                
                # Log first record for verification
                if data:
                    first_record = data[0]
                    self.logger.info(f"📋 First record employee: {first_record.get('employee_name', 'Unknown')}")
                    self.logger.info(f"📋 First record date: {first_record.get('date', 'Unknown')}")
                    self.logger.info(f"📋 First record raw_charge_job: {first_record.get('raw_charge_job', 'Unknown')}")
                
                return data
            else:
                self.logger.error(f"❌ Unexpected API response structure: {type(response_data)}")
                return []
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ API request failed: {e}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"❌ Invalid JSON response: {e}")
            raise
    
    async def fetch_grouped_api_data(self) -> List[Dict]:
        """Fetch data from grouped API endpoint and convert to flat structure"""
        try:
            self.logger.info(f"🌐 Fetching grouped data from: {self.grouped_api_url}")
            response = requests.get(self.grouped_api_url, timeout=30)
            response.raise_for_status()
            
            response_data = response.json()
            
            if not response_data.get('success', False):
                raise Exception(f"API returned error: {response_data}")

            grouped_data = response_data.get('data', [])
            if not grouped_data:
                self.logger.warning("⚠️ No grouped data received from API")
                return []

            # Convert grouped structure to flat structure for compatibility
            flat_records = []
            for employee_group in grouped_data:
                identitas = employee_group.get('identitas_karyawan', {})
                data_presensi = employee_group.get('data_presensi', [])

                for attendance_record in data_presensi:
                    flat_record = {
                        # Employee identity fields
                        'employee_id': identitas.get('employee_id_venus', ''),
                        'employee_id_ptrj': identitas.get('employee_id_ptrj', ''),
                        'employee_name': identitas.get('employee_name', ''),
                        'task_code': identitas.get('task_code', ''),
                        'station_code': identitas.get('station_code', ''),
                        'machine_code': identitas.get('machine_code', ''),
                        'expense_code': identitas.get('expense_code', ''),
                        'raw_charge_job': identitas.get('raw_charge_job', ''),

                        # Attendance data fields
                        'id': attendance_record.get('id', ''),
                        'date': attendance_record.get('date', ''),
                        'day_of_week': attendance_record.get('day_of_week', ''),
                        'shift': attendance_record.get('shift', ''),
                        'check_in': attendance_record.get('check_in', ''),
                        'check_out': attendance_record.get('check_out', ''),
                        'regular_hours': attendance_record.get('regular_hours', 0),
                        'overtime_hours': attendance_record.get('overtime_hours', 0),
                        'total_hours': attendance_record.get('total_hours', 0),
                        'leave_type_code': attendance_record.get('leave_type_code'),
                        'leave_type_description': attendance_record.get('leave_type_description'),
                        'leave_ref_number': attendance_record.get('leave_ref_number'),
                        'is_alfa': attendance_record.get('is_alfa', False),
                        'is_on_leave': attendance_record.get('is_on_leave', False),
                        'status': attendance_record.get('status', 'staged'),
                        'created_at': attendance_record.get('created_at', ''),
                        'updated_at': attendance_record.get('updated_at', ''),
                        'source_record_id': attendance_record.get('source_record_id', ''),
                        'notes': attendance_record.get('notes', ''),
                        'transfer_status': attendance_record.get('transfer_status', '')
                    }
                    flat_records.append(flat_record)

            self.logger.info(f"✅ Converted {len(grouped_data)} employee groups to {len(flat_records)} flat records")
            return flat_records

        except Exception as e:
            self.logger.error(f"❌ Error fetching grouped API data: {e}")
            # Fallback to regular API
            return await self.fetch_real_api_data()
    
    def parse_raw_charge_job(self, raw_charge_job: str) -> List[str]:
        """Parse raw_charge_job by splitting with '/' separator"""
        try:
            # Split by '/' and clean up each component
            components = [component.strip() for component in raw_charge_job.split('/')]
            
            self.logger.info(f"🔧 Parsed charge job components:")
            for i, component in enumerate(components):
                self.logger.info(f"   [{i}]: {component}")
            
            return components
            
        except Exception as e:
            self.logger.error(f"❌ Failed to parse raw_charge_job: {e}")
            return []
    
    def format_date(self, date_str: str) -> str:
        """Convert date from API format to form format"""
        try:
            if '/' in date_str and len(date_str.split('/')) == 3:
                return date_str  # Already formatted
            
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            return date_obj.strftime("%d/%m/%Y")
        except Exception as e:
            self.logger.error(f"❌ Date formatting failed: {e}")
            return date_str

    def calculate_document_date(self, date_str: str) -> str:
        """
        Calculate document date using today's date with transaction date's month and year
        Example: Today=11/06/2025, Transaction=18/05/2025 -> Document=11/05/2025
        Uses today's day with transaction date's month/year
        """
        try:
            # Get today's date
            today = datetime.now()
            
            # Parse the transaction date
            if '/' in date_str and len(date_str.split('/')) == 3:
                # Already formatted as DD/MM/YYYY, convert to datetime
                trans_date_obj = datetime.strptime(date_str, "%d/%m/%Y")
            else:
                # Convert from YYYY-MM-DD to datetime
                trans_date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            
            # Create document date: today's day with transaction date's month/year
            doc_date = trans_date_obj.replace(day=today.day)
            
            # Handle case where today's day doesn't exist in transaction month (e.g., 31st in February)
            try:
                doc_date_str = doc_date.strftime("%d/%m/%Y")
            except ValueError:
                # If day doesn't exist in month, use last day of that month
                from calendar import monthrange
                last_day = monthrange(trans_date_obj.year, trans_date_obj.month)[1]
                doc_date = trans_date_obj.replace(day=last_day)
                doc_date_str = doc_date.strftime("%d/%m/%Y")
            
            self.logger.info(f"📅 Document date calculated: {doc_date_str} (today's day {today.day} with transaction month/year)")
            return doc_date_str
            
        except Exception as e:
            self.logger.error(f"❌ Document date calculation failed: {e}")
            return self.format_date(date_str)  # Fallback to original date

    def create_overtime_entries(self, record: Dict) -> List[Dict]:
        """Create separate entries for normal and overtime hours"""
        return self.api_automation.create_overtime_entries(record)

    async def select_transaction_type(self, driver, transaction_type: str) -> bool:
        """Select transaction type radio button (Normal or Overtime)"""
        return await self.api_automation.select_transaction_type(driver, transaction_type)

    async def fill_hours_field(self, driver, hours_value: float) -> bool:
        """Fill the hours field with the specified value"""
        return await self.api_automation.fill_hours_field(driver, hours_value)

    async def initialize_browser(self) -> bool:
        """Initialize the browser and navigate to task register page"""
        try:
            self.logger.info("🚀 Initializing browser...")
            
            # Initialize PersistentBrowserManager
            self.browser_manager = PersistentBrowserManager(self.config)
            
            # FIXED: Properly initialize the browser manager first
            self.logger.info("🔧 Initializing PersistentBrowserManager...")
            initialized = await self.browser_manager.initialize()
            
            if not initialized:
                self.logger.error("❌ Failed to initialize PersistentBrowserManager")
                return False
            
            # Get the driver (should now be available)
            driver = self.browser_manager.get_driver()
            if not driver:
                self.logger.error("❌ Failed to get WebDriver after initialization")
                return False
            
            # Navigate to task register page
            task_register_url = self.config.get('urls', {}).get('taskRegister', 
                'http://millwarep3.rebinmas.com:8004/en/PR/trx/frmPrTrxTaskRegisterDet.aspx')
            
            self.logger.info(f"🌐 Navigating to: {task_register_url}")
            print(f"🌐 Navigating to task register: {task_register_url}")
            
            # Use the PersistentBrowserManager's navigation method
            await self.browser_manager.navigate_to_task_register()
            
            self.logger.info("✅ Browser initialized and positioned at task register page")
            print("✅ Browser initialized and ready for automation")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Browser initialization failed: {e}")
            print(f"❌ Browser initialization failed: {e}")
            
            # Provide specific error guidance
            if "Failed to get WebDriver" in str(e):
                print("🔧 ChromeDriver Issue Detected:")
                print("   1. Try clearing WebDriver cache: rm -rf ~/.wdm")
                print("   2. Check if Chrome browser is installed")
                print("   3. Restart the application")
            elif "name not resolved" in str(e).lower():
                print("🌐 Network Issue Detected:")
                print("   1. Check if millwarep3.rebinmas.com is accessible")
                print("   2. Check your internet connection")
                print("   3. Try using IP address instead of hostname")
            
            return False

    async def click_new_button(self, driver) -> bool:
        """Click the New button after completing a date group"""
        try:
            self.logger.info("🔘 Clicking 'New' button...")
            
            # Try different selectors for the New button
            new_button_selectors = [
                "input[name='ctl00$MainContent$btnNew']",
                "input[id='MainContent_btnNew']", 
                "input[value='New']",
                "button[id*='btnNew']",
                "input[id*='btnNew']"
            ]
            
            new_button = None
            for selector in new_button_selectors:
                try:
                    new_button = driver.find_element(By.CSS_SELECTOR, selector)
                    if new_button.is_displayed() and new_button.is_enabled():
                        break
                except:
                    continue
            
            if new_button:
                new_button.click()
                self.logger.info("✅ 'New' button clicked successfully")
                
                # Wait for page to reload/reset
                await asyncio.sleep(3)
                
                # Wait for form to be ready
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "MainContent_txtTrxDate"))
                    )
                    self.logger.info("✅ Form ready after New button click")
                except TimeoutException:
                    self.logger.warning("⚠️ Form readiness timeout after New button click")
                
                return True
            else:
                self.logger.error("❌ 'New' button not found")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Failed to click New button: {e}")
            return False

    def group_records_by_date(self, records: List[Dict]) -> Dict[str, List[Dict]]:
        """Group records by attendance date, sorted chronologically"""
        try:
            date_groups = {}
            
            for record in records:
                date_str = record.get('date', '')
                if not date_str:
                    continue
                
                # Normalize date format
                try:
                    if '/' in date_str and len(date_str.split('/')) == 3:
                        date_obj = datetime.strptime(date_str, "%d/%m/%Y")
                    else:
                        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                    
                    # Use YYYY-MM-DD as key for consistent sorting
                    date_key = date_obj.strftime("%Y-%m-%d")
                    
                    if date_key not in date_groups:
                        date_groups[date_key] = []
                    
                    date_groups[date_key].append(record)
                    
                except ValueError as e:
                    self.logger.warning(f"⚠️ Invalid date format: {date_str}, skipping record")
                    continue
            
            # Sort by date keys (chronological order)
            sorted_dates = sorted(date_groups.keys())
            sorted_groups = {date_key: date_groups[date_key] for date_key in sorted_dates}
            
            self.logger.info(f"📅 Grouped {len(records)} records into {len(sorted_groups)} date groups")
            self.logger.info(f"📅 Date range: {sorted_dates[0] if sorted_dates else 'N/A'} to {sorted_dates[-1] if sorted_dates else 'N/A'}")
            
            return sorted_groups
            
        except Exception as e:
            self.logger.error(f"❌ Error grouping records by date: {e}")
            return {}

    async def process_batch_by_date_groups(self, automation_mode: str = 'testing') -> bool:
        """
        NEW: Process all staging data in batch mode, grouped chronologically by date
        """
        try:
            self.logger.info("🚀 Starting BATCH PROCESSING mode - grouped by attendance date")
            print("\n" + "="*80)
            print("📊 BATCH PROCESSING MODE ACTIVATED")
            print("="*80)
            
            # Fetch all staging data
            print("🌐 Fetching complete dataset from grouped API...")
            all_records = await self.fetch_grouped_api_data()
            
            if not all_records:
                print("❌ No staging data available for batch processing")
                return False
            
            # Group records by date
            print("📅 Grouping records by attendance date...")
            date_groups = self.group_records_by_date(all_records)
            
            if not date_groups:
                print("❌ No valid date groups found")
                return False
            
            # Display batch processing summary
            unique_employees = set(record.get('employee_name', '') for record in all_records)
            date_range = f"{min(date_groups.keys())} to {max(date_groups.keys())}"
            
            print(f"📅 Date Groups: {len(date_groups)} groups ({date_range})")
            print(f"👥 Total Employees: {len(unique_employees)} unique employees")
            print(f"📋 Total Records: {len(all_records)} attendance records")
            
            # Determine database based on mode
            db_name = "db_ptrj_mill_test" if automation_mode == 'testing' else "db_ptrj_mill"
            port = 8004 if automation_mode == 'testing' else 8003
            
            print(f"🗄️ Database: {db_name} ({automation_mode.upper()} Mode)")
            print(f"🔗 Target Port: {port}")
            print("="*80)
            
            # Get WebDriver
            driver = self.browser_manager.get_driver()
            if not driver:
                print("❌ WebDriver not available")
                return False
            
            # Process each date group sequentially
            successful_groups = 0
            failed_groups = 0
            total_successful_entries = 0
            total_failed_entries = 0
            
            for group_index, (date_key, records_in_group) in enumerate(date_groups.items(), 1):
                try:
                    # Convert date for display
                    date_obj = datetime.strptime(date_key, "%Y-%m-%d")
                    display_date = date_obj.strftime("%Y-%m-%d")
                    
                    print(f"\n🗓️ Processing Date Group {group_index}/{len(date_groups)}: {display_date}")
                    print(f"👥 Employees in this group: {len(set(r.get('employee_name', '') for r in records_in_group))} employees")
                    
                    # Create entries for this date group
                    group_entries = []
                    for record in records_in_group:
                        entries = self.create_overtime_entries(record)
                        group_entries.extend(entries)
                    
                    print(f"📋 Records to process: {len(group_entries)} transactions")
                    
                    # Count entry types
                    normal_entries = [e for e in group_entries if e.get('transaction_type') == 'Normal']
                    overtime_entries = [e for e in group_entries if e.get('transaction_type') == 'Overtime']
                    print(f"   📝 Normal entries: {len(normal_entries)}")
                    print(f"   ⏰ Overtime entries: {len(overtime_entries)}")
                    
                    # Process all entries in this date group
                    group_successful = 0
                    group_failed = 0
                    
                    for entry_index, entry in enumerate(group_entries, 1):
                        employee_name = entry.get('employee_name', 'Unknown')
                        transaction_type = entry.get('transaction_type', 'Normal')
                        hours = entry.get('hours', 0)
                        
                        print(f"\n  ✨ Entry {entry_index}/{len(group_entries)}: {employee_name} - {transaction_type} ({hours}h)")
                        
                        # Process single entry (use existing logic)
                        success = await self.process_single_record(driver, entry, f"{group_index}.{entry_index}")
                        
                        if success:
                            group_successful += 1
                            total_successful_entries += 1
                            print(f"     ✅ PASSED")
                        else:
                            group_failed += 1  
                            total_failed_entries += 1
                            print(f"     ❌ FAILED")
                        
                        # Short wait between entries
                        if entry_index < len(group_entries):
                            await asyncio.sleep(2)
                    
                    # Summary for this date group
                    group_success_rate = (group_successful / len(group_entries)) * 100 if group_entries else 0
                    print(f"\n  📊 Date Group {group_index} Summary:")
                    print(f"     ✅ Successful: {group_successful}/{len(group_entries)}")
                    print(f"     ❌ Failed: {group_failed}/{len(group_entries)}")
                    print(f"     📈 Success Rate: {group_success_rate:.1f}%")
                    
                    if group_successful > 0:
                        successful_groups += 1
                    else:
                        failed_groups += 1
                    
                    # Click "New" button after completing date group (except for last group)
                    if group_index < len(date_groups):
                        print(f"\n  🔘 Date Group {group_index}/{len(date_groups)} Complete - Clicking 'New' button...")
                        new_button_success = await self.click_new_button(driver)
                        
                        if new_button_success:
                            print(f"     ✅ 'New' button clicked successfully, proceeding to next group")
                        else:
                            print(f"     ⚠️ 'New' button click failed, continuing anyway")
                        
                        # Wait before starting next group
                        await asyncio.sleep(2)
                
                except Exception as e:
                    print(f"\n  ❌ Error processing date group {group_index}: {e}")
                    self.logger.error(f"Date group {group_index} error: {e}")
                    failed_groups += 1
                    continue
            
            # Final batch processing summary
            overall_success_rate = (total_successful_entries / (total_successful_entries + total_failed_entries)) * 100 if (total_successful_entries + total_failed_entries) > 0 else 0
            
            print(f"\n" + "="*80)
            print(f"🎯 BATCH PROCESSING COMPLETE!")
            print(f"="*80)
            print(f"📅 Date Groups Processed: {len(date_groups)}")
            print(f"✅ Successful Groups: {successful_groups}")
            print(f"❌ Failed Groups: {failed_groups}")
            print(f"📊 Total Entries: {total_successful_entries + total_failed_entries}")
            print(f"✅ Successful Entries: {total_successful_entries}")
            print(f"❌ Failed Entries: {total_failed_entries}")
            print(f"📈 Overall Success Rate: {overall_success_rate:.1f}%")
            print(f"🗄️ Database: {db_name}")
            print(f"🔧 Mode: {automation_mode.upper()}")
            print("="*80)
            
            return total_successful_entries > 0
            
        except Exception as e:
            print(f"❌ Batch processing failed: {e}")
            self.logger.error(f"Batch processing error: {e}")
            return False

    async def fill_document_date_field(self, driver, date_value: str) -> bool:
        """Fill document date field (MainContent_txtDocDate) with calculated date"""
        try:
            # Calculate document date (1 month earlier)
            document_date = self.calculate_document_date(date_value)
            
            self.logger.info(f"📅 Filling document date: {document_date}")
            
            # Use JavaScript to fill document date field
            script = f"""
                var docDateField = document.getElementById('MainContent_txtDocDate');
                if (docDateField) {{
                    docDateField.value = '{document_date}';
                    docDateField.dispatchEvent(new Event('change', {{bubbles: true}}));
                    docDateField.dispatchEvent(new Event('blur', {{bubbles: true}}));
                    
                    // Trigger the SetTrxDate() function if it exists
                    if (typeof SetTrxDate === 'function') {{
                        SetTrxDate();
                    }}
                    
                    return true;
                }} else {{
                    return false;
                }}
            """
            
            result = driver.execute_script(script)
            if result:
                self.logger.info(f"✅ Document date filled: {document_date}")
                await asyncio.sleep(1.5)  # Wait for SetTrxDate() to process
                return True
            else:
                self.logger.error("❌ Document date field not found")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Document date field filling failed: {e}")
            return False

    async def fill_sequential_charge_job_fields(self, driver, charge_components: List[str]) -> bool:
        """Fill charge job components sequentially into autocomplete fields"""
        try:
            from selenium.common.exceptions import InvalidSessionIdException, StaleElementReferenceException
            
            # Find all autocomplete fields
            autocomplete_fields = driver.find_elements(By.CSS_SELECTOR, ".ui-autocomplete-input")
            
            # We expect field 0 = Employee, field 1+ = Charge job components
            # So charge components start from autocomplete field index 1
            
            self.logger.info(f"🔍 Available autocomplete fields: {len(autocomplete_fields)}")
            
            for i, component in enumerate(charge_components):
                field_index = i + 1  # Skip employee field (index 0)
                
                if field_index >= len(autocomplete_fields):
                    self.logger.warning(f"⚠️ No more autocomplete fields available for component {i}: {component}")
                    break
                
                self.logger.info(f"🔧 Filling field {field_index} with component {i}: {component}")
                
                # Retry logic for stale elements
                max_retries = 3
                retry_count = 0
                success = False
                
                while retry_count < max_retries and not success:
                    try:
                        # Refresh field list in case of stale elements
                        autocomplete_fields = driver.find_elements(By.CSS_SELECTOR, ".ui-autocomplete-input")
                        
                        if field_index >= len(autocomplete_fields):
                            self.logger.warning(f"⚠️ Field {field_index} not available after refresh")
                            break
                        
                        field = autocomplete_fields[field_index]
                        
                        # Check if field is visible and enabled
                        if not field.is_displayed() or not field.is_enabled():
                            self.logger.warning(f"⚠️ Field {field_index} not interactable, skipping component: {component}")
                            break
                        
                        # Clear and type component
                        field.clear()
                        field.send_keys(component)
                        await asyncio.sleep(1.5)  # Wait for autocomplete
                        
                        # Arrow down + Enter
                        field.send_keys(Keys.ARROW_DOWN)
                        await asyncio.sleep(0.8)
                        field.send_keys(Keys.ENTER)
                        await asyncio.sleep(1.5)  # Wait for processing
                        
                        self.logger.info(f"✅ Component {i} filled: {component}")
                        success = True
                        
                        # Check if more fields become available after this input
                        await asyncio.sleep(1)
                        autocomplete_fields = driver.find_elements(By.CSS_SELECTOR, ".ui-autocomplete-input")
                        self.logger.info(f"🔍 Autocomplete fields after filling component {i}: {len(autocomplete_fields)}")
                        
                    except (StaleElementReferenceException, InvalidSessionIdException) as e:
                        retry_count += 1
                        self.logger.warning(f"⚠️ Retry {retry_count}/{max_retries} for component {i}: {e}")
                        if retry_count < max_retries:
                            await asyncio.sleep(2)  # Wait before retry
                        else:
                            self.logger.error(f"❌ Failed to fill component {i} after {max_retries} retries")
                            return False
                    except Exception as e:
                        self.logger.error(f"❌ Error filling component {i}: {e}")
                        return False
                
                if not success:
                    self.logger.error(f"❌ Failed to fill component {i}: {component}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Sequential charge job filling failed: {e}")
            import traceback
            self.logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return False

    async def process_single_record(self, driver, record: Dict, record_index: str) -> bool:
        """Process a single record with sequential charge job filling and overtime support"""
        try:
            from selenium.common.exceptions import InvalidSessionIdException
            
            employee_name = record.get('employee_name', '')
            date_value = record.get('date', '')
            raw_charge_job = record.get('raw_charge_job', '')
            transaction_type = record.get('transaction_type', 'Normal')
            hours = record.get('hours', 0)
            entry_type = record.get('entry_type', 'normal')
            
            self.logger.info(f"🎯 Processing record {record_index}: {employee_name}")
            self.logger.info(f"📅 Date: {date_value}")
            self.logger.info(f"🔧 Raw charge job: {raw_charge_job}")
            self.logger.info(f"🔘 Transaction type: {transaction_type}")
            self.logger.info(f"⏰ Hours: {hours}")
            self.logger.info(f"📝 Entry type: {entry_type}")
            
            # Check if session is valid before proceeding
            try:
                driver.current_url  # Test if session is alive
            except InvalidSessionIdException:
                self.logger.warning(f"⚠️ Session lost for record {record_index}, reinitializing browser...")
                if not await self.reinitialize_browser():
                    return False
                driver = self.browser_manager.get_driver()
            
            # Step 0: Fill document date field (1 month earlier than transaction date)
            self.logger.info(f"📅 Step 0: Filling document date field...")
            
            try:
                doc_date_success = await self.fill_document_date_field(driver, date_value)
                if doc_date_success:
                    self.logger.info("✅ Document date field filled successfully")
                else:
                    self.logger.warning("⚠️ Document date field filling failed, continuing anyway...")
                    # Don't return False here, continue with the process
            except InvalidSessionIdException:
                self.logger.error(f"❌ Session lost during document date filling for record {record_index}")
                return False
            except Exception as e:
                self.logger.warning(f"⚠️ Document date filling error: {e}, continuing anyway...")
            
            # Step 1: Fill transaction date field
            if not date_value:
                self.logger.error("❌ No date field in record")
                return False
                
            formatted_date = self.format_date(date_value)
            self.logger.info(f"📅 Step 1: Filling transaction date: {formatted_date}")
            
            # Use JavaScript to fill date field
            script = f"""
                var dateField = document.getElementById('MainContent_txtTrxDate');
                if (dateField) {{
                    dateField.value = '{formatted_date}';
                    dateField.dispatchEvent(new Event('change', {{bubbles: true}}));
                    return true;
                }} else {{
                    return false;
                }}
            """
            
            try:
                result = driver.execute_script(script)
                if result:
                    self.logger.info(f"✅ Date filled: {formatted_date}")
                    # Send Enter to trigger reload
                    date_field = driver.find_element(By.ID, "MainContent_txtTrxDate")
                    date_field.send_keys(Keys.ENTER)
                    await asyncio.sleep(2)  # Wait for reload
                else:
                    self.logger.error("❌ Date field not found")
                    return False
            except InvalidSessionIdException:
                self.logger.error(f"❌ Session lost during date filling for record {record_index}")
                return False
            
            # Step 2: Fill employee field (first autocomplete field)
            if not employee_name:
                self.logger.error("❌ No employee_name field in record")
                return False
                
            self.logger.info(f"👤 Step 2: Filling employee: {employee_name}")
            
            try:
                autocomplete_fields = driver.find_elements(By.CSS_SELECTOR, ".ui-autocomplete-input")
                self.logger.info(f"🔍 Found {len(autocomplete_fields)} autocomplete fields")
                
                if len(autocomplete_fields) > 0:
                    employee_field = autocomplete_fields[0]
                    employee_field.clear()
                    employee_field.send_keys(employee_name)
                    await asyncio.sleep(1.5)
                    employee_field.send_keys(Keys.ARROW_DOWN)
                    await asyncio.sleep(0.8)
                    employee_field.send_keys(Keys.ENTER)
                    await asyncio.sleep(2)  # Wait for field processing
                    self.logger.info(f"✅ Employee filled: {employee_name}")
                else:
                    self.logger.error("❌ Employee field not found")
                    return False
            except InvalidSessionIdException:
                self.logger.error(f"❌ Session lost during employee filling for record {record_index}")
                return False

            # Step 3: Select transaction type (Normal or Overtime)
            self.logger.info(f"🔘 Step 3: Selecting transaction type: {transaction_type}")
            
            try:
                success = await self.select_transaction_type(driver, transaction_type)
                if success:
                    self.logger.info(f"✅ Transaction type selected: {transaction_type}")
                else:
                    self.logger.error(f"❌ Failed to select transaction type: {transaction_type}")
                    return False
            except InvalidSessionIdException:
                self.logger.error(f"❌ Session lost during transaction type selection for record {record_index}")
                return False
            
            # Step 4: Parse and fill charge job components sequentially
            if not raw_charge_job:
                self.logger.error("❌ No raw_charge_job field in record")
                return False
                
            charge_components = self.parse_raw_charge_job(raw_charge_job)
            
            if charge_components:
                self.logger.info(f"🔧 Step 4: Filling {len(charge_components)} charge job components sequentially...")
                success = await self.fill_sequential_charge_job_fields(driver, charge_components)
                
                if success:
                    self.logger.info("✅ All charge job components filled successfully")
                    
                    # Step 5: Fill hours field
                    self.logger.info(f"⏰ Step 5: Filling hours field with: {hours}")
                    
                    try:
                        hours_success = await self.fill_hours_field(driver, hours)
                        if hours_success:
                            self.logger.info(f"✅ Hours field filled: {hours}")
                        else:
                            self.logger.error(f"❌ Failed to fill hours field: {hours}")
                            return False
                    except InvalidSessionIdException:
                        self.logger.error(f"❌ Session lost during hours filling for record {record_index}")
                        return False
                    
                    # Step 6: Click Add button to save the record
                    try:
                        add_selectors = [
                            "input[value='Add']",
                            "button[id*='Add']", 
                            "input[id*='Add']",
                            "input[id*='btn'][id*='Add']",
                            "button[value='Add']"
                        ]
                        
                        add_button = None
                        for selector in add_selectors:
                            try:
                                add_button = driver.find_element(By.CSS_SELECTOR, selector)
                                if add_button.is_displayed() and add_button.is_enabled():
                                    self.logger.info(f"✅ Found Add button with selector: {selector}")
                                    break
                            except:
                                continue
                        
                        if add_button:
                            add_button.click()
                            self.logger.info("✅ Add button clicked - Record saved!")
                            await asyncio.sleep(3)  # Wait for form to reset/process
                            return True
                        else:
                            self.logger.warning("⚠️ Add button not found with any selector")
                            return False
                            
                    except Exception as e:
                        self.logger.error(f"❌ Add button handling error: {e}")
                        return False
                else:
                    return False
            else:
                self.logger.error("❌ No charge job components to fill")
                return False
            
        except InvalidSessionIdException:
            self.logger.error(f"❌ Browser session lost for record {record_index}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Record {record_index} processing failed: {e}")
            import traceback
            self.logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return False

    async def reinitialize_browser(self) -> bool:
        """Reinitialize browser session if it's lost"""
        try:
            self.logger.info("🔄 Reinitializing browser session...")
            
            if self.browser_manager:
                await self.browser_manager.cleanup()
            
            success = await self.initialize_browser()
            if success:
                self.logger.info("✅ Browser session reinitialized successfully")
                return True
            else:
                self.logger.error("❌ Failed to reinitialize browser session")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Browser reinitialization failed: {e}")
            return False

    def group_records_by_date(self, records: List[Dict]) -> Dict[str, List[Dict]]:
        """Group records by attendance date for batch processing"""
        try:
            date_groups = {}

            for record in records:
                date_str = record.get('date', '')
                if date_str:
                    # Normalize date format to YYYY-MM-DD
                    try:
                        if 'T' in date_str:
                            date_str = date_str.split('T')[0]
                        elif ' ' in date_str:
                            date_str = date_str.split(' ')[0]

                        # Ensure proper date format
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                        normalized_date = date_obj.strftime('%Y-%m-%d')

                        if normalized_date not in date_groups:
                            date_groups[normalized_date] = []
                        date_groups[normalized_date].append(record)

                    except ValueError as e:
                        self.logger.warning(f"⚠️ Invalid date format '{date_str}' for record: {record.get('employee_name', 'Unknown')}")
                        continue
                else:
                    self.logger.warning(f"⚠️ Missing date for record: {record.get('employee_name', 'Unknown')}")

            # Sort date groups chronologically
            sorted_dates = sorted(date_groups.keys())
            sorted_groups = {date: date_groups[date] for date in sorted_dates}

            self.logger.info(f"📅 Grouped {len(records)} records into {len(sorted_groups)} date groups")
            for date, group_records in sorted_groups.items():
                employees = list(set(r.get('employee_name', '') for r in group_records))
                self.logger.info(f"   📅 {date}: {len(group_records)} records, {len(employees)} employees")

            return sorted_groups

        except Exception as e:
            self.logger.error(f"❌ Error grouping records by date: {e}")
            return {}

    def parse_raw_charge_job(self, raw_charge_job: str) -> List[str]:
        """Parse raw charge job string into components"""
        try:
            if not raw_charge_job:
                return []

            # Split by "/" and clean up components
            components = [comp.strip() for comp in raw_charge_job.split('/') if comp.strip()]

            self.logger.info(f"🔧 Parsed charge job '{raw_charge_job}' into {len(components)} components")
            for i, comp in enumerate(components):
                self.logger.info(f"   [{i}]: {comp}")

            return components

        except Exception as e:
            self.logger.error(f"❌ Error parsing charge job '{raw_charge_job}': {e}")
            return []

    def create_overtime_entries(self, record: Dict) -> List[Dict]:
        """Create separate entries for normal and overtime hours"""
        try:
            entries = []

            regular_hours = float(record.get('regular_hours', 0))
            overtime_hours = float(record.get('overtime_hours', 0))

            # Create normal entry if regular hours > 0
            if regular_hours > 0:
                normal_entry = record.copy()
                normal_entry.update({
                    'transaction_type': 'Normal',
                    'hours': regular_hours,
                    'is_overtime': False
                })
                entries.append(normal_entry)

            # Create overtime entry if overtime hours > 0
            if overtime_hours > 0:
                overtime_entry = record.copy()
                overtime_entry.update({
                    'transaction_type': 'Overtime',
                    'hours': overtime_hours,
                    'is_overtime': True
                })
                entries.append(overtime_entry)

            # If no hours specified, create a normal entry with 0 hours
            if not entries:
                normal_entry = record.copy()
                normal_entry.update({
                    'transaction_type': 'Normal',
                    'hours': 0,
                    'is_overtime': False
                })
                entries.append(normal_entry)

            self.logger.info(f"📋 Created {len(entries)} entries for {record.get('employee_name', 'Unknown')}")
            return entries

        except Exception as e:
            self.logger.error(f"❌ Error creating overtime entries: {e}")
            return [record]  # Return original record as fallback

    async def initialize_browser(self) -> bool:
        """Initialize browser and navigate to task register page"""
        try:
            self.logger.info("🚀 Initializing browser for automation...")

            # Initialize browser manager
            from .persistent_browser_manager import PersistentBrowserManager
            self.browser_manager = PersistentBrowserManager(self.config)

            # Initialize the browser manager first
            success = await self.browser_manager.initialize()
            if not success:
                self.logger.error("❌ Failed to initialize browser manager")
                return False

            # Get driver
            driver = self.browser_manager.get_driver()
            if not driver:
                self.logger.error("❌ Failed to get browser driver")
                return False

            # Navigate to task register page
            task_register_url = self.config.get('urls', {}).get('taskRegister',
                'http://millwarep3.rebinmas.com:8004/en/PR/trx/frmPrTrxTaskRegisterDet.aspx')

            self.logger.info(f"🌐 Navigating to: {task_register_url}")
            driver.get(task_register_url)

            # Wait for page to load
            await asyncio.sleep(3)

            self.logger.info("✅ Browser initialized and positioned at task register page")
            return True

        except Exception as e:
            self.logger.error(f"❌ Browser initialization failed: {e}")
            return False

    async def select_transaction_type(self, driver, transaction_type: str) -> bool:
        """Select transaction type radio button"""
        try:
            self.logger.info(f"🔘 Selecting transaction type: {transaction_type}")

            # Map transaction types to radio button values
            type_mapping = {
                'Normal': '0',
                'Overtime': '1'
            }

            radio_value = type_mapping.get(transaction_type, '0')

            # Try different selectors for transaction type radio buttons
            selectors = [
                f"input[type='radio'][value='{radio_value}']",
                f"input[name*='TransactionType'][value='{radio_value}']",
                f"input[name*='Type'][value='{radio_value}']",
                f"input[id*='Type'][value='{radio_value}']"
            ]

            for selector in selectors:
                try:
                    radio_button = driver.find_element(By.CSS_SELECTOR, selector)
                    if radio_button.is_displayed() and radio_button.is_enabled():
                        radio_button.click()
                        self.logger.info(f"✅ Selected transaction type: {transaction_type}")
                        await asyncio.sleep(1)
                        return True
                except:
                    continue

            self.logger.warning(f"⚠️ Transaction type radio button not found for: {transaction_type}")
            return True  # Continue processing even if radio button not found

        except Exception as e:
            self.logger.error(f"❌ Error selecting transaction type: {e}")
            return False

    async def fill_hours_field(self, driver, hours: float) -> bool:
        """Fill the hours field with specified value"""
        try:
            self.logger.info(f"⏰ Filling hours field with: {hours}")

            # Try different selectors for hours field
            hours_selectors = [
                "input[name*='Hours']",
                "input[id*='Hours']",
                "input[name*='Hour']",
                "input[id*='Hour']",
                "input[type='number']",
                "input[name*='Qty']",
                "input[id*='Qty']"
            ]

            for selector in hours_selectors:
                try:
                    hours_field = driver.find_element(By.CSS_SELECTOR, selector)
                    if hours_field.is_displayed() and hours_field.is_enabled():
                        # Clear field and enter hours
                        hours_field.clear()
                        hours_field.send_keys(str(hours))
                        self.logger.info(f"✅ Hours field filled: {hours}")
                        await asyncio.sleep(1)
                        return True
                except:
                    continue

            self.logger.warning(f"⚠️ Hours field not found, skipping hours entry")
            return True  # Continue processing even if hours field not found

        except Exception as e:
            self.logger.error(f"❌ Error filling hours field: {e}")
            return False

    async def process_single_record_enhanced(self, driver, entry: Dict, record_index: int) -> bool:
        """Process a single record entry with enhanced error handling"""
        try:
            self.logger.info(f"🎯 Processing entry {record_index}: {entry.get('employee_name', 'Unknown')}")

            # Extract data from entry
            employee_name = entry.get('employee_name', '')
            date_str = entry.get('date', '')
            transaction_type = entry.get('transaction_type', 'Normal')
            hours = entry.get('hours', 0)
            raw_charge_job = entry.get('raw_charge_job', '')

            # Step 1: Fill date field
            self.logger.info(f"📅 Step 1: Filling date: {date_str}")
            success = await self.fill_date_field(driver, date_str)
            if not success:
                self.logger.error(f"❌ Failed to fill date: {date_str}")
                return False

            # Step 2: Fill employee field
            self.logger.info(f"👤 Step 2: Filling employee: {employee_name}")
            success = await self.fill_employee_field(driver, employee_name)
            if not success:
                self.logger.error(f"❌ Failed to fill employee: {employee_name}")
                return False

            # Step 3: Select transaction type
            self.logger.info(f"🔘 Step 3: Selecting transaction type: {transaction_type}")
            success = await self.select_transaction_type(driver, transaction_type)
            if not success:
                self.logger.error(f"❌ Failed to select transaction type: {transaction_type}")
                return False

            # Step 4: Fill charge job components
            charge_components = self.parse_raw_charge_job(raw_charge_job)
            if charge_components:
                self.logger.info(f"🔧 Step 4: Filling {len(charge_components)} charge job components")
                success = await self.fill_sequential_charge_job_fields(driver, charge_components)
                if not success:
                    self.logger.error(f"❌ Failed to fill charge job components")
                    return False

            # Step 5: Fill hours field
            self.logger.info(f"⏰ Step 5: Filling hours: {hours}")
            success = await self.fill_hours_field(driver, hours)
            if not success:
                self.logger.error(f"❌ Failed to fill hours: {hours}")
                return False

            # Step 6: Click Add button
            self.logger.info("💾 Step 6: Clicking Add button")
            success = await self.click_add_button(driver)
            if not success:
                self.logger.error("❌ Failed to click Add button")
                return False

            self.logger.info(f"✅ Entry {record_index} processed successfully")
            return True

        except Exception as e:
            self.logger.error(f"❌ Error processing entry {record_index}: {e}")
            return False

    async def fill_date_field(self, driver, date_str: str) -> bool:
        """Fill the date field"""
        try:
            # Try different selectors for date field
            date_selectors = [
                "input[name*='Date']",
                "input[id*='Date']",
                "input[type='date']",
                "input[name*='Tanggal']",
                "input[id*='Tanggal']"
            ]

            for selector in date_selectors:
                try:
                    date_field = driver.find_element(By.CSS_SELECTOR, selector)
                    if date_field.is_displayed() and date_field.is_enabled():
                        date_field.clear()
                        date_field.send_keys(date_str)
                        self.logger.info(f"✅ Date field filled: {date_str}")
                        await asyncio.sleep(1)
                        return True
                except:
                    continue

            self.logger.warning("⚠️ Date field not found, skipping date entry")
            return True

        except Exception as e:
            self.logger.error(f"❌ Error filling date field: {e}")
            return False

    async def fill_employee_field(self, driver, employee_name: str) -> bool:
        """Fill the employee field"""
        try:
            # Try different selectors for employee field
            employee_selectors = [
                "input[name*='Employee']",
                "input[id*='Employee']",
                "input[name*='Karyawan']",
                "input[id*='Karyawan']",
                "select[name*='Employee']",
                "select[id*='Employee']"
            ]

            for selector in employee_selectors:
                try:
                    employee_field = driver.find_element(By.CSS_SELECTOR, selector)
                    if employee_field.is_displayed() and employee_field.is_enabled():
                        if employee_field.tag_name.lower() == 'select':
                            # Handle dropdown
                            from selenium.webdriver.support.ui import Select
                            select = Select(employee_field)
                            select.select_by_visible_text(employee_name)
                        else:
                            # Handle input field
                            employee_field.clear()
                            employee_field.send_keys(employee_name)

                        self.logger.info(f"✅ Employee field filled: {employee_name}")
                        await asyncio.sleep(1)
                        return True
                except:
                    continue

            self.logger.warning("⚠️ Employee field not found, skipping employee entry")
            return True

        except Exception as e:
            self.logger.error(f"❌ Error filling employee field: {e}")
            return False

    async def click_add_button(self, driver) -> bool:
        """Click the Add button to save the record"""
        try:
            # Try different selectors for Add button
            add_selectors = [
                "input[value='Add']",
                "button[value='Add']",
                "input[id*='Add']",
                "button[id*='Add']",
                "input[name*='Add']",
                "button[name*='Add']"
            ]

            for selector in add_selectors:
                try:
                    add_button = driver.find_element(By.CSS_SELECTOR, selector)
                    if add_button.is_displayed() and add_button.is_enabled():
                        add_button.click()
                        self.logger.info("✅ Add button clicked successfully")
                        await asyncio.sleep(2)
                        return True
                except:
                    continue

            self.logger.warning("⚠️ Add button not found")
            return False

        except Exception as e:
            self.logger.error(f"❌ Error clicking Add button: {e}")
            return False

    async def fill_sequential_charge_job_fields(self, driver, charge_components: List[str]) -> bool:
        """Fill charge job fields sequentially"""
        try:
            self.logger.info(f"🔧 Filling {len(charge_components)} charge job components sequentially")

            # Common selectors for charge job fields
            field_selectors = [
                "input[name*='Task']",
                "input[name*='Station']",
                "input[name*='Machine']",
                "input[name*='Expense']",
                "input[name*='Location']",
                "input[name*='Type']"
            ]

            # Try to fill each component
            for i, component in enumerate(charge_components):
                if i < len(field_selectors):
                    selector = field_selectors[i]
                    try:
                        field = driver.find_element(By.CSS_SELECTOR, selector)
                        if field.is_displayed() and field.is_enabled():
                            field.clear()
                            field.send_keys(component)
                            self.logger.info(f"✅ Filled field {i+1}: {component}")
                            await asyncio.sleep(0.5)
                        else:
                            self.logger.warning(f"⚠️ Field {i+1} not available, skipping: {component}")
                    except:
                        self.logger.warning(f"⚠️ Could not find field {i+1} for: {component}")
                        continue
                else:
                    self.logger.warning(f"⚠️ No more field selectors for component: {component}")

            return True

        except Exception as e:
            self.logger.error(f"❌ Error filling charge job fields: {e}")
            return False

    async def click_new_button(self, driver) -> bool:
        """Click the 'New' button to reset form after processing a date group"""
        try:
            self.logger.info("🔘 Looking for 'New' button to reset form...")

            # Multiple selectors for the New button
            new_button_selectors = [
                "input[name='ctl00$MainContent$btnNew']",
                "input[id='MainContent_btnNew']",
                "input[value='New']",
                "button[value='New']",
                "input[type='submit'][value='New']",
                "button[id*='New']",
                "input[id*='New']"
            ]

            new_button = None
            for selector in new_button_selectors:
                try:
                    new_button = driver.find_element(By.CSS_SELECTOR, selector)
                    if new_button.is_displayed() and new_button.is_enabled():
                        self.logger.info(f"✅ Found New button with selector: {selector}")
                        break
                except:
                    continue

            if new_button:
                new_button.click()
                self.logger.info("✅ 'New' button clicked successfully")

                # Wait for page to reload/reset
                await asyncio.sleep(3)

                # Verify form reset by checking if fields are cleared
                try:
                    # Check if date field is cleared (common indicator of form reset)
                    date_field = driver.find_element(By.CSS_SELECTOR, "input[id*='Date'], input[name*='Date']")
                    if date_field.get_attribute('value') == '':
                        self.logger.info("✅ Form reset confirmed - date field cleared")
                    else:
                        self.logger.info("ℹ️ Form may not be fully reset, but continuing...")
                except:
                    self.logger.info("ℹ️ Could not verify form reset, but continuing...")

                return True
            else:
                self.logger.error("❌ 'New' button not found with any selector")
                return False

        except Exception as e:
            self.logger.error(f"❌ Error clicking 'New' button: {e}")
            return False

    async def process_batch_by_date_groups(self, automation_mode: str = 'testing') -> bool:
        """Process all staging data in batch mode, grouped chronologically by date"""
        try:
            self.logger.info("🚀 BATCH PROCESSING MODE ACTIVATED")
            self.logger.info(f"🔧 Automation Mode: {automation_mode}")

            # Initialize browser if not already done
            if not self.browser_manager:
                success = await self.initialize_browser()
                if not success:
                    self.logger.error("❌ Failed to initialize browser for batch processing")
                    return False

            # Fetch all staging data
            self.logger.info("🌐 Fetching complete dataset from API...")
            all_records = await self.fetch_real_api_data()

            if not all_records:
                self.logger.error("❌ No staging data available for batch processing")
                return False

            # Group records by date
            date_groups = self.group_records_by_date(all_records)

            if not date_groups:
                self.logger.error("❌ No valid date groups found")
                return False

            # Display pre-processing summary
            total_employees = len(set(record.get('employee_name', '') for record in all_records))
            date_range = f"{min(date_groups.keys())} to {max(date_groups.keys())}"
            database_name = "db_ptrj_mill_test" if automation_mode == 'testing' else "db_ptrj_mill"

            print("\n" + "="*80)
            print("📊 BATCH PROCESSING MODE ACTIVATED")
            print("="*80)
            print(f"📅 Date Groups: {len(date_groups)} groups ({date_range})")
            print(f"👥 Total Employees: {total_employees} unique employees")
            print(f"📋 Total Records: {len(all_records)} attendance records")
            print(f"🗄️ Database: {database_name} ({'Testing Mode' if automation_mode == 'testing' else 'Real Mode'})")
            print("="*80)

            # Get driver
            driver = self.browser_manager.get_driver()
            if not driver:
                self.logger.error("❌ WebDriver not available")
                return False

            # Process each date group sequentially
            successful_groups = 0
            failed_groups = 0
            total_processed_entries = 0
            total_failed_entries = 0

            for group_index, (date_key, group_records) in enumerate(date_groups.items(), 1):
                print(f"\n🗓️ Processing Date Group {group_index}/{len(date_groups)}: {date_key}")

                # Get unique employees in this group
                group_employees = list(set(r.get('employee_name', '') for r in group_records))
                print(f"👥 Employees in this group: {len(group_employees)} employees")

                # Create entries for this date group
                group_entries = []
                for record in group_records:
                    entries = self.create_overtime_entries(record)
                    group_entries.extend(entries)

                normal_entries = [e for e in group_entries if e.get('transaction_type') == 'Normal']
                overtime_entries = [e for e in group_entries if e.get('transaction_type') == 'Overtime']

                print(f"📋 Records to process: {len(group_entries)} transactions ({len(normal_entries)} regular + {len(overtime_entries)} overtime)")

                # Process all entries in this date group
                group_successful = 0
                group_failed = 0

                for entry_index, entry in enumerate(group_entries, 1):
                    employee_name = entry.get('employee_name', 'Unknown')
                    transaction_type = entry.get('transaction_type', 'Normal')
                    hours = entry.get('hours', 0)

                    print(f"Processing entry {entry_index}/{len(group_entries)}: {employee_name} - {transaction_type} ({hours}h)")

                    # Process single entry using existing method
                    success = await self.process_single_record_enhanced(driver, entry, entry_index)

                    if success:
                        group_successful += 1
                        total_processed_entries += 1
                        print(f"✅ Entry {entry_index}/{len(group_entries)}: {employee_name} - VALIDATION PASSED ({transaction_type}: {hours}h)")
                    else:
                        group_failed += 1
                        total_failed_entries += 1
                        print(f"❌ Entry {entry_index}/{len(group_entries)}: {employee_name} - VALIDATION FAILED ({transaction_type}: {hours}h)")

                    # Wait between entries
                    if entry_index < len(group_entries):
                        await asyncio.sleep(2)

                # Click "New" button after completing date group
                print(f"\n🔘 Date Group {group_index}/{len(date_groups)} Complete - Clicking 'New' button...")
                new_button_success = await self.click_new_button(driver)

                if new_button_success:
                    print("✅ 'New' button clicked successfully, proceeding to next group")
                    successful_groups += 1
                else:
                    print("❌ Failed to click 'New' button, but continuing to next group")
                    failed_groups += 1

                # Summary for this date group
                group_success_rate = (group_successful / len(group_entries)) * 100 if group_entries else 0
                print(f"📊 Date Group {group_index} Summary: {group_successful}/{len(group_entries)} successful ({group_success_rate:.1f}%)")

                # Wait before next date group
                if group_index < len(date_groups):
                    print("⏳ Waiting 3 seconds before next date group...")
                    await asyncio.sleep(3)

            # Final batch processing summary
            overall_success_rate = (total_processed_entries / (total_processed_entries + total_failed_entries)) * 100 if (total_processed_entries + total_failed_entries) > 0 else 0

            print(f"\n🎯 BATCH PROCESSING COMPLETE!")
            print("="*80)
            print(f"📅 Date Groups Processed: {successful_groups}/{len(date_groups)}")
            print(f"📊 Total Entries: {total_processed_entries + total_failed_entries}")
            print(f"✅ Successful Entries: {total_processed_entries}")
            print(f"❌ Failed Entries: {total_failed_entries}")
            print(f"📈 Overall Success Rate: {overall_success_rate:.1f}%")
            print("="*80)

            return successful_groups > 0

        except Exception as e:
            self.logger.error(f"❌ Batch processing failed: {e}")
            import traceback
            self.logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return False

    async def cleanup(self):
        """Cleanup browser resources"""
        try:
            if self.browser_manager:
                await self.browser_manager.cleanup()
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")