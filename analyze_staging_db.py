import sqlite3
import os
import json

def analyze_staging_database():
    db_path = r'D:\Gawean Rebinmas\Autofill Venus Millware\Rollback Venus Rekap Web\venus_autofill_rekap_web\data\staging_attendance.db'
    
    if not os.path.exists(db_path):
        print(f"Database tidak ditemukan di: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Analisis struktur tabel
        print("=" * 100)
        print("1. STRUKTUR TABEL STAGING_ATTENDANCE")
        print("=" * 100)
        
        cursor.execute("PRAGMA table_info(staging_attendance)")
        columns = cursor.fetchall()
        
        print(f"{'No':<3} | {'Nama Kolom':<25} | {'Tipe Data':<15} | {'Not Null':<8} | {'Default':<15} | {'PK':<3}")
        print("-" * 100)
        
        for i, col in enumerate(columns):
            cid, name, dtype, notnull, default, pk = col
            default_str = str(default) if default is not None else 'None'
            print(f"{i+1:<3} | {name:<25} | {dtype:<15} | {notnull:<8} | {default_str:<15} | {pk:<3}")
        
        # 2. Hitung total record
        cursor.execute("SELECT COUNT(*) FROM staging_attendance")
        total_records = cursor.fetchone()[0]
        print(f"\nTotal Records: {total_records}")
        
        # 3. Tampilkan data lengkap dalam format JSON untuk 5 record pertama
        print("\n" + "=" * 100)
        print("2. DATA LENGKAP (5 RECORD PERTAMA) - FORMAT JSON")
        print("=" * 100)
        
        cursor.execute("SELECT * FROM staging_attendance LIMIT 5")
        sample_data = cursor.fetchall()
        
        column_names = [desc[1] for desc in columns]
        
        for i, row in enumerate(sample_data, 1):
            print(f"\n--- RECORD {i} ---")
            record_dict = {}
            for j, value in enumerate(row):
                record_dict[column_names[j]] = value
            
            # Print in readable format
            for key, value in record_dict.items():
                print(f"{key:<25}: {value}")
        
        # 4. Analisis data unik untuk kolom penting
        print("\n" + "=" * 100)
        print("3. ANALISIS DATA UNIK")
        print("=" * 100)
        
        # Employee names dengan ID
        cursor.execute("SELECT DISTINCT employee_id, employee_name FROM staging_attendance ORDER BY employee_name LIMIT 20")
        unique_employees = cursor.fetchall()
        print(f"\nEmployee Data (20 pertama dari total unique employees):")
        for emp_id, emp_name in unique_employees:
            print(f"  ID: {emp_id:<15} | Name: {emp_name}")
        
        # Task codes
        cursor.execute("SELECT DISTINCT task_code FROM staging_attendance WHERE task_code IS NOT NULL AND task_code != '' ORDER BY task_code")
        unique_tasks = cursor.fetchall()
        print(f"\nTask Codes ({len(unique_tasks)} unique):")
        if unique_tasks:
            for task in unique_tasks:
                print(f"  - {task[0]}")
        else:
            print("  Tidak ada task code yang terisi")
        
        # Station codes
        cursor.execute("SELECT DISTINCT station_code FROM staging_attendance WHERE station_code IS NOT NULL AND station_code != '' ORDER BY station_code")
        unique_stations = cursor.fetchall()
        print(f"\nStation Codes ({len(unique_stations)} unique):")
        if unique_stations:
            for station in unique_stations:
                print(f"  - {station[0]}")
        else:
            print("  Tidak ada station code yang terisi")
        
        # 5. Cari data PT RJ dengan berbagai variasi
        print("\n" + "=" * 100)
        print("4. PENCARIAN DATA KARYAWAN 'PT RJ' / 'PTRJ'")
        print("=" * 100)
        
        search_queries = [
            "SELECT * FROM staging_attendance WHERE employee_name LIKE '%PT RJ%'",
            "SELECT * FROM staging_attendance WHERE employee_name LIKE '%PTRJ%'",
            "SELECT * FROM staging_attendance WHERE employee_id LIKE '%PTRJ%'",
            "SELECT * FROM staging_attendance WHERE ptrj_employee_id LIKE '%PTRJ%'"
        ]
        
        all_pt_rj_data = []
        for query in search_queries:
            cursor.execute(query)
            results = cursor.fetchall()
            all_pt_rj_data.extend(results)
        
        # Remove duplicates
        unique_pt_rj_data = list(set(all_pt_rj_data))
        
        if unique_pt_rj_data:
            print(f"Ditemukan {len(unique_pt_rj_data)} record untuk karyawan PT RJ:")
            for i, row in enumerate(unique_pt_rj_data[:3], 1):  # Show first 3 records
                print(f"\n--- PT RJ RECORD {i} ---")
                record_dict = {}
                for j, value in enumerate(row):
                    record_dict[column_names[j]] = value
                
                # Print key fields
                key_fields = ['id', 'employee_id', 'employee_name', 'date', 'task_code', 'station_code', 'ptrj_employee_id']
                for field in key_fields:
                    if field in record_dict:
                        print(f"{field:<20}: {record_dict[field]}")
        else:
            print("Tidak ditemukan data karyawan PT RJ dengan berbagai variasi pencarian")
        
        # 6. Statistik data
        print("\n" + "=" * 100)
        print("5. STATISTIK DATA")
        print("=" * 100)
        
        # Count by status
        cursor.execute("SELECT status, COUNT(*) FROM staging_attendance GROUP BY status")
        status_counts = cursor.fetchall()
        print("\nDistribusi Status:")
        for status, count in status_counts:
            print(f"  {status}: {count} records")
        
        # Date range
        cursor.execute("SELECT MIN(date), MAX(date) FROM staging_attendance")
        date_range = cursor.fetchone()
        print(f"\nRentang Tanggal: {date_range[0]} sampai {date_range[1]}")
        
        # Total hours statistics
        cursor.execute("SELECT AVG(total_hours), MIN(total_hours), MAX(total_hours) FROM staging_attendance WHERE total_hours > 0")
        hours_stats = cursor.fetchone()
        if hours_stats[0]:
            print(f"\nStatistik Total Hours:")
            print(f"  Rata-rata: {hours_stats[0]:.2f} jam")
            print(f"  Minimum: {hours_stats[1]} jam")
            print(f"  Maximum: {hours_stats[2]} jam")
        
        conn.close()
        print("\n" + "=" * 100)
        print("ANALISIS DATABASE STAGING SELESAI")
        print("=" * 100)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_staging_database()