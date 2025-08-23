import sqlite3
import os

db_path = r'D:\Gawean Rebinmas\Autofill Venus Millware\Rollback Venus Rekap Web\venus_autofill_rekap_web\data\staging_attendance.db'

print('Database file exists:', os.path.exists(db_path))

if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print('Tables:', [t[0] for t in tables])
        
        # Check for PT RJ data in each table
        for table in tables:
            table_name = table[0]
            print(f"\nChecking table: {table_name}")
            
            # Get column names
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            print(f"Columns: {column_names}")
            
            # Search for PT RJ in text columns
            text_columns = [col for col in column_names if 'name' in col.lower() or 'id' in col.lower()]
            
            for col in text_columns:
                cursor.execute(f"SELECT * FROM {table_name} WHERE {col} LIKE '%PT RJ%' OR {col} LIKE '%PTRJ%' LIMIT 5")
                results = cursor.fetchall()
                if results:
                    print(f"Found PT RJ data in column {col}:")
                    for row in results:
                        print(f"  {row}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
else:
    print("Database file not found!")