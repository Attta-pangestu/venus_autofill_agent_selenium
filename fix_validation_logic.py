#!/usr/bin/env python3
"""
Fix Validation Logic - Venus AutoFill
Corrects the POM validation logic based on debugging findings

The issue is in the staging data vs database comparison logic
"""

import sys
import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_fixed_validation_function():
    """Create the corrected POM validation function"""
    
    fixed_function = '''
    async def validate_single_entry_realtime_with_pom_FIXED(self, entry: Dict) -> Dict:
        """
        FIXED: Validate a single processed entry with POM prefix support
        Addresses the specific issues found in debugging
        """
        try:
            # Import with error handling
            try:
                import pyodbc
            except ImportError:
                return {
                    'status': 'ERROR',
                    'message': 'pyodbc module not available',
                    'employee_name': entry.get('employee_name', ''),
                    'employee_id_ptrj': entry.get('employee_id_ptrj', ''),
                    'date': entry.get('date', ''),
                    'expected_regular': entry.get('regular_hours', 0),
                    'expected_overtime': entry.get('overtime_hours', 0),
                    'actual_regular': 0,
                    'actual_overtime': 0
                }

            from datetime import datetime

            employee_id_ptrj = entry.get('employee_id_ptrj', '').strip()
            original_date = entry.get('date', '')
            
            # FIXED: Handle different hour field names and ensure proper conversion
            regular_hours = float(entry.get('regular_hours', 0) or 0)
            overtime_hours = float(entry.get('overtime_hours', 0) or 0)
            
            # Alternative field names check
            if regular_hours == 0 and overtime_hours == 0:
                # Check for alternative field names from staging data
                total_hours = float(entry.get('total_hours', 0) or 0)
                if total_hours > 0:
                    # If only total_hours available, assume it's regular hours unless specified
                    regular_hours = total_hours
                    overtime_hours = 0
                    
                    # Check if there's overtime data in other fields
                    if entry.get('overtime', 0) or entry.get('ot_hours', 0):
                        overtime_hours = float(entry.get('overtime', 0) or entry.get('ot_hours', 0) or 0)
                        regular_hours = max(0, total_hours - overtime_hours)

            self.logger.info(f"🔍 POM Validation Input: Regular={regular_hours}h, Overtime={overtime_hours}h")
            print(f"🔍 POM Validation Input: Regular={regular_hours}h, Overtime={overtime_hours}h")

            # Validate PTRJ Employee ID format
            if not employee_id_ptrj or not employee_id_ptrj.startswith('POM'):
                return {
                    'status': 'ERROR',
                    'message': f'Invalid PTRJ Employee ID format: {employee_id_ptrj} (must start with POM)',
                    'employee_name': entry.get('employee_name', ''),
                    'employee_id_ptrj': employee_id_ptrj,
                    'date': entry.get('date', ''),
                    'expected_regular': regular_hours,
                    'expected_overtime': overtime_hours,
                    'actual_regular': 0,
                    'actual_overtime': 0
                }

            # Get database connection based on mode
            db_name = "db_ptrj_mill_test" if self.automation_mode == 'testing' else "db_ptrj_mill"

            # FIXED: Enhanced connection configuration with better error handling
            connection_configs = [
                {
                    'name': 'Primary Config (VenusHR14 Compatible)',
                    'connection_string': f"""
                        DRIVER={{ODBC Driver 17 for SQL Server}};
                        SERVER=10.0.0.7,1888;
                        DATABASE={db_name};
                        UID=sa;
                        PWD=supp0rt@;
                        TrustServerCertificate=yes;
                        Connection Timeout=15;
                    """
                },
                {
                    'name': 'Alternative Config (No Encryption)',
                    'connection_string': f"""
                        DRIVER={{ODBC Driver 17 for SQL Server}};
                        SERVER=10.0.0.7,1888;
                        DATABASE={db_name};
                        UID=sa;
                        PWD=supp0rt@;
                        Encrypt=no;
                        Connection Timeout=15;
                    """
                }
            ]

            # FIXED: Improved date calculation using the working logic from debugging
            trx_date = self.calculate_transaction_date_by_mode(original_date, self.automation_mode)

            # FIXED: Enhanced date parsing with multiple format support
            sql_date = None
            
            # Try different parsing approaches
            try:
                if '/' in trx_date:
                    # DD/MM/YYYY format
                    date_obj = datetime.strptime(trx_date, "%d/%m/%Y")
                else:
                    # YYYY-MM-DD format
                    date_obj = datetime.strptime(trx_date, "%Y-%m-%d")
                
                sql_date = date_obj.strftime("%Y-%m-%d")
                
            except Exception as date_error:
                self.logger.error(f"❌ Date parsing error: {date_error}")
                return {
                    'status': 'ERROR',
                    'message': f'Date parsing error: {date_error}',
                    'employee_name': entry.get('employee_name', ''),
                    'employee_id_ptrj': employee_id_ptrj,
                    'date': original_date,
                    'expected_regular': regular_hours,
                    'expected_overtime': overtime_hours,
                    'actual_regular': 0,
                    'actual_overtime': 0
                }

            self.logger.info(f"🔍 POM Validation: {employee_id_ptrj} on {sql_date} (mode: {self.automation_mode})")
            print(f"🔍 POM Validation: {employee_id_ptrj} on {sql_date}")

            # Try to connect and validate with POM prefix support
            for config in connection_configs:
                try:
                    conn = pyodbc.connect(config['connection_string'], timeout=15)
                    cursor = conn.cursor()

                    # FIXED: Enhanced query with explicit POM validation
                    query = """
                        SELECT [EmpCode], [EmpName], [TrxDate], [OT], [Hours], [Status]
                        FROM [PR_TASKREGLN]
                        WHERE [EmpCode] = ? AND [TrxDate] = ?
                        ORDER BY [TrxDate] DESC, [OT]
                    """

                    self.logger.info(f"🔍 Executing query: EmpCode='{employee_id_ptrj}', TrxDate='{sql_date}'")
                    cursor.execute(query, (employee_id_ptrj, sql_date))
                    db_records = cursor.fetchall()

                    conn.close()

                    if not db_records:
                        self.logger.warning(f"⚠️ No records found for {employee_id_ptrj} on {sql_date}")
                        return {
                            'status': 'NOT_FOUND',
                            'message': f'No records found for {employee_id_ptrj} on {sql_date}',
                            'employee_name': entry.get('employee_name', ''),
                            'employee_id_ptrj': employee_id_ptrj,
                            'date': trx_date,
                            'expected_regular': regular_hours,
                            'expected_overtime': overtime_hours,
                            'actual_regular': 0,
                            'actual_overtime': 0
                        }

                    # FIXED: Improved OT flag interpretation with explicit boolean checking
                    db_regular_hours = 0.0
                    db_overtime_hours = 0.0

                    for record in db_records:
                        emp_code = record[0]      # EmpCode column
                        emp_name = record[1]      # EmpName column
                        trx_date_db = record[2]   # TrxDate column
                        ot_flag = record[3]       # OT column (boolean)
                        hours = float(record[4])  # Hours column

                        self.logger.info(f"📋 DB Record: {emp_code}, OT={ot_flag}, Hours={hours}")
                        
                        # FIXED: Explicit boolean comparison for OT flag
                        if ot_flag == True or ot_flag == 1:  # Overtime
                            db_overtime_hours += hours
                            self.logger.info(f"   ➕ Added to overtime: {hours}h (total overtime: {db_overtime_hours}h)")
                        else:  # Regular (OT == False or OT == 0)
                            db_regular_hours += hours
                            self.logger.info(f"   ➕ Added to regular: {hours}h (total regular: {db_regular_hours}h)")

                    self.logger.info(f"✅ Database totals: Regular={db_regular_hours}h, Overtime={db_overtime_hours}h")
                    print(f"✅ Database totals: Regular={db_regular_hours}h, Overtime={db_overtime_hours}h")
                    print(f"🎯 Expected totals: Regular={regular_hours}h, Overtime={overtime_hours}h")

                    # FIXED: Enhanced comparison with better tolerance and logging
                    tolerance = 0.1
                    regular_diff = abs(float(regular_hours) - float(db_regular_hours))
                    overtime_diff = abs(float(overtime_hours) - float(db_overtime_hours))
                    
                    regular_match = regular_diff < tolerance
                    overtime_match = overtime_diff < tolerance

                    self.logger.info(f"🔍 Comparison details:")
                    self.logger.info(f"   Regular: Expected={regular_hours}, Found={db_regular_hours}, Diff={regular_diff}, Match={regular_match}")
                    self.logger.info(f"   Overtime: Expected={overtime_hours}, Found={db_overtime_hours}, Diff={overtime_diff}, Match={overtime_match}")

                    if regular_match and overtime_match:
                        self.logger.info(f"✅ POM validation PASSED for {employee_id_ptrj}")
                        return {
                            'status': 'SUCCESS',
                            'message': f'POM validation passed: Hours match perfectly',
                            'employee_name': entry.get('employee_name', ''),
                            'employee_id_ptrj': employee_id_ptrj,
                            'date': trx_date,
                            'expected_regular': regular_hours,
                            'expected_overtime': overtime_hours,
                            'actual_regular': db_regular_hours,
                            'actual_overtime': db_overtime_hours,
                            'regular_diff': regular_diff,
                            'overtime_diff': overtime_diff
                        }
                    else:
                        self.logger.warning(f"❌ POM validation FAILED for {employee_id_ptrj}")
                        return {
                            'status': 'MISMATCH',
                            'message': f'POM validation failed: Expected R={regular_hours}h|OT={overtime_hours}h, Found R={db_regular_hours}h|OT={db_overtime_hours}h',
                            'employee_name': entry.get('employee_name', ''),
                            'employee_id_ptrj': employee_id_ptrj,
                            'date': trx_date,
                            'expected_regular': regular_hours,
                            'expected_overtime': overtime_hours,
                            'actual_regular': db_regular_hours,
                            'actual_overtime': db_overtime_hours,
                            'regular_diff': regular_diff,
                            'overtime_diff': overtime_diff
                        }

                except Exception as e:
                    self.logger.warning(f"⚠️ POM validation connection attempt failed: {e}")
                    continue

            # If all connection attempts failed
            return {
                'status': 'ERROR',
                'message': f'POM validation failed: Database connection error',
                'employee_name': entry.get('employee_name', ''),
                'employee_id_ptrj': employee_id_ptrj,
                'date': entry.get('date', ''),
                'expected_regular': regular_hours,
                'expected_overtime': overtime_hours,
                'actual_regular': 0,
                'actual_overtime': 0
            }

        except Exception as e:
            self.logger.error(f"❌ POM validation failed: {e}")
            return {
                'status': 'ERROR',
                'message': str(e),
                'employee_name': entry.get('employee_name', ''),
                'employee_id_ptrj': entry.get('employee_id_ptrj', ''),
                'date': entry.get('date', ''),
                'expected_regular': entry.get('regular_hours', 0),
                'expected_overtime': entry.get('overtime_hours', 0),
                'actual_regular': 0,
                'actual_overtime': 0
            }
    '''
    
    return fixed_function

