import sqlite3

conn = sqlite3.connect('data/staging_attendance.db')
cursor = conn.cursor()

# Check total records
cursor.execute('SELECT COUNT(*) FROM staging_attendance')
total_records = cursor.fetchone()[0]
print(f'Total records in staging_attendance: {total_records}')

# Check records by status
cursor.execute('SELECT status, COUNT(*) FROM staging_attendance GROUP BY status')
print('\nRecords by status:')
for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1]}')

# Check unique employees
cursor.execute('SELECT COUNT(DISTINCT employee_name) FROM staging_attendance WHERE status = "staged"')
staged_employees = cursor.fetchone()[0]
print(f'\nUnique employees with staged status: {staged_employees}')

conn.close()