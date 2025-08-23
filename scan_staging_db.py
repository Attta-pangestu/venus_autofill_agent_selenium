import sqlite3
import json
import os

def scan_staging_database():
    """Scan staging database structure and schema"""
    db_path = r"D:\Gawean Rebinmas\Autofill Venus Millware\Rollback Venus Rekap Web\venus_autofill_rekap_web\data\staging_attendance.db"
    
    if not os.path.exists(db_path):
        print(f"Database tidak ditemukan di: {db_path}")
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        database_structure = {
            "database_path": db_path,
            "tables": {}
        }
        
        print("=== STRUKTUR DATABASE STAGING ===")
        print(f"Database: {db_path}")
        print(f"Jumlah tabel: {len(tables)}")
        print()
        
        for table in tables:
            table_name = table[0]
            print(f"Tabel: {table_name}")
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            # Get sample data
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
            sample_data = cursor.fetchall()
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            
            table_info = {
                "columns": [],
                "sample_data": sample_data,
                "row_count": row_count
            }
            
            print(f"  Jumlah baris: {row_count}")
            print("  Kolom:")
            
            for col in columns:
                col_info = {
                    "name": col[1],
                    "type": col[2],
                    "not_null": bool(col[3]),
                    "default_value": col[4],
                    "primary_key": bool(col[5])
                }
                table_info["columns"].append(col_info)
                
                pk_marker = " (PK)" if col[5] else ""
                null_marker = " NOT NULL" if col[3] else ""
                print(f"    - {col[1]} ({col[2]}){pk_marker}{null_marker}")
            
            if sample_data:
                print("  Sample data (3 baris pertama):")
                for i, row in enumerate(sample_data, 1):
                    print(f"    Row {i}: {row}")
            
            database_structure["tables"][table_name] = table_info
            print()
        
        # Save to JSON file
        output_file = "staging_database_structure.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(database_structure, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"Struktur database disimpan ke: {output_file}")
        
        conn.close()
        return database_structure
        
    except Exception as e:
        print(f"Error scanning database: {e}")
        return None

if __name__ == "__main__":
    scan_staging_database()