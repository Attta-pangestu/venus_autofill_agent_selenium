#!/usr/bin/env python3
"""
Debug API Filtering - Test endpoint filtering behavior
"""

import requests
import json
import sqlite3
from pathlib import Path

def test_database_direct():
    """Test direct database access"""
    print("=== TESTING DIRECT DATABASE ACCESS ===")
    
    db_path = Path("data/staging_attendance.db")
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get total records
        cursor.execute("SELECT COUNT(*) as total FROM staging_attendance WHERE status = 'staged'")
        total = cursor.fetchone()['total']
        print(f"📊 Total records in database: {total}")
        
        # Get unique employees
        cursor.execute("SELECT COUNT(DISTINCT employee_name) as unique_employees FROM staging_attendance WHERE status = 'staged'")
        unique_employees = cursor.fetchone()['unique_employees']
        print(f"👥 Unique employees in database: {unique_employees}")
        
        # Get sample employee names
        cursor.execute("SELECT DISTINCT employee_name FROM staging_attendance WHERE status = 'staged' LIMIT 10")
        sample_names = [row['employee_name'] for row in cursor.fetchall()]
        print(f"📝 Sample employee names:")
        for name in sample_names:
            print(f"   - {name}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")

def test_api_endpoint():
    """Test API endpoint"""
    print("\n=== TESTING API ENDPOINT ===")
    
    try:
        response = requests.get('http://localhost:5000/api/staging/data', timeout=10)
        response.raise_for_status()
        
        data = response.json()
        api_records = data.get('data', [])
        
        print(f"📊 API returned {len(api_records)} records")
        
        if api_records:
            print(f"📝 First record structure:")
            first_record = api_records[0]
            for key, value in first_record.items():
                print(f"   {key}: {value}")
        else:
            print("❌ No records returned from API")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ API request failed: {e}")
    except Exception as e:
        print(f"❌ API error: {e}")

def check_exclusion_config():
    """Check exclusion configuration"""
    print("\n=== CHECKING EXCLUSION CONFIGURATION ===")
    
    config_path = Path("config/employee_exclusion_list.json")
    if not config_path.exists():
        print(f"❌ Exclusion config not found: {config_path}")
        return
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        excluded_employees = config.get('excluded_employees', [])
        exclusion_settings = config.get('exclusion_settings', {})
        
        print(f"📊 Exclusion settings:")
        print(f"   - Enabled: {exclusion_settings.get('enabled', False)}")
        print(f"   - Case sensitive: {exclusion_settings.get('case_sensitive', False)}")
        print(f"   - Partial match: {exclusion_settings.get('partial_match', False)}")
        
        print(f"📝 Excluded employees ({len(excluded_employees)}):")
        for name in excluded_employees:
            print(f"   - {name}")
            
    except Exception as e:
        print(f"❌ Config error: {e}")

def main():
    """Main function"""
    print("🔍 DEBUGGING API FILTERING ISSUE")
    print("=" * 50)
    
    # Test database directly
    test_database_direct()
    
    # Check exclusion config
    check_exclusion_config()
    
    # Test API endpoint
    test_api_endpoint()
    
    print("\n" + "=" * 50)
    print("🔍 DEBUG COMPLETE")

if __name__ == '__main__':
    main()