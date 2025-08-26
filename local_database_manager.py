#!/usr/bin/env python3
"""
Local Database Manager for Staging Attendance Database

This module provides direct database access to staging_attendance.db,
with functionality to insert sample records and manage local data operations.
"""

import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import uuid

class LocalDatabaseManager:
    """Manages direct SQLite database connections and operations for staging attendance data"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        
        # Set default database path if not provided
        if db_path is None:
            self.db_path = Path(__file__).parent / "data" / "staging_attendance.db"
        else:
            self.db_path = Path(db_path)
        
        self.logger.info(f"🗄️ Local Database Manager initialized with path: {self.db_path}")
        
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
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM staging_attendance")
                count = cursor.fetchone()[0]
                self.logger.info(f"✅ Database connection successful. Records count: {count}")
                return True
        except Exception as e:
            self.logger.error(f"❌ Database connection failed: {e}")
            return False
    
    def insert_sample_records(self, num_records: int = 5) -> List[str]:
        """Insert sample records into staging_attendance table"""
        sample_employees = [
            {"id": "PTRJ.241000001", "name": "Ade Prasetya"},
            {"id": "PTRJ.241000002", "name": "Budi Santoso"},
            {"id": "PTRJ.241000003", "name": "Citra Dewi"},
            {"id": "PTRJ.241000004", "name": "Doni Kurniawan"},
            {"id": "PTRJ.241000005", "name": "Eka Sari"}
        ]
        
        sample_tasks = [
            {"code": "(OC7190) BOILER OPERATION", "station": "STN-BLR (STATION BOILER)", "machine": "BLR00000 (LABOUR COST)", "expense": "L (LABOUR)"},
            {"code": "(OC7200) TURBINE OPERATION", "station": "STN-TRB (STATION TURBINE)", "machine": "TRB00000 (LABOUR COST)", "expense": "L (LABOUR)"},
            {"code": "(OC7300) MAINTENANCE", "station": "STN-MNT (MAINTENANCE)", "machine": "MNT00000 (LABOUR COST)", "expense": "L (LABOUR)"},
            {"code": "(OC7400) INSPECTION", "station": "STN-INS (INSPECTION)", "machine": "INS00000 (LABOUR COST)", "expense": "L (LABOUR)"},
            {"code": "(OC7500) CLEANING", "station": "STN-CLN (CLEANING)", "machine": "CLN00000 (LABOUR COST)", "expense": "L (LABOUR)"}
        ]
        
        inserted_ids = []
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Generate records for the last few days
                base_date = datetime.now() - timedelta(days=3)
                
                for i in range(num_records):
                    record_date = base_date + timedelta(days=i % 3)
                    employee = sample_employees[i % len(sample_employees)]
                    task = sample_tasks[i % len(sample_tasks)]
                    
                    record_id = str(uuid.uuid4())
                    
                    # Create raw_charge_job string
                    raw_charge_job = f"{task['code']} / {task['station']} / {task['machine']} / {task['expense']}"
                    
                    insert_query = """
                    INSERT INTO staging_attendance (
                        id, employee_id, employee_name, date, day_of_week, shift,
                        check_in, check_out, regular_hours, overtime_hours, total_hours,
                        task_code, station_code, machine_code, expense_code, status,
                        created_at, updated_at, source_record_id, notes, raw_charge_job,
                        ptrj_employee_id
                    ) VALUES (
                        ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?,
                        ?
                    )
                    """
                    
                    values = (
                        record_id,
                        employee['id'],
                        employee['name'],
                        record_date.strftime('%Y-%m-%d'),
                        record_date.strftime('%A'),
                        'BEW 2',  # Sample shift
                        '07:00',  # Check in
                        '15:00',  # Check out
                        8.0,      # Regular hours
                        0.0,      # Overtime hours
                        8.0,      # Total hours
                        task['code'],
                        task['station'],
                        task['machine'],
                        task['expense'],
                        'staged',
                        datetime.now().isoformat(),
                        datetime.now().isoformat(),
                        f"{employee['id']}_{record_date.strftime('%Y%m%d')}",
                        f"Sample record for {employee['name']}",
                        raw_charge_job,
                        employee['id']
                    )
                    
                    cursor.execute(insert_query, values)
                    inserted_ids.append(record_id)
                    
                    self.logger.info(f"✅ Inserted record for {employee['name']} on {record_date.strftime('%Y-%m-%d')}")
                
                conn.commit()
                self.logger.info(f"🎉 Successfully inserted {len(inserted_ids)} sample records")
                
        except Exception as e:
            self.logger.error(f"❌ Error inserting sample records: {e}")
            raise
        
        return inserted_ids
    
    def fetch_all_staging_data(self, status: str = 'staged') -> List[Dict[str, Any]]:
        """Fetch all staging attendance data from database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                SELECT * FROM staging_attendance 
                WHERE status = ? 
                ORDER BY date DESC, employee_name ASC
                """
                
                cursor.execute(query, (status,))
                rows = cursor.fetchall()
                
                # Convert rows to dictionaries
                records = []
                for row in rows:
                    record = dict(row)
                    records.append(record)
                
                self.logger.info(f"📊 Fetched {len(records)} records with status '{status}'")
                return records
                
        except Exception as e:
            self.logger.error(f"❌ Error fetching staging data: {e}")
            raise
    
    def fetch_grouped_staging_data(self, status: str = 'staged') -> List[Dict[str, Any]]:
        """Fetch staging data grouped by employee"""
        try:
            records = self.fetch_all_staging_data(status)
            
            # Group by employee
            grouped_data = {}
            for record in records:
                employee_id = record['employee_id']
                if employee_id not in grouped_data:
                    grouped_data[employee_id] = {
                        'employee_id': employee_id,
                        'employee_name': record['employee_name'],
                        'records': []
                    }
                grouped_data[employee_id]['records'].append(record)
            
            result = list(grouped_data.values())
            self.logger.info(f"📊 Grouped {len(records)} records into {len(result)} employee groups")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Error fetching grouped staging data: {e}")
            raise
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Total records
                cursor.execute("SELECT COUNT(*) FROM staging_attendance")
                total_records = cursor.fetchone()[0]
                
                # Records by status
                cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM staging_attendance 
                GROUP BY status
                """)
                status_counts = dict(cursor.fetchall())
                
                # Unique employees
                cursor.execute("SELECT COUNT(DISTINCT employee_id) FROM staging_attendance")
                unique_employees = cursor.fetchone()[0]
                
                # Date range
                cursor.execute("""
                SELECT MIN(date) as min_date, MAX(date) as max_date 
                FROM staging_attendance
                """)
                date_range = cursor.fetchone()
                
                stats = {
                    'total_records': total_records,
                    'status_counts': status_counts,
                    'unique_employees': unique_employees,
                    'date_range': {
                        'min_date': date_range[0],
                        'max_date': date_range[1]
                    }
                }
                
                return stats
                
        except Exception as e:
            self.logger.error(f"❌ Error getting database stats: {e}")
            raise
    
    def clear_sample_data(self) -> int:
        """Clear all sample data (records with 'Sample record' in notes)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Delete sample records
                cursor.execute("""
                DELETE FROM staging_attendance 
                WHERE notes LIKE 'Sample record%'
                """)
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                self.logger.info(f"🗑️ Cleared {deleted_count} sample records")
                return deleted_count
                
        except Exception as e:
            self.logger.error(f"❌ Error clearing sample data: {e}")
            raise

def main():
    """Main function to test the local database manager"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Initialize database manager
        db_manager = LocalDatabaseManager()
        
        # Test connection
        if not db_manager.test_connection():
            print("❌ Database connection failed")
            return
        
        print("\n" + "="*50)
        print("🗄️ LOCAL DATABASE MANAGER DEMO")
        print("="*50)
        
        # Show current stats
        print("\n📊 Current Database Stats:")
        stats = db_manager.get_database_stats()
        print(json.dumps(stats, indent=2))
        
        # Ask user what to do
        print("\n🔧 Available Operations:")
        print("1. Insert sample records")
        print("2. View all staging data")
        print("3. View grouped staging data")
        print("4. Clear sample data")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            num_records = int(input("Enter number of sample records to insert (default 5): ") or 5)
            inserted_ids = db_manager.insert_sample_records(num_records)
            print(f"\n✅ Inserted {len(inserted_ids)} sample records")
            
        elif choice == '2':
            records = db_manager.fetch_all_staging_data()
            print(f"\n📋 Found {len(records)} staging records:")
            for i, record in enumerate(records[:10]):  # Show first 10
                print(f"{i+1}. {record['employee_name']} - {record['date']} - {record['task_code']}")
            if len(records) > 10:
                print(f"... and {len(records) - 10} more records")
                
        elif choice == '3':
            grouped_data = db_manager.fetch_grouped_staging_data()
            print(f"\n👥 Found {len(grouped_data)} employee groups:")
            for group in grouped_data:
                print(f"- {group['employee_name']} ({group['employee_id']}): {len(group['records'])} records")
                
        elif choice == '4':
            deleted_count = db_manager.clear_sample_data()
            print(f"\n🗑️ Cleared {deleted_count} sample records")
            
        elif choice == '5':
            print("\n👋 Goodbye!")
            
        else:
            print("\n❌ Invalid choice")
        
        # Show final stats
        print("\n📊 Final Database Stats:")
        final_stats = db_manager.get_database_stats()
        print(json.dumps(final_stats, indent=2))
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()