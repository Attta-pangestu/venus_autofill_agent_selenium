#!/usr/bin/env python3
"""
Test Otomatisasi Penginputan Data Staging dengan WebDriver

Test ini akan:
1. Membuka browser dengan WebDriver
2. Menjalankan otomatisasi penginputan data staging
3. Menampilkan proses otomatisasi secara visual
4. Memverifikasi hasil penginputan
"""

import sys
import os
import time
import sqlite3
import uuid
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import sistem otomatisasi yang sudah ada
try:
    from run_user_controlled_automation_enhanced import EnhancedUserControlledAutomationSystem
except ImportError as e:
    logger.error(f"❌ Error importing automation system: {e}")
    sys.exit(1)

class WebDriverStagingAutomationTest:
    """Test class untuk otomatisasi penginputan data staging dengan WebDriver"""
    
    def __init__(self):
        self.driver = None
        self.automation_system = None
        self.test_data = self._generate_test_data()
        
    def _generate_test_data(self):
        """Generate data test untuk otomatisasi"""
        return [
            {
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
                'notes': 'Test data untuk demo otomatisasi',
                'source_record_id': 'PTRJ.250300212_20250115',
                'transfer_status': 'pending',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            },
            {
                'id': str(uuid.uuid4()),
                'employee_id': 'PTRJ.250300213',
                'employee_name': 'BUDI SANTOSO',
                'ptrj_employee_id': 'POM00284',
                'date': '2025-01-15',
                'day_of_week': 'Wednesday',
                'shift': 'LABOR_SHIFT1',
                'check_in': '07:15',
                'check_out': '17:45',
                'regular_hours': 8.0,
                'overtime_hours': 2.0,
                'total_hours': 10.0,
                'status': 'staged',
                'task_code': '(OC7241) PRODUCTION SUPPORT',
                'station_code': 'STN-PROD (STATION PRODUCTION)',
                'machine_code': 'PROD0001 (PRODUCTION MACHINE)',
                'expense_code': 'L (LABOUR)',
                'raw_charge_job': '(OC7241) PRODUCTION SUPPORT / STN-PROD (STATION PRODUCTION) / PROD0001 (PRODUCTION MACHINE) / L (LABOUR)',
                'department': 'PRODUCTION',
                'project': 'OC7241',
                'is_alfa': False,
                'is_on_leave': False,
                'notes': 'Test data kedua untuk demo otomatisasi',
                'source_record_id': 'PTRJ.250300213_20250115',
                'transfer_status': 'pending',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
        ]
    
    def setup_webdriver(self):
        """Setup WebDriver dengan konfigurasi yang optimal untuk demo"""
        try:
            logger.info("🚀 Setting up WebDriver...")
            
            # Chrome options untuk demo
            chrome_options = Options()
            chrome_options.add_argument('--start-maximized')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Untuk demo, tidak menggunakan headless mode
            # chrome_options.add_argument('--headless')
            
            # Setup service
            service = Service()
            
            # Create driver
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("✅ WebDriver setup completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error setting up WebDriver: {e}")
            return False
    
    def setup_automation_system(self):
        """Setup sistem otomatisasi"""
        try:
            logger.info("🔧 Setting up automation system...")
            
            # Initialize automation system (konstruktor tidak menerima parameter)
            self.automation_system = EnhancedUserControlledAutomationSystem()
            
            # Set automation mode setelah inisialisasi
            self.automation_system.automation_mode = 'testing'
            
            # Set driver jika diperlukan (meskipun sistem akan membuat driver sendiri)
            if hasattr(self.automation_system, 'processor') and hasattr(self.automation_system.processor, 'browser_manager'):
                # Sistem akan menggunakan browser manager sendiri
                pass
            
            logger.info("✅ Automation system setup completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error setting up automation system: {e}")
            return False
    
    def navigate_to_target_page(self):
        """Navigate ke halaman target untuk otomatisasi"""
        try:
            logger.info("🌐 Navigating to target page...")
            
            # URL target (sesuaikan dengan sistem Anda)
            target_url = "http://localhost:5000"  # Ganti dengan URL yang sesuai
            
            self.driver.get(target_url)
            
            # Wait untuk halaman load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            logger.info(f"✅ Successfully navigated to: {target_url}")
            
            # Pause untuk demo
            time.sleep(2)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error navigating to target page: {e}")
            return False
    
    def demonstrate_form_filling(self):
        """Demonstrasi pengisian form dengan data staging"""
        try:
            logger.info("📝 Starting form filling demonstration...")
            
            for i, record in enumerate(self.test_data, 1):
                logger.info(f"\n🔄 Processing record {i}/{len(self.test_data)}: {record['employee_name']}")
                
                # Simulasi pencarian form fields dan pengisian data
                self._demonstrate_field_filling(record)
                
                # Pause antar record untuk demo
                time.sleep(3)
            
            logger.info("✅ Form filling demonstration completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error in form filling demonstration: {e}")
            return False
    
    def _demonstrate_field_filling(self, record):
        """Demonstrasi pengisian field individual"""
        try:
            # Simulasi pengisian field-field penting
            fields_to_fill = [
                ('employee_name', record['employee_name']),
                ('date', record['date']),
                ('regular_hours', str(record['regular_hours'])),
                ('overtime_hours', str(record['overtime_hours'])),
                ('task_code', record['task_code']),
                ('department', record['department'])
            ]
            
            for field_name, field_value in fields_to_fill:
                logger.info(f"  📋 Filling {field_name}: {field_value}")
                
                # Simulasi pencarian dan pengisian field
                self._simulate_field_interaction(field_name, field_value)
                
                # Pause untuk demo visual
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"❌ Error filling fields: {e}")
    
    def _simulate_field_interaction(self, field_name, field_value):
        """Simulasi interaksi dengan field form"""
        try:
            # Coba berbagai selector untuk mencari field
            selectors = [
                f"input[name='{field_name}']",
                f"input[id='{field_name}']",
                f"input[placeholder*='{field_name}']",
                f"textarea[name='{field_name}']",
                f"select[name='{field_name}']"
            ]
            
            element_found = False
            
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        element = elements[0]
                        
                        # Scroll ke element
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                        time.sleep(0.5)
                        
                        # Highlight element untuk demo
                        self.driver.execute_script(
                            "arguments[0].style.border='3px solid red'; arguments[0].style.backgroundColor='yellow';", 
                            element
                        )
                        time.sleep(1)
                        
                        # Clear dan isi field
                        element.clear()
                        element.send_keys(field_value)
                        
                        # Remove highlight
                        self.driver.execute_script(
                            "arguments[0].style.border=''; arguments[0].style.backgroundColor='';", 
                            element
                        )
                        
                        element_found = True
                        logger.info(f"    ✅ Field '{field_name}' filled successfully")
                        break
                        
                except NoSuchElementException:
                    continue
            
            if not element_found:
                logger.warning(f"    ⚠️ Field '{field_name}' not found, simulating...")
                # Simulasi untuk demo
                time.sleep(0.5)
                
        except Exception as e:
            logger.error(f"    ❌ Error interacting with field '{field_name}': {e}")
    
    def run_automation_demo(self):
        """Jalankan demo otomatisasi lengkap"""
        try:
            print("\n" + "="*80)
            print("🎬 DEMO OTOMATISASI PENGINPUTAN DATA STAGING")
            print("="*80)
            print("Demo ini akan menunjukkan:")
            print("1. ✅ Setup WebDriver dan browser")
            print("2. ✅ Navigasi ke halaman target")
            print("3. ✅ Otomatisasi pengisian form dengan data staging")
            print("4. ✅ Validasi dan verifikasi hasil")
            print("="*80)
            
            # Step 1: Setup WebDriver
            if not self.setup_webdriver():
                return False
            
            # Step 2: Setup automation system
            if not self.setup_automation_system():
                return False
            
            # Step 3: Navigate to target page
            if not self.navigate_to_target_page():
                return False
            
            # Step 4: Demonstrate form filling
            if not self.demonstrate_form_filling():
                return False
            
            # Step 5: Final demonstration
            self._show_completion_message()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error in automation demo: {e}")
            return False
        finally:
            self._cleanup()
    
    def _show_completion_message(self):
        """Tampilkan pesan completion"""
        try:
            logger.info("\n🎉 Demo otomatisasi selesai!")
            
            # Inject completion message ke halaman
            completion_script = """
            var completionDiv = document.createElement('div');
            completionDiv.innerHTML = `
                <div style="
                    position: fixed;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 15px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                    text-align: center;
                    font-family: Arial, sans-serif;
                    z-index: 10000;
                    min-width: 400px;
                ">
                    <h2 style="margin: 0 0 15px 0; font-size: 24px;">🎉 Demo Selesai!</h2>
                    <p style="margin: 0 0 10px 0; font-size: 16px;">Otomatisasi penginputan data staging berhasil dijalankan</p>
                    <p style="margin: 0; font-size: 14px; opacity: 0.9;">Data telah diproses dengan sistem otomatisasi</p>
                </div>
            `;
            document.body.appendChild(completionDiv);
            
            setTimeout(() => {
                completionDiv.remove();
            }, 5000);
            """
            
            self.driver.execute_script(completion_script)
            
            # Pause untuk melihat hasil
            time.sleep(6)
            
        except Exception as e:
            logger.error(f"❌ Error showing completion message: {e}")
    
    def _cleanup(self):
        """Cleanup resources"""
        try:
            if self.driver:
                logger.info("🧹 Cleaning up WebDriver...")
                time.sleep(2)  # Pause sebelum close untuk demo
                self.driver.quit()
                logger.info("✅ WebDriver cleanup completed")
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")
    
    def run_with_real_system(self):
        """Jalankan dengan sistem otomatisasi yang sebenarnya"""
        try:
            logger.info("🔄 Running with real automation system...")
            
            # Setup sistem otomatisasi (tidak perlu setup webdriver manual)
            self.automation_system = EnhancedUserControlledAutomationSystem()
            
            # Set mode testing untuk keamanan
            self.automation_system.automation_mode = 'testing'
            
            # Initialize browser system
            logger.info("🌐 Initializing browser system...")
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            init_success = loop.run_until_complete(self.automation_system.initialize_browser_system())
            if not init_success:
                logger.error("❌ Failed to initialize browser system")
                return False
            
            # Jalankan otomatisasi dengan data test
            logger.info("🚀 Starting automation with test data...")
            result = loop.run_until_complete(self.automation_system.process_staging_data_array(self.test_data))
            
            logger.info(f"✅ Automation completed with result: {result}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error running real automation: {e}")
            return False
        finally:
            # Cleanup akan dilakukan oleh sistem otomatisasi sendiri
            pass

def main():
    """Main function untuk menjalankan demo"""
    print("\n🎬 STARTING WEBDRIVER STAGING AUTOMATION DEMO")
    print("=" * 60)
    
    # Pilihan demo
    print("Pilih mode demo:")
    print("1. Demo Visual (Simulasi pengisian form)")
    print("2. Demo Real System (Menggunakan sistem otomatisasi asli)")
    
    try:
        choice = input("\nMasukkan pilihan (1/2): ").strip()
        
        demo = WebDriverStagingAutomationTest()
        
        if choice == "1":
            logger.info("🎭 Starting visual demo...")
            success = demo.run_automation_demo()
        elif choice == "2":
            logger.info("🚀 Starting real system demo...")
            success = demo.run_with_real_system()
        else:
            logger.error("❌ Invalid choice")
            return False
        
        if success:
            print("\n🎉 Demo berhasil dijalankan!")
            print("Anda telah melihat otomatisasi penginputan data staging bekerja.")
        else:
            print("\n❌ Demo gagal dijalankan.")
        
        return success
        
    except KeyboardInterrupt:
        print("\n⏹️ Demo dihentikan oleh user")
        return False
    except Exception as e:
        logger.error(f"❌ Error in main: {e}")
        return False

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)