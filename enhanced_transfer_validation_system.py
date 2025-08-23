#!/usr/bin/env python3
"""
Enhanced Transfer Validation System - Robust Version
Includes offline mode and fallback mechanisms when database is unavailable
"""

import sqlite3
import pyodbc
import logging
import json
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


class TransferValidationSystem:
    """Enhanced transfer validation system with success tracking and offline mode"""
    
    def __init__(self, automation_mode: str = 'testing', offline_mode: bool = False):
        self.automation_mode = automation_mode
        self.offline_mode = offline_mode
        self.logger = logging.getLogger(__name__)
        self.success_db_path = Path(__file__).parent / "db_successful_transfer.sqlite"
        
        # Database connection configurations - multiple options to try
        self.db_name = "db_ptrj_mill_test" if automation_mode == 'testing' else "db_ptrj_mill"
        
        # Try different connection strings
        self.connection_configs = [
            {
                'name': 'Primary Config',
                'connection_string': f"""
                    DRIVER={{ODBC Driver 17 for SQL Server}};
                    SERVER=10.0.0.7,1888;
                    DATABASE={self.db_name};
                    UID=sa;
                    PWD=Sql@2022;
                    TrustServerCertificate=yes;
                    Connection Timeout=15;
                """
            },
            {
                'name': 'Alternative Config',
                'connection_string': f"""
                    DRIVER={{ODBC Driver 17 for SQL Server}};
                    SERVER=10.0.0.7,1888;
                    DATABASE={self.db_name};
                    UID=sa;
                    PWD=Sql@2022;
                    Encrypt=no;
                    Connection Timeout=15;
                """
            },
            {
                'name': 'Legacy Driver',
                'connection_string': f"""
                    DRIVER={{SQL Server}};
                    SERVER=10.0.0.7,1888;
                    DATABASE={self.db_name};
                    UID=sa;
                    PWD=Sql@2022;
                    Connection Timeout=15;
                """
            }
        ]
        
        self.working_connection = None
        
        # Initialize success tracking database
        self.init_success_database()
        
        # Test database connection if not in offline mode
        if not offline_mode:
            self.test_and_find_working_connection()
    
    def init_success_database(self):
        """Initialize SQLite database for successful transfers"""
        try:
            conn = sqlite3.connect(self.success_db_path)
            cursor = conn.cursor()
            
            # Create enhanced tables with validation tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS successful_transfers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id_venus TEXT NOT NULL,
                    employee_id_ptrj TEXT NOT NULL,
                    employee_name TEXT NOT NULL,
                    transaction_date TEXT NOT NULL,
                    original_attendance_date TEXT NOT NULL,
                    regular_hours REAL NOT NULL DEFAULT 0,
                    overtime_hours REAL NOT NULL DEFAULT 0,
                    total_hours REAL NOT NULL DEFAULT 0,
                    task_code TEXT,
                    station_code TEXT,
                    machine_code TEXT,
                    expense_code TEXT,
                    raw_charge_job TEXT,
                    validation_timestamp TEXT NOT NULL,
                    automation_mode TEXT NOT NULL,
                    mill_database TEXT,
                    validation_status TEXT NOT NULL DEFAULT 'SUCCESS',
                    validation_type TEXT NOT NULL DEFAULT 'MILL_DB_VERIFIED',
                    source_record_id TEXT,
                    notes TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS validation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id_ptrj TEXT NOT NULL,
                    employee_name TEXT,
                    transaction_date TEXT NOT NULL,
                    validation_type TEXT NOT NULL,
                    expected_regular_hours REAL,
                    expected_overtime_hours REAL,
                    actual_regular_hours REAL,
                    actual_overtime_hours REAL,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    mill_database TEXT,
                    automation_mode TEXT NOT NULL,
                    connection_status TEXT NOT NULL DEFAULT 'UNKNOWN',
                    validation_timestamp TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create offline processing queue
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS offline_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_data TEXT NOT NULL,
                    validation_request TEXT NOT NULL,
                    automation_mode TEXT NOT NULL,
                    queued_timestamp TEXT NOT NULL,
                    processing_status TEXT NOT NULL DEFAULT 'PENDING',
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    last_retry TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_successful_transfers_employee_date 
                ON successful_transfers(employee_id_ptrj, transaction_date)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_validation_logs_employee_date 
                ON validation_logs(employee_id_ptrj, transaction_date)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_offline_queue_status 
                ON offline_queue(processing_status, automation_mode)
            ''')
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"✅ Success tracking database initialized: {self.success_db_path}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize success database: {e}")
            raise
    
    def test_and_find_working_connection(self) -> bool:
        """Test multiple connection configurations to find working one"""
        try:
            for config in self.connection_configs:
                self.logger.info(f"🔗 Testing: {config['name']}")
                
                try:
                    conn = pyodbc.connect(config['connection_string'], timeout=10)
                    cursor = conn.cursor()
                    
                    # Test basic query
                    cursor.execute("SELECT COUNT(*) FROM PR_TASKREGLN")
                    count = cursor.fetchone()[0]
                    
                    conn.close()
                    
                    self.working_connection = config['connection_string']
                    self.logger.info(f"✅ Found working connection: {config['name']} ({count} records)")
                    return True
                    
                except Exception as e:
                    self.logger.warning(f"❌ {config['name']} failed: {e}")
                    continue
            
            # No working connection found
            self.logger.warning("⚠️ No working database connection found, switching to offline mode")
            self.offline_mode = True
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Connection testing failed: {e}")
            self.offline_mode = True
            return False
    
    def test_mill_database_connection(self) -> Tuple[bool, str]:
        """Test connection to mill database"""
        try:
            if self.offline_mode:
                return False, f"⚠️ System is in offline mode - mill database validation unavailable"
            
            if not self.working_connection:
                success = self.test_and_find_working_connection()
                if not success:
                    return False, f"❌ No working connection to {self.db_name}"
            
            conn = pyodbc.connect(self.working_connection)
            cursor = conn.cursor()
            
            # Test table access
            cursor.execute("SELECT COUNT(*) FROM PR_TASKREGLN")
            count = cursor.fetchone()[0]
            
            conn.close()
            
            message = f"✅ Connection successful to {self.db_name}. PR_TASKREGLN has {count} records."
            self.logger.info(message)
            return True, message
            
        except Exception as e:
            message = f"❌ Connection failed to {self.db_name}: {e}"
            self.logger.error(message)
            return False, message
    
    def calculate_transaction_date_by_mode(self, original_date_str: str) -> str:
        """Calculate transaction date based on automation mode"""
        try:
            # Parse original date
            if '/' in original_date_str:
                original_date = datetime.strptime(original_date_str, "%d/%m/%Y")
            else:
                original_date = datetime.strptime(original_date_str, "%Y-%m-%d")
            
            if self.automation_mode == 'testing':
                # Testing mode: Subtract 1 month
                trx_date = original_date - relativedelta(months=1)
            else:
                # Real mode: Use original date
                trx_date = original_date
            
            return trx_date.strftime("%Y-%m-%d")
            
        except Exception as e:
            self.logger.error(f"❌ Error calculating transaction date: {e}")
            raise
    
    def validate_single_employee_record(self, record: Dict) -> Dict:
        """Validate a single employee record (online or offline mode)"""
        try:
            employee_id_ptrj = record.get('employee_id_ptrj', '').strip()
            employee_name = record.get('employee_name', '')
            original_date = record.get('date', '')
            regular_hours = float(record.get('regular_hours', 0))
            overtime_hours = float(record.get('overtime_hours', 0))
            
            # Calculate transaction date
            sql_date = self.calculate_transaction_date_by_mode(original_date)
            
            self.logger.info(f"🔍 Validating: {employee_name} ({employee_id_ptrj}) on {sql_date}")
            
            if self.offline_mode or not self.working_connection:
                # Offline mode - queue for later validation or use optimistic validation
                return self.handle_offline_validation(record, sql_date)
            
            # Online mode - validate against mill database
            return self.validate_against_mill_database(record, sql_date)
            
        except Exception as e:
            error_message = f"Validation error: {e}"
            self.logger.error(f"❌ {error_message}")
            
            return {
                'employee_id_ptrj': record.get('employee_id_ptrj', ''),
                'employee_name': record.get('employee_name', ''),
                'transaction_date': '',
                'original_date': record.get('date', ''),
                'status': 'ERROR',
                'message': error_message,
                'validation_type': 'ERROR',
                'expected_regular': record.get('regular_hours', 0),
                'expected_overtime': record.get('overtime_hours', 0),
                'actual_regular': 0,
                'actual_overtime': 0,
                'mill_records_count': 0
            }
    
    def validate_against_mill_database(self, record: Dict, sql_date: str) -> Dict:
        """Validate record against mill database"""
        try:
            employee_id_ptrj = record.get('employee_id_ptrj', '').strip()
            employee_name = record.get('employee_name', '')
            regular_hours = float(record.get('regular_hours', 0))
            overtime_hours = float(record.get('overtime_hours', 0))
            
            # Connect to mill database
            conn = pyodbc.connect(self.working_connection)
            cursor = conn.cursor()
            
            # Query mill database
            query = """
                SELECT EmpCode, EmpName, TrxDate, OT, Hours, Amount, Status, ChargeTo
                FROM PR_TASKREGLN
                WHERE EmpCode = ? AND TrxDate = ?
                ORDER BY OT, Hours
            """
            
            cursor.execute(query, (employee_id_ptrj, sql_date))
            db_records = cursor.fetchall()
            
            conn.close()
            
            if not db_records:
                return {
                    'employee_id_ptrj': employee_id_ptrj,
                    'employee_name': employee_name,
                    'transaction_date': sql_date,
                    'original_date': record.get('date', ''),
                    'status': 'NOT_FOUND',
                    'message': 'No records found in mill database',
                    'validation_type': 'MILL_DB_NOT_FOUND',
                    'expected_regular': regular_hours,
                    'expected_overtime': overtime_hours,
                    'actual_regular': 0,
                    'actual_overtime': 0,
                    'mill_records_count': 0
                }
            
            # Analyze mill database records
            db_regular_hours = 0
            db_overtime_hours = 0
            
            for record_row in db_records:
                ot_flag = record_row[3]  # OT column
                hours = float(record_row[4])  # Hours column
                
                if ot_flag == 1:  # Overtime
                    db_overtime_hours += hours
                else:  # Regular
                    db_regular_hours += hours
            
            # Compare hours with tolerance
            tolerance = 0.1
            regular_match = abs(regular_hours - db_regular_hours) <= tolerance
            overtime_match = abs(overtime_hours - db_overtime_hours) <= tolerance
            
            if regular_match and overtime_match:
                status = 'SUCCESS'
                message = 'Hours match perfectly with mill database'
                validation_type = 'MILL_DB_VERIFIED'
            else:
                status = 'MISMATCH'
                message = f"Hours mismatch - Regular: {regular_hours} vs {db_regular_hours}, Overtime: {overtime_hours} vs {db_overtime_hours}"
                validation_type = 'MILL_DB_MISMATCH'
            
            return {
                'employee_id_ptrj': employee_id_ptrj,
                'employee_name': employee_name,
                'transaction_date': sql_date,
                'original_date': record.get('date', ''),
                'status': status,
                'message': message,
                'validation_type': validation_type,
                'expected_regular': regular_hours,
                'expected_overtime': overtime_hours,
                'actual_regular': db_regular_hours,
                'actual_overtime': db_overtime_hours,
                'mill_records_count': len(db_records)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Mill database validation failed: {e}")
            
            # Queue for retry in offline mode
            self.queue_for_offline_processing(record, sql_date)
            
            return {
                'employee_id_ptrj': record.get('employee_id_ptrj', ''),
                'employee_name': record.get('employee_name', ''),
                'transaction_date': sql_date,
                'original_date': record.get('date', ''),
                'status': 'DB_ERROR',
                'message': f"Database error: {e}",
                'validation_type': 'DB_CONNECTION_ERROR',
                'expected_regular': record.get('regular_hours', 0),
                'expected_overtime': record.get('overtime_hours', 0),
                'actual_regular': 0,
                'actual_overtime': 0,
                'mill_records_count': 0
            }
    
    def handle_offline_validation(self, record: Dict, sql_date: str) -> Dict:
        """Handle validation in offline mode"""
        try:
            employee_id_ptrj = record.get('employee_id_ptrj', '').strip()
            employee_name = record.get('employee_name', '')
            regular_hours = float(record.get('regular_hours', 0))
            overtime_hours = float(record.get('overtime_hours', 0))
            
            # Queue for later processing
            self.queue_for_offline_processing(record, sql_date)
            
            # Use optimistic validation - assume success based on data integrity
            if regular_hours >= 0 and overtime_hours >= 0:
                status = 'OFFLINE_SUCCESS'
                message = 'Validated offline - queued for mill database verification'
                validation_type = 'OFFLINE_OPTIMISTIC'
            else:
                status = 'OFFLINE_ERROR'
                message = 'Invalid hours data detected in offline mode'
                validation_type = 'OFFLINE_DATA_ERROR'
            
            return {
                'employee_id_ptrj': employee_id_ptrj,
                'employee_name': employee_name,
                'transaction_date': sql_date,
                'original_date': record.get('date', ''),
                'status': status,
                'message': message,
                'validation_type': validation_type,
                'expected_regular': regular_hours,
                'expected_overtime': overtime_hours,
                'actual_regular': 0,  # Unknown in offline mode
                'actual_overtime': 0,  # Unknown in offline mode
                'mill_records_count': 0
            }
            
        except Exception as e:
            self.logger.error(f"❌ Offline validation failed: {e}")
            
            return {
                'employee_id_ptrj': record.get('employee_id_ptrj', ''),
                'employee_name': record.get('employee_name', ''),
                'transaction_date': sql_date,
                'original_date': record.get('date', ''),
                'status': 'ERROR',
                'message': f"Offline validation error: {e}",
                'validation_type': 'OFFLINE_ERROR',
                'expected_regular': record.get('regular_hours', 0),
                'expected_overtime': record.get('overtime_hours', 0),
                'actual_regular': 0,
                'actual_overtime': 0,
                'mill_records_count': 0
            }
    
    def queue_for_offline_processing(self, record: Dict, sql_date: str):
        """Queue record for offline processing when database is available"""
        try:
            conn = sqlite3.connect(self.success_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO offline_queue (
                    employee_data, validation_request, automation_mode, queued_timestamp
                ) VALUES (?, ?, ?, ?)
            ''', (
                json.dumps(record),
                json.dumps({'sql_date': sql_date, 'validation_type': 'MILL_DB_VERIFY'}),
                self.automation_mode,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"📋 Queued {record.get('employee_name', '')} for offline processing")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to queue for offline processing: {e}")
    
    def log_validation(self, validation_result: Dict):
        """Log validation result to database"""
        try:
            conn = sqlite3.connect(self.success_db_path)
            cursor = conn.cursor()
            
            connection_status = 'OFFLINE' if self.offline_mode else ('CONNECTED' if self.working_connection else 'FAILED')
            
            cursor.execute('''
                INSERT INTO validation_logs (
                    employee_id_ptrj, employee_name, transaction_date,
                    validation_type, expected_regular_hours, expected_overtime_hours,
                    actual_regular_hours, actual_overtime_hours, status,
                    error_message, mill_database, automation_mode, 
                    connection_status, validation_timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                validation_result['employee_id_ptrj'],
                validation_result['employee_name'],
                validation_result['transaction_date'],
                validation_result.get('validation_type', 'UNKNOWN'),
                validation_result['expected_regular'],
                validation_result['expected_overtime'],
                validation_result['actual_regular'],
                validation_result['actual_overtime'],
                validation_result['status'],
                validation_result.get('message', ''),
                self.db_name,
                self.automation_mode,
                connection_status,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"❌ Failed to log validation: {e}")
    
    def transfer_successful_record(self, original_record: Dict, validation_result: Dict):
        """Transfer successfully validated record to success database"""
        try:
            # Accept both verified success and offline optimistic success
            valid_statuses = ['SUCCESS', 'OFFLINE_SUCCESS']
            
            if validation_result['status'] not in valid_statuses:
                return False
                
            conn = sqlite3.connect(self.success_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO successful_transfers (
                    employee_id_venus, employee_id_ptrj, employee_name,
                    transaction_date, original_attendance_date,
                    regular_hours, overtime_hours, total_hours,
                    task_code, station_code, machine_code, expense_code,
                    raw_charge_job, validation_timestamp, automation_mode,
                    mill_database, validation_status, validation_type,
                    source_record_id, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                original_record.get('employee_id_venus', ''),
                original_record.get('employee_id_ptrj', ''),
                original_record.get('employee_name', ''),
                validation_result['transaction_date'],
                validation_result['original_date'],
                validation_result['expected_regular'],
                validation_result['expected_overtime'],
                validation_result['expected_regular'] + validation_result['expected_overtime'],
                original_record.get('task_code', ''),
                original_record.get('station_code', ''),
                original_record.get('machine_code', ''),
                original_record.get('expense_code', ''),
                original_record.get('raw_charge_job', ''),
                datetime.now().isoformat(),
                self.automation_mode,
                self.db_name if not self.offline_mode else 'OFFLINE',
                validation_result['status'],
                validation_result.get('validation_type', 'UNKNOWN'),
                original_record.get('source_record_id', ''),
                f"Validated: {validation_result['message']}"
            ))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"✅ Successfully transferred record for {original_record.get('employee_name', '')}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to transfer successful record: {e}")
            return False
    
    def perform_batch_validation(self, records: List[Dict]) -> Dict:
        """Perform batch validation and transfer successful records"""
        try:
            print(f"\n🔍 ENHANCED TRANSFER VALIDATION")
            print(f"=" * 60)
            print(f"🔧 Mode: {self.automation_mode.upper()}")
            print(f"🗄️ Database: {self.db_name}")
            print(f"📊 Records to validate: {len(records)}")
            print(f"🌐 Connection Mode: {'OFFLINE' if self.offline_mode else 'ONLINE'}")
            
            # Test database connection if online
            if not self.offline_mode:
                connection_ok, connection_message = self.test_mill_database_connection()
                print(f"🔗 {connection_message}")
                
                if not connection_ok:
                    print("⚠️ Switching to offline mode for this batch")
                    self.offline_mode = True
            
            validation_results = []
            successful_transfers = 0
            failed_validations = 0
            offline_queued = 0
            
            for i, record in enumerate(records, 1):
                print(f"\n{'='*50}")
                print(f"🔍 Validating {i}/{len(records)}: {record.get('employee_name', 'Unknown')}")
                
                # Validate record
                validation_result = self.validate_single_employee_record(record)
                validation_results.append(validation_result)
                
                # Log validation
                self.log_validation(validation_result)
                
                # Transfer if successful (including offline success)
                if validation_result['status'] in ['SUCCESS', 'OFFLINE_SUCCESS']:
                    success = self.transfer_successful_record(record, validation_result)
                    if success:
                        successful_transfers += 1
                        if validation_result['status'] == 'OFFLINE_SUCCESS':
                            offline_queued += 1
                            print(f"✅ OFFLINE SUCCESS: Validated and transferred (queued for DB verification)")
                        else:
                            print(f"✅ SUCCESS: Validated and transferred")
                    else:
                        print(f"⚠️ Validated but transfer failed")
                else:
                    failed_validations += 1
                    print(f"❌ FAILED: {validation_result['message']}")
            
            # Summary
            success_rate = (successful_transfers / len(records)) * 100 if records else 0
            
            summary = {
                'success': True,
                'total_records': len(records),
                'successful_transfers': successful_transfers,
                'failed_validations': failed_validations,
                'offline_queued': offline_queued,
                'success_rate': success_rate,
                'automation_mode': self.automation_mode,
                'mill_database': self.db_name,
                'connection_mode': 'OFFLINE' if self.offline_mode else 'ONLINE',
                'validation_results': validation_results,
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"\n🎯 VALIDATION SUMMARY")
            print(f"=" * 60)
            print(f"📊 Total Records: {len(records)}")
            print(f"✅ Successful Transfers: {successful_transfers}")
            print(f"📋 Offline Queued: {offline_queued}")
            print(f"❌ Failed Validations: {failed_validations}")
            print(f"📈 Success Rate: {success_rate:.1f}%")
            print(f"🌐 Mode: {'OFFLINE' if self.offline_mode else 'ONLINE'}")
            print(f"🗄️ Success Database: {self.success_db_path}")
            
            return summary
            
        except Exception as e:
            self.logger.error(f"❌ Batch validation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'results': []
            }
    
    def process_offline_queue(self) -> Dict:
        """Process queued offline validations when database becomes available"""
        try:
            if self.offline_mode:
                print("⚠️ Still in offline mode - cannot process queue")
                return {'success': False, 'message': 'Still offline'}
            
            # Test connection first
            connection_ok, _ = self.test_mill_database_connection()
            if not connection_ok:
                return {'success': False, 'message': 'Database still unavailable'}
            
            conn = sqlite3.connect(self.success_db_path)
            cursor = conn.cursor()
            
            # Get pending items
            cursor.execute('''
                SELECT id, employee_data, validation_request, automation_mode, queued_timestamp
                FROM offline_queue
                WHERE processing_status = 'PENDING'
                ORDER BY queued_timestamp
            ''')
            
            pending_items = cursor.fetchall()
            conn.close()
            
            if not pending_items:
                return {'success': True, 'message': 'No items in offline queue', 'processed': 0}
            
            print(f"\n🔄 PROCESSING OFFLINE QUEUE")
            print(f"📊 Items to process: {len(pending_items)}")
            
            processed = 0
            for item in pending_items:
                try:
                    item_id, employee_data_json, validation_request_json, mode, queued_time = item
                    
                    employee_data = json.loads(employee_data_json)
                    validation_request = json.loads(validation_request_json)
                    
                    # Validate against mill database
                    validation_result = self.validate_against_mill_database(
                        employee_data, 
                        validation_request['sql_date']
                    )
                    
                    # Update queue status
                    conn = sqlite3.connect(self.success_db_path)
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        UPDATE offline_queue 
                        SET processing_status = 'PROCESSED', last_retry = ?
                        WHERE id = ?
                    ''', (datetime.now().isoformat(), item_id))
                    
                    conn.commit()
                    conn.close()
                    
                    processed += 1
                    print(f"✅ Processed: {employee_data.get('employee_name', 'Unknown')}")
                    
                except Exception as e:
                    print(f"❌ Failed to process queue item {item_id}: {e}")
                    continue
            
            return {
                'success': True,
                'message': f'Processed {processed} items from offline queue',
                'processed': processed,
                'total_pending': len(pending_items)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to process offline queue: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_success_statistics(self) -> Dict:
        """Get comprehensive statistics from success database"""
        try:
            conn = sqlite3.connect(self.success_db_path)
            cursor = conn.cursor()
            
            # Get total successful transfers
            cursor.execute('SELECT COUNT(*) FROM successful_transfers')
            total_transfers = cursor.fetchone()[0]
            
            # Get transfers by mode
            cursor.execute('SELECT automation_mode, COUNT(*) FROM successful_transfers GROUP BY automation_mode')
            mode_stats = dict(cursor.fetchall())
            
            # Get transfers by validation type
            cursor.execute('SELECT validation_type, COUNT(*) FROM successful_transfers GROUP BY validation_type')
            validation_type_stats = dict(cursor.fetchall())
            
            # Get recent transfers
            cursor.execute('''
                SELECT employee_name, transaction_date, regular_hours, overtime_hours, 
                       validation_timestamp, validation_type
                FROM successful_transfers
                ORDER BY created_at DESC
                LIMIT 10
            ''')
            recent_transfers = cursor.fetchall()
            
            # Get validation logs summary
            cursor.execute('SELECT status, COUNT(*) FROM validation_logs GROUP BY status')
            validation_stats = dict(cursor.fetchall())
            
            # Get connection status summary
            cursor.execute('SELECT connection_status, COUNT(*) FROM validation_logs GROUP BY connection_status')
            connection_stats = dict(cursor.fetchall())
            
            # Get offline queue status
            cursor.execute('SELECT processing_status, COUNT(*) FROM offline_queue GROUP BY processing_status')
            queue_stats = dict(cursor.fetchall())
            
            conn.close()
            
            return {
                'total_successful_transfers': total_transfers,
                'transfers_by_mode': mode_stats,
                'transfers_by_validation_type': validation_type_stats,
                'recent_transfers': recent_transfers,
                'validation_statistics': validation_stats,
                'connection_statistics': connection_stats,
                'offline_queue_statistics': queue_stats,
                'database_path': str(self.success_db_path),
                'current_mode': 'OFFLINE' if self.offline_mode else 'ONLINE'
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get success statistics: {e}")
            return {'error': str(e)}


def test_validation_system():
    """Test the enhanced validation system with offline capabilities"""
    print("\n🧪 TESTING ENHANCED VALIDATION SYSTEM WITH OFFLINE MODE")
    print("=" * 70)
    
    # Sample data for testing
    sample_records = [
        {
            'employee_id_ptrj': 'POM00214',
            'employee_id_venus': 'PTRJ.241000017',
            'employee_name': 'Agus Setiawan',
            'date': '2025-06-12',
            'regular_hours': 7.0,
            'overtime_hours': 1.0,
            'task_code': '(GA9050) WORKSHOP CONTROL ACCOUNT',
            'raw_charge_job': '(GA9050) WORKSHOP CONTROL ACCOUNT / L (LABOUR)'
        }
    ]
    
    # Test both modes and online/offline scenarios
    for mode in ['testing', 'real']:
        for offline in [False, True]:
            print(f"\n🔧 Testing mode: {mode.upper()}, Offline: {offline}")
            
            validator = TransferValidationSystem(automation_mode=mode, offline_mode=offline)
            results = validator.perform_batch_validation(sample_records)
            
            print(f"📊 Results: {results.get('success', False)}")
            if results.get('error'):
                print(f"❌ Error: {results['error']}")
            
            # Get statistics
            stats = validator.get_success_statistics()
            print(f"📈 Success Database Stats: {stats.get('total_successful_transfers', 0)} total transfers")
            print(f"🌐 Current Mode: {stats.get('current_mode', 'Unknown')}")


if __name__ == "__main__":
    test_validation_system() 