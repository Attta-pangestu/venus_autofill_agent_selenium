"""
Persistent Browser Manager - Enhanced browser management with persistent sessions
Provides pre-initialized WebDriver and session persistence for optimal performance
"""

import os
import time
import logging
import asyncio
import threading
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException

from .browser_manager import BrowserManager


class PersistentBrowserManager:
    """Enhanced browser manager with persistent sessions and pre-initialization"""
    
    # Class-level WebDriver instance tracking for singleton pattern
    _active_driver_instance: Optional[webdriver.Chrome] = None
    _driver_creation_lock = threading.Lock()
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Browser management
        self.browser_manager = BrowserManager(config.get('browser', {}))
        self.driver: Optional[webdriver.Chrome] = None
        self.is_initialized = False
        self.is_logged_in = False
        self.last_activity_time = None
        
        # Session management
        self.login_url = config.get('urls', {}).get('login', 'http://millwarep3:8004/')
        self.task_register_url = config.get('urls', {}).get('taskRegister', 
            'http://millwarep3:8004/en/PR/trx/frmPrTrxTaskRegisterDet.aspx')
        self.username = config.get('credentials', {}).get('username', 'adm075')
        self.password = config.get('credentials', {}).get('password', 'adm075')
        
        # Configuration
        self.session_timeout_minutes = config.get('session', {}).get('timeout_minutes', 30)
        self.keepalive_interval_minutes = config.get('session', {}).get('keepalive_interval', 10)
        
        # Threading for session keepalive
        self.keepalive_thread: Optional[threading.Thread] = None
        self.shutdown_event = threading.Event()
    
    async def initialize(self) -> bool:
        """Initialize the browser and establish persistent session"""
        try:
            if self.is_initialized and self.is_driver_healthy():
                self.logger.info("Browser already initialized and healthy")
                return True
            
            self.logger.info("Initializing persistent browser session...")
            
            # Create WebDriver instance
            await self._create_driver()
            
            # Perform initial login
            await self._perform_initial_login()
            
            # Start session keepalive
            self._start_session_keepalive()
            
            self.is_initialized = True
            self.last_activity_time = datetime.now()
            
            self.logger.info("✅ Persistent browser session initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize persistent browser session: {e}")
            await self.cleanup()
            return False
    
    async def _create_driver(self):
        """Create WebDriver instance with robust timeout settings and singleton pattern"""
        try:
            # Check if there's already an active WebDriver instance
            with PersistentBrowserManager._driver_creation_lock:
                if PersistentBrowserManager._active_driver_instance is not None:
                    try:
                        # Test if the existing driver is still functional
                        PersistentBrowserManager._active_driver_instance.current_url
                        self.logger.info("✅ Reusing existing WebDriver instance (singleton pattern)")
                        self.driver = PersistentBrowserManager._active_driver_instance
                        return
                    except Exception as e:
                        self.logger.warning(f"Existing WebDriver instance is not functional: {e}")
                        # Clean up the non-functional instance
                        try:
                            PersistentBrowserManager._active_driver_instance.quit()
                        except:
                            pass
                        PersistentBrowserManager._active_driver_instance = None
                
                self.logger.info("🔧 Creating new WebDriver instance with enhanced stability (singleton pattern)...")
                
                # Enhanced robust config to prevent connection timeouts and renderer issues
                robust_config = {
                    'page_load_timeout': 60,   # Further increased to prevent renderer timeout
                    'script_timeout': 45,      # Increased for better stability
                    'implicit_wait': 15,       # Increased for better element detection
                    'disable_dev_shm_usage': True,  # Prevent memory issues
                    'no_sandbox': True,        # Improve stability in some environments
                    'disable_extensions': True, # Reduce interference
                    'disable_notifications': True,
                    'window_size': (1280, 720)
                }
                self.driver = self.browser_manager.create_driver(robust_config)
                
                # Store the new instance as the active one
                PersistentBrowserManager._active_driver_instance = self.driver
                self.logger.info("✅ New WebDriver instance created and registered (singleton pattern)")
            
            # Set very robust timeouts to prevent renderer timeout errors and connection issues
            self.driver.set_page_load_timeout(60)  # Further increased for stability
            self.driver.implicitly_wait(15)        # Increased for better element detection
            self.driver.set_script_timeout(45)     # Increased for complex operations
            
            # Navigate to login page with retry mechanism
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    self.logger.info(f"Navigating to login page (attempt {attempt + 1}/{max_retries}): {self.login_url}")
                    self.driver.get(self.login_url)
                    
                    # Wait for page to load with robust timeout
                    await self._wait_for_page_load(timeout=25)
                    self.logger.info("WebDriver created and page loaded successfully")
                    break
                    
                except Exception as e:
                    self.logger.warning(f"Navigation attempt {attempt + 1} failed: {e}")
                    if attempt == max_retries - 1:
                        raise
                    await asyncio.sleep(2)
            
        except Exception as e:
            self.logger.error(f"Failed to create WebDriver: {e}")
            raise
    
    async def _perform_initial_login(self):
        """Perform initial login and handle any popups"""
        try:
            self.logger.info("Performing initial login...")
            
            # Check if already logged in
            if await self._check_login_status():
                self.logger.info("Already logged in, skipping login process")
                self.is_logged_in = True
                return
            
            # Perform login
            await self._login_sequence()
            
            # Verify login success
            if await self._check_login_status():
                self.is_logged_in = True
                self.logger.info("✅ Initial login completed successfully")
            else:
                raise Exception("Login verification failed")
                
        except Exception as e:
            self.logger.error(f"Initial login failed: {e}")
            raise
    
    async def _login_sequence(self):
        """Execute the login sequence"""
        try:
            # Wait for login form to be available with robust timeout
            wait = WebDriverWait(self.driver, 20)  # Increased from 10 to 20 for stability
            
            # Find and fill username
            username_field = wait.until(
                EC.element_to_be_clickable((By.ID, "txtUsername"))
            )
            username_field.clear()
            username_field.send_keys(self.username)
            
            # Find and fill password
            password_field = self.driver.find_element(By.ID, "txtPassword")
            password_field.clear()
            password_field.send_keys(self.password)
            
            # Click login button
            login_button = self.driver.find_element(By.ID, "btnLogin")
            login_button.click()
            
            # Wait for navigation after login with shorter timeout
            await asyncio.sleep(2)  # Reduced from 3 to 2
            
            # Handle any popups that appear after login
            await self._handle_post_login_popups()
            
        except Exception as e:
            self.logger.error(f"Login sequence failed: {e}")
            raise
    
    async def _handle_post_login_popups(self):
        """Handle popups that appear after login and location setting page"""
        try:
            # Common popup selectors to dismiss
            popup_selectors = [
                "#MainContent_btnOkay",
                "#btnOK",
                ".btn-primary",
                "[value='OK']",
                "[value='Okay']"
            ]
            
            for selector in popup_selectors:
                try:
                    popup = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    popup.click()
                    self.logger.info(f"Dismissed popup using selector: {selector}")
                    await asyncio.sleep(2)
                    break
                except TimeoutException:
                    continue
            
            # Handle location setting page if redirected there
            await self._handle_location_setting_page()
                    
        except Exception as e:
            self.logger.warning(f"Popup handling warning: {e}")
            # Don't raise exception for popup handling failures
    
    async def _handle_location_setting_page(self):
        """Handle the location setting page that appears after login"""
        try:
            current_url = self.driver.current_url
            self.logger.info(f"Current URL after popup handling: {current_url}")
            
            # Check if we're on the location setting page
            if "frmSystemUserSetlocation.aspx" in current_url:
                self.logger.info("🎯 Detected location setting page - IMMEDIATE REDIRECT to task register...")
                
                # IMMEDIATE REDIRECT - Don't wait, just navigate directly to task register
                task_register_url = self.config.get('urls', {}).get('taskRegister', 
                    'http://millwarep3:8004/en/PR/trx/frmPrTrxTaskRegisterDet.aspx')
                
                print(f"🚀 IMMEDIATE REDIRECT: {current_url} → {task_register_url}")
                self.logger.info(f"🚀 IMMEDIATE REDIRECT: {current_url} → {task_register_url}")
                
                # Set very short timeout for redirect
                original_page_load_timeout = self.driver.timeouts.page_load
                self.driver.set_page_load_timeout(10)  # Very short timeout for redirect
                
                try:
                    # Navigate directly to task register
                    self.driver.get(task_register_url)
                    
                    # Wait briefly for navigation
                    await asyncio.sleep(1)  # Reduced from 2 to 1
                    
                    # Verify redirect worked
                    new_url = self.driver.current_url
                    self.logger.info(f"After redirect - Current URL: {new_url}")
                    
                    if "frmPrTrxTaskRegisterDet.aspx" in new_url:
                        self.logger.info("✅ IMMEDIATE REDIRECT SUCCESSFUL - Now at task register")
                        print("✅ IMMEDIATE REDIRECT SUCCESSFUL - Now at task register")
                    elif "frmSystemUserSetlocation.aspx" in new_url:
                        # If still on location page, force refresh and redirect
                        self.logger.warning("⚠️ Still on location page - forcing refresh and redirect...")
                        self.driver.refresh()
                        await asyncio.sleep(1)
                        self.driver.get(task_register_url)
                        await asyncio.sleep(2)
                        
                        final_url = self.driver.current_url
                        if "frmPrTrxTaskRegisterDet.aspx" in final_url:
                            self.logger.info("✅ Force refresh redirect successful")
                            print("✅ Force refresh redirect successful")
                        else:
                            self.logger.warning(f"⚠️ Force redirect failed, still at: {final_url}")
                            print(f"⚠️ Force redirect failed, still at: {final_url}")
                    else:
                        self.logger.info(f"✅ Redirected to different page: {new_url}")
                
                finally:
                    # Restore original timeout
                    self.driver.set_page_load_timeout(original_page_load_timeout)
                
            else:
                self.logger.info("✅ No location setting page detected")
                
        except Exception as e:
            self.logger.error(f"Error handling location setting page: {e}")
            print(f"❌ Error handling location setting page: {e}")
            # Don't raise exception - try to continue anyway
    
    async def _handle_location_page_strategies(self):
        """Try multiple strategies to handle the location setting page"""
        try:
            strategies = [
                self._strategy_click_ok_button,
                self._strategy_skip_location_setting,
                self._strategy_navigate_away,
                self._strategy_refresh_and_continue
            ]
            
            for i, strategy in enumerate(strategies, 1):
                try:
                    self.logger.info(f"🔄 Trying location page strategy {i}/{len(strategies)}")
                    await strategy()
                    
                    # Check if strategy worked
                    await asyncio.sleep(2)
                    current_url = self.driver.current_url
                    if "frmSystemUserSetlocation.aspx" not in current_url:
                        self.logger.info(f"✅ Strategy {i} successful - moved away from location page")
                        return
                        
                except Exception as e:
                    self.logger.warning(f"Strategy {i} failed: {e}")
                    continue
            
            self.logger.warning("⚠️ All location page strategies failed, continuing anyway...")
            
        except Exception as e:
            self.logger.error(f"Error in location page strategies: {e}")
    
    async def _strategy_click_ok_button(self):
        """Strategy 1: Click OK/Continue button on location page"""
        try:
            # Look for common button selectors on location page
            button_selectors = [
                "#MainContent_btnOK",
                "#MainContent_btnContinue", 
                "#MainContent_btnSave",
                ".btn-primary",
                "[value='OK']",
                "[value='Continue']",
                "[value='Save']"
            ]
            
            for selector in button_selectors:
                try:
                    button = WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    button.click()
                    self.logger.info(f"Clicked button using selector: {selector}")
                    await asyncio.sleep(2)
                    return
                except TimeoutException:
                    continue
                    
            raise Exception("No clickable buttons found")
            
        except Exception as e:
            raise Exception(f"Click OK strategy failed: {e}")
    
    async def _strategy_skip_location_setting(self):
        """Strategy 2: Look for skip/close options"""
        try:
            # Look for skip/close options
            skip_selectors = [
                "a[href*='skip']",
                "a[href*='close']",
                ".close",
                ".skip",
                "[onclick*='close']"
            ]
            
            for selector in skip_selectors:
                try:
                    skip_element = WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    skip_element.click()
                    self.logger.info(f"Used skip option: {selector}")
                    await asyncio.sleep(2)
                    return
                except TimeoutException:
                    continue
                    
            raise Exception("No skip options found")
            
        except Exception as e:
            raise Exception(f"Skip strategy failed: {e}")
    
    async def _strategy_navigate_away(self):
        """Strategy 3: Direct navigation to main page or task register"""
        try:
            # Try navigating to main page first
            main_page = self.login_url.rstrip('/') + '/en/main.aspx'
            self.logger.info(f"Attempting direct navigation to: {main_page}")
            
            self.driver.get(main_page)
            await asyncio.sleep(3)
            
            # Check if navigation was successful
            current_url = self.driver.current_url
            if "frmSystemUserSetlocation.aspx" not in current_url:
                self.logger.info("✅ Successfully navigated away from location page")
                return
            else:
                raise Exception("Navigation didn't work")
                
        except Exception as e:
            raise Exception(f"Navigate away strategy failed: {e}")
    
    async def _strategy_refresh_and_continue(self):
        """Strategy 4: Refresh page and continue"""
        try:
            self.logger.info("Refreshing page to bypass location setting...")
            self.driver.refresh()
            await asyncio.sleep(3)
            
            # Check if we're still on location page after refresh
            current_url = self.driver.current_url
            if "frmSystemUserSetlocation.aspx" in current_url:
                # Try to navigate to main page after refresh
                main_page = self.login_url.rstrip('/') + '/en/main.aspx'
                self.driver.get(main_page)
                await asyncio.sleep(2)
            
        except Exception as e:
            raise Exception(f"Refresh strategy failed: {e}")

    async def _strategy_force_main_page(self):
        """Strategy 5: Force navigation to main page"""
        try:
            self.logger.info("Forcing navigation to main page...")
            main_page = self.login_url.rstrip('/') + '/en/main.aspx'

            # Try multiple navigation methods
            self.driver.get(main_page)
            await asyncio.sleep(2)

            # If still on location page, try JavaScript navigation
            current_url = self.driver.current_url
            if "frmSystemUserSetlocation.aspx" in current_url:
                self.driver.execute_script(f"window.location.href = '{main_page}';")
                await asyncio.sleep(2)

        except Exception as e:
            raise Exception(f"Force main page strategy failed: {e}")

    async def _force_immediate_redirect(self):
        """Force immediate redirect away from location page"""
        try:
            self.logger.info("🚨 FORCING IMMEDIATE REDIRECT FROM LOCATION PAGE")

            # Get target URL (task register or main page)
            task_register_url = self.config.get('urls', {}).get('taskRegister',
                'http://millwarep3:8004/en/PR/trx/frmPrTrxTaskRegisterDet.aspx')
            main_page = self.login_url.rstrip('/') + '/en/main.aspx'

            # Try multiple immediate redirect methods
            redirect_methods = [
                lambda: self.driver.get(task_register_url),
                lambda: self.driver.execute_script(f"window.location.href = '{task_register_url}';"),
                lambda: self.driver.get(main_page),
                lambda: self.driver.execute_script(f"window.location.href = '{main_page}';")
            ]

            for i, method in enumerate(redirect_methods, 1):
                try:
                    self.logger.info(f"Trying redirect method {i}/{len(redirect_methods)}")
                    method()
                    await asyncio.sleep(1)

                    # Check if redirect worked
                    current_url = self.driver.current_url
                    if "frmSystemUserSetlocation.aspx" not in current_url:
                        self.logger.info(f"✅ Immediate redirect method {i} successful")
                        return

                except Exception as e:
                    self.logger.warning(f"Redirect method {i} failed: {e}")
                    continue

            self.logger.warning("⚠️ All immediate redirect methods failed")

        except Exception as e:
            self.logger.error(f"Force immediate redirect failed: {e}")

    async def _verify_location_page_exit(self):
        """Verify that we've successfully exited the location setting page"""
        try:
            max_attempts = 3
            for attempt in range(max_attempts):
                current_url = self.driver.current_url
                self.logger.info(f"Verification attempt {attempt + 1}: Current URL = {current_url}")
                
                if "frmSystemUserSetlocation.aspx" not in current_url:
                    self.logger.info("✅ Successfully exited location setting page")
                    return True
                
                # Wait and check again
                await asyncio.sleep(2)
            
            self.logger.warning("⚠️ Still on location setting page after all attempts")
            return False
            
        except Exception as e:
            self.logger.error(f"Error verifying location page exit: {e}")
            return False
    
    async def _check_login_status(self) -> bool:
        """Check if currently logged in - simplified approach"""
        try:
            current_url = self.driver.current_url
            
            # If we're on login page, we're not logged in
            if "login" in current_url.lower() or current_url.endswith("/"):
                return False
            
            # If we're on any other page (location, task register, main), we're logged in
            if any(page in current_url for page in ["frmSystemUserSetlocation", "frmPrTrxTaskRegister", "main.aspx"]):
                return True
            
            # Fallback: Check for absence of login form
            username_fields = self.driver.find_elements(By.ID, "txtUsername")
            return len(username_fields) == 0
            
        except Exception:
            # If we can't check, assume we're logged in to avoid re-login loops
            return True
    
    def get_driver(self) -> Optional[webdriver.Chrome]:
        """Get the current WebDriver instance"""
        if not self.is_initialized or not self.is_driver_healthy():
            return None
        
        self.last_activity_time = datetime.now()
        return self.driver
    
    def is_driver_healthy(self) -> bool:
        """Check if the WebDriver is healthy and responsive"""
        try:
            if not self.driver:
                return False
            
            # Try to get current URL to test responsiveness
            _ = self.driver.current_url
            return True
            
        except WebDriverException:
            return False
    
    async def ensure_session_ready(self) -> bool:
        """Ensure the browser session is ready for automation"""
        try:
            # Check if initialization is needed
            if not self.is_initialized or not self.is_driver_healthy():
                self.logger.info("Session not ready, reinitializing...")
                return await self.initialize()
            
            # Check if login is still valid
            if not await self._check_login_status():
                self.logger.info("Session expired, re-logging in...")
                await self._perform_initial_login()
            
            # Update activity time
            self.last_activity_time = datetime.now()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to ensure session ready: {e}")
            return False
    
    async def navigate_to_task_register(self) -> bool:
        """Navigate to task register page with enhanced connection stability and retry mechanisms"""
        max_attempts = 5
        
        for attempt in range(max_attempts):
            try:
                # Check driver responsiveness before navigation
                if not self._is_driver_responsive():
                    self.logger.warning(f"Driver not responsive on attempt {attempt + 1}, recovering...")
                    if not await self._recover_driver_connection():
                        continue
                
                # Get the actual task register URL
                task_register_url = self.config.get('urls', {}).get('taskRegister', 
                    'http://millwarep3:8004/en/PR/trx/frmPrTrxTaskRegisterDet.aspx')
                
                self.logger.info(f"🎯 Navigation attempt {attempt + 1}/{max_attempts} to: {task_register_url}")
                print(f"🎯 Navigation attempt {attempt + 1}/{max_attempts} to: {task_register_url}")
                
                # Ensure session is ready
                if not await self.ensure_session_ready():
                    self.logger.warning("Session not ready, retrying...")
                    continue
                
                # Check current URL before navigation
                current_url = self.driver.current_url
                self.logger.info(f"Current URL before navigation: {current_url}")
                print(f"📍 Current URL: {current_url}")
                
                # AGGRESSIVE LOCATION PAGE HANDLING - If on location page, immediately redirect
                if "frmSystemUserSetlocation.aspx" in current_url:
                    print("🚨 DETECTED LOCATION PAGE - FORCING IMMEDIATE REDIRECT!")
                    self.logger.info("🚨 DETECTED LOCATION PAGE - FORCING IMMEDIATE REDIRECT!")
                    
                    # Force immediate navigation to task register
                    print(f"🚀 FORCE REDIRECT: {current_url} → {task_register_url}")
                    
                    try:
                        self.driver.execute_script(f"window.location.href = '{task_register_url}';")
                    except Exception as js_error:
                        self.logger.warning(f"JavaScript navigation failed: {js_error}, trying direct navigation")
                        self.driver.get(task_register_url)
                    
                    await asyncio.sleep(2)  # Wait for redirect
                    
                    # Check if redirect worked
                    immediate_url = self.driver.current_url
                    print(f"📍 After immediate redirect: {immediate_url}")
                    
                    if "frmSystemUserSetlocation.aspx" in immediate_url:
                        # Try one more time with direct navigation
                        print("🔄 Trying secondary redirect method...")
                        self.driver.get(task_register_url)
                        await asyncio.sleep(2)
                else:
                    # Normal navigation with enhanced error handling
                    print("🚀 Normal navigation to task register...")
                    try:
                        self.driver.execute_script(f"window.location.href = '{task_register_url}';")
                    except Exception as js_error:
                        self.logger.warning(f"JavaScript navigation failed: {js_error}, trying direct navigation")
                        self.driver.get(task_register_url)
                
                # Wait for page to load with enhanced stability checks
                if not await self._wait_for_page_load():
                    self.logger.warning(f"Page load failed on attempt {attempt + 1}")
                    continue
                
                # Verify we reached the task register page
                final_url = self.driver.current_url
                print(f"📍 Final URL after navigation: {final_url}")
                self.logger.info(f"Final URL after navigation: {final_url}")
                
                if "frmPrTrxTaskRegisterDet.aspx" in final_url:
                    print("✅ SUCCESS: Reached task register page!")
                    self.logger.info("✅ SUCCESS: Reached task register page!")
                    
                    # Update activity time
                    self.last_activity_time = datetime.now()
                    return True
                else:
                    print(f"⚠️ WARNING: Not on task register page. Current: {final_url}")
                    self.logger.warning(f"⚠️ WARNING: Not on task register page. Current: {final_url}")
                    
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(3)  # Wait before retry
                        continue
                
            except Exception as e:
                print(f"❌ Navigation attempt {attempt + 1} failed: {e}")
                self.logger.error(f"Navigation attempt {attempt + 1} failed: {e}")
                if attempt < max_attempts - 1:
                    await asyncio.sleep(5)  # Longer wait on error
                    continue
        
        # All attempts failed, try recovery
        self.logger.error("All navigation attempts failed, attempting recovery...")
        return await self._recover_task_register_navigation()
    
    async def _verify_task_register_page(self):
        """Verify that we've successfully reached the task register page"""
        try:
            current_url = self.driver.current_url
            self.logger.info(f"Verification: Current URL = {current_url}")
            
            # Check if we're on the task register page
            if "frmPrTrxTaskRegisterDet.aspx" in current_url:
                self.logger.info("✅ Successfully reached task register page")
                return True
            
            # Check if we're redirected to location page again
            if "frmSystemUserSetlocation.aspx" in current_url:
                self.logger.warning("⚠️ Redirected back to location setting page")
                await self._handle_location_setting_page()
                
                # Try navigation again
                self.driver.get(self.task_register_url)
                await self._wait_for_page_load()
                
                # Check again
                current_url = self.driver.current_url
                if "frmPrTrxTaskRegisterDet.aspx" in current_url:
                    self.logger.info("✅ Successfully reached task register page after retry")
                    return True
            
            self.logger.warning(f"⚠️ Unexpected page: {current_url}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error verifying task register page: {e}")
            return False
    
    async def _recover_task_register_navigation(self) -> bool:
        """Attempt to recover from navigation failure with enhanced retry mechanisms"""
        try:
            self.logger.info("🔄 Attempting navigation recovery...")
            
            # First, try to recover driver connection
            if not await self._recover_driver_connection():
                self.logger.error("Driver recovery failed")
                return False
            
            # Try navigating to main page first
            main_page = self.login_url.rstrip('/') + '/en/main.aspx'
            self.logger.info(f"Recovery step 1: Navigating to main page: {main_page}")
            
            try:
                self.driver.get(main_page)
                await asyncio.sleep(3)
            except Exception as e:
                self.logger.warning(f"Main page navigation failed: {e}")
            
            # Then try task register again
            task_register_url = self.config.get('urls', {}).get('taskRegister', 
                'http://millwarep3:8004/en/PR/trx/frmPrTrxTaskRegisterDet.aspx')
            
            self.logger.info(f"Recovery step 2: Navigating to task register: {task_register_url}")
            
            try:
                self.driver.get(task_register_url)
                if await self._wait_for_page_load():
                    current_url = self.driver.current_url
                    if "frmPrTrxTaskRegisterDet.aspx" in current_url:
                        self.logger.info("✅ Recovery navigation successful")
                        self.last_activity_time = datetime.now()
                        return True
                    else:
                        self.logger.warning(f"⚠️ Recovery failed, still at: {current_url}")
                        return False
                else:
                    self.logger.warning("Recovery navigation page load failed")
                    return False
            except Exception as e:
                self.logger.error(f"Recovery task register navigation failed: {e}")
                return False
                
        except Exception as e:
            self.logger.error(f"Recovery navigation failed: {e}")
            return False
    
    async def _wait_for_page_load(self, timeout: int = 45) -> bool:
        """Wait for page to fully load with enhanced stability checks and connection recovery"""
        try:
            # Check driver connection first
            if not self._is_driver_responsive():
                self.logger.warning("Driver not responsive, attempting recovery...")
                if not await self._recover_driver_connection():
                    return False
            
            # Wait for document ready state with longer timeout and retry mechanism
            max_wait_attempts = 3
            for wait_attempt in range(max_wait_attempts):
                try:
                    WebDriverWait(self.driver, timeout // max_wait_attempts).until(
                        lambda driver: driver.execute_script("return document.readyState") == "complete"
                    )
                    break
                except Exception as wait_error:
                    self.logger.warning(f"Page load wait attempt {wait_attempt + 1} failed: {wait_error}")
                    if wait_attempt == max_wait_attempts - 1:
                        raise
                    await asyncio.sleep(2)
            
            # Additional wait for AJAX content and network stability
            await asyncio.sleep(3)
            
            # Verify page is still responsive
            if not self._is_driver_responsive():
                self.logger.warning("Page became unresponsive after load")
                return False
            
            return True
        except Exception as e:
            self.logger.warning(f"Page load wait failed: {e}")
            # Attempt recovery before giving up
            return await self._recover_driver_connection()
    
    def _is_driver_responsive(self) -> bool:
        """Check if driver is responsive to commands"""
        try:
            if not self.driver:
                return False
            # Quick responsiveness test
            _ = self.driver.current_url
            return True
        except Exception:
            return False
    
    async def _recover_driver_connection(self) -> bool:
        """Attempt to recover driver connection with multiple strategies"""
        try:
            self.logger.info("Attempting driver connection recovery...")
            
            # Strategy 1: Try to refresh the page
            if self.driver:
                try:
                    self.logger.info("Recovery strategy 1: Refreshing page...")
                    self.driver.refresh()
                    await asyncio.sleep(3)
                    if self._is_driver_responsive():
                        self.logger.info("Driver recovery successful via page refresh")
                        return True
                except Exception as refresh_error:
                    self.logger.warning(f"Page refresh recovery failed: {refresh_error}")
            
            # Strategy 2: Try to navigate to a simple page
            if self.driver:
                try:
                    self.logger.info("Recovery strategy 2: Navigating to login page...")
                    self.driver.get(self.login_url)
                    await asyncio.sleep(3)
                    if self._is_driver_responsive():
                        self.logger.info("Driver recovery successful via navigation")
                        # Re-login if needed
                        if not await self._check_login_status():
                            await self._perform_initial_login()
                        return True
                except Exception as nav_error:
                    self.logger.warning(f"Navigation recovery failed: {nav_error}")
            
            # Strategy 3: Recreate driver as last resort
            self.logger.info("Recovery strategy 3: Recreating driver...")
            try:
                if self.driver:
                    self.driver.quit()
            except:
                pass
            
            await self._create_driver()
            await self._perform_initial_login()
            
            if self._is_driver_responsive():
                self.logger.info("Driver recovery successful via recreation")
                return True
            else:
                self.logger.error("All driver recovery strategies failed")
                return False
            
        except Exception as e:
            self.logger.error(f"Driver recovery failed: {e}")
            return False
    
    async def _wait_for_navigation_completion(self, target_url: str, timeout: int = 30) -> bool:
        """Wait for navigation to complete and verify we reached the target"""
        try:
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    current_url = self.driver.current_url
                    
                    # Check if we've reached a page that contains our target path
                    if "frmPrTrxTaskRegisterDet.aspx" in current_url:
                        self.logger.info(f"Navigation completed successfully to: {current_url}")
                        return True
                    
                    # If still on location page, that's expected during transition
                    if "frmSystemUserSetlocation.aspx" in current_url:
                        self.logger.debug("Still on location page, waiting for redirect...")
                    
                    await asyncio.sleep(1)
                    
                except Exception as check_error:
                    self.logger.warning(f"URL check failed during navigation wait: {check_error}")
                    await asyncio.sleep(1)
            
            # Timeout reached
            try:
                final_url = self.driver.current_url
                self.logger.warning(f"Navigation timeout reached. Final URL: {final_url}")
            except:
                self.logger.warning("Navigation timeout and unable to get current URL")
            
            return False
            
        except Exception as e:
            self.logger.error(f"Navigation completion wait failed: {e}")
            return False
    
    def _start_session_keepalive(self):
        """Start background thread for session keepalive"""
        if self.keepalive_thread and self.keepalive_thread.is_alive():
            return
        
        self.shutdown_event.clear()
        self.keepalive_thread = threading.Thread(
            target=self._session_keepalive_worker,
            daemon=True
        )
        self.keepalive_thread.start()
        
        self.logger.info("Started session keepalive thread")
    
    def _session_keepalive_worker(self):
        """Worker thread for session keepalive"""
        while not self.shutdown_event.is_set():
            try:
                # Wait for keepalive interval
                if self.shutdown_event.wait(self.keepalive_interval_minutes * 60):
                    break
                
                # Check if session needs keepalive
                if self._should_perform_keepalive():
                    self._perform_keepalive()
                    
            except Exception as e:
                self.logger.error(f"Keepalive worker error: {e}")
    
    def _should_perform_keepalive(self) -> bool:
        """Check if keepalive should be performed"""
        if not self.last_activity_time:
            return False
        
        time_since_activity = datetime.now() - self.last_activity_time
        return time_since_activity.total_seconds() < (self.session_timeout_minutes * 60)
    
    def _perform_keepalive(self):
        """Perform session keepalive action"""
        try:
            if self.driver and self.is_driver_healthy():
                # Simple keepalive - refresh current page or get current URL
                _ = self.driver.current_url
                self.logger.debug("Performed session keepalive")
                
        except Exception as e:
            self.logger.warning(f"Keepalive action failed: {e}")
    
    async def cleanup(self):
        """Clean up resources"""
        try:
            self.logger.info("Cleaning up persistent browser manager...")
            
            # Stop keepalive thread
            if self.keepalive_thread:
                self.shutdown_event.set()
                self.keepalive_thread.join(timeout=5)
            
            # Quit WebDriver
            if self.driver:
                try:
                    self.driver.quit()
                    self.logger.info("Chrome WebDriver quit successfully")
                except Exception as e:
                    self.logger.warning(f"Error quitting WebDriver: {e}")
            
            # Clear singleton instance
            with PersistentBrowserManager._driver_creation_lock:
                PersistentBrowserManager._active_driver_instance = None
                self.logger.info("Cleared singleton WebDriver instance")
            
            # Reset state
            self.driver = None
            self.is_initialized = False
            self.is_logged_in = False
            self.last_activity_time = None
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass