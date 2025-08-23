#!/usr/bin/env python3
"""
Database Migration Script for Success Tracking Database
Fixes schema issues and recreates the database with proper structure
"""

import sqlite3
import os
from pathlib import Path
from datetime import datetime

def backup_existing_database(db_path: Path):
    """Backup existing database before migration"""
    if db_path.exists():
        backup_path = db_path.with_name(f"{db_path.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sqlite")
        try:
            import shutil
            shutil.copy2(db_path, backup_path)
            print(f"✅ Backup created: {backup_path}")
            return backup_path
        except Exception as e:
            print(f"⚠️ Backup failed: {e}")
            return None
    return None

def create_new_success_database(db_path: Path):
    """Create new success tracking database with correct schema"""
    try:
        # Remove existing database
        if db_path.exists():
            os.remove(db_path)
            print(f"🗑️ Removed existing database: {db_path}")
        
        # Create new database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔧 Creating new database schema...")
        
        # Create successful_transfers table with all required columns
        cursor.execute('''
            CREATE TABLE successful_transfers (
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
        
        # Create validation_logs table with all required columns
        cursor.execute('''
            CREATE TABLE validation_logs (
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
        
        # Create offline_queue table
        cursor.execute('''
            CREATE TABLE offline_queue (
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
            CREATE INDEX idx_successful_transfers_employee_date 
            ON successful_transfers(employee_id_ptrj, transaction_date)
        ''')
        
        cursor.execute('''
            CREATE INDEX idx_validation_logs_employee_date 
            ON validation_logs(employee_id_ptrj, transaction_date)
        ''')
        
        cursor.execute('''
            CREATE INDEX idx_offline_queue_status 
            ON offline_queue(processing_status, automation_mode)
        ''')
        
        # Commit and close
        conn.commit()
        conn.close()
        
        print("✅ New database created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create new database: {e}")
        return False

def verify_database_schema(db_path: Path):
    """Verify that the database schema is correct"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n🔍 VERIFYING DATABASE SCHEMA")
        print("=" * 50)
        
        # Check successful_transfers table
        cursor.execute("PRAGMA table_info(successful_transfers)")
        columns = cursor.fetchall()
        
        print("📊 successful_transfers table columns:")
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")
        
        # Check validation_logs table
        cursor.execute("PRAGMA table_info(validation_logs)")
        columns = cursor.fetchall()
        
        print("\n📊 validation_logs table columns:")
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")
        
        # Check offline_queue table
        cursor.execute("PRAGMA table_info(offline_queue)")
        columns = cursor.fetchall()
        
        print("\n📊 offline_queue table columns:")
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")
        
        # Check indexes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = cursor.fetchall()
        
        print(f"\n📊 Database indexes ({len(indexes)}):")
        for idx in indexes:
            if not idx[0].startswith('sqlite_'):  # Skip system indexes
                print(f"   - {idx[0]}")
        
        conn.close()
        
        print("\n✅ Database schema verification completed!")
        return True
        
    except Exception as e:
        print(f"❌ Schema verification failed: {e}")
        return False

def test_database_operations(db_path: Path):
    """Test basic database operations"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n🧪 TESTING DATABASE OPERATIONS")
        print("=" * 50)
        
        # Test insert into successful_transfers
        test_timestamp = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO successful_transfers (
                employee_id_venus, employee_id_ptrj, employee_name,
                transaction_date, original_attendance_date,
                regular_hours, overtime_hours, total_hours,
                task_code, validation_timestamp, automation_mode,
                mill_database, validation_status, validation_type, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'TEST001', 'POM00001', 'Test Employee',
            '2025-06-10', '2025-06-10',
            7.0, 1.0, 8.0,
            'TEST_TASK', test_timestamp, 'testing',
            'db_ptrj_mill_test', 'SUCCESS', 'MILL_DB_VERIFIED',
            'Test record for schema verification'
        ))
        
        # Test insert into validation_logs
        cursor.execute('''
            INSERT INTO validation_logs (
                employee_id_ptrj, employee_name, transaction_date,
                validation_type, expected_regular_hours, expected_overtime_hours,
                actual_regular_hours, actual_overtime_hours, status,
                mill_database, automation_mode, connection_status, validation_timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'POM00001', 'Test Employee', '2025-06-10',
            'MILL_DB_VERIFIED', 7.0, 1.0, 7.0, 1.0, 'SUCCESS',
            'db_ptrj_mill_test', 'testing', 'CONNECTED', test_timestamp
        ))
        
        # Test insert into offline_queue
        cursor.execute('''
            INSERT INTO offline_queue (
                employee_data, validation_request, automation_mode, queued_timestamp
            ) VALUES (?, ?, ?, ?)
        ''', (
            '{"test": "data"}', '{"test": "request"}', 'testing', test_timestamp
        ))
        
        conn.commit()
        
        # Test queries
        cursor.execute('SELECT COUNT(*) FROM successful_transfers')
        transfer_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM validation_logs')
        log_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM offline_queue')
        queue_count = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"✅ Insert operations successful:")
        print(f"   - successful_transfers: {transfer_count} records")
        print(f"   - validation_logs: {log_count} records")
        print(f"   - offline_queue: {queue_count} records")
        
        return True
        
    except Exception as e:
        print(f"❌ Database operations test failed: {e}")
        return False

def main():
    """Main migration function"""
    print("\n🚀 SUCCESS DATABASE MIGRATION SCRIPT")
    print("=" * 60)
    
    db_path = Path(__file__).parent / "db_successful_transfer.sqlite"
    
    print(f"📍 Database path: {db_path}")
    
    # Step 1: Backup existing database
    backup_path = backup_existing_database(db_path)
    
    # Step 2: Create new database with correct schema
    success = create_new_success_database(db_path)
    
    if not success:
        print("❌ Migration failed!")
        return
    
    # Step 3: Verify schema
    verify_success = verify_database_schema(db_path)
    
    if not verify_success:
        print("❌ Schema verification failed!")
        return
    
    # Step 4: Test operations
    test_success = test_database_operations(db_path)
    
    if not test_success:
        print("❌ Database operations test failed!")
        return
    
    print(f"\n🎯 MIGRATION COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print(f"✅ New database: {db_path}")
    if backup_path:
        print(f"📋 Backup: {backup_path}")
    print("🔧 Schema: All required columns and indexes created")
    print("🧪 Tests: All basic operations working")
    print("\n🚀 Ready to use Enhanced Transfer Validation System!")

if __name__ == "__main__":
    main() 