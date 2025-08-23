#!/usr/bin/env python3
"""
Transfer History Manager - Venus AutoFill
Comprehensive SQLite database management for transfer history and data lifecycle

Features:
- SQLite database for storing successful transfers
- Complete audit trail with validation results
- Data filtering and lifecycle management
- Performance optimized queries with indexing
"""

import sqlite3
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import hashlib

class TransferHistoryManager:
    """
    Manages the transfer history database for Venus AutoFill system
    Handles successful transfers, validation results, and data lifecycle
    """
    
    def __init__(self, db_path: str = "database/transfer_history.db"):
        """Initialize the transfer history manager"""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database with proper schema"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create transfer_history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transfer_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    record_hash TEXT UNIQUE NOT NULL,
                    employee_id_venus TEXT,
                    employee_id_ptrj TEXT NOT NULL,
                    employee_name TEXT NOT NULL,
                    attendance_date TEXT NOT NULL,
                    regular_hours REAL NOT NULL,
                    overtime_hours REAL NOT NULL,
                    total_hours REAL NOT NULL,
                    task_code TEXT,
                    station_code TEXT,
                    machine_code TEXT,
                    expense_code TEXT,
                    raw_charge_job TEXT,
                    automation_mode TEXT NOT NULL,
                    mill_database TEXT NOT NULL,
                    transfer_timestamp TEXT NOT NULL,
                    validation_status TEXT NOT NULL,
                    validation_details TEXT,
                    original_staging_data TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create validation_results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS validation_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transfer_id INTEGER NOT NULL,
                    validation_type TEXT NOT NULL,
                    expected_regular REAL,
                    expected_overtime REAL,
                    actual_regular REAL,
                    actual_overtime REAL,
                    regular_diff REAL,
                    overtime_diff REAL,
                    tolerance REAL,
                    status TEXT NOT NULL,
                    message TEXT,
                    validation_timestamp TEXT NOT NULL,
                    FOREIGN KEY (transfer_id) REFERENCES transfer_history (id)
                )
            """)
            
            # Create transfer_statistics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transfer_statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    automation_mode TEXT NOT NULL,
                    total_transfers INTEGER DEFAULT 0,
                    successful_validations INTEGER DEFAULT 0,
                    failed_validations INTEGER DEFAULT 0,
                    total_regular_hours REAL DEFAULT 0,
                    total_overtime_hours REAL DEFAULT 0,
                    unique_employees INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date, automation_mode)
                )
            """)
            
            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_employee_id_ptrj ON transfer_history (employee_id_ptrj)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_date ON transfer_history (attendance_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transfer_timestamp ON transfer_history (transfer_timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_automation_mode ON transfer_history (automation_mode)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_validation_status ON transfer_history (validation_status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_record_hash ON transfer_history (record_hash)")
            
            conn.commit()
            conn.close()
            
            self.logger.info("✅ Transfer history database initialized successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize transfer history database: {e}")
            raise
    
    def _generate_record_hash(self, record: Dict) -> str:
        """Generate a unique hash for a record to prevent duplicates"""
        # Create hash based on key identifying fields
        hash_data = {
            'employee_id_ptrj': record.get('employee_id_ptrj', ''),
            'attendance_date': record.get('date', ''),
            'regular_hours': float(record.get('regular_hours', 0)),
            'overtime_hours': float(record.get('overtime_hours', 0))
        }
        
        hash_string = json.dumps(hash_data, sort_keys=True)
        return hashlib.md5(hash_string.encode()).hexdigest()
    
    def store_successful_transfer(self, record: Dict, validation_result: Dict, 
                                automation_mode: str = 'testing') -> bool:
        """
        Store a successful transfer record with validation results
        
        Args:
            record: Original staging data record
            validation_result: POM validation result
            automation_mode: 'testing' or 'real'
            
        Returns:
            bool: True if stored successfully, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Generate record hash
            record_hash = self._generate_record_hash(record)
            
            # Check if record already exists
            cursor.execute("SELECT id FROM transfer_history WHERE record_hash = ?", (record_hash,))
            existing = cursor.fetchone()
            
            if existing:
                self.logger.warning(f"⚠️ Transfer record already exists: {record.get('employee_name', '')} on {record.get('date', '')}")
                conn.close()
                return False
            
            # Determine mill database based on automation mode
            mill_database = "db_ptrj_mill_test" if automation_mode == 'testing' else "db_ptrj_mill"
            
            # Insert transfer record
            transfer_data = (
                record_hash,
                record.get('employee_id', ''),
                record.get('employee_id_ptrj', ''),
                record.get('employee_name', ''),
                record.get('date', ''),
                float(record.get('regular_hours', 0)),
                float(record.get('overtime_hours', 0)),
                float(record.get('total_hours', 0)),
                record.get('task_code', ''),
                record.get('station_code', ''),
                record.get('machine_code', ''),
                record.get('expense_code', ''),
                record.get('raw_charge_job', ''),
                automation_mode,
                mill_database,
                datetime.now(timezone.utc).isoformat(),
                validation_result.get('status', 'UNKNOWN'),
                json.dumps(validation_result),
                json.dumps(record)
            )
            
            cursor.execute("""
                INSERT INTO transfer_history (
                    record_hash, employee_id_venus, employee_id_ptrj, employee_name,
                    attendance_date, regular_hours, overtime_hours, total_hours,
                    task_code, station_code, machine_code, expense_code, raw_charge_job,
                    automation_mode, mill_database, transfer_timestamp,
                    validation_status, validation_details, original_staging_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, transfer_data)
            
            transfer_id = cursor.lastrowid
            
            # Store detailed validation results
            if validation_result.get('status') == 'SUCCESS':
                validation_data = (
                    transfer_id,
                    'POM_VALIDATION',
                    validation_result.get('expected_regular', 0),
                    validation_result.get('expected_overtime', 0),
                    validation_result.get('actual_regular', 0),
                    validation_result.get('actual_overtime', 0),
                    validation_result.get('regular_diff', 0),
                    validation_result.get('overtime_diff', 0),
                    validation_result.get('tolerance', 0.1),
                    validation_result.get('status', 'UNKNOWN'),
                    validation_result.get('message', ''),
                    datetime.now(timezone.utc).isoformat()
                )
                
                cursor.execute("""
                    INSERT INTO validation_results (
                        transfer_id, validation_type, expected_regular, expected_overtime,
                        actual_regular, actual_overtime, regular_diff, overtime_diff,
                        tolerance, status, message, validation_timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, validation_data)
            
            # Update statistics
            self._update_statistics(cursor, record, automation_mode)
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"✅ Successfully stored transfer: {record.get('employee_name', '')} ({record.get('employee_id_ptrj', '')})")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to store transfer record: {e}")
            return False
    
    def _update_statistics(self, cursor, record: Dict, automation_mode: str):
        """Update daily transfer statistics"""
        try:
            today = datetime.now().date().isoformat()
            
            # Get current stats
            cursor.execute("""
                SELECT total_transfers, successful_validations, total_regular_hours, 
                       total_overtime_hours, unique_employees
                FROM transfer_statistics 
                WHERE date = ? AND automation_mode = ?
            """, (today, automation_mode))
            
            current_stats = cursor.fetchone()
            
            if current_stats:
                # Update existing stats
                new_total = current_stats[0] + 1
                new_successful = current_stats[1] + 1
                new_regular_hours = current_stats[2] + float(record.get('regular_hours', 0))
                new_overtime_hours = current_stats[3] + float(record.get('overtime_hours', 0))
                
                # Count unique employees
                cursor.execute("""
                    SELECT COUNT(DISTINCT employee_id_ptrj) 
                    FROM transfer_history 
                    WHERE DATE(transfer_timestamp) = ? AND automation_mode = ?
                """, (today, automation_mode))
                unique_employees = cursor.fetchone()[0]
                
                cursor.execute("""
                    UPDATE transfer_statistics 
                    SET total_transfers = ?, successful_validations = ?, 
                        total_regular_hours = ?, total_overtime_hours = ?,
                        unique_employees = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE date = ? AND automation_mode = ?
                """, (new_total, new_successful, new_regular_hours, new_overtime_hours,
                      unique_employees, today, automation_mode))
            else:
                # Create new stats entry
                cursor.execute("""
                    INSERT INTO transfer_statistics (
                        date, automation_mode, total_transfers, successful_validations,
                        total_regular_hours, total_overtime_hours, unique_employees
                    ) VALUES (?, ?, 1, 1, ?, ?, 1)
                """, (today, automation_mode, float(record.get('regular_hours', 0)),
                      float(record.get('overtime_hours', 0))))
                
        except Exception as e:
            self.logger.error(f"❌ Failed to update statistics: {e}")
    
    def get_transferred_record_hashes(self) -> List[str]:
        """Get all record hashes for transferred records (for filtering staging data)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT record_hash FROM transfer_history")
            hashes = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            return hashes
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get transferred record hashes: {e}")
            return []
    
    def is_record_transferred(self, record: Dict) -> bool:
        """Check if a specific record has already been transferred"""
        try:
            record_hash = self._generate_record_hash(record)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM transfer_history WHERE record_hash = ?", (record_hash,))
            exists = cursor.fetchone() is not None
            
            conn.close()
            return exists
            
        except Exception as e:
            self.logger.error(f"❌ Failed to check record transfer status: {e}")
            return False
    
    def get_transfer_history(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get transfer history records with pagination"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT th.*, vr.status as validation_status_detail,
                       vr.expected_regular, vr.expected_overtime,
                       vr.actual_regular, vr.actual_overtime,
                       vr.regular_diff, vr.overtime_diff
                FROM transfer_history th
                LEFT JOIN validation_results vr ON th.id = vr.transfer_id
                ORDER BY th.transfer_timestamp DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
            
            columns = [description[0] for description in cursor.description]
            records = []
            
            for row in cursor.fetchall():
                record = dict(zip(columns, row))
                
                # Parse JSON fields
                try:
                    if record['validation_details']:
                        record['validation_details'] = json.loads(record['validation_details'])
                    if record['original_staging_data']:
                        record['original_staging_data'] = json.loads(record['original_staging_data'])
                except:
                    pass
                
                records.append(record)
            
            conn.close()
            return records
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get transfer history: {e}")
            return []
    
    def get_transfer_statistics(self, days: int = 30) -> Dict:
        """Get transfer statistics for the last N days"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get recent statistics
            cursor.execute("""
                SELECT automation_mode, 
                       SUM(total_transfers) as total_transfers,
                       SUM(successful_validations) as successful_validations,
                       SUM(failed_validations) as failed_validations,
                       SUM(total_regular_hours) as total_regular_hours,
                       SUM(total_overtime_hours) as total_overtime_hours,
                       SUM(unique_employees) as total_unique_employees
                FROM transfer_statistics 
                WHERE date >= date('now', '-{} days')
                GROUP BY automation_mode
            """.format(days))
            
            stats_by_mode = {}
            for row in cursor.fetchall():
                mode = row[0]
                stats_by_mode[mode] = {
                    'total_transfers': row[1] or 0,
                    'successful_validations': row[2] or 0,
                    'failed_validations': row[3] or 0,
                    'total_regular_hours': row[4] or 0,
                    'total_overtime_hours': row[5] or 0,
                    'unique_employees': row[6] or 0
                }
            
            # Get today's statistics
            cursor.execute("""
                SELECT automation_mode, total_transfers, successful_validations,
                       total_regular_hours, total_overtime_hours, unique_employees
                FROM transfer_statistics 
                WHERE date = date('now')
            """)
            
            today_stats = {}
            for row in cursor.fetchall():
                mode = row[0]
                today_stats[mode] = {
                    'total_transfers': row[1] or 0,
                    'successful_validations': row[2] or 0,
                    'total_regular_hours': row[3] or 0,
                    'total_overtime_hours': row[4] or 0,
                    'unique_employees': row[5] or 0
                }
            
            conn.close()
            
            return {
                'period_days': days,
                'period_stats': stats_by_mode,
                'today_stats': today_stats,
                'generated_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get transfer statistics: {e}")
            return {}
    
    def filter_staging_data(self, staging_records: List[Dict]) -> List[Dict]:
        """
        Filter out already transferred records from staging data
        
        Args:
            staging_records: List of staging data records
            
        Returns:
            List of records that haven't been transferred yet
        """
        try:
            if not staging_records:
                return []
            
            # Get all transferred record hashes
            transferred_hashes = set(self.get_transferred_record_hashes())
            
            # Filter out transferred records
            filtered_records = []
            for record in staging_records:
                record_hash = self._generate_record_hash(record)
                if record_hash not in transferred_hashes:
                    filtered_records.append(record)
                else:
                    self.logger.debug(f"🔄 Filtered out transferred record: {record.get('employee_name', '')} on {record.get('date', '')}")
            
            self.logger.info(f"🔄 Filtered staging data: {len(staging_records)} → {len(filtered_records)} records (removed {len(staging_records) - len(filtered_records)} transferred)")
            
            return filtered_records
            
        except Exception as e:
            self.logger.error(f"❌ Failed to filter staging data: {e}")
            return staging_records  # Return original data on error
    
    def get_database_info(self) -> Dict:
        """Get database information and health status"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get table counts
            cursor.execute("SELECT COUNT(*) FROM transfer_history")
            total_transfers = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM validation_results")
            total_validations = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM transfer_statistics")
            total_stats_entries = cursor.fetchone()[0]
            
            # Get database size
            cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
            db_size = cursor.fetchone()[0]
            
            # Get latest transfer
            cursor.execute("SELECT transfer_timestamp FROM transfer_history ORDER BY transfer_timestamp DESC LIMIT 1")
            latest_transfer = cursor.fetchone()
            latest_transfer = latest_transfer[0] if latest_transfer else None
            
            conn.close()
            
            return {
                'database_path': str(self.db_path),
                'database_size_bytes': db_size,
                'database_size_mb': round(db_size / (1024 * 1024), 2),
                'total_transfers': total_transfers,
                'total_validations': total_validations,
                'total_statistics_entries': total_stats_entries,
                'latest_transfer': latest_transfer,
                'status': 'healthy'
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get database info: {e}")
            return {
                'database_path': str(self.db_path),
                'status': 'error',
                'error': str(e)
            }

# Global instance for easy access
transfer_history_manager = TransferHistoryManager()

if __name__ == "__main__":
    # Test the transfer history manager
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 Testing Transfer History Manager")
    print("="*50)
    
    # Test database initialization
    manager = TransferHistoryManager("database/test_transfer_history.db")
    
    # Test record creation
    test_record = {
        'employee_id': 'VEN00123',
        'employee_id_ptrj': 'POM00214',
        'employee_name': 'AGUS SETIAWAN',
        'date': '13/05/2025',
        'regular_hours': 7.0,
        'overtime_hours': 7.5,
        'total_hours': 14.5,
        'task_code': 'TSK001'
    }
    
    test_validation = {
        'status': 'SUCCESS',
        'expected_regular': 7.0,
        'expected_overtime': 7.5,
        'actual_regular': 7.0,
        'actual_overtime': 7.5,
        'regular_diff': 0.0,
        'overtime_diff': 0.0,
        'tolerance': 0.1,
        'message': 'Test validation passed'
    }
    
    # Test storing transfer
    success = manager.store_successful_transfer(test_record, test_validation, 'testing')
    print(f"Store transfer: {'✅ SUCCESS' if success else '❌ FAILED'}")
    
    # Test filtering
    staging_data = [test_record, {
        'employee_id': 'VEN00124',
        'employee_id_ptrj': 'POM00215',
        'employee_name': 'BUDI SANTOSO',
        'date': '14/05/2025',
        'regular_hours': 8.0,
        'overtime_hours': 2.0,
        'total_hours': 10.0
    }]
    
    filtered = manager.filter_staging_data(staging_data)
    print(f"Filter staging data: {len(staging_data)} → {len(filtered)} records")
    
    # Test statistics
    stats = manager.get_transfer_statistics()
    print(f"Statistics: {stats}")
    
    # Test database info
    info = manager.get_database_info()
    print(f"Database info: {info}")
    
    print("\n✅ Transfer History Manager test completed!") 