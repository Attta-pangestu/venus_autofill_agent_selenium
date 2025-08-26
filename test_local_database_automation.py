#!/usr/bin/env python3
"""
Local Database WebDriver Automation for Millware Task Register

This script demonstrates automated form filling using local database records
instead of API-based data fetching.
"""

import logging
import time
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path
import sys

# Add src directory to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from local_database_manager import LocalDatabaseManager
from core.browser_manager import BrowserManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class LocalDatabaseAutomationDemo:
    """Demonstrates WebDriver automation using local database records"""
    
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        self.db_manager = LocalDatabaseManager()
        self.browser_manager = None
        self.driver = None
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('local_database_automation.log', encoding='utf-8')
            ]
        )
    
    def initialize_browser(self):
        """Initialize browser and navigate to Millware Task Register"""
        try:
            self.logger.info("[INFO] Initializing browser...")
            self.browser_manager = BrowserManager()
            self.driver = self.browser_manager.create_driver()
            
            if not self.driver:
                self.logger.error("[ERROR] Failed to create WebDriver")
                return False
            
            # Navigate to Millware Task Register page
            millware_url = "http://millwarep3.rebinmas.com:8004/en/PR/trx/frmPrTrxTaskRegisterDet.aspx"
            self.logger.info(f"[INFO] Navigating to: {millware_url}")
            
            self.driver.get(millware_url)
            time.sleep(3)  # Wait for page load
            
            # Verify we're on the correct page
            if self._verify_task_register_page():
                self.logger.info("[SUCCESS] Successfully navigated to Task Register page")
                return True
            else:
                self.logger.error("[ERROR] Failed to verify Task Register page")
                return False
                
        except Exception as e:
            self.logger.error(f"[ERROR] Error initializing browser: {e}")
            return False
    
    def _verify_task_register_page(self) -> bool:
        """Verify we're on the Task Register page by checking key elements"""
        try:
            wait = WebDriverWait(self.driver, 10)
            
            # Check for key elements that should be present
            key_elements = [
                "MainContent_txtTrxDate",
                "MainContent_txtEmployee",
                "MainContent_txtActivity"
            ]
            
            for element_id in key_elements:
                try:
                    wait.until(EC.presence_of_element_located((By.ID, element_id)))
                    self.logger.info(f"[SUCCESS] Found element: {element_id}")
                except TimeoutException:
                    self.logger.warning(f"[WARNING] Element not found: {element_id}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"[ERROR] Error verifying page: {e}")
            return False
    
    def get_sample_local_data(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get sample data from local database"""
        try:
            self.logger.info(f"[INFO] Fetching {limit} sample records from local database...")
            
            # Get all staging data
            all_records = self.db_manager.fetch_all_staging_data('staged')
            
            if not all_records:
                self.logger.warning("[WARNING] No staging records found, inserting sample data...")
                self.db_manager.insert_sample_records(5)
                all_records = self.db_manager.fetch_all_staging_data('staged')
            
            # Take the most recent records
            sample_records = all_records[:limit]
            
            # Convert to format expected by automation system
            processed_records = []
            for record in sample_records:
                processed_record = {
                    'id': record['id'],
                    'employee_id': record['employee_id'],
                    'employee_name': record['employee_name'],
                    'date': record['date'],
                    'regular_hours': record['regular_hours'],
                    'overtime_hours': record['overtime_hours'],
                    'total_hours': record['total_hours'],
                    'task_code': record['task_code'],
                    'station_code': record['station_code'],
                    'machine_code': record['machine_code'],
                    'expense_code': record['expense_code'],
                    'raw_charge_job': record['raw_charge_job'],
                    'shift': record['shift'],
                    'check_in': record['check_in'],
                    'check_out': record['check_out']
                }
                processed_records.append(processed_record)
            
            self.logger.info(f"[SUCCESS] Processed {len(processed_records)} records for automation")
            return processed_records
            
        except Exception as e:
            self.logger.error(f"[ERROR] Error getting sample data: {e}")
            return []
    
    def group_records_by_date(self, records: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group records by date for processing"""
        try:
            grouped = {}
            
            for record in records:
                date_key = record.get('date', '')
                if not date_key:
                    self.logger.warning(f"[WARNING] Skipping record with missing date: {record.get('id', 'unknown')}")
                    continue
                
                # Normalize date format
                try:
                    if 'T' in date_key:
                        date_key = date_key.split('T')[0]
                    elif ' ' in date_key:
                        date_key = date_key.split(' ')[0]
                    
                    # Validate date format
                    datetime.strptime(date_key, '%Y-%m-%d')
                    
                    if date_key not in grouped:
                        grouped[date_key] = []
                    grouped[date_key].append(record)
                    
                except ValueError as e:
                    self.logger.warning(f"[WARNING] Invalid date format '{date_key}': {e}")
                    continue
            
            self.logger.info(f"[INFO] Grouped {len(records)} records into {len(grouped)} date groups")
            for date_key, date_records in grouped.items():
                employees = set(r.get('employee_name', 'Unknown') for r in date_records)
                self.logger.info(f"  [DATE] {date_key}: {len(date_records)} records, {len(employees)} employees")
            
            return grouped
            
        except Exception as e:
            self.logger.error(f"[ERROR] Error grouping records: {e}")
            return {}
    
    def fill_form_with_record(self, record: Dict[str, Any]) -> bool:
        """Fill the Millware form with a single record"""
        try:
            self.logger.info(f"[FORM] Filling form for {record.get('employee_name', 'Unknown')} on {record.get('date', 'Unknown')}")
            
            wait = WebDriverWait(self.driver, 10)
            
            # Fill date field
            date_field = wait.until(EC.element_to_be_clickable((By.ID, "MainContent_txtTrxDate")))
            date_field.clear()
            date_field.send_keys(record.get('date', ''))
            time.sleep(1)
            
            # Fill employee field
            employee_field = wait.until(EC.element_to_be_clickable((By.ID, "MainContent_txtEmployee")))
            employee_field.clear()
            employee_field.send_keys(record.get('employee_name', ''))
            time.sleep(1)
            
            # Fill activity/task field
            activity_field = wait.until(EC.element_to_be_clickable((By.ID, "MainContent_txtActivity")))
            activity_field.clear()
            activity_field.send_keys(record.get('task_code', ''))
            time.sleep(1)
            
            # Fill hours if field exists
            try:
                hours_field = self.driver.find_element(By.ID, "MainContent_txtHours")
                hours_field.clear()
                hours_field.send_keys(str(record.get('total_hours', 0)))
                time.sleep(1)
            except NoSuchElementException:
                self.logger.info("[INFO] Hours field not found, skipping")
            
            self.logger.info(f"[SUCCESS] Successfully filled form for {record.get('employee_name', 'Unknown')}")
            return True
            
        except Exception as e:
            self.logger.error(f"[ERROR] Error filling form: {e}")
            return False
    
    def process_records(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process multiple records with visual demonstration"""
        results = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'details': []
        }
        
        try:
            # Group records by date
            grouped_records = self.group_records_by_date(records)
            
            if not grouped_records:
                self.logger.warning("⚠️ No valid records to process")
                return results
            
            # Process each date group
            for date_key, date_records in grouped_records.items():
                self.logger.info(f"\n📅 Processing {len(date_records)} records for date: {date_key}")
                
                for i, record in enumerate(date_records, 1):
                    self.logger.info(f"\n🔄 Processing record {i}/{len(date_records)}")
                    
                    results['total_processed'] += 1
                    
                    if self.fill_form_with_record(record):
                        results['successful'] += 1
                        status = 'success'
                    else:
                        results['failed'] += 1
                        status = 'failed'
                    
                    results['details'].append({
                        'employee_name': record.get('employee_name', 'Unknown'),
                        'date': record.get('date', 'Unknown'),
                        'status': status
                    })
                    
                    # Visual pause between records
                    time.sleep(2)
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Error processing records: {e}")
            return results
    
    def run_automation_demo(self) -> bool:
        """Run the complete automation demonstration"""
        try:
            self.logger.info("\n" + "="*60)
            self.logger.info("[START] LOCAL DATABASE AUTOMATION DEMO STARTING")
            self.logger.info("="*60)
            
            # Test database connection
            if not self.db_manager.test_connection():
                self.logger.error("[ERROR] Database connection failed")
                return False
            
            # Show database stats
            stats = self.db_manager.get_database_stats()
            self.logger.info(f"[INFO] Database Stats: {stats['total_records']} total records, {stats['unique_employees']} employees")
            
            # Initialize browser
            if not self.initialize_browser():
                self.logger.error("[ERROR] Browser initialization failed")
                return False
            
            # Get sample data
            sample_records = self.get_sample_local_data(3)
            if not sample_records:
                self.logger.error("[ERROR] No sample records available")
                return False
            
            # Process records
            results = self.process_records(sample_records)
            
            # Show results
            self.logger.info("\n" + "="*60)
            self.logger.info("[RESULTS] AUTOMATION RESULTS")
            self.logger.info("="*60)
            self.logger.info(f"Total Processed: {results['total_processed']}")
            self.logger.info(f"Successful: {results['successful']}")
            self.logger.info(f"Failed: {results['failed']}")
            
            if results['total_processed'] > 0:
                success_rate = (results['successful'] / results['total_processed']) * 100
                self.logger.info(f"Success Rate: {success_rate:.1f}%")
            
            self.logger.info("\n[DETAILS] Detailed Results:")
            for detail in results['details']:
                status_icon = "[SUCCESS]" if detail['status'] == 'success' else "[FAILED]"
                self.logger.info(f"  {status_icon} {detail['employee_name']} - {detail['date']} - {detail['status']}")
            
            return results['successful'] > 0
            
        except Exception as e:
            self.logger.error(f"[ERROR] Error in automation demo: {e}")
            return False
        
        finally:
            self.cleanup()
    
    def test_connection_only(self) -> bool:
        """Test database and browser connections without processing records"""
        try:
            self.logger.info("\n" + "="*50)
            self.logger.info("[TEST] CONNECTION TEST")
            self.logger.info("="*50)
            
            # Test database
            self.logger.info("\n[1] Testing database connection...")
            if self.db_manager.test_connection():
                stats = self.db_manager.get_database_stats()
                self.logger.info(f"[SUCCESS] Database OK: {stats['total_records']} records available")
            else:
                self.logger.error("[ERROR] Database connection failed")
                return False
            
            # Test browser
            self.logger.info("\n[2] Testing browser connection...")
            if self.initialize_browser():
                self.logger.info("[SUCCESS] Browser OK: Successfully connected to Millware")
                return True
            else:
                self.logger.error("[ERROR] Browser connection failed")
                return False
                
        except Exception as e:
            self.logger.error(f"[ERROR] Connection test failed: {e}")
            return False
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if self.browser_manager:
                self.logger.info("[CLEANUP] Cleaning up browser resources...")
                self.browser_manager.quit_driver()
                self.logger.info("[SUCCESS] Cleanup completed")
        except Exception as e:
            self.logger.error(f"[ERROR] Error during cleanup: {e}")

def main():
    """Main function"""
    print("\n" + "="*60)
    print("LOCAL DATABASE AUTOMATION FOR MILLWARE")
    print("="*60)
    
    print("\nChoose an option:")
    print("1. Run full automation demo")
    print("2. Test connections only")
    print("3. Exit")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == '1':
        demo = LocalDatabaseAutomationDemo()
        success = demo.run_automation_demo()
        if success:
            print("\n[SUCCESS] Automation demo completed successfully!")
        else:
            print("\n[ERROR] Automation demo completed with issues.")
            
    elif choice == '2':
        demo = LocalDatabaseAutomationDemo()
        success = demo.test_connection_only()
        if success:
            print("\n[SUCCESS] All connections are working properly!")
        else:
            print("\n[ERROR] Connection test failed.")
            
    elif choice == '3':
        print("\nGoodbye!")
        
    else:
        print("\n[ERROR] Invalid choice")

if __name__ == "__main__":
    main()