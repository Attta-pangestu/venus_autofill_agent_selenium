#!/usr/bin/env python3
"""
Database Manager for Staging Attendance Database

This module provides direct database access to staging_attendance.db,
replacing the previous API-based data fetching approach.
"""

import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

class DatabaseManager:
    """Manages direct SQLite database connections and operations for staging attendance data"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        
        # Set default database path if not provided
        if db_path is None:
            self.db_path = Path(__file__).parent.parent.parent / "data" / "staging_attendance.db"
        else:
            self.db_path = Path(db_path)
        
        self.logger.info(f"🗄️ Database Manager initialized with path: {self.db_path}")
        
        # Verify database exists
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database file not found: {self.db_path}")
    
    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection with proper configuration"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row  # Enable column access by name
            return conn
        except Exception as e:
            self.logger.error(f"❌ Error connecting to database: {e}")
            raise
    
    def fetch_all_staging_data(self, status: str = 'staged') -> List[Dict[str, Any]]:
        """Fetch all staging attendance data from database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                SELECT 
                    id,
                    employee_id,
                    employee_name,
                    date,
                    day_of_week,
                    shift,
                    check_in,
                    check_out,
                    regular_hours,
                    overtime_hours,
                    total_hours,
                    task_code,
                    station_code,
                    machine_code,
                    expense_code,
                    status,
                    created_at,
                    updated_at,
                    source_record_id,
                    notes,
                    raw_charge_job,
                    leave_type_code,
                    leave_type_description,
                    leave_ref_number,
                    is_alfa,
                    is_on_leave,
                    ptrj_employee_id
                FROM staging_attendance
                WHERE status = ?
                ORDER BY employee_name, date
                """
                
                cursor.execute(query, (status,))
                rows = cursor.fetchall()
                
                # Convert rows to dictionaries
                data = []
                for row in rows:
                    record = dict(row)
                    # Convert boolean fields
                    record['is_alfa'] = bool(record['is_alfa'])
                    record['is_on_leave'] = bool(record['is_on_leave'])
                    data.append(record)
                
                self.logger.info(f"📊 Fetched {len(data)} staging records from database")
                return data
                
        except Exception as e:
            self.logger.error(f"❌ Error fetching staging data: {e}")
            return []
    
    def fetch_grouped_staging_data(self, status: str = 'staged') -> List[Dict[str, Any]]:
        """Fetch staging data grouped by employee (mimics API grouped response)"""
        try:
            # First get all data
            all_data = self.fetch_all_staging_data(status)
            
            if not all_data:
                return []
            
            # Group by employee
            grouped_data = {}
            
            for record in all_data:
                employee_name = record['employee_name']
                employee_id = record['employee_id']
                ptrj_employee_id = record.get('ptrj_employee_id', 'N/A')
                
                if employee_name not in grouped_data:
                    grouped_data[employee_name] = {
                        'employee_name': employee_name,
                        'employee_id': employee_id,
                        'ptrj_employee_id': ptrj_employee_id,
                        'data_presensi': []
                    }
                
                # Add attendance record
                attendance_record = {
                    'id': record['id'],
                    'date': record['date'],
                    'day_of_week': record['day_of_week'],
                    'shift': record['shift'],
                    'check_in': record['check_in'],
                    'check_out': record['check_out'],
                    'regular_hours': record['regular_hours'],
                    'overtime_hours': record['overtime_hours'],
                    'total_hours': record['total_hours'],
                    'task_code': record['task_code'],
                    'station_code': record['station_code'],
                    'machine_code': record['machine_code'],
                    'expense_code': record['expense_code'],
                    'raw_charge_job': record['raw_charge_job'],
                    'leave_type_code': record['leave_type_code'],
                    'leave_type_description': record['leave_type_description'],
                    'leave_ref_number': record['leave_ref_number'],
                    'is_alfa': record['is_alfa'],
                    'is_on_leave': record['is_on_leave'],
                    'notes': record['notes'],
                    'source_record_id': record['source_record_id']
                }
                
                grouped_data[employee_name]['data_presensi'].append(attendance_record)
            
            # Convert to list format (similar to API response)
            result = list(grouped_data.values())
            
            total_employees = len(result)
            total_records = sum(len(emp['data_presensi']) for emp in result)
            
            self.logger.info(f"📊 Grouped data: {total_employees} employees, {total_records} attendance records")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Error fetching grouped staging data: {e}")
            return []
    
    def get_employee_data(self, employee_name: str = None, employee_id: str = None, 
                         ptrj_employee_id: str = None) -> List[Dict[str, Any]]:
        """Get data for specific employee by name, ID, or PTRJ ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                conditions = []
                params = []
                
                if employee_name:
                    conditions.append("employee_name = ?")
                    params.append(employee_name)
                
                if employee_id:
                    conditions.append("employee_id = ?")
                    params.append(employee_id)
                
                if ptrj_employee_id:
                    conditions.append("ptrj_employee_id = ?")
                    params.append(ptrj_employee_id)
                
                if not conditions:
                    self.logger.warning("⚠️ No search criteria provided for employee data")
                    return []
                
                query = f"""
                SELECT * FROM staging_attendance
                WHERE {' OR '.join(conditions)}
                ORDER BY date
                """
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                data = [dict(row) for row in rows]
                self.logger.info(f"📊 Found {len(data)} records for employee criteria")
                
                return data
                
        except Exception as e:
            self.logger.error(f"❌ Error fetching employee data: {e}")
            return []
    
    def update_record_status(self, record_id: str, new_status: str) -> bool:
        """Update the status of a specific record"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    "UPDATE staging_attendance SET status = ?, updated_at = ? WHERE id = ?",
                    (new_status, datetime.now().isoformat(), record_id)
                )
                
                if cursor.rowcount > 0:
                    conn.commit()
                    self.logger.info(f"✅ Updated record {record_id} status to {new_status}")
                    return True
                else:
                    self.logger.warning(f"⚠️ No record found with ID: {record_id}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"❌ Error updating record status: {e}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Total records
                cursor.execute("SELECT COUNT(*) FROM staging_attendance")
                total_records = cursor.fetchone()[0]
                
                # Records by status
                cursor.execute("SELECT status, COUNT(*) FROM staging_attendance GROUP BY status")
                status_counts = dict(cursor.fetchall())
                
                # Unique employees
                cursor.execute("SELECT COUNT(DISTINCT employee_name) FROM staging_attendance")
                unique_employees = cursor.fetchone()[0]
                
                # Date range
                cursor.execute("SELECT MIN(date), MAX(date) FROM staging_attendance")
                date_range = cursor.fetchone()
                
                stats = {
                    'total_records': total_records,
                    'status_counts': status_counts,
                    'unique_employees': unique_employees,
                    'date_range': {
                        'earliest': date_range[0],
                        'latest': date_range[1]
                    },
                    'database_path': str(self.db_path)
                }
                
                self.logger.info(f"📊 Database stats: {total_records} records, {unique_employees} employees")
                return stats
                
        except Exception as e:
            self.logger.error(f"❌ Error getting database stats: {e}")
            return {}
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                
                if result and result[0] == 1:
                    self.logger.info("✅ Database connection test successful")
                    return True
                else:
                    self.logger.error("❌ Database connection test failed")
                    return False
                    
        except Exception as e:
            self.logger.error(f"❌ Database connection test error: {e}")
            return False

# Example usage and testing
if __name__ == "__main__":
    # Initialize logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Test database manager
        db_manager = DatabaseManager()
        
        # Test connection
        if db_manager.test_connection():
            print("✅ Database connection successful")
            
            # Get stats
            stats = db_manager.get_database_stats()
            print(f"📊 Database Stats: {json.dumps(stats, indent=2)}")
            
            # Test grouped data fetch
            grouped_data = db_manager.fetch_grouped_staging_data()
            print(f"📊 Grouped data: {len(grouped_data)} employee groups")
            
        else:
            print("❌ Database connection failed")
            
    except Exception as e:
        print(f"❌ Error testing database manager: {e}")
        import traceback
        traceback.print_exc()