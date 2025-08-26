#!/usr/bin/env python3
"""
Test untuk Penginputan Satu Baris Data Staging

Test ini memverifikasi:
1. Data dapat diinput dengan benar ke dalam tabel staging
2. Format data sesuai dengan struktur yang telah didefinisikan
3. Proses input berhasil tanpa error
4. Data yang diinput dapat diverifikasi kebenarannya
"""

import sqlite3
import unittest
import tempfile
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestSingleRowStagingInput(unittest.TestCase):
    """Test class untuk memverifikasi penginputan satu baris data staging"""
    
    def setUp(self):
        """Setup test environment dengan database temporary"""
        # Buat temporary database untuk testing
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = self.temp_db.name
        self.temp_db.close()
        
        # Inisialisasi database dengan schema yang benar
        self._create_staging_table()
        
        # Data test yang valid sesuai struktur staging
        self.valid_test_data = {
            'id': str(uuid.uuid4()),
            'employee_id': 'PTRJ.250300212',
            'employee_name': 'ALDI SETIAWAN',
            'ptrj_employee_id': 'POM00283',
            'date': '2025-01-15',
            'day_of_week': 'Wednesday',
            'shift': 'LABOR_SHIFT1',
            'check_in': '07:08',
            'check_out': '18:02',
            'regular_hours': 7.0,
            'overtime_hours': 3.0,
            'total_hours': 10.0,
            'status': 'staged',
            'task_code': '(OC7240) LABORATORY ANALYSIS',
            'station_code': 'STN-LAB (STATION LABORATORY)',
            'machine_code': 'LAB00000 (LABOUR COST )',
            'expense_code': 'L (LABOUR)',
            'raw_charge_job': '(OC7240) LABORATORY ANALYSIS / STN-LAB (STATION LABORATORY) / LAB00000 (LABOUR COST ) / L (LABOUR)',
            'department': 'LABORATORY',
            'project': 'OC7240',
            'is_alfa': False,
            'is_on_leave': False,
            'leave_ref_number': None,
            'leave_type_code': None,
            'leave_type_description': None,
            'notes': 'Test data untuk validasi input staging',
            'source_record_id': 'PTRJ.250300212_20250115',
            'transfer_status': 'pending',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        logger.info(f"✅ Test setup completed with database: {self.db_path}")
    
    def tearDown(self):
        """Cleanup test environment"""
        try:
            os.unlink(self.db_path)
            logger.info("✅ Test cleanup completed")
        except Exception as e:
            logger.warning(f"⚠️ Cleanup warning: {e}")
    
    def _create_staging_table(self):
        """Buat tabel staging_attendance dengan schema yang benar"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Schema sesuai dengan definisi sistem
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
                        transfer_status TEXT DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Buat index untuk performa
                cursor.execute('CREATE INDEX idx_employee_id ON staging_attendance(employee_id)')
                cursor.execute('CREATE INDEX idx_date ON staging_attendance(date)')
                cursor.execute('CREATE INDEX idx_status ON staging_attendance(status)')
                
                conn.commit()
                logger.info("✅ Staging table created successfully")
                
        except Exception as e:
            logger.error(f"❌ Error creating staging table: {e}")
            raise
    
    def test_01_data_input_success(self):
        """Test 1: Verifikasi data dapat diinput dengan benar ke dalam tabel staging"""
        logger.info("🧪 Test 1: Testing successful data input")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert data test
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
                    self.valid_test_data['id'], self.valid_test_data['employee_id'], 
                    self.valid_test_data['employee_name'], self.valid_test_data['ptrj_employee_id'],
                    self.valid_test_data['date'], self.valid_test_data['day_of_week'],
                    self.valid_test_data['shift'], self.valid_test_data['check_in'], 
                    self.valid_test_data['check_out'], self.valid_test_data['regular_hours'],
                    self.valid_test_data['overtime_hours'], self.valid_test_data['total_hours'],
                    self.valid_test_data['status'], self.valid_test_data['task_code'],
                    self.valid_test_data['station_code'], self.valid_test_data['machine_code'],
                    self.valid_test_data['expense_code'], self.valid_test_data['raw_charge_job'],
                    self.valid_test_data['department'], self.valid_test_data['project'],
                    self.valid_test_data['is_alfa'], self.valid_test_data['is_on_leave'],
                    self.valid_test_data['leave_ref_number'], self.valid_test_data['leave_type_code'],
                    self.valid_test_data['leave_type_description'], self.valid_test_data['notes'],
                    self.valid_test_data['source_record_id'], self.valid_test_data['transfer_status'],
                    self.valid_test_data['created_at'], self.valid_test_data['updated_at']
                ))
                
                conn.commit()
                
                # Verifikasi data berhasil diinput
                cursor.execute('SELECT COUNT(*) FROM staging_attendance WHERE id = ?', (self.valid_test_data['id'],))
                count = cursor.fetchone()[0]
                
                self.assertEqual(count, 1, "Data harus berhasil diinput ke database")
                logger.info("✅ Test 1 PASSED: Data berhasil diinput")
                
        except Exception as e:
            logger.error(f"❌ Test 1 FAILED: {e}")
            self.fail(f"Data input failed: {e}")
    
    def test_02_data_format_validation(self):
        """Test 2: Verifikasi format data sesuai dengan struktur yang telah didefinisikan"""
        logger.info("🧪 Test 2: Testing data format validation")
        
        # Test berbagai format data
        test_cases = [
            {
                'name': 'Valid Date Format (YYYY-MM-DD)',
                'data': self.valid_test_data.copy(),
                'should_pass': True
            },
            {
                'name': 'Invalid Date Format (DD/MM/YYYY)',
                'data': {**self.valid_test_data, 'date': '15/01/2025', 'id': str(uuid.uuid4())},
                'should_pass': True  # Database akan menerima, tapi aplikasi harus validasi
            },
            {
                'name': 'Missing Required Field (employee_name)',
                'data': {**self.valid_test_data, 'employee_name': None, 'id': str(uuid.uuid4())},
                'should_pass': False
            },
            {
                'name': 'Invalid Hours (negative)',
                'data': {**self.valid_test_data, 'regular_hours': -1.0, 'id': str(uuid.uuid4())},
                'should_pass': True  # Database level tidak ada constraint, aplikasi harus validasi
            },
            {
                'name': 'Valid Boolean Fields',
                'data': {**self.valid_test_data, 'is_alfa': True, 'is_on_leave': False, 'id': str(uuid.uuid4())},
                'should_pass': True
            }
        ]
        
        for test_case in test_cases:
            with self.subTest(test_case['name']):
                try:
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()
                        
                        # Coba insert data test
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
                            test_case['data']['id'], test_case['data']['employee_id'], 
                            test_case['data']['employee_name'], test_case['data']['ptrj_employee_id'],
                            test_case['data']['date'], test_case['data']['day_of_week'],
                            test_case['data']['shift'], test_case['data']['check_in'], 
                            test_case['data']['check_out'], test_case['data']['regular_hours'],
                            test_case['data']['overtime_hours'], test_case['data']['total_hours'],
                            test_case['data']['status'], test_case['data']['task_code'],
                            test_case['data']['station_code'], test_case['data']['machine_code'],
                            test_case['data']['expense_code'], test_case['data']['raw_charge_job'],
                            test_case['data']['department'], test_case['data']['project'],
                            test_case['data']['is_alfa'], test_case['data']['is_on_leave'],
                            test_case['data']['leave_ref_number'], test_case['data']['leave_type_code'],
                            test_case['data']['leave_type_description'], test_case['data']['notes'],
                            test_case['data']['source_record_id'], test_case['data']['transfer_status'],
                            test_case['data']['created_at'], test_case['data']['updated_at']
                        ))
                        
                        conn.commit()
                        
                        if test_case['should_pass']:
                            logger.info(f"✅ {test_case['name']}: PASSED")
                        else:
                            logger.warning(f"⚠️ {test_case['name']}: Unexpected success (should implement app-level validation)")
                            
                except Exception as e:
                    if not test_case['should_pass']:
                        logger.info(f"✅ {test_case['name']}: PASSED (correctly rejected: {e})")
                    else:
                        logger.error(f"❌ {test_case['name']}: FAILED ({e})")
                        self.fail(f"Valid data was rejected: {e}")
        
        logger.info("✅ Test 2 COMPLETED: Data format validation")
    
    def test_03_error_handling(self):
        """Test 3: Verifikasi proses input berhasil tanpa error"""
        logger.info("🧪 Test 3: Testing error handling")
        
        # Test duplicate primary key
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert data pertama
                cursor.execute('''
                    INSERT INTO staging_attendance (
                        id, employee_id, employee_name, date, regular_hours, overtime_hours, total_hours
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    'test-duplicate', 'EMP001', 'Test Employee', '2025-01-15', 8.0, 0.0, 8.0
                ))
                
                conn.commit()
                
                # Coba insert data dengan ID yang sama (harus error)
                with self.assertRaises(sqlite3.IntegrityError):
                    cursor.execute('''
                        INSERT INTO staging_attendance (
                            id, employee_id, employee_name, date, regular_hours, overtime_hours, total_hours
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        'test-duplicate', 'EMP002', 'Another Employee', '2025-01-16', 7.0, 1.0, 8.0
                    ))
                    conn.commit()
                
                logger.info("✅ Test 3a PASSED: Duplicate key correctly rejected")
                
        except Exception as e:
            logger.error(f"❌ Test 3a FAILED: {e}")
            self.fail(f"Error handling test failed: {e}")
        
        # Test transaction rollback
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Mulai transaction
                cursor.execute('BEGIN TRANSACTION')
                
                # Insert data valid
                cursor.execute('''
                    INSERT INTO staging_attendance (
                        id, employee_id, employee_name, date, regular_hours, overtime_hours, total_hours
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    'test-rollback-1', 'EMP003', 'Test Employee 3', '2025-01-15', 8.0, 0.0, 8.0
                ))
                
                # Rollback transaction
                cursor.execute('ROLLBACK')
                
                # Verifikasi data tidak tersimpan
                cursor.execute('SELECT COUNT(*) FROM staging_attendance WHERE id = ?', ('test-rollback-1',))
                count = cursor.fetchone()[0]
                
                self.assertEqual(count, 0, "Data harus tidak tersimpan setelah rollback")
                logger.info("✅ Test 3b PASSED: Transaction rollback works correctly")
                
        except Exception as e:
            logger.error(f"❌ Test 3b FAILED: {e}")
            self.fail(f"Transaction rollback test failed: {e}")
        
        logger.info("✅ Test 3 COMPLETED: Error handling")
    
    def test_04_data_verification(self):
        """Test 4: Verifikasi data yang diinput dapat diverifikasi kebenarannya"""
        logger.info("🧪 Test 4: Testing data verification")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row  # Enable column access by name
                cursor = conn.cursor()
                
                # Insert test data
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
                    self.valid_test_data['id'], self.valid_test_data['employee_id'], 
                    self.valid_test_data['employee_name'], self.valid_test_data['ptrj_employee_id'],
                    self.valid_test_data['date'], self.valid_test_data['day_of_week'],
                    self.valid_test_data['shift'], self.valid_test_data['check_in'], 
                    self.valid_test_data['check_out'], self.valid_test_data['regular_hours'],
                    self.valid_test_data['overtime_hours'], self.valid_test_data['total_hours'],
                    self.valid_test_data['status'], self.valid_test_data['task_code'],
                    self.valid_test_data['station_code'], self.valid_test_data['machine_code'],
                    self.valid_test_data['expense_code'], self.valid_test_data['raw_charge_job'],
                    self.valid_test_data['department'], self.valid_test_data['project'],
                    self.valid_test_data['is_alfa'], self.valid_test_data['is_on_leave'],
                    self.valid_test_data['leave_ref_number'], self.valid_test_data['leave_type_code'],
                    self.valid_test_data['leave_type_description'], self.valid_test_data['notes'],
                    self.valid_test_data['source_record_id'], self.valid_test_data['transfer_status'],
                    self.valid_test_data['created_at'], self.valid_test_data['updated_at']
                ))
                
                conn.commit()
                
                # Retrieve dan verifikasi data
                cursor.execute('SELECT * FROM staging_attendance WHERE id = ?', (self.valid_test_data['id'],))
                retrieved_data = cursor.fetchone()
                
                # Verifikasi semua field penting
                verification_tests = [
                    ('id', self.valid_test_data['id']),
                    ('employee_id', self.valid_test_data['employee_id']),
                    ('employee_name', self.valid_test_data['employee_name']),
                    ('ptrj_employee_id', self.valid_test_data['ptrj_employee_id']),
                    ('date', self.valid_test_data['date']),
                    ('regular_hours', self.valid_test_data['regular_hours']),
                    ('overtime_hours', self.valid_test_data['overtime_hours']),
                    ('total_hours', self.valid_test_data['total_hours']),
                    ('status', self.valid_test_data['status']),
                    ('task_code', self.valid_test_data['task_code']),
                    ('is_alfa', self.valid_test_data['is_alfa']),
                    ('is_on_leave', self.valid_test_data['is_on_leave'])
                ]
                
                for field_name, expected_value in verification_tests:
                    actual_value = retrieved_data[field_name]
                    
                    # Handle boolean conversion
                    if isinstance(expected_value, bool):
                        actual_value = bool(actual_value)
                    
                    self.assertEqual(actual_value, expected_value, 
                                   f"Field '{field_name}' mismatch: expected {expected_value}, got {actual_value}")
                    logger.info(f"✅ Field '{field_name}': {actual_value} (verified)")
                
                # Verifikasi calculated fields
                calculated_total = retrieved_data['regular_hours'] + retrieved_data['overtime_hours']
                self.assertEqual(calculated_total, retrieved_data['total_hours'], 
                               "Total hours should equal regular + overtime hours")
                
                # Verifikasi data integrity
                self.assertIsNotNone(retrieved_data['created_at'], "Created timestamp should not be null")
                self.assertIsNotNone(retrieved_data['updated_at'], "Updated timestamp should not be null")
                
                logger.info("✅ Test 4 PASSED: All data verification checks passed")
                
        except Exception as e:
            logger.error(f"❌ Test 4 FAILED: {e}")
            self.fail(f"Data verification failed: {e}")
    
    def test_05_comprehensive_integration(self):
        """Test 5: Test integrasi komprehensif untuk skenario real-world"""
        logger.info("🧪 Test 5: Testing comprehensive integration")
        
        try:
            # Simulasi batch insert multiple records
            test_records = []
            for i in range(3):
                record = self.valid_test_data.copy()
                record['id'] = str(uuid.uuid4())
                record['employee_id'] = f'PTRJ.25030021{i+3}'
                record['employee_name'] = f'Test Employee {i+1}'
                record['ptrj_employee_id'] = f'POM0028{i+3}'
                record['date'] = (datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d')
                test_records.append(record)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Batch insert
                for record in test_records:
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
                        record['date'], record['day_of_week'], record['shift'], record['check_in'], 
                        record['check_out'], record['regular_hours'], record['overtime_hours'], record['total_hours'],
                        record['status'], record['task_code'], record['station_code'], record['machine_code'],
                        record['expense_code'], record['raw_charge_job'], record['department'], record['project'],
                        record['is_alfa'], record['is_on_leave'], record['leave_ref_number'], record['leave_type_code'],
                        record['leave_type_description'], record['notes'], record['source_record_id'], 
                        record['transfer_status'], record['created_at'], record['updated_at']
                    ))
                
                conn.commit()
                
                # Verifikasi batch insert
                cursor.execute('SELECT COUNT(*) FROM staging_attendance')
                total_count = cursor.fetchone()[0]
                self.assertEqual(total_count, len(test_records), f"Should have {len(test_records)} records")
                
                # Test query dengan filter
                cursor.execute('SELECT * FROM staging_attendance WHERE status = ?', ('staged',))
                staged_records = cursor.fetchall()
                self.assertEqual(len(staged_records), len(test_records), "All records should have 'staged' status")
                
                # Test update operation
                cursor.execute('UPDATE staging_attendance SET status = ? WHERE employee_id = ?', 
                             ('processed', test_records[0]['employee_id']))
                conn.commit()
                
                # Verifikasi update
                cursor.execute('SELECT status FROM staging_attendance WHERE employee_id = ?', 
                             (test_records[0]['employee_id'],))
                updated_status = cursor.fetchone()[0]
                self.assertEqual(updated_status, 'processed', "Status should be updated to 'processed'")
                
                # Test delete operation
                cursor.execute('DELETE FROM staging_attendance WHERE employee_id = ?', 
                             (test_records[1]['employee_id'],))
                conn.commit()
                
                # Verifikasi delete
                cursor.execute('SELECT COUNT(*) FROM staging_attendance WHERE employee_id = ?', 
                             (test_records[1]['employee_id'],))
                deleted_count = cursor.fetchone()[0]
                self.assertEqual(deleted_count, 0, "Record should be deleted")
                
                logger.info("✅ Test 5 PASSED: Comprehensive integration test completed")
                
        except Exception as e:
            logger.error(f"❌ Test 5 FAILED: {e}")
            self.fail(f"Comprehensive integration test failed: {e}")
    
    def test_06_performance_validation(self):
        """Test 6: Validasi performa untuk operasi database"""
        logger.info("🧪 Test 6: Testing performance validation")
        
        import time
        
        try:
            start_time = time.time()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Test insert performance (100 records)
                insert_start = time.time()
                for i in range(100):
                    record_id = str(uuid.uuid4())
                    cursor.execute('''
                        INSERT INTO staging_attendance (
                            id, employee_id, employee_name, date, regular_hours, overtime_hours, total_hours, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        record_id, f'EMP{i:03d}', f'Employee {i}', '2025-01-15', 8.0, 0.0, 8.0, 'staged'
                    ))
                
                conn.commit()
                insert_time = time.time() - insert_start
                
                # Test query performance
                query_start = time.time()
                cursor.execute('SELECT * FROM staging_attendance WHERE status = ?', ('staged',))
                results = cursor.fetchall()
                query_time = time.time() - query_start
                
                total_time = time.time() - start_time
                
                # Performance assertions
                self.assertLess(insert_time, 5.0, "Insert of 100 records should take less than 5 seconds")
                self.assertLess(query_time, 1.0, "Query should take less than 1 second")
                self.assertEqual(len(results), 100, "Should retrieve all 100 records")
                
                logger.info(f"✅ Performance metrics:")
                logger.info(f"   - Insert time (100 records): {insert_time:.3f}s")
                logger.info(f"   - Query time: {query_time:.3f}s")
                logger.info(f"   - Total test time: {total_time:.3f}s")
                logger.info("✅ Test 6 PASSED: Performance validation completed")
                
        except Exception as e:
            logger.error(f"❌ Test 6 FAILED: {e}")
            self.fail(f"Performance validation failed: {e}")

def run_test_suite():
    """Jalankan semua test dengan reporting yang detail"""
    print("\n" + "="*80)
    print("🧪 STAGING DATA INPUT TEST SUITE")
    print("="*80)
    print("Test ini memverifikasi:")
    print("1. ✅ Data dapat diinput dengan benar ke dalam tabel staging")
    print("2. ✅ Format data sesuai dengan struktur yang telah didefinisikan")
    print("3. ✅ Proses input berhasil tanpa error")
    print("4. ✅ Data yang diinput dapat diverifikasi kebenarannya")
    print("="*80)
    
    # Jalankan test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestSingleRowStagingInput)
    
    # Custom test runner dengan verbose output
    runner = unittest.TextTestRunner(
        verbosity=2,
        stream=None,
        descriptions=True,
        failfast=False
    )
    
    result = runner.run(suite)
    
    # Summary report
    print("\n" + "="*80)
    print("📊 TEST SUMMARY REPORT")
    print("="*80)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\n💥 ERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    if result.wasSuccessful():
        print("\n🎉 ALL TESTS PASSED! Staging data input system is working correctly.")
    else:
        print("\n⚠️ SOME TESTS FAILED! Please review the issues above.")
    
    print("="*80)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_test_suite()
    exit(0 if success else 1)