def analyze_staging_data_structure():
    """Analyze the staging data structure to understand field mappings"""
    
    print("\n" + "="*80)
    print("🔍 STAGING DATA STRUCTURE ANALYSIS")
    print("="*80)
    
    # Expected staging data fields based on the system
    expected_fields = [
        'employee_id',           # Venus Employee ID
        'employee_id_ptrj',      # PTRJ Employee ID (POM prefixed)
        'employee_name',         # Employee Name
        'date',                  # Attendance Date (DD/MM/YYYY)
        'regular_hours',         # Regular working hours
        'overtime_hours',        # Overtime hours
        'total_hours',           # Total hours (regular + overtime)
        'task_code',             # Task code for automation
        'station_code',          # Station code
        'machine_code',          # Machine code
        'expense_code',          # Expense code
    ]
    
    print("📋 Expected staging data fields:")
    for field in expected_fields:
        print(f"   - {field}")
    
    print("\n🎯 Common Issues Found:")
    print("1. Field name variations (regular_hours vs normal_hours)")
    print("2. Data type inconsistencies (string vs float)")
    print("3. Zero value handling (0 vs null vs empty string)")
    print("4. Date format variations (DD/MM/YYYY vs YYYY-MM-DD)")
    
    return expected_fields

if __name__ == "__main__":
    print("🔧 VALIDATION LOGIC FIX GENERATOR")
    print("="*50)
    
    # Analyze staging data structure
    analyze_staging_data_structure()
    
    # Generate fixed validation function
    fixed_function = create_fixed_validation_function()
    
    print("\n✅ Fixed validation function generated!")
    print("📝 Next step: Apply this fix to run_user_controlled_automation.py") 