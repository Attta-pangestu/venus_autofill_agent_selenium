#!/usr/bin/env python3
"""
Script untuk mengisi database staging_attendance.db dengan sample data
yang sesuai dengan struktur API response dari server port 5173
"""

import sqlite3
import json
import uuid
from datetime import datetime, timedelta
import random
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StagingDataPopulator:
    """Populate staging database with sample data"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        
    def create_sample_data(self, num_employees: int = 10, days_back: int = 30) -> list:
        """Create sample staging data similar to API response structure"""
        
        # Sample employee data
        employees = [
            {"id": "PTRJ.241000161", "name": "Abdu Ricken", "ptrj_id": "POM00250"},
            {"id": "PTRJ.241000162", "name": "Ahmad Suharto", "ptrj_id": "POM00251"},
            {"id": "PTRJ.241000163", "name": "Budi Santoso", "ptrj_id": "POM00252"},
            {"id": "PTRJ.241000164", "name": "Citra Dewi", "ptrj_id": "POM00253"},
            {"id": "PTRJ.241000165", "name": "Dedi Kurniawan", "ptrj_id": "POM00254"},
            {"id": "PTRJ.241000166", "name": "Eka Pratama", "ptrj_id": "POM00255"},
            {"id": "PTRJ.241000167", "name": "Fitri Handayani", "ptrj_id": "POM00256"},
            {"id": "PTRJ.241000168", "name": "Gunawan Wijaya", "ptrj_id": "POM00257"},
            {"id": "PTRJ.241000169", "name": "Hendra Saputra", "ptrj_id": "POM00258"},
            {"id": "PTRJ.241000170", "name": "Indira Sari", "ptrj_id": "POM00259"}
        ]
        
        # Sample shifts and departments
        shifts = ["PROSES _SHIFT1", "PROSES _SHIFT2", "PROSES _SHIFT3"]
        departments = ["FRUIT RECEPTION", "PROCESSING", "PACKAGING", "QUALITY CONTROL"]
        
        sample_data = []
        
        # Generate data for each employee
        for emp in employees[:num_employees]:
            for day in range(days_back):
                date = (datetime.now() - timedelta(days=day)).strftime("%Y-%m-%d")
                
                # Skip some days randomly (weekends, absences)
                if random.random() < 0.2:  # 20% chance to skip
                    continue
                    
                # Generate attendance record
                check_in_hour = random.randint(6, 8)
                check_in_minute = random.randint(0, 59)
                check_in = f"{check_in_hour:02d}:{check_in_minute:02d}"
                
                # Sometimes no check out (incomplete data)
                if random.random() < 0.1:  # 10% chance of no check out
                    check_out = ""
                    regular_hours = 0.0
                    total_hours = 0.0
                else:
                    check_out_hour = check_in_hour + random.randint(7, 9)
                    check_out_minute = random.randint(0, 59)
                    check_out = f"{check_out_hour:02d}:{check_out_minute:02d}"
                    regular_hours = random.choice([7.0, 8.0, 8.5])
                    total_hours = regular_hours
                
                overtime_hours = random.choice([0.0, 1.0, 2.0]) if total_hours > 0 else 0.0
                if overtime_hours > 0:
                    total_hours += overtime_hours
                
                record = {
                    "id": str(uuid.uuid4()),
                    "employee_id": emp["id"],
                    "employee_name": emp["name"],
                    "ptrj_employee_id": emp["ptrj_id"],
                    "date": date,
                    "day_of_week": "",
                    "shift": random.choice(shifts),
                    "check_in": check_in,
                    "check_out": check_out,
                    "regular_hours": regular_hours,
                    "overtime_hours": overtime_hours,
                    "total_hours": total_hours,
                    "status": "staged",
                    "task_code": "(OC7110) FRUIT RECEPTION AND STORAGE",
                    "station_code": "STN-FRC (STATION FRUIT RECEPTION)",
                    "machine_code": "FRC00000 (LABOUR COST)",
                    "expense_code": "L (LABOUR)",
                    "raw_charge_job": "(OC7110) FRUIT RECEPTION AND STORAGE / STN-FRC (STATION FRUIT RECEPTION) / FRC00000 (LABOUR COST) / L (LABOUR)",
                    "department": random.choice(departments),
                    "project": "Venus Millware Project",
                    "is_alfa": False,
                    "is_on_leave": False,
                    "leave_ref_number": None,
                    "leave_type_code": None,
                    "leave_type_description": None,
                    "notes": f"Enhanced transfer {str(uuid.uuid4())[:8]} - bulk mode",
                    "source_record_id": f"{emp['id']}_{date.replace('-', '')}",
                    "transfer_status": "success",
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                sample_data.append(record)
        
        logger.info(f"Generated {len(sample_data)} sample records for {num_employees} employees")
        return sample_data
    
    def update_database_schema(self):
        """Update database schema to match API response structure"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Drop existing table to recreate with new schema
                cursor.execute('DROP TABLE IF EXISTS staging_attendance')
                
                # Create new table with extended schema
                cursor.execute('''
                    CREATE TABLE staging_attendance (
                        id TEXT PRIMARY KEY,
                        employee_id TEXT NOT NULL,
                        employee_name TEXT NOT NULL,
                        ptrj_employee_id TEXT,
                        date TEXT NOT NULL,
                        day_of_week TEXT,
                        shift TEXT,
                        check_in TEXT,
                        check_out TEXT,
                        regular_hours REAL DEFAULT 0,
                        overtime_hours REAL DEFAULT 0,
                        total_hours REAL DEFAULT 0,
                        status TEXT DEFAULT 'staged',
                        task_code TEXT,
                        station_code TEXT,
                        machine_code TEXT,
                        expense_code TEXT,
                        raw_charge_job TEXT,
                        department TEXT,
                        project TEXT,
                        is_alfa BOOLEAN DEFAULT 0,
                        is_on_leave BOOLEAN DEFAULT 0,
                        leave_ref_number TEXT,
                        leave_type_code TEXT,
                        leave_type_description TEXT,
                        notes TEXT,
                        source_record_id TEXT,
                        transfer_status TEXT DEFAULT 'success',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create indexes for better performance
                cursor.execute('CREATE INDEX idx_employee_id ON staging_attendance(employee_id)')
                cursor.execute('CREATE INDEX idx_date ON staging_attendance(date)')
                cursor.execute('CREATE INDEX idx_status ON staging_attendance(status)')
                
                conn.commit()
                logger.info("✅ Database schema updated successfully")
                
        except Exception as e:
            logger.error(f"❌ Error updating database schema: {e}")
            raise
    
    def populate_database(self, sample_data: list):
        """Insert sample data into database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Clear existing data
                cursor.execute('DELETE FROM staging_attendance')
                
                # Insert sample data
                for record in sample_data:
                    cursor.execute('''
                        INSERT INTO staging_attendance (
                            id, employee_id, employee_name, ptrj_employee_id, date, day_of_week,
                            shift, check_in, check_out, regular_hours, overtime_hours, total_hours,
                            status, task_code, station_code, machine_code, expense_code, raw_charge_job,
                            department, project, is_alfa, is_on_leave, leave_ref_number, leave_type_code,
                            leave_type_description, notes, source_record_id, transfer_status,
                            created_at, updated_at
                        ) VALUES (
                            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                        )
                    ''', (
                        record['id'], record['employee_id'], record['employee_name'], record['ptrj_employee_id'],
                        record['date'], record['day_of_week'], record['shift'], record['check_in'], record['check_out'],
                        record['regular_hours'], record['overtime_hours'], record['total_hours'], record['status'],
                        record['task_code'], record['station_code'], record['machine_code'], record['expense_code'],
                        record['raw_charge_job'], record['department'], record['project'], record['is_alfa'],
                        record['is_on_leave'], record['leave_ref_number'], record['leave_type_code'],
                        record['leave_type_description'], record['notes'], record['source_record_id'],
                        record['transfer_status'], record['created_at'], record['updated_at']
                    ))
                
                conn.commit()
                logger.info(f"✅ Inserted {len(sample_data)} records into database")
                
                # Log statistics
                cursor.execute('SELECT COUNT(*) FROM staging_attendance')
                total_records = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(DISTINCT employee_id) FROM staging_attendance')
                unique_employees = cursor.fetchone()[0]
                
                logger.info(f"📊 Database stats: {total_records} total records, {unique_employees} unique employees")
                
        except Exception as e:
            logger.error(f"❌ Error populating database: {e}")
            raise
    
    def run(self, num_employees: int = 10, days_back: int = 30):
        """Run the complete population process"""
        logger.info("🚀 Starting database population process...")
        
        # Update schema
        self.update_database_schema()
        
        # Generate sample data
        sample_data = self.create_sample_data(num_employees, days_back)
        
        # Populate database
        self.populate_database(sample_data)
        
        logger.info("✅ Database population completed successfully")

def main():
    """Main function"""
    db_path = "data/staging_attendance.db"
    
    populator = StagingDataPopulator(db_path)
    populator.run(num_employees=10, days_back=30)
    
    print("\n" + "="*60)
    print("📊 STAGING DATABASE POPULATION COMPLETED")
    print("="*60)
    print(f"Database: {db_path}")
    print("Ready for venus_desktop_app.py integration")
    print("="*60)

if __name__ == "__main__":
    main()