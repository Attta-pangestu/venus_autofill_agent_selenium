import requests
import json
import sqlite3

# Test the API endpoint
print("Testing /api/staging/data endpoint...")
try:
    response = requests.get('http://localhost:5000/api/staging/data')
    if response.status_code == 200:
        data = response.json()
        print(f"API returned {len(data)} records")
        
        # Show first few records structure
        if data:
            print("\nFirst record structure:")
            first_record = data[0]
            for key, value in first_record.items():
                print(f"  {key}: {value}")
            
            # Count unique employees in API response
            unique_employees_api = set()
            for record in data:
                unique_employees_api.add(record.get('employee_name', ''))
            print(f"\nUnique employees in API response: {len(unique_employees_api)}")
        
    else:
        print(f"API request failed with status code: {response.status_code}")
        print(f"Response: {response.text}")
except Exception as e:
    print(f"Error calling API: {e}")

# Compare with database
print("\n" + "="*50)
print("Comparing with database...")
conn = sqlite3.connect('data/staging_attendance.db')
cursor = conn.cursor()

# Get database stats
cursor.execute('SELECT COUNT(*) FROM staging_attendance WHERE status = "staged"')
db_total = cursor.fetchone()[0]
print(f"Database total records (staged): {db_total}")

cursor.execute('SELECT COUNT(DISTINCT employee_name) FROM staging_attendance WHERE status = "staged"')
db_unique_employees = cursor.fetchone()[0]
print(f"Database unique employees (staged): {db_unique_employees}")

conn.close()

# Summary
print("\n" + "="*50)
print("SUMMARY:")
if 'data' in locals():
    print(f"API records: {len(data)}")
    print(f"Database records: {db_total}")
    print(f"Difference: {db_total - len(data)} records missing from API")
else:
    print("Could not retrieve API data for comparison")