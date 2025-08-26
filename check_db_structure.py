#!/usr/bin/env python3
"""
Script to check database structure
"""

import sqlite3
from pathlib import Path

def check_database_structure():
    """Check the structure of staging_attendance.db"""
    db_path = Path("data/staging_attendance.db")
    
    if not db_path.exists():
        print(f"Database file not found: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Tables in database:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Get columns for staging_attendance table
        if any('staging_attendance' in str(table) for table in tables):
            cursor.execute("PRAGMA table_info(staging_attendance);")
            columns = cursor.fetchall()
            print("\nColumns in staging_attendance table:")
            for col in columns:
                print(f"  {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULL'}")
            
            # Get sample data
            cursor.execute("SELECT * FROM staging_attendance LIMIT 3;")
            sample_data = cursor.fetchall()
            print("\nSample data (first 3 rows):")
            for i, row in enumerate(sample_data, 1):
                print(f"  Row {i}: {dict(zip([col[1] for col in columns], row))}")
        
        # Get record count
        cursor.execute("SELECT COUNT(*) FROM staging_attendance;")
        count = cursor.fetchone()[0]
        print(f"\nTotal records: {count}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_database_structure()