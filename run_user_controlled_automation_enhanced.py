#!/usr/bin/env python3
"""
Enhanced User-Controlled Automation System with Crosscheck
Uses new grouped API and includes data validation with Millware database
"""

import sys
import json
import logging
import asyncio
import threading
import time
import webbrowser
import requests
import pyodbc
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import the RealAPIDataProcessor from core
from core.api_data_automation import RealAPIDataProcessor

# Import employee exclusion validator
from core.employee_exclusion_validator import EmployeeExclusionValidator


class EnhancedUserControlledAutomationSystem:
    """
    Enhanced User-controlled automation with grouped API and crosscheck functionality
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Use new grouped API endpoint - connect to external staging server
        self.api_url = "http://localhost:5173/api/staging/data-grouped"
        self.web_server_thread = None
        
        # Use the EXACT same processor from test_real_api_data.py
        self.processor = RealAPIDataProcessor()
        self.is_browser_ready = False
        self.automation_mode = 'testing'  # Default mode
        
        # Progress tracking
        self.current_progress = {
            'current_employee': '',
            'current_date': '',
            'processed_entries': 0,
            'total_entries': 0,
            'successful_entries': 0,
            'failed_entries': 0,
            'status': 'idle'
        }
        
        # Crosscheck data storage
        self.processed_data = []
        
        # Initialize employee exclusion validator
        self.exclusion_validator = EmployeeExclusionValidator()
        self.logger.info(f"🔒 Employee exclusion validation: {'Enabled' if self.exclusion_validator.is_enabled() else 'Disabled'}")
        
        # Enhanced logging configuration
        self._setup_enhanced_logging()
        
    def _setup_enhanced_logging(self):
        """Setup enhanced logging for WebDriver debugging"""
        try:
            # Create detailed formatter
            detailed_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'
            )
            
            # Add file handler for WebDriver specific logs
            webdriver_log_file = Path(__file__).parent / "logs" / "webdriver_debug.log"
            webdriver_log_file.parent.mkdir(exist_ok=True)
            
            webdriver_handler = logging.FileHandler(webdriver_log_file)
            webdriver_handler.setLevel(logging.DEBUG)
            webdriver_handler.setFormatter(detailed_formatter)
            
            # Add handler to logger
            self.logger.addHandler(webdriver_handler)
            self.logger.setLevel(logging.DEBUG)
            
        except Exception as e:
            print(f"Warning: Could not setup enhanced logging: {e}")
    
    def _log_driver_state(self, driver, context: str = ""):
        """Log comprehensive driver state for debugging"""
        try:
            if not driver:
                self.logger.error(f"[{context}] Driver is None")
                return
                
            state_info = {
                'context': context,
                'current_url': getattr(driver, 'current_url', 'Unknown'),
                'title': getattr(driver, 'title', 'Unknown'),
                'window_handles': len(getattr(driver, 'window_handles', [])),
                'session_id': getattr(driver, 'session_id', 'Unknown'),
            }
            
            # Try to get additional state info
            try:
                state_info['page_source_length'] = len(driver.page_source) if driver.page_source else 0
            except Exception:
                state_info['page_source_length'] = 'Error getting page source'
                
            try:
                state_info['window_size'] = driver.get_window_size()
            except Exception:
                state_info['window_size'] = 'Error getting window size'
                
            self.logger.debug(f"Driver State [{context}]: {json.dumps(state_info, indent=2)}")
            
        except Exception as e:
            self.logger.error(f"Error logging driver state [{context}]: {e}")
    
    def _log_element_state(self, element, element_name: str, context: str = ""):
        """Log comprehensive element state for debugging"""
        try:
            if not element:
                self.logger.error(f"[{context}] Element {element_name} is None")
                return
                
            element_info = {
                'context': context,
                'element_name': element_name,
                'tag_name': 'Unknown',
                'is_displayed': False,
                'is_enabled': False,
                'is_selected': False,
                'location': 'Unknown',
                'size': 'Unknown',
                'attributes': {}
            }
            
            try:
                element_info['tag_name'] = element.tag_name
                element_info['is_displayed'] = element.is_displayed()
                element_info['is_enabled'] = element.is_enabled()
                element_info['is_selected'] = element.is_selected()
                element_info['location'] = element.location
                element_info['size'] = element.size
                
                # Get common attributes
                common_attrs = ['id', 'class', 'name', 'type', 'value', 'placeholder']
                for attr in common_attrs:
                    try:
                        element_info['attributes'][attr] = element.get_attribute(attr)
                    except Exception:
                        element_info['attributes'][attr] = 'Error getting attribute'
                        
            except Exception as e:
                element_info['error'] = str(e)
                
            self.logger.debug(f"Element State [{context}] {element_name}: {json.dumps(element_info, indent=2)}")
            
        except Exception as e:
            self.logger.error(f"Error logging element state [{context}] {element_name}: {e}")
    
    def _log_automation_step(self, step_name: str, details: Dict[str, Any] = None, success: bool = None):
        """Log automation step with detailed information"""
        try:
            log_data = {
                'step': step_name,
                'timestamp': datetime.now().isoformat(),
                'details': details or {},
            }
            
            if success is not None:
                log_data['success'] = success
                
            if success is False:
                self.logger.error(f"Automation Step Failed: {json.dumps(log_data, indent=2)}")
            elif success is True:
                self.logger.info(f"Automation Step Success: {step_name}")
                self.logger.debug(f"Automation Step Details: {json.dumps(log_data, indent=2)}")
            else:
                self.logger.info(f"Automation Step: {step_name}")
                self.logger.debug(f"Automation Step Details: {json.dumps(log_data, indent=2)}")
                
        except Exception as e:
            self.logger.error(f"Error logging automation step {step_name}: {e}")
    
    def _log_performance_metrics(self, operation: str, start_time: float, end_time: float, additional_data: Dict = None):
        """Log performance metrics for operations"""
        try:
            duration = end_time - start_time
            metrics = {
                'operation': operation,
                'duration_seconds': round(duration, 3),
                'start_time': datetime.fromtimestamp(start_time).isoformat(),
                'end_time': datetime.fromtimestamp(end_time).isoformat(),
            }
            
            if additional_data:
                metrics.update(additional_data)
                
            # Log warning if operation is slow
            if duration > 10:  # More than 10 seconds
                self.logger.warning(f"Slow Operation Detected: {json.dumps(metrics, indent=2)}")
            else:
                self.logger.debug(f"Performance Metrics: {json.dumps(metrics, indent=2)}")
                
        except Exception as e:
            self.logger.error(f"Error logging performance metrics for {operation}: {e}")
        
    async def initialize_browser_system(self) -> bool:
        """Initialize browser using exact same logic from test_real_api_data.py"""
        try:
            print("🚀 Initializing browser system using proven logic...")
            print(f"🔧 Initial automation mode: {self.automation_mode}")
            
            # Use exact same initialization from test_real_api_data.py
            success = await self.processor.initialize_browser()
            
            if success:
                self.is_browser_ready = True
                print("✅ Browser positioned at task register page and ready!")
                driver = self.processor.browser_manager.get_driver()
                print(f"📍 Current URL: {driver.current_url}")
                print(f"🔧 Mode will be applied during automation process")
                return True
            else:
                print("❌ Failed to initialize browser")
                return False
                
        except Exception as e:
            print(f"❌ Browser initialization failed: {e}")
            self.logger.error(f"Browser initialization error: {e}")
            return False
    
    async def fetch_grouped_staging_data(self) -> List[Dict]:
        """Fetch grouped staging data from new API endpoint"""
        try:
            self.logger.info("🌐 Fetching grouped staging data from enhanced API...")
            
            response = requests.get(self.api_url, timeout=30)
            response.raise_for_status()
            
            response_data = response.json()
            
            if isinstance(response_data, dict) and 'data' in response_data:
                grouped_data = response_data['data']
                
                total_employees = len(grouped_data)
                total_records = sum(len(emp.get('data_presensi', [])) for emp in grouped_data)
                
                self.logger.info(f"📊 Grouped data received: {total_employees} employees, {total_records} attendance records")
                
                # Log enhancement info
                if 'charge_job_enhancement' in response_data:
                    enhancement = response_data['charge_job_enhancement']
                    self.logger.info(f"🔧 Charge job enhancement: {enhancement.get('enabled', False)}, {enhancement.get('records_enhanced', 0)} records")
                
                return grouped_data
            else:
                self.logger.error("❌ Invalid grouped data structure")
                return []
                
        except Exception as e:
            self.logger.error(f"❌ Error fetching grouped staging data: {e}")
            return []
    
    def _filter_excluded_employees_grouped(self, grouped_data: List[Dict]) -> List[Dict]:
        """Filter out excluded employees from grouped staging data"""
        try:
            if not self.exclusion_validator.is_enabled():
                self.logger.info("🔓 Exclusion filtering disabled - returning all data")
                return grouped_data
            
            filtered_data = []
            excluded_employees = []
            
            for employee_group in grouped_data:
                identitas = employee_group.get('identitas_karyawan', {})
                employee_name = identitas.get('employee_name', '')
                
                if not employee_name:
                    # Keep groups without employee name
                    filtered_data.append(employee_group)
                    continue
                
                # Check if employee is in exclusion list
                is_excluded = self._is_employee_excluded(employee_name)
                
                if is_excluded:
                    excluded_employees.append(employee_name)
                    self.logger.info(f"🚫 FILTERED OUT: {employee_name}")
                else:
                    filtered_data.append(employee_group)
                    self.logger.debug(f"✅ ALLOWED: {employee_name}")
            
            if excluded_employees:
                print(f"\n🚫 EXCLUDED EMPLOYEES (filtered from grouped data):")
                for name in excluded_employees:
                    print(f"   - {name}")
                print(f"📊 Filter Summary: {len(excluded_employees)} employees excluded, {len(filtered_data)} groups remaining")
            
            return filtered_data
            
        except Exception as e:
            self.logger.error(f"❌ Error filtering excluded employees: {e}")
            # Return original data on error
            return grouped_data
    
    def _is_employee_excluded(self, employee_name: str) -> bool:
        """Check if employee name matches any exclusion list entry"""
        try:
            if not employee_name:
                return False
            
            excluded_list = self.exclusion_validator.get_excluded_employees_list()
            settings = self.exclusion_validator.config.get('exclusion_settings', {})
            
            # Normalize employee name
            normalized_name = employee_name.strip()
            if not settings.get('case_sensitive', False):
                normalized_name = normalized_name.lower()
            
            # Check against normalized exclusion list
            for excluded_name in excluded_list:
                normalized_excluded = excluded_name.strip()
                if not settings.get('case_sensitive', False):
                    normalized_excluded = normalized_excluded.lower()
                
                # Exact match (primary check)
                if normalized_name == normalized_excluded:
                    return True
                
                # Partial match with word overlap
                if settings.get('partial_match', True):
                    name_words = set(normalized_name.split())
                    excluded_words = set(normalized_excluded.split())
                    
                    if name_words and excluded_words:
                        overlap = len(name_words.intersection(excluded_words))
                        total_words = len(name_words.union(excluded_words))
                        similarity = overlap / total_words if total_words > 0 else 0
                        
                        if similarity >= 0.7:
                            return True
                        
                        # Check for exact substring match
                        if (len(normalized_name) >= 4 and normalized_name in normalized_excluded) or \
                           (len(normalized_excluded) >= 4 and normalized_excluded in normalized_name):
                            return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error checking employee exclusion: {e}")
            return False
    
    def flatten_grouped_data_for_selection(self, grouped_data: List[Dict]) -> List[Dict]:
        """Convert grouped data to flat format for user selection interface"""
        try:
            flattened_records = []
            
            for employee_group in grouped_data:
                identitas = employee_group.get('identitas_karyawan', {})
                data_presensi = employee_group.get('data_presensi', [])
                
                for attendance in data_presensi:
                    # Combine identity and attendance data
                    flat_record = {
                        # Identity data (with string trimming for clean data)
                        'employee_name': identitas.get('employee_name', '').strip(),
                        'employee_id_venus': identitas.get('employee_id_venus', '').strip(),
                        'employee_id_ptrj': identitas.get('employee_id_ptrj', '').strip(),
                        'task_code': identitas.get('task_code', '').strip(),
                        'station_code': identitas.get('station_code', '').strip(),
                        'machine_code': identitas.get('machine_code', '').strip(),
                        'expense_code': identitas.get('expense_code', '').strip(),
                        'raw_charge_job': identitas.get('raw_charge_job', '').strip(),
                        
                        # Attendance data
                        'id': attendance.get('id', ''),
                        'date': attendance.get('date', ''),
                        'shift': attendance.get('shift', ''),
                        'check_in': attendance.get('check_in', ''),
                        'check_out': attendance.get('check_out', ''),
                        'regular_hours': attendance.get('regular_hours', 0),
                        'overtime_hours': attendance.get('overtime_hours', 0),
                        'total_hours': attendance.get('total_hours', 0),
                        'status': attendance.get('status', ''),
                        'created_at': attendance.get('created_at', ''),
                        'notes': attendance.get('notes', ''),
                        
                        # Additional metadata
                        'source_record_id': attendance.get('source_record_id', ''),
                        'transfer_status': attendance.get('transfer_status', '')
                    }
                    
                    flattened_records.append(flat_record)
            
            self.logger.info(f"📊 Flattened {len(flattened_records)} attendance records from grouped data")
            return flattened_records
            
        except Exception as e:
            self.logger.error(f"❌ Error flattening grouped data: {e}")
            return []
    
    def update_progress(self, status: str, current_employee: str = '', current_date: str = '', 
                       processed: int = 0, total: int = 0, successful: int = 0, failed: int = 0):
        """Update progress information for web interface"""
        self.current_progress.update({
            'status': status,
            'current_employee': current_employee,
            'current_date': current_date,
            'processed_entries': processed,
            'total_entries': total,
            'successful_entries': successful,
            'failed_entries': failed
        })
        
        # Log progress update
        if status == 'processing':
            self.logger.info(f"🔄 Progress: {current_employee} - {current_date} ({processed}/{total})")
        elif status == 'completed':
            self.logger.info(f"✅ Completed: {successful} successful, {failed} failed out of {total}")
    
    async def process_selected_records(self, selected_data) -> bool:
        """Process user-selected records with progress tracking and crosscheck preparation
        
        Args:
            selected_data: Either List[int] (indices) or List[Dict] (actual records)
        """
        try:
            if not self.is_browser_ready:
                print("❌ Browser system not ready")
                return False
            
            self.update_progress('initializing')
            
            # Handle different input types
            if not selected_data:
                print("❌ No data selected")
                return False
            
            # Check if input is indices or actual records
            if isinstance(selected_data[0], int):
                # Input is indices - fetch and filter data
                print("🌐 Fetching grouped staging data...")
                grouped_data = await self.fetch_grouped_staging_data()
                
                if not grouped_data:
                    print("❌ No grouped staging data available")
                    return False
                
                # Apply exclusion filtering
                grouped_data = self._filter_excluded_employees_grouped(grouped_data)
                
                # Flatten for selection processing
                all_records = self.flatten_grouped_data_for_selection(grouped_data)
                
                # Get selected records based on indices
                selected_records = []
                for index in selected_data:
                    if 0 <= index < len(all_records):
                        selected_records.append(all_records[index])
                    else:
                        print(f"⚠️ Invalid index {index}, skipping")
                
                if not selected_records:
                    print("❌ No valid records selected")
                    return False
            else:
                # Input is actual records - use directly
                selected_records = selected_data
                print(f"📊 Processing {len(selected_records)} pre-selected records")
            
            # Create entries using EXACT same logic from test_real_api_data.py
            all_entries = []
            for record in selected_records:
                entries = self.processor.create_overtime_entries(record)
                all_entries.extend(entries)
            
            print(f"\n📊 AUTOMATION SUMMARY:")
            print(f"📋 Selected Records: {len(selected_records)}")
            print(f"🔄 Total Entries to Process: {len(all_entries)}")
            
            self.update_progress('processing', total=len(all_entries))
            
            # Get driver using same method
            driver = self.processor.browser_manager.get_driver()
            if not driver:
                print("❌ WebDriver not available")
                return False
            
            # Process each entry with progress tracking
            successful_entries = 0
            failed_entries = 0
            
            for i, entry in enumerate(all_entries, 1):
                employee_name = entry.get('employee_name', 'Unknown')
                entry_date = entry.get('date', 'Unknown')
                
                print(f"\n{'='*70}")
                print(f"🎯 Processing Entry {i}/{len(all_entries)}")
                print(f"👤 Employee: {employee_name}")
                print(f"📅 Date: {entry_date}")
                print(f"🔘 Type: {entry.get('transaction_type', 'Normal')} - ⏰ Hours: {entry.get('hours', 0)}")
                
                # Update progress
                self.update_progress(
                    'processing', 
                    employee_name, 
                    entry_date, 
                    i, 
                    len(all_entries), 
                    successful_entries, 
                    failed_entries
                )
                
                # Process single record
                success = await self.process_single_record_enhanced(driver, entry, i, len(all_entries))
                
                if success:
                    successful_entries += 1
                    # Store processed data for crosscheck
                    self.processed_data.append({
                        'employee_id_ptrj': entry.get('employee_id_ptrj', ''),
                        'employee_name': employee_name,
                        'transaction_date': self.calculate_transaction_date_by_mode(entry_date, self.automation_mode),
                        'transaction_type': entry.get('transaction_type', 'Normal'),
                        'hours': entry.get('hours', 0),
                        'is_overtime': entry.get('transaction_type') == 'Overtime',
                        'source_data': entry
                    })
                    print(f"✅ Entry {i} completed successfully")
                else:
                    failed_entries += 1
                    print(f"❌ Entry {i} failed to process")
                
                # Same wait timing as test_real_api_data.py
                if i < len(all_entries):
                    print(f"⏳ Waiting 3 seconds before next entry...")
                    await asyncio.sleep(3)
            
            # Final summary
            success_rate = (successful_entries / len(all_entries)) * 100 if all_entries else 0
            
            self.update_progress(
                'completed', 
                total=len(all_entries), 
                processed=len(all_entries),
                successful=successful_entries, 
                failed=failed_entries
            )
            
            print(f"\n🎯 AUTOMATION COMPLETE!")
            print(f"📊 Total Entries: {len(all_entries)}")
            print(f"✅ Successful: {successful_entries}/{len(all_entries)}")
            print(f"❌ Failed: {failed_entries}/{len(all_entries)}")
            print(f"📈 Success Rate: {success_rate:.1f}%")
            
            # Trigger crosscheck if successful entries exist
            if successful_entries > 0:
                print(f"\n🔍 Starting crosscheck validation...")
                await self.perform_crosscheck()
            
            return successful_entries > 0
            
        except Exception as e:
            print(f"❌ Error processing selected records: {e}")
            self.logger.error(f"Processing error: {e}")
            import traceback
            print(f"📋 Stack trace: {traceback.format_exc()}")
            return False
    
    async def perform_crosscheck(self):
        """Enhanced crosscheck validation against Millware database with comprehensive validation"""
        try:
            print(f"\n🔍 ENHANCED CROSSCHECK VALIDATION")
            print(f"=" * 60)
            
            # Get database connection string based on mode
            db_name = "db_ptrj_mill_test" if self.automation_mode == 'testing' else "db_ptrj_mill"
            
            # Use correct password as specified in requirements
            connection_string = f"""
                DRIVER={{ODBC Driver 17 for SQL Server}};
                SERVER=10.0.0.7,1888;
                DATABASE={db_name};
                UID=sa;
                PWD=supp0rt@;
                TrustServerCertificate=yes;
            """
            
            print(f"🔗 Connecting to database: {db_name}")
            print(f"🔧 Automation mode: {self.automation_mode.upper()}")
            
            conn = pyodbc.connect(connection_string, timeout=30)
            cursor = conn.cursor()
            
            # Enhanced crosscheck with comprehensive validation
            total_checks = len(self.processed_data)
            successful_checks = 0
            failed_checks = 0
            validation_details = []
            
            print(f"📊 Performing enhanced crosscheck on {total_checks} entries...")
            
            for i, entry in enumerate(self.processed_data, 1):
                print(f"\n🔍 Crosscheck {i}/{total_checks}")
                print(f"👤 Employee: {entry['employee_name']}")
                print(f"🆔 Employee ID (PTRJ): {entry['employee_id_ptrj']}")
                print(f"📅 Transaction Date: {entry['transaction_date']}")
                print(f"🔘 Type: {'Overtime' if entry['is_overtime'] else 'Regular'}")
                print(f"⏰ Hours: {entry['hours']}")
                
                # Enhanced database query with comprehensive fields
                query = """
                    SELECT [ID], [MasterID], [TaskCode], [TaskRtnVal], [EmpCode], [EmpName], 
                           [OT], [ShiftCode], [Hours], [Unit], [Rate], [Amount], [Status],
                           [CreatedBy], [CreatedDate], [UpdatedBy], [UpdatedDate], 
                           [ImpFlag], [TrxDate], [NormalDay], [ChargeTo]
                    FROM [{db_name}].[dbo].[PR_TASKREGLN]
                    WHERE EmpCode = ?
                      AND TrxDate = ?
                """.format(db_name=db_name)
                
                # Convert transaction date to database format (YYYY-MM-DD)
                try:
                    if '/' in entry['transaction_date']:
                        trx_date = datetime.strptime(entry['transaction_date'], "%d/%m/%Y").strftime("%Y-%m-%d")
                    else:
                        trx_date = entry['transaction_date']
                except Exception as e:
                    print(f"⚠️ Date conversion error: {e}")
                    trx_date = entry['transaction_date']
                
                # Prepare employee ID with POM prefix if needed
                employee_id = entry['employee_id_ptrj']
                if employee_id and not employee_id.startswith('POM'):
                    employee_id = f"POM{employee_id}"
                
                print(f"🔍 Query parameters: EmpCode={employee_id}, TrxDate={trx_date}")
                
                try:
                    cursor.execute(query, [employee_id, trx_date])
                    db_records = cursor.fetchall()
                    
                    print(f"📊 Found {len(db_records)} database records")
                    
                    if db_records:
                        # Separate regular and overtime records
                        regular_records = [r for r in db_records if r.OT == 0]
                        overtime_records = [r for r in db_records if r.OT == 1]
                        
                        print(f"   📋 Regular records: {len(regular_records)}")
                        print(f"   📋 Overtime records: {len(overtime_records)}")
                        
                        # Calculate totals from database
                        regular_hours_total = sum(float(r.Hours) for r in regular_records)
                        overtime_hours_total = sum(float(r.Hours) for r in overtime_records)
                        
                        print(f"   ⏰ DB Regular Hours Total: {regular_hours_total}")
                        print(f"   ⏰ DB Overtime Hours Total: {overtime_hours_total}")
                        
                        # Validation logic with 0.1 hour tolerance
                        validation_result = self.validate_hours_with_tolerance(
                            entry, regular_hours_total, overtime_hours_total
                        )
                        
                        if validation_result['is_valid']:
                            successful_checks += 1
                            print(f"✅ VALIDATION SUCCESS: {validation_result['message']}")
                        else:
                            failed_checks += 1
                            print(f"❌ VALIDATION FAILED: {validation_result['message']}")
                        
                        # Store detailed validation info
                        validation_details.append({
                            'entry_index': i,
                            'employee_name': entry['employee_name'],
                            'employee_id': employee_id,
                            'transaction_date': trx_date,
                            'input_hours': entry['hours'],
                            'input_type': entry['transaction_type'],
                            'db_regular_total': regular_hours_total,
                            'db_overtime_total': overtime_hours_total,
                            'db_records_count': len(db_records),
                            'validation_result': validation_result,
                            'is_valid': validation_result['is_valid']
                        })
                        
                    else:
                        failed_checks += 1
                        print(f"❌ NO RECORDS FOUND in database")
                        
                        validation_details.append({
                            'entry_index': i,
                            'employee_name': entry['employee_name'],
                            'employee_id': employee_id,
                            'transaction_date': trx_date,
                            'input_hours': entry['hours'],
                            'input_type': entry['transaction_type'],
                            'db_regular_total': 0,
                            'db_overtime_total': 0,
                            'db_records_count': 0,
                            'validation_result': {'is_valid': False, 'message': 'No records found in database'},
                            'is_valid': False
                        })
                        
                except Exception as query_error:
                    failed_checks += 1
                    print(f"❌ DATABASE QUERY ERROR: {query_error}")
                    
                    validation_details.append({
                        'entry_index': i,
                        'employee_name': entry['employee_name'],
                        'employee_id': employee_id,
                        'transaction_date': trx_date,
                        'input_hours': entry['hours'],
                        'input_type': entry['transaction_type'],
                        'db_regular_total': 0,
                        'db_overtime_total': 0,
                        'db_records_count': 0,
                        'validation_result': {'is_valid': False, 'message': f'Query error: {query_error}'},
                        'is_valid': False
                    })
            
            conn.close()
            
            # Enhanced crosscheck summary with detailed reporting
            success_rate = (successful_checks / total_checks) * 100 if total_checks > 0 else 0
            
            print(f"\n🎯 ENHANCED CROSSCHECK SUMMARY")
            print(f"=" * 60)
            print(f"📊 Total Validation Checks: {total_checks}")
            print(f"✅ Successful Matches: {successful_checks}")
            print(f"❌ Failed Matches: {failed_checks}")
            print(f"📈 Match Rate: {success_rate:.1f}%")
            print(f"🔗 Database: {db_name}")
            print(f"🔧 Mode: {self.automation_mode}")
            print(f"🔑 Connection: SERVER=10.0.0.7,1888 | UID=sa")
            
            # Generate detailed validation report
            self.generate_validation_report(validation_details, db_name)
            
            # Update progress with enhanced crosscheck results
            self.current_progress['crosscheck'] = {
                'total_checks': total_checks,
                'successful_checks': successful_checks,
                'failed_checks': failed_checks,
                'success_rate': success_rate,
                'database': db_name,
                'automation_mode': self.automation_mode,
                'validation_details': validation_details
            }
            
        except Exception as e:
            print(f"❌ Enhanced crosscheck error: {e}")
            self.logger.error(f"Enhanced crosscheck error: {e}")
            import traceback
            print(f"📋 Stack trace: {traceback.format_exc()}")

    def validate_hours_with_tolerance(self, entry: Dict, db_regular_total: float, db_overtime_total: float) -> Dict:
        """Validate hours with 0.1 hour tolerance and comprehensive logic"""
        try:
            input_hours = float(entry['hours'])
            is_overtime_entry = entry['is_overtime']
            
            tolerance = 0.1
            
            if is_overtime_entry:
                # Overtime entry validation
                hours_diff = abs(db_overtime_total - input_hours)
                if hours_diff <= tolerance:
                    return {
                        'is_valid': True,
                        'message': f"Overtime hours match (DB: {db_overtime_total}, Input: {input_hours}, Diff: {hours_diff:.2f})"
                    }
                else:
                    return {
                        'is_valid': False,
                        'message': f"Overtime hours mismatch (DB: {db_overtime_total}, Input: {input_hours}, Diff: {hours_diff:.2f})"
                    }
            else:
                # Regular entry validation
                hours_diff = abs(db_regular_total - input_hours)
                if hours_diff <= tolerance:
                    return {
                        'is_valid': True,
                        'message': f"Regular hours match (DB: {db_regular_total}, Input: {input_hours}, Diff: {hours_diff:.2f})"
                    }
                else:
                    return {
                        'is_valid': False,
                        'message': f"Regular hours mismatch (DB: {db_regular_total}, Input: {input_hours}, Diff: {hours_diff:.2f})"
                    }
                    
        except Exception as e:
            return {
                'is_valid': False,
                'message': f"Validation error: {e}"
            }

    def generate_validation_report(self, validation_details: List[Dict], db_name: str):
        """Generate detailed validation report"""
        try:
            print(f"\n📋 DETAILED VALIDATION REPORT")
            print(f"=" * 80)
            
            for detail in validation_details:
                status_icon = "✅" if detail['is_valid'] else "❌"
                print(f"{status_icon} Entry {detail['entry_index']}: {detail['employee_name']}")
                print(f"   🆔 Employee ID: {detail['employee_id']}")
                print(f"   📅 Date: {detail['transaction_date']}")
                print(f"   💼 Input: {detail['input_type']} - {detail['input_hours']}h")
                print(f"   💾 DB Records: {detail['db_records_count']} (Regular: {detail['db_regular_total']}h, Overtime: {detail['db_overtime_total']}h)")
                print(f"   📊 Result: {detail['validation_result']['message']}")
                print()
            
            # Summary statistics
            valid_count = sum(1 for d in validation_details if d['is_valid'])
            print(f"📈 VALIDATION STATISTICS:")
            print(f"   ✅ Valid: {valid_count}/{len(validation_details)}")
            print(f"   ❌ Invalid: {len(validation_details) - valid_count}/{len(validation_details)}")
            print(f"   📊 Success Rate: {(valid_count/len(validation_details)*100):.1f}%")
            print(f"   🔗 Database: {db_name}")
            
        except Exception as e:
            self.logger.error(f"Validation report generation error: {e}")
    
    def start_web_interface(self):
        """Start Flask web interface with enhanced progress tracking"""
        try:
            from flask import Flask, render_template, jsonify, request
            
            app = Flask(__name__, template_folder='.')
            
            @app.route('/')
            def index():
                return render_template('enhanced_user_controlled_crosscheck.html')
            
            @app.route('/api/staging/data')
            def get_staging_data():
                try:
                    # Fetch grouped data and flatten for interface
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    try:
                        grouped_data = loop.run_until_complete(self.fetch_grouped_staging_data())
                        
                        # Apply exclusion filtering
                        filtered_grouped_data = self._filter_excluded_employees_grouped(grouped_data)
                        
                        # Flatten for interface
                        flattened_data = self.flatten_grouped_data_for_selection(filtered_grouped_data)
                        
                        self.logger.info(f"📊 API response: {len(flattened_data)} flattened records")
                        
                        return jsonify({'data': flattened_data})
                        
                    finally:
                        loop.close()
                        
                except Exception as e:
                    self.logger.error(f"Error fetching staging data: {e}")
                    return jsonify({'error': str(e)}), 500
            
            @app.route('/api/progress')
            def get_progress():
                """Get current automation progress"""
                return jsonify(self.current_progress)
            
            @app.route('/api/crosscheck-results')
            def get_crosscheck_results():
                """Get crosscheck validation results"""
                return jsonify({
                    'processed_data': self.processed_data,
                    'crosscheck': self.current_progress.get('crosscheck', {}),
                    'automation_mode': self.automation_mode
                })
            
            @app.route('/api/process-selected', methods=['POST'])
            def process_selected():
                try:
                    data = request.get_json()
                    selected_indices = data.get('selected_indices', [])
                    automation_mode = data.get('automation_mode', 'testing')
                    bypass_validation = data.get('bypass_validation', False)
                    
                    if not selected_indices:
                        return jsonify({'error': 'No records selected'}), 400
                    
                    # Set automation mode
                    self.automation_mode = automation_mode
                    
                    print(f"\n🎯 USER SELECTION RECEIVED:")
                    print(f"📋 Selected indices: {selected_indices}")
                    print(f"📊 Total selected: {len(selected_indices)} records")
                    print(f"🔧 Automation mode: {automation_mode.upper()}")
                    
                    # Reset processed data for new automation
                    self.processed_data = []
                    
                    # Create a new event loop for the async function in a thread
                    def run_automation():
                        try:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            loop.run_until_complete(self.process_selected_records(selected_indices))
                        except Exception as e:
                            print(f"❌ Automation thread error: {e}")
                            self.logger.error(f"Automation thread error: {e}")
                        finally:
                            loop.close()
                    
                    automation_thread = threading.Thread(target=run_automation, daemon=True)
                    automation_thread.start()
                    
                    return jsonify({
                        'success': True,
                        'message': f'Processing {len(selected_indices)} selected records with crosscheck validation',
                        'selected_count': len(selected_indices),
                        'automation_mode': automation_mode,
                        'crosscheck_enabled': True
                    })
                    
                except Exception as e:
                    self.logger.error(f"Process selected error: {e}")
                    return jsonify({'error': str(e)}), 500
            
            def run_flask():
                app.run(host='0.0.0.0', port=5000, debug=False, threaded=True, use_reloader=False)
            
            self.web_server_thread = threading.Thread(target=run_flask, daemon=True)
            self.web_server_thread.start()
            
            time.sleep(2)
            print("✅ Enhanced web interface started at http://localhost:5000")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start web interface: {e}")
            self.logger.error(f"Web interface error: {e}")
            return False
    
    def calculate_transaction_date_by_mode(self, original_date_str: str, mode: str = 'testing') -> str:
        """Calculate transaction date based on automation mode"""
        try:
            from datetime import datetime
            from dateutil.relativedelta import relativedelta
            
            # Parse original date
            original_date = None
            if '/' in original_date_str and len(original_date_str.split('/')) == 3:
                try:
                    original_date = datetime.strptime(original_date_str, "%d/%m/%Y")
                except:
                    original_date = datetime.strptime(original_date_str, "%Y-%m-%d")
            else:
                original_date = datetime.strptime(original_date_str, "%Y-%m-%d")
            
            if mode == 'testing':
                # Testing mode: Kurangi 1 bulan dari tanggal original absen
                trx_date = original_date - relativedelta(months=1)
                formatted_date = trx_date.strftime("%d/%m/%Y")
                return formatted_date
            else:
                # Real mode: Gunakan tanggal original dari data absen
                formatted_date = original_date.strftime("%d/%m/%Y")
                return formatted_date
                
        except Exception as e:
            self.logger.error(f"❌ Error calculating transaction date: {e}")
            try:
                if '/' in original_date_str:
                    return original_date_str
                else:
                    date_obj = datetime.strptime(original_date_str, "%Y-%m-%d")
                    return date_obj.strftime("%d/%m/%Y")
            except:
                return original_date_str
    
    async def process_single_record_enhanced(self, driver, record: Dict, record_index: int, total_records: int = 0) -> bool:
        """Enhanced single record processing with smart button selection (Add vs New)"""
        start_time = time.time()
        
        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.common.keys import Keys
            
            employee_name = record.get('employee_name', '')
            date_value = record.get('date', '')
            raw_charge_job = record.get('raw_charge_job', '')
            transaction_type = record.get('transaction_type', 'Normal')
            
            # Calculate working hours using business logic
            calculated_hours = self.calculate_working_hours(record, transaction_type)
            
            # Log record processing start
            self._log_automation_step("Record Processing Start", {
                'record_index': record_index,
                'total_records': total_records,
                'employee_name': employee_name,
                'date_value': date_value,
                'transaction_type': transaction_type,
                'calculated_hours': calculated_hours
            })
            
            # Log initial driver state
            self._log_driver_state(driver, f"Record {record_index} Processing - Initial")
            
            self.logger.info(f"🎯 Processing record {record_index}/{total_records}: {employee_name}")
            
            # Step 0: Fill document date field
            formatted_doc_date = self.calculate_document_date_by_mode(date_value, self.automation_mode)
            
            script = f"""
                var docDateField = document.getElementById('MainContent_txtDocDate');
                if (docDateField) {{
                    docDateField.value = '{formatted_doc_date}';
                    docDateField.dispatchEvent(new Event('change', {{bubbles: true}}));
                    return true;
                }}
                return false;
            """
            
            driver.execute_script(script)
            await asyncio.sleep(1.5)
            
            # Step 1: Fill transaction date field
            formatted_trx_date = self.calculate_transaction_date_by_mode(date_value, self.automation_mode)
            
            script = f"""
                var dateField = document.getElementById('MainContent_txtTrxDate');
                if (dateField) {{
                    dateField.value = '{formatted_trx_date}';
                    dateField.dispatchEvent(new Event('change', {{bubbles: true}}));
                    return true;
                }}
                return false;
            """
            
            result = driver.execute_script(script)
            if result:
                date_field = driver.find_element(By.ID, "MainContent_txtTrxDate")
                date_field.send_keys(Keys.ENTER)
                await asyncio.sleep(2)
            else:
                self.logger.error(f"❌ Failed to fill transaction date field")
                return False
            
            # Step 2: Fill employee field using enhanced autocomplete with Employee ID priority
            autocomplete_fields = driver.find_elements(By.CSS_SELECTOR, ".ui-autocomplete-input")
            if len(autocomplete_fields) > 0:
                employee_field = autocomplete_fields[0]
                # Use enhanced employee autocomplete with ID priority
                success = await self.smart_employee_autocomplete_input(driver, employee_field, record, "Employee")
                if not success:
                    self.logger.error(f"❌ Failed to fill employee field: {employee_name}")
                    return False
                await asyncio.sleep(2)
            else:
                self.logger.error(f"❌ Employee autocomplete field not found")
                return False
            
            # Step 3: Select transaction type
            success = await self.processor.select_transaction_type(driver, transaction_type)
            if not success:
                self.logger.error(f"❌ Failed to select transaction type: {transaction_type}")
                return False
            
            # Step 4: Fill charge job components
            charge_components = self.processor.parse_raw_charge_job(raw_charge_job)
            if charge_components:
                success = await self.fill_charge_job_smart_autocomplete(driver, charge_components)
                if not success:
                    self.logger.error(f"❌ Failed to fill charge job components")
                    return False
            
            # Step 5: Fill hours field
            success = await self.processor.fill_hours_field(driver, calculated_hours)
            if not success:
                self.logger.error(f"❌ Failed to fill hours field: {calculated_hours}")
                return False
            
            # Step 6: Enhanced Button Click Logic
            is_final_record = (record_index == total_records)
            success = await self.enhanced_button_click(driver, is_final_record, record_index, total_records)
            
            if success:
                self.logger.info(f"✅ Record {record_index}/{total_records} processed successfully")
                return True
            else:
                self.logger.error(f"❌ Failed to click button for record {record_index}/{total_records}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Record processing error: {e}")
            import traceback
            self.logger.error(f"📋 Stack trace: {traceback.format_exc()}")
            return False

    async def enhanced_button_click(self, driver, is_final_record: bool, record_index: int, total_records: int) -> bool:
        """Enhanced button click logic with Add/New button selection based on record position"""
        try:
            from selenium.webdriver.common.by import By
            
            if is_final_record:
                # Final record: Click "New" button
                print(f"🔄 Final record ({record_index}/{total_records}) - Clicking 'New' button")
                success = await self.click_new_button(driver)
                if success:
                    print(f"✅ 'New' button clicked successfully - Form reset completed")
                    await asyncio.sleep(3)  # Wait for complete form reset
                    return True
                else:
                    print(f"❌ Failed to click 'New' button - attempting retry")
                    await asyncio.sleep(2)
                    success = await self.click_new_button(driver)
                    if success:
                        print(f"✅ 'New' button clicked on retry")
                        await asyncio.sleep(3)
                        return True
                    else:
                        print(f"❌ 'New' button failed on retry - marking batch as completed")
                        return True  # Mark as completed regardless
            else:
                # Non-final record: Click "Add" button
                print(f"➕ Record {record_index}/{total_records} - Clicking 'Add' button")
                success = await self.click_add_button(driver)
                if success:
                    print(f"✅ 'Add' button clicked successfully - Waiting for form reset")
                    await asyncio.sleep(3)  # Wait for form reset confirmation
                    return True
                else:
                    print(f"❌ Failed to click 'Add' button - attempting retry")
                    await asyncio.sleep(2)
                    success = await self.click_add_button(driver)
                    if success:
                        print(f"✅ 'Add' button clicked on retry")
                        await asyncio.sleep(3)
                        return True
                    else:
                        print(f"⚠️ 'Add' button failed on retry - continuing to next record")
                        return False
                        
        except Exception as e:
            self.logger.error(f"❌ Enhanced button click error: {e}")
            return False

    async def click_add_button(self, driver) -> bool:
        """Click Add button with multiple selector strategies"""
        try:
            from selenium.webdriver.common.by import By
            
            # Add Button Selectors (in priority order)
            add_selectors = [
                "input[value='Add']",
                "button[value='Add']", 
                "input[id*='Add']",
                "button[id*='Add']"
            ]
            
            add_button = None
            for selector in add_selectors:
                try:
                    add_button = driver.find_element(By.CSS_SELECTOR, selector)
                    if add_button.is_displayed() and add_button.is_enabled():
                        self.logger.info(f"🎯 Found Add button with selector: {selector}")
                        break
                except:
                    continue
            
            if add_button:
                add_button.click()
                self.logger.info(f"✅ Add button clicked successfully")
                return True
            else:
                self.logger.error(f"❌ Add button not found with any selector")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Click Add button error: {e}")
            return False

    async def click_new_button(self, driver) -> bool:
        """Click New button with multiple selector strategies"""
        try:
            from selenium.webdriver.common.by import By
            
            # New Button Selectors (in priority order)
            new_selectors = [
                'input[name="ctl00$MainContent$btnNew"]',
                'input[id="MainContent_btnNew"]',
                'input[value="New"]'
            ]
            
            new_button = None
            for selector in new_selectors:
                try:
                    new_button = driver.find_element(By.CSS_SELECTOR, selector)
                    if new_button.is_displayed() and new_button.is_enabled():
                        self.logger.info(f"🎯 Found New button with selector: {selector}")
                        break
                except:
                    continue
            
            if new_button:
                new_button.click()
                self.logger.info(f"✅ New button clicked successfully")
                return True
            else:
                self.logger.error(f"❌ New button not found with any selector")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Click New button error: {e}")
            return False
    
    def calculate_working_hours(self, record: Dict, transaction_type: str) -> float:
        """Calculate working hours based on business rules"""
        try:
            if transaction_type == 'Overtime':
                return float(record.get('overtime_hours', 0))
            
            regular_hours = record.get('regular_hours', 0)
            if regular_hours > 0:
                date_str = record.get('date', '')
                try:
                    if '/' in date_str:
                        date_obj = datetime.strptime(date_str, "%d/%m/%Y")
                    else:
                        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                    
                    is_saturday = date_obj.weekday() == 5
                    return 5.0 if is_saturday else 7.0
                    
                except Exception:
                    return float(regular_hours)
            else:
                return float(regular_hours)
                
        except Exception as e:
            self.logger.error(f"❌ Working hours calculation failed: {e}")
            if transaction_type == 'Overtime':
                return float(record.get('overtime_hours', 0))
            else:
                return float(record.get('regular_hours', 0))
    
    def calculate_document_date_by_mode(self, attendance_date_str: str, mode: str = 'testing') -> str:
        """Calculate document date based on automation mode - doc date month must match transaction date month"""
        try:
            # Parse attendance date to get the transaction date
            attendance_date = None
            if '/' in attendance_date_str and len(attendance_date_str.split('/')) == 3:
                try:
                    attendance_date = datetime.strptime(attendance_date_str, "%d/%m/%Y")
                except:
                    attendance_date = datetime.strptime(attendance_date_str, "%Y-%m-%d")
            else:
                attendance_date = datetime.strptime(attendance_date_str, "%Y-%m-%d")
            
            # Calculate transaction date based on mode
            if mode == 'testing':
                # Testing mode: attendance date - 1 month
                transaction_date = attendance_date - relativedelta(months=1)
            else:
                # Real mode: use attendance date as-is
                transaction_date = attendance_date
            
            # Document date: current day with transaction date's month and year
            current_date = datetime.now()
            doc_date = datetime(transaction_date.year, transaction_date.month, current_date.day)
            
            # Handle edge case where current day doesn't exist in target month (e.g., Feb 30)
            try:
                doc_date_formatted = doc_date.strftime("%d/%m/%Y")
            except ValueError:
                # If current day doesn't exist in target month, use last day of target month
                from calendar import monthrange
                last_day = monthrange(transaction_date.year, transaction_date.month)[1]
                doc_date = datetime(transaction_date.year, transaction_date.month, min(current_date.day, last_day))
                doc_date_formatted = doc_date.strftime("%d/%m/%Y")
            
            self.logger.info(f"📅 Document date calculation: Attendance={attendance_date_str}, Mode={mode}, Transaction={transaction_date.strftime('%d/%m/%Y')}, Document={doc_date_formatted}")
            return doc_date_formatted
            
        except Exception as e:
            self.logger.error(f"❌ Error calculating document date: {e}")
            # Fallback to current date
            return datetime.now().strftime("%d/%m/%Y")
    
    async def smart_employee_autocomplete_input(self, driver, field, record: Dict, field_name: str = "Employee") -> bool:
        """Enhanced employee autocomplete input with Employee ID priority and robust error handling"""
        start_time = time.time()
        
        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.common.keys import Keys
            from selenium.common.exceptions import StaleElementReferenceException
            
            employee_name = record.get('employee_name', '')
            employee_id_ptrj = record.get('employee_id_ptrj', '')
            
            # Log automation step start
            self._log_automation_step("Employee Autocomplete Start", {
                'employee_name': employee_name,
                'employee_id_ptrj': employee_id_ptrj,
                'field_name': field_name
            })
            
            # Log initial driver and element state
            self._log_driver_state(driver, "Employee Autocomplete - Initial")
            self._log_element_state(field, "Employee Field", "Initial State")
            
            self.logger.info(f"🎯 Employee autocomplete - Name: {employee_name}, PTRJ ID: {employee_id_ptrj}")
            
            # Check driver responsiveness before proceeding
            responsiveness_start = time.time()
            if not await self._check_driver_responsiveness(driver):
                self.logger.error("❌ Driver not responsive, aborting employee autocomplete")
                self._log_automation_step("Employee Autocomplete", {'error': 'Driver not responsive'}, success=False)
                return False
            self._log_performance_metrics("Driver Responsiveness Check", responsiveness_start, time.time())
            
            # Ensure field is still valid and interactable
            field_validation_start = time.time()
            field = await self._ensure_field_validity(driver, field, field_name)
            if not field:
                self.logger.error("❌ Employee field not valid or accessible")
                self._log_automation_step("Employee Autocomplete", {'error': 'Field not valid'}, success=False)
                return False
            self._log_performance_metrics("Field Validation", field_validation_start, time.time())
            
            # Log field state after validation
            self._log_element_state(field, "Employee Field", "After Validation")
            
            # Priority 1: Try using Employee ID (PTRJ ID) if available
            if employee_id_ptrj and employee_id_ptrj.strip():
                # Prepare employee ID with POM prefix if needed
                employee_id_with_prefix = employee_id_ptrj
                if not employee_id_ptrj.startswith('POM'):
                    employee_id_with_prefix = f"POM{employee_id_ptrj}"
                
                self.logger.info(f"🆔 Trying Employee ID first: {employee_id_with_prefix}")
                
                id_attempt_start = time.time()
                success = await self._try_employee_id_autocomplete_robust(driver, field, employee_id_with_prefix)
                self._log_performance_metrics("Employee ID Autocomplete", id_attempt_start, time.time())
                
                if success:
                    self.logger.info(f"✅ Employee selected successfully using ID: {employee_id_with_prefix}")
                    self._log_automation_step("Employee Autocomplete", {
                        'method': 'Employee ID',
                        'value': employee_id_with_prefix,
                        'total_time': time.time() - start_time
                    }, success=True)
                    return True
                else:
                    self.logger.info(f"⚠️ Employee ID failed, falling back to name: {employee_name}")
            else:
                self.logger.info(f"⚠️ No Employee ID available, using name directly: {employee_name}")
            
            # Priority 2: Fall back to employee name if ID is not available or failed
            if employee_name and employee_name.strip():
                name_attempt_start = time.time()
                success = await self._try_employee_name_autocomplete_robust(driver, field, employee_name)
                self._log_performance_metrics("Employee Name Autocomplete", name_attempt_start, time.time())
                
                if success:
                    self.logger.info(f"✅ Employee selected successfully using name: {employee_name}")
                    self._log_automation_step("Employee Autocomplete", {
                        'method': 'Employee Name',
                        'value': employee_name,
                        'total_time': time.time() - start_time
                    }, success=True)
                    return True
                else:
                    self.logger.error(f"❌ Employee name autocomplete also failed: {employee_name}")
            
            # Log failure
            self._log_automation_step("Employee Autocomplete", {
                'error': 'All methods failed',
                'employee_name': employee_name,
                'employee_id_ptrj': employee_id_ptrj,
                'total_time': time.time() - start_time
            }, success=False)
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Enhanced employee autocomplete failed: {e}")
            self._log_automation_step("Employee Autocomplete", {
                'error': str(e),
                'exception_type': type(e).__name__,
                'total_time': time.time() - start_time
            }, success=False)
            return False

    async def _try_employee_id_autocomplete_robust(self, driver, field, employee_id: str) -> bool:
        """Try autocomplete using employee ID with robust error handling"""
        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.common.keys import Keys
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
            
            max_attempts = 3
            
            for attempt in range(max_attempts):
                try:
                    # Check driver responsiveness before each attempt
                    if not await self._check_driver_responsiveness(driver):
                        self.logger.warning(f"Driver not responsive on attempt {attempt + 1}")
                        await asyncio.sleep(2)
                        continue
                    
                    # Re-find field if stale
                    field = await self._ensure_field_validity(driver, field, "Employee")
                    if not field:
                        continue
                    
                    # Clear field with enhanced method
                    await self._safe_clear_field(field)
                    await asyncio.sleep(0.5)
                    
                    # Type employee ID with character-by-character validation
                    for char in employee_id:
                        field.send_keys(char)
                        await asyncio.sleep(0.1)
                    
                    # Wait for autocomplete with timeout
                    await asyncio.sleep(2.0)  # Increased wait time
                    
                    # Check for dropdown options with retry
                    dropdown_found = False
                    for dropdown_attempt in range(3):
                        try:
                            dropdown_options = driver.find_elements(By.CSS_SELECTOR, ".ui-autocomplete .ui-menu-item")
                            
                            if dropdown_options:
                                visible_options = [opt for opt in dropdown_options if opt.is_displayed()]
                                self.logger.info(f"🔍 Found {len(visible_options)} autocomplete options for ID: {employee_id}")
                                
                                if visible_options:
                                    # Select first option (most accurate match)
                                    field.send_keys(Keys.ARROW_DOWN)
                                    await asyncio.sleep(0.8)
                                    field.send_keys(Keys.ENTER)
                                    await asyncio.sleep(2.0)
                                    dropdown_found = True
                                    break
                            
                            await asyncio.sleep(0.5)
                        except Exception as dropdown_error:
                            self.logger.warning(f"Dropdown check attempt {dropdown_attempt + 1} failed: {dropdown_error}")
                            await asyncio.sleep(0.5)
                    
                    if dropdown_found:
                        return True
                    else:
                        self.logger.info(f"⚠️ No autocomplete options found for ID: {employee_id}")
                        
                except StaleElementReferenceException:
                    self.logger.warning(f"Stale element on attempt {attempt + 1}, retrying...")
                    await asyncio.sleep(1)
                    continue
                except Exception as e:
                    self.logger.warning(f"⚠️ Employee ID autocomplete attempt {attempt + 1} failed: {e}")
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(2)
                        continue
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Employee ID autocomplete error: {e}")
            return False
    
    async def _try_employee_id_autocomplete(self, driver, field, employee_id: str) -> bool:
        """Legacy method - redirects to robust version"""
        return await self._try_employee_id_autocomplete_robust(driver, field, employee_id)

    async def _try_employee_name_autocomplete_robust(self, driver, field, employee_name: str) -> bool:
        """Try autocomplete using employee name with robust error handling"""
        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.common.keys import Keys
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
            
            max_attempts = 3
            
            for attempt in range(max_attempts):
                try:
                    # Check driver responsiveness before each attempt
                    if not await self._check_driver_responsiveness(driver):
                        self.logger.warning(f"Driver not responsive on attempt {attempt + 1}")
                        await asyncio.sleep(2)
                        continue
                    
                    # Re-find field if stale
                    field = await self._ensure_field_validity(driver, field, "Employee")
                    if not field:
                        continue
                    
                    # Clear field with enhanced method
                    await self._safe_clear_field(field)
                    await asyncio.sleep(0.5)
                    
                    # Type character by character for name with enhanced checking
                    dropdown_found = False
                    for i, char in enumerate(employee_name):
                        field.send_keys(char)
                        await asyncio.sleep(0.2)
                        
                        # Check for dropdown options with retry
                        for dropdown_attempt in range(2):
                            try:
                                dropdown_options = driver.find_elements(By.CSS_SELECTOR, ".ui-autocomplete .ui-menu-item")
                                
                                if dropdown_options:
                                    visible_options = [opt for opt in dropdown_options if opt.is_displayed()]
                                    
                                    if len(visible_options) == 1:
                                        field.send_keys(Keys.ARROW_DOWN)
                                        await asyncio.sleep(0.8)
                                        field.send_keys(Keys.ENTER)
                                        await asyncio.sleep(2.0)
                                        dropdown_found = True
                                        break
                                    elif len(visible_options) > 1 and i >= len(employee_name) // 2:
                                        # If multiple options and we've typed enough, select first
                                        field.send_keys(Keys.ARROW_DOWN)
                                        await asyncio.sleep(0.8)
                                        field.send_keys(Keys.ENTER)
                                        await asyncio.sleep(2.0)
                                        dropdown_found = True
                                        break
                                
                                await asyncio.sleep(0.3)
                            except Exception as dropdown_error:
                                self.logger.warning(f"Dropdown check failed: {dropdown_error}")
                                await asyncio.sleep(0.3)
                        
                        if dropdown_found:
                            break
                    
                    if dropdown_found:
                        return True
                    
                    # Final fallback method with enhanced error handling
                    try:
                        field.send_keys(Keys.ARROW_DOWN)
                        await asyncio.sleep(1.0)
                        field.send_keys(Keys.ENTER)
                        await asyncio.sleep(2.0)
                        return True
                    except Exception as fallback_error:
                        self.logger.warning(f"Fallback method failed: {fallback_error}")
                    
                except StaleElementReferenceException:
                    self.logger.warning(f"Stale element on attempt {attempt + 1}, retrying...")
                    await asyncio.sleep(1)
                    continue
                except Exception as e:
                    self.logger.warning(f"⚠️ Employee name autocomplete attempt {attempt + 1} failed: {e}")
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(2)
                        continue
                    else:
                        return False
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Employee name autocomplete error: {e}")
            return False
    
    async def _try_employee_name_autocomplete(self, driver, field, employee_name: str) -> bool:
        """Legacy method - redirects to robust version"""
        return await self._try_employee_name_autocomplete_robust(driver, field, employee_name)

    async def _check_driver_responsiveness(self, driver, timeout: int = 10) -> bool:
        """Enhanced WebDriver responsiveness check with comprehensive tests"""
        try:
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.common.by import By
            from selenium.common.exceptions import TimeoutException, WebDriverException
            import time
            
            start_time = time.time()
            
            # Test 1: Check if driver session is alive
            try:
                driver.current_url
            except WebDriverException as e:
                self.logger.error(f"Driver session is dead: {e}")
                return False
            
            # Test 2: Execute simple JavaScript with timeout
            try:
                result = driver.execute_script("return document.readyState;")
                if result not in ["complete", "interactive"]:
                    self.logger.warning(f"Document state: {result}")
                    # Give it a moment if loading
                    if result == "loading":
                        await asyncio.sleep(2)
                        result = driver.execute_script("return document.readyState;")
                        if result not in ["complete", "interactive"]:
                            return False
            except Exception as e:
                self.logger.error(f"JavaScript execution failed: {e}")
                return False
            
            # Test 3: Check page responsiveness with DOM interaction
            try:
                driver.execute_script("return document.title;")
            except Exception as e:
                self.logger.error(f"DOM interaction failed: {e}")
                return False
            
            # Test 4: Verify body element exists and is interactable
            try:
                body = WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                if not body.is_displayed():
                    self.logger.warning("Body element not displayed")
                    return False
            except TimeoutException:
                self.logger.error("Body element not found within timeout")
                return False
            
            # Test 5: Check if we can interact with the page
            try:
                driver.execute_script("return window.innerHeight;")
            except Exception as e:
                self.logger.error(f"Window interaction failed: {e}")
                return False
            
            # Test 6: Verify we're on the expected domain (Venus system)
            try:
                current_url = driver.current_url
                if not any(domain in current_url.lower() for domain in ['venus', 'localhost', '127.0.0.1']):
                    self.logger.warning(f"Unexpected URL: {current_url}")
                    # Don't fail immediately, but log for monitoring
            except Exception as e:
                self.logger.error(f"URL check failed: {e}")
                return False
            
            # Test 7: Performance check - ensure responsiveness is reasonable
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout:
                self.logger.warning(f"Responsiveness check took too long: {elapsed_time:.2f}s")
                return False
            
            self.logger.debug(f"Driver responsiveness check passed in {elapsed_time:.2f}s")
            return True
                
        except Exception as e:
            self.logger.error(f"Driver responsiveness check failed: {e}")
            return False
    
    async def _ensure_field_validity(self, driver, field, field_name: str):
        """Ensure field is still valid and interactable with enhanced waiting and recovery"""
        try:
            from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, NoSuchElementException
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.common.by import By
            import asyncio
            
            # Check if field is stale or invalid
            try:
                # Test multiple properties to ensure field is truly valid
                is_displayed = field.is_displayed()
                is_enabled = field.is_enabled()
                tag_name = field.tag_name  # This will throw if stale
                
                if is_displayed and is_enabled:
                    # Additional interactability check
                    try:
                        # Try to get field attributes to ensure it's fully loaded
                        field.get_attribute('id')
                        field.get_attribute('class')
                        return field
                    except Exception:
                        # Field exists but may not be fully interactive
                        self.logger.warning(f"Field {field_name} exists but not fully interactive")
                        
            except StaleElementReferenceException:
                self.logger.warning(f"Field {field_name} is stale, attempting recovery")
            except Exception as e:
                self.logger.warning(f"Field {field_name} validity check failed: {e}")
                
            # Enhanced field recovery with multiple strategies
            return await self._recover_field_with_strategies(driver, field_name)
                    
        except Exception as e:
            self.logger.error(f"Field validity check failed for {field_name}: {e}")
            return None
    
    async def _recover_field_with_strategies(self, driver, field_name: str):
        """Recover field using multiple locator strategies with progressive waiting"""
        try:
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.common.by import By
            import asyncio
            
            # Define multiple locator strategies for different field types
            locator_strategies = []
            
            if field_name.lower() == "employee":
                locator_strategies = [
                    (By.ID, "employee"),
                    (By.NAME, "employee"),
                    (By.CSS_SELECTOR, "input[id='employee']"),
                    (By.CSS_SELECTOR, "input[name='employee']"),
                    (By.XPATH, "//input[@id='employee']"),
                    (By.XPATH, "//input[@name='employee']"),
                    (By.XPATH, "//input[contains(@class, 'employee')]"),
                ]
            else:
                # Generic field strategies
                field_lower = field_name.lower()
                locator_strategies = [
                    (By.ID, field_lower),
                    (By.NAME, field_lower),
                    (By.CSS_SELECTOR, f"input[id='{field_lower}']"),
                    (By.CSS_SELECTOR, f"input[name='{field_lower}']"),
                    (By.XPATH, f"//input[@id='{field_lower}']"),
                    (By.XPATH, f"//input[@name='{field_lower}']"),
                ]
            
            # Progressive waiting times
            wait_times = [5, 10, 15]
            
            for wait_time in wait_times:
                for strategy in locator_strategies:
                    try:
                        self.logger.debug(f"Trying to find {field_name} with {strategy[0].name}='{strategy[1]}' (wait: {wait_time}s)")
                        
                        # Wait for element to be present and clickable
                        wait = WebDriverWait(driver, wait_time)
                        new_field = wait.until(EC.element_to_be_clickable(strategy))
                        
                        # Additional validation
                        if new_field and new_field.is_displayed() and new_field.is_enabled():
                            # Test interactability
                            try:
                                new_field.get_attribute('id')
                                self.logger.info(f"Successfully recovered field {field_name} using {strategy[0].name}='{strategy[1]}'")
                                return new_field
                            except Exception:
                                continue
                                
                    except Exception as e:
                        self.logger.debug(f"Strategy {strategy[0].name}='{strategy[1]}' failed: {e}")
                        continue
                
                # Wait between different wait time attempts
                if wait_time < wait_times[-1]:
                    await asyncio.sleep(2)
            
            self.logger.error(f"All recovery strategies failed for field {field_name}")
            return None
            
        except Exception as e:
             self.logger.error(f"Field recovery failed for {field_name}: {e}")
             return None
    
    async def _safe_clear_field(self, field):
        """Safely clear field with multiple methods"""
        try:
            from selenium.webdriver.common.keys import Keys
            
            # Method 1: Standard clear
            try:
                field.clear()
                return
            except:
                pass
            
            # Method 2: Select all and delete
            try:
                field.send_keys(Keys.CONTROL + "a")
                field.send_keys(Keys.DELETE)
                return
            except:
                pass
            
            # Method 3: Backspace method
            try:
                field_value = field.get_attribute("value")
                if field_value:
                    for _ in range(len(field_value)):
                        field.send_keys(Keys.BACKSPACE)
            except Exception as e:
                self.logger.warning(f"All clear methods failed: {e}")
                
        except Exception as e:
            self.logger.error(f"Safe clear field failed: {e}")
    
    async def _recover_driver_if_needed(self, driver) -> bool:
        """Attempt to recover driver if it becomes unresponsive"""
        try:
            self.logger.info("Attempting driver recovery...")
            
            # Check if we have access to browser manager
            if hasattr(self, 'browser_manager') and self.browser_manager:
                try:
                    # Use browser manager's recovery mechanism
                    recovered_driver = await self.browser_manager._recover_driver_connection()
                    if recovered_driver:
                        self.logger.info("Driver recovered using browser manager")
                        return True
                except Exception as e:
                    self.logger.error(f"Browser manager recovery failed: {e}")
            
            # Fallback recovery methods
            try:
                # Method 1: Refresh the page
                driver.refresh()
                await asyncio.sleep(3)
                
                if await self._check_driver_responsiveness(driver):
                    self.logger.info("Driver recovered with page refresh")
                    return True
            except Exception as e:
                self.logger.debug(f"Page refresh recovery failed: {e}")
            
            try:
                # Method 2: Navigate back to current URL
                current_url = driver.current_url
                driver.get(current_url)
                await asyncio.sleep(5)
                
                if await self._check_driver_responsiveness(driver):
                    self.logger.info("Driver recovered with navigation")
                    return True
            except Exception as e:
                self.logger.debug(f"Navigation recovery failed: {e}")
            
            try:
                # Method 3: Execute simple JavaScript to wake up driver
                driver.execute_script("window.focus();")
                await asyncio.sleep(2)
                
                if await self._check_driver_responsiveness(driver):
                    self.logger.info("Driver recovered with JavaScript focus")
                    return True
            except Exception as e:
                self.logger.debug(f"JavaScript recovery failed: {e}")
            
            self.logger.error("All driver recovery methods failed")
            return False
            
        except Exception as e:
            self.logger.error(f"Driver recovery process failed: {e}")
            return False
    
    async def _handle_stale_element_recovery(self, driver, element_locator, timeout: int = 10):
        """Handle stale element reference by re-finding the element"""
        try:
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.common.exceptions import TimeoutException
            
            self.logger.debug(f"Attempting to recover stale element: {element_locator}")
            
            # Wait for element to be present again
            try:
                element = WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located(element_locator)
                )
                
                # Additional wait for element to be interactable
                WebDriverWait(driver, timeout).until(
                    EC.element_to_be_clickable(element_locator)
                )
                
                self.logger.debug("Stale element recovered successfully")
                return element
                
            except TimeoutException:
                self.logger.error(f"Timeout waiting for element recovery: {element_locator}")
                return None
                
        except Exception as e:
            self.logger.error(f"Stale element recovery failed: {e}")
            return None

    async def smart_autocomplete_input(self, driver, field, target_value: str, field_name: str = "field") -> bool:
        """Smart autocomplete input with options selection (for non-employee fields) - Enhanced"""
        start_time = time.time()
        
        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.common.keys import Keys
            from selenium.common.exceptions import StaleElementReferenceException
            
            # Log automation step start
            self._log_automation_step(f"{field_name} Autocomplete Start", {
                'target_value': target_value,
                'field_name': field_name
            })
            
            # Log initial driver and element state
            self._log_driver_state(driver, f"{field_name} Autocomplete - Initial")
            self._log_element_state(field, field_name, "Initial State")
            
            # Check driver responsiveness with recovery
            responsiveness_start = time.time()
            if not await self._check_driver_responsiveness(driver):
                self.logger.warning(f"Driver not responsive for {field_name} autocomplete, attempting recovery")
                recovery_start = time.time()
                if not await self._recover_driver_if_needed(driver):
                    self.logger.error(f"Driver recovery failed for {field_name} autocomplete")
                    self._log_automation_step(f"{field_name} Autocomplete", {
                        'error': 'Driver recovery failed',
                        'total_time': time.time() - start_time
                    }, success=False)
                    return False
                self._log_performance_metrics("Driver Recovery", recovery_start, time.time())
            self._log_performance_metrics("Driver Responsiveness Check", responsiveness_start, time.time())
            
            max_attempts = 3
            
            for attempt in range(max_attempts):
                try:
                    # Ensure field validity
                    field = await self._ensure_field_validity(driver, field, field_name)
                    if not field:
                        continue
                    
                    # Safe clear field
                    await self._safe_clear_field(field)
                    await asyncio.sleep(0.5)
                    
                    # Type character by character with validation
                    for i, char in enumerate(target_value):
                        field.send_keys(char)
                        await asyncio.sleep(0.3)
                        
                        # Check for dropdown options with retry
                        for dropdown_attempt in range(2):
                            try:
                                dropdown_options = driver.find_elements(By.CSS_SELECTOR, ".ui-autocomplete .ui-menu-item")
                                
                                if dropdown_options:
                                    visible_options = [opt for opt in dropdown_options if opt.is_displayed()]
                                    
                                    if len(visible_options) == 1:
                                        field.send_keys(Keys.ARROW_DOWN)
                                        await asyncio.sleep(0.8)
                                        field.send_keys(Keys.ENTER)
                                        await asyncio.sleep(1.5)
                                        return True
                                break
                            except Exception:
                                await asyncio.sleep(0.3)
                                continue
                    
                    # Enhanced fallback method
                    fallback_start = time.time()
                    await asyncio.sleep(1.0)  # Wait for autocomplete to stabilize
                    field.send_keys(Keys.ARROW_DOWN)
                    await asyncio.sleep(1.0)
                    field.send_keys(Keys.ENTER)
                    await asyncio.sleep(2.0)
                    
                    self._log_performance_metrics(f"{field_name} Fallback Method", fallback_start, time.time())
                    self._log_automation_step(f"{field_name} Autocomplete", {
                        'method': 'Fallback',
                        'target_value': target_value,
                        'attempt': attempt + 1,
                        'total_time': time.time() - start_time
                    }, success=True)
                    return True
                    
                except StaleElementReferenceException:
                    self.logger.warning(f"Stale element on attempt {attempt + 1} for {field_name}")
                    recovery_start = time.time()
                    
                    # Try to recover stale element
                    if field_name.lower() == "employee":
                        recovered_field = await self._handle_stale_element_recovery(driver, (By.ID, "employee"))
                    else:
                        recovered_field = await self._handle_stale_element_recovery(driver, (By.ID, field_name.lower()))
                    
                    self._log_performance_metrics(f"{field_name} Stale Element Recovery", recovery_start, time.time())
                    
                    if recovered_field:
                        field = recovered_field
                        self.logger.info(f"Successfully recovered stale element for {field_name}")
                        self._log_element_state(field, field_name, "After Recovery")
                        continue
                    else:
                        self.logger.error(f"Failed to recover stale element for {field_name}")
                        await asyncio.sleep(1)
                        continue
                except Exception as e:
                    self.logger.warning(f"Autocomplete attempt {attempt + 1} failed for {field_name}: {e}")
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(2)
                        continue
                    else:
                        self._log_automation_step(f"{field_name} Autocomplete", {
                            'error': f'All attempts failed: {str(e)}',
                            'attempt': attempt + 1,
                            'total_time': time.time() - start_time
                        }, success=False)
                        return False
            
            # Log final failure
            self._log_automation_step(f"{field_name} Autocomplete", {
                'error': 'All attempts exhausted',
                'target_value': target_value,
                'max_attempts': max_attempts,
                'total_time': time.time() - start_time
            }, success=False)
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Smart autocomplete for {field_name} failed: {e}")
            self._log_automation_step(f"{field_name} Autocomplete", {
                'error': str(e),
                'exception_type': type(e).__name__,
                'target_value': target_value,
                'total_time': time.time() - start_time
            }, success=False)
            return False
    
    async def fill_charge_job_smart_autocomplete(self, driver, charge_components: List[str]) -> bool:
        """Fill charge job components using smart autocomplete"""
        try:
            from selenium.webdriver.common.by import By
            
            autocomplete_fields = driver.find_elements(By.CSS_SELECTOR, ".ui-autocomplete-input")
            
            for i, component in enumerate(charge_components):
                field_index = i + 1  # Skip employee field
                
                if field_index >= len(autocomplete_fields):
                    break
                
                field = autocomplete_fields[field_index]
                
                if not field.is_displayed() or not field.is_enabled():
                    break
                
                success = await self.smart_autocomplete_input(driver, field, component, f"Charge Component {i+1}")
                
                if not success:
                    return False
                
                await asyncio.sleep(1)
                autocomplete_fields = driver.find_elements(By.CSS_SELECTOR, ".ui-autocomplete-input")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Smart autocomplete charge job filling failed: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            await self.processor.cleanup()
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")


def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('enhanced_user_controlled_automation.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )


async def main():
    """Main function for enhanced user-controlled automation with crosscheck"""
    try:
        setup_logging()
        
        print("\n" + "="*80)
        print("🚀 ENHANCED USER-CONTROLLED AUTOMATION WITH CROSSCHECK")
        print("="*80)
        print("Features:")
        print("1. 🔧 Uses new grouped API endpoint (data-grouped)")
        print("2. 🔍 Real-time progress tracking")
        print("3. ✅ Automatic crosscheck validation with Millware database")
        print("4. 🚫 Employee exclusion filtering")
        print("5. 📊 Enhanced web interface with progress monitoring")
        print("6. 🎯 Database validation (test/real mode support)")
        print("="*80)
        
        # Initialize enhanced system
        system = EnhancedUserControlledAutomationSystem()
        
        # Initialize browser
        print("🔧 Initializing browser system...")
        if not await system.initialize_browser_system():
            print("❌ Failed to initialize browser system")
            return
        
        # Start enhanced web interface
        print("🌐 Starting enhanced web interface...")
        if not system.start_web_interface():
            print("❌ Failed to start web interface")
            return
        
        print("\n" + "="*80)
        print("✅ ENHANCED SYSTEM READY WITH CROSSCHECK")
        print("="*80)
        print("🌐 Web interface: http://localhost:5000")
        print("📊 New API endpoint: http://localhost:5173/api/staging/data-grouped")
        print("🔍 Features: Progress tracking + Database crosscheck validation")
        print("🎯 Supported modes: Testing (db_ptrj_mill_test) | Real (db_ptrj_mill)")
        print("="*80)
        
        # Open web browser
        try:
            webbrowser.open('http://localhost:5000')
            print("🌐 Web browser opened automatically")
        except:
            print("⚠️ Please manually open: http://localhost:5000")
        
        print("\n⏳ System running with crosscheck validation...")
        print("   (Press Ctrl+C to exit)")
        
        # Keep system running
        try:
            while True:
                await asyncio.sleep(5)
                
        except KeyboardInterrupt:
            print("\n🛑 User requested shutdown")
        
    except Exception as e:
        print(f"❌ System error: {e}")
        logging.exception("System error occurred")
    finally:
        print("\n🧹 Cleaning up...")
        try:
            if 'system' in locals():
                await system.cleanup()
            print("✅ Cleanup completed")
        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")


if __name__ == "__main__":
    print("🚀 Starting Enhanced User-Controlled Automation with Crosscheck...")
    asyncio.run(main())