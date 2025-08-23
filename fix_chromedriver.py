#!/usr/bin/env python3
"""
Quick ChromeDriver Fix Script
Clears cache and reinstalls ChromeDriver to fix common issues
"""

import os
import shutil
import sys

def clear_webdriver_cache():
    """Clear WebDriver Manager cache"""
    print("🧹 Clearing WebDriver Manager cache...")
    
    cache_dirs = [
        os.path.expanduser("~/.wdm"),  # Linux/Mac
        os.path.expanduser("~/AppData/Local/Temp/.wdm"),  # Windows temp
        os.path.expanduser("~/AppData/Roaming/.wdm"),  # Windows roaming
        os.path.expanduser("~/Library/Application Support/.wdm")  # macOS
    ]
    
    cleared_any = False
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                shutil.rmtree(cache_dir)
                print(f"✅ Cleared cache: {cache_dir}")
                cleared_any = True
            except Exception as e:
                print(f"⚠️ Failed to clear {cache_dir}: {e}")
    
    if not cleared_any:
        print("ℹ️ No WebDriver cache found to clear")

def test_chromedriver_fresh():
    """Test ChromeDriver with fresh download"""
    print("\n🔧 Testing ChromeDriver with fresh download...")
    
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        
        # Force fresh download
        print("🌐 Downloading fresh ChromeDriver...")
        driver_path = ChromeDriverManager(cache_valid_range=1).install()
        print(f"✅ ChromeDriver installed at: {driver_path}")
        
        # Validate the path
        if os.path.exists(driver_path):
            file_size = os.path.getsize(driver_path)
            print(f"✅ File exists, size: {file_size} bytes")
            
            if file_size > 1000000:  # Should be several MB
                print("✅ File size looks reasonable")
                return True
            else:
                print("⚠️ File size seems too small")
                return False
        else:
            print(f"❌ File does not exist: {driver_path}")
            return False
            
    except Exception as e:
        print(f"❌ ChromeDriver test failed: {e}")
        return False

def test_simple_selenium():
    """Test simple Selenium functionality"""
    print("\n🧪 Testing simple Selenium functionality...")
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager
        
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run headless for testing
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-gpu')
        
        # Setup service
        service = Service(ChromeDriverManager().install())
        
        print("🚀 Creating WebDriver...")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print("🌐 Testing navigation...")
        driver.get("about:blank")
        
        current_url = driver.current_url
        print(f"✅ Current URL: {current_url}")
        
        print("🧹 Closing WebDriver...")
        driver.quit()
        
        print("✅ Selenium test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Selenium test failed: {e}")
        print(f"🔍 Error type: {type(e).__name__}")
        return False

def main():
    """Main function"""
    print("🔧 CHROMEDRIVER FIX SCRIPT")
    print("=" * 50)
    
    # Step 1: Clear cache
    clear_webdriver_cache()
    
    # Step 2: Test fresh ChromeDriver
    if test_chromedriver_fresh():
        print("\n✅ ChromeDriver installation successful!")
    else:
        print("\n❌ ChromeDriver installation failed!")
        return False
    
    # Step 3: Test Selenium
    if test_simple_selenium():
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ ChromeDriver is working correctly")
        print("✅ You can now run the automation system")
        return True
    else:
        print("\n❌ Selenium test failed!")
        print("🔧 Try these solutions:")
        print("1. Update Google Chrome browser")
        print("2. Run as administrator")
        print("3. Check antivirus/firewall settings")
        print("4. Restart your computer")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 