"""
Venus AutoFill - API Data Automation Runner
Fetches data from API and automates form filling with exact sequence
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.persistent_browser_manager import PersistentBrowserManager
from core.api_data_automation import APIDataAutomation


def setup_logging():
    """Setup comprehensive logging for API automation"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('api_automation.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Reduce selenium noise
    logging.getLogger('selenium.webdriver.remote.remote_connection').setLevel(logging.WARNING)
    logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)


async def main():
    """Main automation runner"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("🚀 Venus AutoFill - API Data Automation")
    print("=" * 50)
    
    browser_manager = None
    try:
        # Initialize browser manager
        logger.info("Initializing browser manager...")
        browser_manager = PersistentBrowserManager()
        
        # Initialize API automation
        logger.info("Initializing API automation...")
        api_automation = APIDataAutomation(browser_manager)
        
        # Check API connectivity first
        logger.info("Testing API connectivity...")
        try:
            records = await api_automation.fetch_staging_data()
            logger.info(f"✅ API connected successfully, found {len(records)} records")
            
            # Show sample data
            if records:
                sample = records[0]
                logger.info("📋 Sample record:")
                logger.info(f"  Employee: {sample.get('employee_name', 'N/A')}")
                logger.info(f"  Date: {sample.get('date', 'N/A')}")
                logger.info(f"  Charge Job: {sample.get('raw_charge_job', 'N/A')[:50]}...")
        
        except Exception as e:
            logger.error(f"❌ API connectivity test failed: {e}")
            logger.error("Please ensure API server is running at http://localhost:5173")
            return False
        
        # Confirm before proceeding
        print("\n🔍 Ready to start automation!")
        print(f"📊 Records to process: {len(records)}")
        print("🔄 Sequence: Date → Employee → Task → Station → Machine → Expense")
        print("⚠️  Transaction type and shift will be skipped")
        
        confirm = input("\nProceed with automation? (y/N): ").strip().lower()
        if confirm != 'y':
            logger.info("Automation cancelled by user")
            return False
        
        # Run automation
        logger.info("🚀 Starting API automation...")
        success = await api_automation.run_api_automation()
        
        if success:
            logger.info("🎉 API automation completed successfully!")
            return True
        else:
            logger.error("❌ API automation failed")
            return False
            
    except KeyboardInterrupt:
        logger.info("🛑 Automation interrupted by user")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False
    finally:
        # Cleanup
        if browser_manager:
            logger.info("🧹 Cleaning up browser resources...")
            try:
                await browser_manager.cleanup()
            except Exception as e:
                logger.warning(f"⚠️ Cleanup warning: {e}")


if __name__ == "__main__":
    print("🌟 Venus AutoFill - API Data Automation")
    print("📡 Fetching data from: http://localhost:5173/api/staging/data")
    print("🎯 Target: Millware ERP Task Register")
    
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n🛑 Automation stopped by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1) 