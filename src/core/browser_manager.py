"""
Browser Manager - Handles Chrome WebDriver setup and configuration
Provides centralized browser management for the automation application
"""

import os
import time
import logging
import socket
import requests
import platform
from typing import Dict, List, Any, Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


class BrowserManager:
    """Manages Chrome WebDriver instance and configuration"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.driver = None
        self.logger = logging.getLogger(__name__)
        
        # Default browser options
        self.default_options = {
            'headless': False,
            'window_size': (1280, 720),
            'disable_notifications': True,
            'disable_popup_blocking': False,
            'disable_dev_shm_usage': True,
            'no_sandbox': False,
            'disable_extensions': False,
            'user_data_dir': None,
            'profile_directory': None,
            'download_directory': None,
            'user_agent': None,
            'language': 'en-US',
            'timezone': None,
            'viewport_size': None,
            'device_emulation': None,
            'proxy': None,
            'certificate_errors': False,
            'incognito': False,
            'disable_images': False,
            'disable_javascript': False,
            'page_load_strategy': 'normal',  # normal, eager, none
            'implicit_wait': 10,
            'page_load_timeout': 60,  # Increased to prevent renderer timeout issues
            'script_timeout': 30,
            'enable_logging': True,
            'log_level': 'INFO'
        }

    def create_driver(self, options_override: Dict[str, Any] = None) -> webdriver.Chrome:
        """Create and configure Chrome WebDriver instance with enhanced error handling"""
        try:
            # Perform pre-flight checks
            self._perform_preflight_checks()

            # Merge options
            merged_options = {**self.default_options, **self.config, **(options_override or {})}

            # Setup Chrome options
            chrome_options = self._setup_chrome_options(merged_options)

            # Setup Chrome service with retry logic
            service = self._setup_chrome_service_with_retry(merged_options)

            # Create driver with retry mechanism
            self.driver = self._create_driver_with_retry(service, chrome_options, max_retries=3)

            # Configure timeouts and settings
            self._configure_driver_settings(merged_options)

            # Set window size and position
            self._configure_window(merged_options)

            self.logger.info("Chrome WebDriver created successfully")
            return self.driver

        except Exception as e:
            self.logger.error(f"Failed to create Chrome WebDriver: {e}")
            # Provide helpful error messages
            self._provide_error_guidance(e)
            raise

    def _setup_chrome_options(self, options: Dict[str, Any]) -> Options:
        """Setup Chrome options based on configuration with enhanced stability features"""
        chrome_options = Options()
        
        # Basic options
        if options.get('headless', False):
            chrome_options.add_argument('--headless=new')
        
        if options.get('disable_notifications', True):
            chrome_options.add_argument('--disable-notifications')
        
        if options.get('disable_popup_blocking', False):
            chrome_options.add_argument('--disable-popup-blocking')
        
        if options.get('disable_dev_shm_usage', True):
            chrome_options.add_argument('--disable-dev-shm-usage')
        
        if options.get('no_sandbox', False):
            chrome_options.add_argument('--no-sandbox')
        
        if options.get('disable_extensions', False):
            chrome_options.add_argument('--disable-extensions')
        
        if options.get('incognito', False):
            chrome_options.add_argument('--incognito')
        
        # Certificate and security options
        if options.get('certificate_errors', False):
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--ignore-ssl-errors')
            chrome_options.add_argument('--ignore-certificate-errors-spki-list')
        
        # User data directory and profile
        if options.get('user_data_dir'):
            chrome_options.add_argument(f'--user-data-dir={options["user_data_dir"]}')
        
        if options.get('profile_directory'):
            chrome_options.add_argument(f'--profile-directory={options["profile_directory"]}')
        
        # Language and locale
        if options.get('language'):
            chrome_options.add_argument(f'--lang={options["language"]}')
        
        # User agent
        if options.get('user_agent'):
            chrome_options.add_argument(f'--user-agent={options["user_agent"]}')
        
        # Proxy configuration
        if options.get('proxy'):
            proxy_config = options['proxy']
            if isinstance(proxy_config, str):
                chrome_options.add_argument(f'--proxy-server={proxy_config}')
            elif isinstance(proxy_config, dict):
                if proxy_config.get('http'):
                    chrome_options.add_argument(f'--proxy-server=http://{proxy_config["http"]}')
                elif proxy_config.get('socks5'):
                    chrome_options.add_argument(f'--proxy-server=socks5://{proxy_config["socks5"]}')
        
        # Performance and resource options
        if options.get('disable_images', False):
            chrome_options.add_argument('--blink-settings=imagesEnabled=false')
        
        if options.get('disable_javascript', False):
            chrome_options.add_experimental_option('prefs', {
                'profile.managed_default_content_settings.javascript': 2
            })
        
        # Download directory
        if options.get('download_directory'):
            chrome_options.add_experimental_option('prefs', {
                'download.default_directory': options['download_directory'],
                'download.prompt_for_download': False,
                'download.directory_upgrade': True,
                'safebrowsing.enabled': True
            })
        
        # Device emulation
        if options.get('device_emulation'):
            device_config = options['device_emulation']
            mobile_emulation = {
                'deviceMetrics': {
                    'width': device_config.get('width', 375),
                    'height': device_config.get('height', 667),
                    'pixelRatio': device_config.get('pixel_ratio', 2.0)
                },
                'userAgent': device_config.get('user_agent', 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)')
            }
            chrome_options.add_experimental_option('mobileEmulation', mobile_emulation)
        
        # Page load strategy
        page_load_strategy = options.get('page_load_strategy', 'normal')
        chrome_options.page_load_strategy = page_load_strategy
        
        # Enhanced stability arguments for connection issues
        stability_args = [
            '--disable-blink-features=AutomationControlled',
            '--disable-extensions-file-access-check',
            '--disable-extensions-http-throttling',
            '--disable-component-extensions-with-background-pages',
            '--disable-default-apps',
            '--disable-sync',
            '--disable-translate',
            '--hide-scrollbars',
            '--mute-audio',
            '--no-first-run',
            '--no-default-browser-check',
            '--disable-logging',
            '--disable-gpu-logging',
            '--silent',
            '--disable-web-security',
            '--disable-features=TranslateUI',
            '--disable-ipc-flooding-protection',
            '--max_old_space_size=4096',
            '--disable-renderer-backgrounding',
            '--disable-backgrounding-occluded-windows',
            '--disable-background-timer-throttling',
            '--disable-features=VizDisplayCompositor',
            '--force-device-scale-factor=1',
            '--disable-hang-monitor'
        ]
        
        for arg in stability_args:
            chrome_options.add_argument(arg)
        
        # Additional experimental options
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Enhanced prefs for stability and connection handling
        prefs = {
            'profile.default_content_setting_values.notifications': 2,
            'profile.default_content_settings.popups': 0,
            'profile.managed_default_content_settings.images': 2 if options.get('disable_images', False) else 1,
            'profile.default_content_setting_values.media_stream_mic': 2,
            'profile.default_content_setting_values.media_stream_camera': 2,
            'profile.default_content_setting_values.geolocation': 2,
            'profile.default_content_setting_values.desktop_notifications': 2,
            'profile.content_settings.exceptions.automatic_downloads.*.setting': 1,
            'download.prompt_for_download': False,
            'download.directory_upgrade': True,
            'safebrowsing.enabled': False,
            'safebrowsing.disable_download_protection': True
        }
        chrome_options.add_experimental_option('prefs', prefs)
        
        # Enable logging if requested
        if options.get('enable_logging', True):
            log_level = options.get('log_level', 'INFO')
            chrome_options.add_argument(f'--log-level={log_level}')
            chrome_options.set_capability('goog:loggingPrefs', {
                'browser': log_level,
                'driver': log_level,
                'performance': log_level
            })
        
        return chrome_options

    def _perform_preflight_checks(self):
        """Perform pre-flight checks before creating WebDriver"""
        try:
            # Check system architecture and Chrome compatibility
            self._check_system_compatibility()

            # Check network connectivity to target server
            self._check_network_connectivity()

        except Exception as e:
            self.logger.warning(f"Pre-flight check warning: {e}")
            # Don't fail here, just warn

    def _check_system_compatibility(self):
        """Check system compatibility for WebDriver"""
        try:
            system_info = {
                'platform': platform.system(),
                'architecture': platform.architecture()[0],
                'machine': platform.machine(),
                'python_version': platform.python_version()
            }

            self.logger.info(f"System info: {system_info}")

            # Check for common compatibility issues
            if system_info['platform'] == 'Windows' and system_info['architecture'] == '32bit':
                self.logger.warning("32-bit Windows detected - may have WebDriver compatibility issues")

        except Exception as e:
            self.logger.warning(f"System compatibility check failed: {e}")

    def _check_network_connectivity(self):
        """Check network connectivity to target servers"""
        try:
            # Extract hostname from login URL if available
            login_url = self.config.get('urls', {}).get('login', 'http://millwarep3:8004/')
            if login_url:
                # Parse hostname from URL
                from urllib.parse import urlparse
                parsed_url = urlparse(login_url)
                hostname = parsed_url.hostname
                port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)

                if hostname:
                    # Test network connectivity
                    self._test_network_connection(hostname, port)

        except Exception as e:
            self.logger.warning(f"Network connectivity check failed: {e}")

    def _test_network_connection(self, hostname: str, port: int, timeout: int = 5):
        """Test network connection to hostname:port"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((hostname, port))
            sock.close()

            if result == 0:
                self.logger.info(f"✅ Network connectivity to {hostname}:{port} - OK")
            else:
                self.logger.warning(f"⚠️ Network connectivity to {hostname}:{port} - Failed (code: {result})")
                self.logger.warning(f"   This may cause WebDriver navigation issues")

        except socket.gaierror as e:
            self.logger.warning(f"⚠️ DNS resolution failed for {hostname}: {e}")
            self.logger.warning(f"   Please check if {hostname} is accessible from this machine")
        except Exception as e:
            self.logger.warning(f"⚠️ Network test failed for {hostname}:{port}: {e}")

    def _setup_chrome_service(self, options: Dict[str, Any]) -> Service:
        """Setup Chrome service"""
        try:
            # Use ChromeDriverManager to automatically download and manage ChromeDriver
            driver_path = ChromeDriverManager().install()
            service = Service(driver_path)

            # Configure service options
            if options.get('enable_logging', True):
                service.log_path = 'chromedriver.log'

            return service

        except Exception as e:
            self.logger.error(f"Failed to setup Chrome service: {e}")
            raise

    def _setup_chrome_service_with_retry(self, options: Dict[str, Any], max_retries: int = 3) -> Service:
        """Setup Chrome service with retry logic"""
        last_error = None

        for attempt in range(max_retries):
            try:
                self.logger.info(f"Setting up Chrome service (attempt {attempt + 1}/{max_retries})")

                # Use ChromeDriverManager with specific version handling
                driver_path = self._get_chromedriver_path_with_fallback()
                service = Service(driver_path)

                # Configure service options
                if options.get('enable_logging', True):
                    service.log_path = 'chromedriver.log'

                # Verify the driver executable is valid
                if not os.path.exists(driver_path):
                    raise Exception(f"ChromeDriver not found at: {driver_path}")

                # Test if the driver is executable
                if not os.access(driver_path, os.X_OK):
                    self.logger.warning(f"ChromeDriver may not be executable: {driver_path}")

                self.logger.info(f"✅ Chrome service setup successful with driver: {driver_path}")
                return service

            except Exception as e:
                last_error = e
                self.logger.warning(f"Chrome service setup attempt {attempt + 1} failed: {e}")

                if attempt < max_retries - 1:
                    # Wait before retry
                    time.sleep(2)

        # All attempts failed
        self.logger.error(f"Failed to setup Chrome service after {max_retries} attempts")
        raise last_error

    def _get_chromedriver_path_with_fallback(self) -> str:
        """Get ChromeDriver path with fallback strategies and proper path validation"""
        import glob
        import shutil
        
        try:
            # Try standard ChromeDriverManager
            driver_path = ChromeDriverManager().install()
            
            # Validate and fix the path if it's pointing to wrong file
            if "THIRD_PARTY_NOTICES" in driver_path or not driver_path.endswith(".exe"):
                self.logger.warning(f"Invalid driver path detected: {driver_path}")
                
                # Extract directory and find the actual chromedriver.exe
                driver_dir = os.path.dirname(driver_path)
                
                # Look for chromedriver.exe in the same directory
                possible_paths = [
                    os.path.join(driver_dir, "chromedriver.exe"),
                    os.path.join(driver_dir, "chromedriver-win32", "chromedriver.exe"),
                    os.path.join(os.path.dirname(driver_dir), "chromedriver.exe")
                ]
                
                for possible_path in possible_paths:
                    if os.path.exists(possible_path):
                        self.logger.info(f"Found correct ChromeDriver at: {possible_path}")
                        return possible_path
                
                # If not found, search recursively
                for root, dirs, files in os.walk(os.path.dirname(driver_dir)):
                    for file in files:
                        if file == "chromedriver.exe":
                            correct_path = os.path.join(root, file)
                            self.logger.info(f"Found ChromeDriver via search: {correct_path}")
                            return correct_path
                
                # Last resort: clear cache and try again
                self.logger.warning("ChromeDriver not found, clearing cache and retrying...")
                raise Exception("ChromeDriver path validation failed")
            
            return driver_path

        except Exception as e:
            self.logger.warning(f"Standard ChromeDriverManager failed: {e}")

            # Try with cache clear
            try:
                # Clear WebDriver Manager cache
                cache_dir = os.path.expanduser("~/.wdm")
                if os.path.exists(cache_dir):
                    shutil.rmtree(cache_dir)
                    self.logger.info("Cleared WebDriver Manager cache")
                
                # Try again with fresh download
                driver_path = ChromeDriverManager(cache_valid_range=1).install()
                
                # Validate the new path
                if os.path.exists(driver_path) and driver_path.endswith(".exe"):
                    return driver_path
                else:
                    raise Exception(f"Downloaded ChromeDriver is invalid: {driver_path}")
                    
            except Exception as e2:
                self.logger.error(f"ChromeDriverManager with cache clear also failed: {e2}")
                raise e2

    def _create_driver_with_retry(self, service: Service, chrome_options: Options, max_retries: int = 3) -> webdriver.Chrome:
        """Create WebDriver with retry logic"""
        last_error = None

        for attempt in range(max_retries):
            try:
                self.logger.info(f"Creating WebDriver (attempt {attempt + 1}/{max_retries})")

                # Create driver
                driver = webdriver.Chrome(service=service, options=chrome_options)

                # Test driver responsiveness
                try:
                    _ = driver.current_url
                    self.logger.info("✅ WebDriver created and responsive")
                    return driver
                except Exception as e:
                    driver.quit()
                    raise Exception(f"WebDriver created but not responsive: {e}")

            except Exception as e:
                last_error = e
                self.logger.warning(f"WebDriver creation attempt {attempt + 1} failed: {e}")

                if attempt < max_retries - 1:
                    time.sleep(3)  # Wait before retry

        # All attempts failed
        self.logger.error(f"Failed to create WebDriver after {max_retries} attempts")
        raise last_error

    def _provide_error_guidance(self, error: Exception):
        """Provide helpful error guidance based on the error type"""
        error_str = str(error).lower()

        if "win32 application" in error_str:
            self.logger.error("🔧 SOLUTION: ChromeDriver architecture mismatch detected")
            self.logger.error("   Try: 1. Clear WebDriver cache: rm -rf ~/.wdm")
            self.logger.error("        2. Restart the application")
            self.logger.error("        3. Check Chrome browser version compatibility")

        elif "name not resolved" in error_str or "err_name_not_resolved" in error_str:
            self.logger.error("🌐 SOLUTION: Network connectivity issue detected")
            self.logger.error("   Try: 1. Check if millwarep3:8004 is accessible")
            self.logger.error("        2. Add millwarep3 to your hosts file")
            self.logger.error("        3. Use IP address instead of hostname")

        elif "timeout" in error_str:
            self.logger.error("⏱️ SOLUTION: Timeout issue detected")
            self.logger.error("   Try: 1. Check network connection speed")
            self.logger.error("        2. Increase timeout values in config")
            self.logger.error("        3. Run with --headless for better performance")

        elif "session" in error_str and "not created" in error_str:
            self.logger.error("🔄 SOLUTION: WebDriver session creation failed")
            self.logger.error("   Try: 1. Update Chrome browser")
            self.logger.error("        2. Clear browser cache and data")
            self.logger.error("        3. Run as administrator (Windows)")

    def _configure_driver_settings(self, options: Dict[str, Any]):
        """Configure driver timeouts and settings"""
        if not self.driver:
            return
        
        # Set timeouts with robust values to prevent renderer timeouts
        implicit_wait = options.get('implicit_wait', 12)
        page_load_timeout = options.get('page_load_timeout', 60)  # Increased default fallback
        script_timeout = options.get('script_timeout', 30)
        
        self.driver.implicitly_wait(implicit_wait)
        self.driver.set_page_load_timeout(page_load_timeout)
        self.driver.set_script_timeout(script_timeout)
        
        # Execute script to remove automation indicators
        try:
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
            """)
        except Exception:
            pass

    def _configure_window(self, options: Dict[str, Any]):
        """Configure browser window"""
        if not self.driver:
            return
        
        try:
            # Set window size
            window_size = options.get('window_size', (1280, 720))
            if window_size:
                self.driver.set_window_size(window_size[0], window_size[1])
            
            # Set viewport size if different from window size
            viewport_size = options.get('viewport_size')
            if viewport_size:
                self.driver.execute_script(f"""
                    window.resizeTo({viewport_size[0]}, {viewport_size[1]});
                """)
            
            # Maximize window if requested
            if options.get('maximize_window', False):
                self.driver.maximize_window()
            
            # Position window if specified
            window_position = options.get('window_position')
            if window_position:
                self.driver.set_window_position(window_position[0], window_position[1])
                
        except Exception as e:
            self.logger.warning(f"Failed to configure window: {e}")

    def create_driver_with_profile(self, profile_name: str = "AutoFill") -> webdriver.Chrome:
        """Create driver with specific Chrome profile"""
        profile_options = {
            'user_data_dir': os.path.expanduser(f'~/ChromeProfiles'),
            'profile_directory': profile_name
        }
        
        return self.create_driver(profile_options)

    def create_headless_driver(self) -> webdriver.Chrome:
        """Create headless Chrome driver for background operations"""
        headless_options = {
            'headless': True,
            'disable_notifications': True,
            'disable_popup_blocking': True,
            'disable_dev_shm_usage': True,
            'no_sandbox': True,
            'disable_images': True,
            'window_size': (1920, 1080)
        }
        
        return self.create_driver(headless_options)

    def create_mobile_driver(self, device_name: str = "iPhone 12") -> webdriver.Chrome:
        """Create driver with mobile device emulation"""
        device_configs = {
            "iPhone 12": {
                'width': 390,
                'height': 844,
                'pixel_ratio': 3.0,
                'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15'
            },
            "iPad": {
                'width': 768,
                'height': 1024,
                'pixel_ratio': 2.0,
                'user_agent': 'Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X) AppleWebKit/605.1.15'
            },
            "Samsung Galaxy S21": {
                'width': 360,
                'height': 800,
                'pixel_ratio': 3.0,
                'user_agent': 'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36'
            }
        }
        
        device_config = device_configs.get(device_name, device_configs["iPhone 12"])
        mobile_options = {
            'device_emulation': device_config
        }
        
        return self.create_driver(mobile_options)

    def get_driver(self) -> Optional[webdriver.Chrome]:
        """Get current driver instance"""
        return self.driver

    def is_driver_alive(self) -> bool:
        """Check if driver is still alive and responsive"""
        if not self.driver:
            return False
        
        try:
            # Try to get current URL to test if driver is responsive
            _ = self.driver.current_url
            return True
        except Exception:
            return False

    def restart_driver(self, options_override: Dict[str, Any] = None) -> webdriver.Chrome:
        """Restart the driver with same or new options"""
        self.quit_driver()
        return self.create_driver(options_override)

    def quit_driver(self):
        """Safely quit the driver"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("Chrome WebDriver quit successfully")
            except Exception as e:
                self.logger.warning(f"Error quitting driver: {e}")
            finally:
                self.driver = None

    def close_current_tab(self):
        """Close current tab"""
        if self.driver:
            try:
                self.driver.close()
            except Exception as e:
                self.logger.warning(f"Error closing tab: {e}")

    def switch_to_tab(self, tab_index: int = 0):
        """Switch to specific tab by index"""
        if self.driver:
            try:
                handles = self.driver.window_handles
                if 0 <= tab_index < len(handles):
                    self.driver.switch_to.window(handles[tab_index])
                else:
                    self.logger.warning(f"Tab index {tab_index} out of range")
            except Exception as e:
                self.logger.warning(f"Error switching to tab: {e}")

    def open_new_tab(self, url: str = None):
        """Open new tab and optionally navigate to URL"""
        if self.driver:
            try:
                self.driver.execute_script("window.open('');")
                self.switch_to_tab(-1)  # Switch to last tab
                
                if url:
                    self.driver.get(url)
            except Exception as e:
                self.logger.warning(f"Error opening new tab: {e}")

    def get_driver_info(self) -> Dict[str, Any]:
        """Get information about current driver"""
        if not self.driver:
            return {}
        
        try:
            info = {
                'current_url': self.driver.current_url,
                'title': self.driver.title,
                'window_handles': len(self.driver.window_handles),
                'window_size': self.driver.get_window_size(),
                'capabilities': dict(self.driver.capabilities),
                'session_id': self.driver.session_id
            }
            return info
        except Exception as e:
            self.logger.warning(f"Error getting driver info: {e}")
            return {}

    def take_screenshot(self, filename: str = None) -> str:
        """Take screenshot and return filename"""
        if not self.driver:
            return ""
        
        try:
            if not filename:
                timestamp = int(time.time())
                filename = f"screenshot_{timestamp}.png"
            
            success = self.driver.save_screenshot(filename)
            if success:
                self.logger.info(f"Screenshot saved: {filename}")
                return filename
            else:
                self.logger.warning("Failed to save screenshot")
                return ""
        except Exception as e:
            self.logger.warning(f"Error taking screenshot: {e}")
            return ""

    def get_page_source(self) -> str:
        """Get current page source"""
        if self.driver:
            try:
                return self.driver.page_source
            except Exception as e:
                self.logger.warning(f"Error getting page source: {e}")
        return ""

    def execute_script(self, script: str, *args) -> Any:
        """Execute JavaScript in browser"""
        if self.driver:
            try:
                return self.driver.execute_script(script, *args)
            except Exception as e:
                self.logger.warning(f"Error executing script: {e}")
        return None

    def clear_browser_data(self):
        """Clear browser data (cookies, cache, etc.)"""
        if self.driver:
            try:
                # Clear cookies
                self.driver.delete_all_cookies()
                
                # Clear local storage and session storage
                self.driver.execute_script("window.localStorage.clear();")
                self.driver.execute_script("window.sessionStorage.clear();")
                
                # Clear cache via DevTools (if available)
                try:
                    self.driver.execute_cdp_cmd('Network.clearBrowserCache', {})
                    self.driver.execute_cdp_cmd('Network.clearBrowserCookies', {})
                except Exception:
                    pass  # CDP commands might not be available
                    
                self.logger.info("Browser data cleared")
            except Exception as e:
                self.logger.warning(f"Error clearing browser data: {e}")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.quit_driver()