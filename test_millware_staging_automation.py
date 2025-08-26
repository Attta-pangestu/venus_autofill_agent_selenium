#!/usr/bin/env python3
"""
Test WebDriver Staging Data Input Automation for Millware Task Register
Demonstrates real-time staging data input automation using WebDriver
Targets the actual Millware system at millwarep3.rebinmas.com
"""

import asyncio
import sys
import os
import logging
from datetime import datetime
from typing import Dict, List

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.api_data_automation import RealAPIDataProcessor
from core.persistent_browser_manager import PersistentBrowserManager
from core.database_manager import DatabaseManager

class MillwareAutomationDemo:
    """Demonstrates staging data input automation for Millware Task Register"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.db_manager = DatabaseManager()
        self.processor = None
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('millware_automation_demo.log')
            ]
        )
        return logging.getLogger(__name__)
    
    def get_sample_staging_data(self) -> List[Dict]:
        """Get sample staging data for demonstration"""
        try:
            # Connect to staging database
            if not self.db_manager.test_connection():
                self.logger.error("❌ Cannot connect to staging database")
                return []
            
            # Fetch recent staging data (limit to 3 records for demo)
            results = self.db_manager.fetch_all_staging_data('staged')[:3]
            
            if not results:
                # If no recent data, create sample data
                self.logger.info("📝 No recent staging data found, using sample data")
                return [
                    {
                        'employee_name': 'JOHN DOE',
                        'trx_date': '2024-01-15',
                        'normal_hours': 8.0,
                        'overtime_hours': 2.0,
                        'charge_job': 'PRJ001-ACT001-LAB001',
                        'activity_name': 'Construction Work',
                        'labour_type': 'Regular'
                    },
                    {
                        'employee_name': 'JANE SMITH',
                        'trx_date': '2024-01-15',
                        'normal_hours': 8.0,
                        'overtime_hours': 0.0,
                        'charge_job': 'PRJ002-ACT002-LAB002',
                        'activity_name': 'Engineering Work',
                        'labour_type': 'Skilled'
                    }
                ]
            
            # Convert database results to the expected format
            staging_data = []
            for record in results:
                staging_data.append({
                    'employee_name': record['employee_name'],
                    'trx_date': record['date'],  # Note: database uses 'date' field
                    'normal_hours': float(record['regular_hours']) if record['regular_hours'] else 0.0,
                    'overtime_hours': float(record['overtime_hours']) if record['overtime_hours'] else 0.0,
                    'charge_job': record['raw_charge_job'] or '',
                    'activity_name': record['task_code'] or '',  # Using task_code as activity
                    'labour_type': 'Regular'  # Default value
                })
            
            self.logger.info(f"📊 Retrieved {len(staging_data)} staging records")
            return staging_data
            
        except Exception as e:
            self.logger.error(f"❌ Error fetching staging data: {e}")
            return []
    
    async def run_millware_automation_demo(self):
        """Run the complete Millware automation demonstration"""
        print("\n" + "="*60)
        print("🚀 MILLWARE TASK REGISTER AUTOMATION DEMO")
        print("="*60)
        
        try:
            # Initialize the RealAPIDataProcessor
            self.logger.info("🔧 Initializing RealAPIDataProcessor...")
            self.processor = RealAPIDataProcessor()
            
            # Initialize browser and connect to Millware
            print("\n📱 Step 1: Initializing browser and connecting to Millware...")
            browser_initialized = await self.processor.initialize_browser()
            
            if not browser_initialized:
                print("❌ Failed to initialize browser or connect to Millware")
                print("🔧 Please check:")
                print("   - Internet connection")
                print("   - Millware server accessibility (millwarep3.rebinmas.com)")
                print("   - Chrome browser installation")
                return False
            
            print("✅ Browser initialized and connected to Millware Task Register")
            
            # Get staging data
            print("\n📊 Step 2: Fetching staging data...")
            staging_data = self.get_sample_staging_data()
            
            if not staging_data:
                print("❌ No staging data available for demonstration")
                return False
            
            print(f"✅ Retrieved {len(staging_data)} staging records")
            
            # Display staging data
            print("\n📋 Staging Data to be processed:")
            for i, record in enumerate(staging_data, 1):
                print(f"   {i}. Employee: {record['employee_name']}")
                print(f"      Date: {record['trx_date']}")
                print(f"      Normal Hours: {record['normal_hours']}")
                print(f"      Overtime Hours: {record['overtime_hours']}")
                print(f"      Charge Job: {record['charge_job']}")
                print("")
            
            # Process records with visual demonstration
            print("\n🎯 Step 3: Processing records in Millware Task Register...")
            print("⏳ This will demonstrate real-time form filling...")
            
            # Group records by date for batch processing
            grouped_records = self.processor.group_records_by_date(staging_data)
            
            success_count = 0
            total_count = len(staging_data)
            
            for date_group, records in grouped_records.items():
                print(f"\n📅 Processing date group: {date_group} ({len(records)} records)")
                
                driver = self.processor.browser_manager.get_driver()
                if not driver:
                    print("❌ WebDriver not available")
                    continue
                
                # Process each record in the date group
                for i, record in enumerate(records, 1):
                    print(f"\n   🔄 Processing record {i}/{len(records)}: {record['employee_name']}")
                    
                    try:
                        # Process the record using the real automation system
                        success = await self.processor.process_single_record(
                            driver, record, f"{date_group}-{i}"
                        )
                        
                        if success:
                            print(f"   ✅ Successfully processed: {record['employee_name']}")
                            success_count += 1
                        else:
                            print(f"   ❌ Failed to process: {record['employee_name']}")
                        
                        # Add delay between records for demonstration
                        await asyncio.sleep(2)
                        
                    except Exception as e:
                        print(f"   ❌ Error processing {record['employee_name']}: {e}")
                        self.logger.error(f"Record processing error: {e}")
                
                # Click New button after completing date group
                if len(records) > 0:
                    print(f"\n   🔘 Clicking 'New' button for next date group...")
                    await self.processor.click_new_button(driver)
                    await asyncio.sleep(1)
            
            # Summary
            print("\n" + "="*60)
            print("📊 AUTOMATION DEMO SUMMARY")
            print("="*60)
            print(f"✅ Successfully processed: {success_count}/{total_count} records")
            print(f"📈 Success rate: {(success_count/total_count)*100:.1f}%")
            print(f"🕒 Demo completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            if success_count == total_count:
                print("🎉 All records processed successfully!")
            elif success_count > 0:
                print("⚠️  Some records processed with issues")
            else:
                print("❌ No records were processed successfully")
            
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"❌ Demo execution error: {e}")
            print(f"❌ Demo failed: {e}")
            return False
        
        finally:
            # Cleanup
            if self.processor:
                print("\n🧹 Cleaning up resources...")
                await self.processor.cleanup()
                print("✅ Cleanup completed")
    
    async def run_connection_test(self):
        """Test connection to Millware system"""
        print("\n🔍 Testing connection to Millware system...")
        
        try:
            self.processor = RealAPIDataProcessor()
            
            # Test browser initialization
            browser_initialized = await self.processor.initialize_browser()
            
            if browser_initialized:
                print("✅ Successfully connected to Millware Task Register")
                
                # Get current page info
                driver = self.processor.browser_manager.get_driver()
                if driver:
                    current_url = driver.current_url
                    page_title = driver.title
                    print(f"📄 Current URL: {current_url}")
                    print(f"📋 Page Title: {page_title}")
                
                return True
            else:
                print("❌ Failed to connect to Millware system")
                return False
                
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False
        
        finally:
            if self.processor:
                await self.processor.cleanup()

async def main():
    """Main execution function"""
    demo = MillwareAutomationDemo()
    
    print("Choose demo mode:")
    print("1. Full automation demo (process staging data)")
    print("2. Connection test only")
    
    try:
        choice = input("Enter choice (1 or 2): ").strip()
        
        if choice == "1":
            success = await demo.run_millware_automation_demo()
            if success:
                print("\n🎉 Demo completed successfully!")
            else:
                print("\n❌ Demo completed with issues")
        
        elif choice == "2":
            success = await demo.run_connection_test()
            if success:
                print("\n✅ Connection test passed!")
            else:
                print("\n❌ Connection test failed")
        
        else:
            print("❌ Invalid choice. Please run again and select 1 or 2.")
    
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(main())