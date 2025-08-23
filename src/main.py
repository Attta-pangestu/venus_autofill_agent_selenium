"""
Selenium AutoFill - Main Application
Standalone browser automation application replicating Chrome extension functionality
"""

import asyncio
import json
import logging
import os
import sys
from typing import Dict, List, Any
from pathlib import Path
from selenium.webdriver.common.by import By

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from core.browser_manager import BrowserManager
from core.automation_engine import AutomationEngine
from core.element_finder import ElementFinder
from core.visual_feedback import VisualFeedback
from action_recorder import ActionRecorder


class SeleniumAutoFillApp:
    """Main application class"""
    
    def __init__(self):
        self.setup_logging()
        self.browser_manager = None
        self.automation_engine = None
        self.driver = None
        self.action_recorder = None
        
        # Load configuration
        self.config = self.load_configuration()
        
        self.logger = logging.getLogger(__name__)

    def setup_logging(self):
        """Setup logging configuration"""
        # Configure console output to handle UTF-8
        import io
        import codecs
        
        # Ensure stdout can handle UTF-8
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        
        # Create stream handler with UTF-8 encoding
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.INFO)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('selenium_autofill.log', encoding='utf-8'),
                stream_handler
            ]
        )

    def load_configuration(self) -> Dict[str, Any]:
        """Load application configuration"""
        config_file = Path(__file__).parent.parent / "config" / "app_config.json"
        
        default_config = {
            "browser": {
                "headless": False,
                "window_size": [1280, 720],
                "disable_notifications": True,
                "event_delay": 0.5
            },
            "automation": {
                "implicit_wait": 10,
                "page_load_timeout": 30,
                "script_timeout": 30,
                "max_retries": 3
            },
            "credentials": {
                "username": "adm075",
                "password": "adm075"
            },
            "urls": {
                "login": "http://millwarep3.rebinmas.com:8003/",
                "attendance": "http://millwarep3.rebinmas.com:8003/attendance",
                "taskRegister": "http://millwarep3.rebinmas.com:8003/en/PR/trx/frmPrTrxTaskRegisterDet.aspx"
            }
        }
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    # Deep merge configurations
                    for key, value in user_config.items():
                        if isinstance(value, dict) and key in default_config:
                            default_config[key].update(value)
                        else:
                            default_config[key] = value
            except Exception as e:
                print(f"Error loading config file: {e}, using defaults")
        
        return default_config

    async def initialize(self):
        """Initialize the automation system"""
        try:
            self.logger.info("Initializing Selenium AutoFill Application")
            
            # Initialize browser manager
            self.browser_manager = BrowserManager(self.config.get('browser', {}))
            
            # Create browser driver
            self.driver = self.browser_manager.create_driver()
            
            # Initialize automation engine
            self.automation_engine = AutomationEngine(self.driver, self.config.get('automation', {}))
            
            # Initialize action recorder
            self.action_recorder = ActionRecorder(self.driver)
            
            # Show automation badge
            self.automation_engine.visual_feedback.show_automation_badge()
            
            # Open Millware system by default
            default_url = self.config["urls"]["login"]
            self.logger.info(f"Opening default Millware URL: {default_url}")
            self.driver.get(default_url)
            
            # Wait for page to load
            await self._wait_for_page_stability()
            
            self.logger.info("Application initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize application: {e}")
            raise

    async def check_login_status(self) -> Dict[str, Any]:
        """Check if user is already logged in to the Millware system"""
        try:
            current_url = self.driver.current_url
            page_title = self.driver.title
            
            # Check for login indicators
            login_indicators = {
                'is_logged_in': False,
                'current_url': current_url,
                'page_title': page_title,
                'detected_state': 'unknown',
                'recommended_flow': 'pre_login'
            }
            
            # Check if we're on login page
            if 'login' in current_url.lower() or any(indicator in page_title.lower() for indicator in ['login', 'sign in']):
                login_indicators.update({
                    'is_logged_in': False,
                    'detected_state': 'login_page',
                    'recommended_flow': 'pre_login'
                })
            
            # Check for login form elements
            try:
                username_field = self.driver.find_element(By.CSS_SELECTOR, "#txtUsername")
                password_field = self.driver.find_element(By.CSS_SELECTOR, "#txtPassword")
                login_button = self.driver.find_element(By.CSS_SELECTOR, "#btnLogin")
                
                if username_field and password_field and login_button:
                    login_indicators.update({
                        'is_logged_in': False,
                        'detected_state': 'login_form_present',
                        'recommended_flow': 'pre_login'
                    })
            except:
                pass
            
            # Check for logged-in indicators
            try:
                # Look for navigation menu or user indicators
                nav_elements = self.driver.find_elements(By.CSS_SELECTOR, "a.popout.level1.static")
                user_elements = self.driver.find_elements(By.CSS_SELECTOR, ".user-info, .username, .user-name")
                
                if nav_elements or user_elements:
                    login_indicators.update({
                        'is_logged_in': True,
                        'detected_state': 'logged_in_dashboard',
                        'recommended_flow': 'post_login'
                    })
            except:
                pass
            
            # Check if we're on a task/form page
            if 'frmPrTrxTaskRegisterDet.aspx' in current_url:
                login_indicators.update({
                    'is_logged_in': True,
                    'detected_state': 'task_register_page',
                    'recommended_flow': 'post_login'
                })
            
            return login_indicators
            
        except Exception as e:
            self.logger.warning(f"Error checking login status: {e}")
            return {
                'is_logged_in': False,
                'current_url': self.driver.current_url if self.driver else 'unknown',
                'page_title': 'unknown',
                'detected_state': 'error',
                'recommended_flow': 'pre_login'
            }

    async def smart_flow_selection(self):
        """Smart flow selection based on current login status"""
        self.logger.info("Analyzing current page state...")
        
        # Check login status
        status = await self.check_login_status()
        
        print("\n" + "="*60)
        print("SMART FLOW SELECTION - Current State Analysis")
        print("="*60)
        print(f"Current URL: {status['current_url']}")
        print(f"Page Title: {status['page_title']}")
        print(f"Detected State: {status['detected_state']}")
        print(f"Login Status: {'LOGGED IN' if status['is_logged_in'] else 'NOT LOGGED IN'}")
        print(f"Recommended Flow: {status['recommended_flow']}")
        print("-" * 60)
        
        if status['is_logged_in']:
            print("You appear to be logged in. Options:")
            print("1. Run Post-Login Flow (Task Register)")
            print("2. Run Pre-Login Flow (Full login sequence)")
            print("3. Return to main menu")
            
            choice = input("Select option (1-3): ").strip()
            
            if choice == "1":
                await self.run_post_login_flow()
            elif choice == "2":
                await self.run_pre_login_flow()
            elif choice == "3":
                return
            else:
                print("Invalid choice!")
        else:
            print("You appear to need login. Options:")
            print("1. Run Complete Flow (Login + Task Register)")
            print("2. Run Pre-Login Flow (Login only)")
            print("3. Return to main menu")
            
            choice = input("Select option (1-3): ").strip()
            
            if choice == "1":
                await self.run_complete_millware_flow()
            elif choice == "2":
                await self.run_pre_login_flow()
            elif choice == "3":
                return
            else:
                print("Invalid choice!")

    async def run_login_flow(self):
        """Run automated login flow"""
        self.logger.info("🔐 Starting login automation flow")
        
        # Define login flow based on the extension's structure
        login_flow = [
            {
                "id": 1,
                "type": "open_to",
                "url": self.config["urls"]["login"],
                "waitForLoad": True,
                "description": "Navigate to login page"
            },
            {
                "id": 2,
                "type": "wait_for_element",
                "selector": "#username",
                "timeout": 10000,
                "description": "Wait for username field"
            },
            {
                "id": 3,
                "type": "input",
                "selector": "#username",
                "value": self.config["credentials"]["username"],
                "clearFirst": True,
                "description": "Enter username"
            },
            {
                "id": 4,
                "type": "input",
                "selector": "#password",
                "value": self.config["credentials"]["password"],
                "clearFirst": True,
                "description": "Enter password"
            },
            {
                "id": 5,
                "type": "click",
                "selector": "#login-button",
                "description": "Click login button"
            },
            {
                "id": 6,
                "type": "wait_for_page_stability",
                "timeout": 15000,
                "description": "Wait for login to complete"
            }
        ]
        
        try:
            result = await self.automation_engine.execute_automation_flow(login_flow)
            
            if result.success:
                self.logger.info("✅ Login flow completed successfully")
                self.automation_engine.visual_feedback.show_success_notification("Login successful!")
            else:
                self.logger.error(f"❌ Login flow failed: {result.errors}")
                self.automation_engine.visual_feedback.show_error_notification("Login failed!")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Error during login flow: {e}")
            self.automation_engine.visual_feedback.show_error_notification(f"Login error: {str(e)}")
            raise

    async def run_attendance_flow(self):
        """Run automated attendance entry flow"""
        self.logger.info("📝 Starting attendance automation flow")
        
        # Define attendance flow
        attendance_flow = [
            {
                "id": 1,
                "type": "open_to",
                "url": self.config["urls"]["attendance"],
                "waitForLoad": True,
                "description": "Navigate to attendance page"
            },
            {
                "id": 2,
                "type": "wait_for_element",
                "selector": "#employee-search-btn",
                "timeout": 10000,
                "description": "Wait for employee search button"
            },
            {
                "id": 3,
                "type": "click",
                "selector": "#employee-search-btn",
                "description": "Click employee search button"
            },
            {
                "id": 4,
                "type": "wait",
                "duration": 2000,
                "description": "Wait for search form to load"
            },
            {
                "id": 5,
                "type": "input",
                "selector": "#employee-id-field",
                "value": "EMP001",
                "description": "Enter employee ID"
            },
            {
                "id": 6,
                "type": "click",
                "selector": "#search-submit",
                "description": "Submit employee search"
            },
            {
                "id": 7,
                "type": "wait",
                "duration": 3000,
                "description": "Wait for search results"
            },
            {
                "id": 8,
                "type": "input",
                "selector": "#regular-hours",
                "value": "8",
                "description": "Enter regular hours"
            },
            {
                "id": 9,
                "type": "input",
                "selector": "#overtime-hours",
                "value": "0",
                "description": "Enter overtime hours"
            },
            {
                "id": 10,
                "type": "click",
                "selector": "#save-attendance",
                "description": "Save attendance record"
            }
        ]
        
        try:
            result = await self.automation_engine.execute_automation_flow(attendance_flow)
            
            if result.success:
                self.logger.info("✅ Attendance flow completed successfully")
                self.automation_engine.visual_feedback.show_success_notification("Attendance recorded!")
            else:
                self.logger.error(f"❌ Attendance flow failed: {result.errors}")
                self.automation_engine.visual_feedback.show_error_notification("Attendance recording failed!")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Error during attendance flow: {e}")
            self.automation_engine.visual_feedback.show_error_notification(f"Attendance error: {str(e)}")
            raise

    async def run_custom_flow(self, flow_definition: List[Dict[str, Any]]):
        """Run a custom automation flow"""
        self.logger.info("⚙️ Starting custom automation flow")
        
        try:
            result = await self.automation_engine.execute_automation_flow(flow_definition)
            
            if result.success:
                self.logger.info("✅ Custom flow completed successfully")
                self.automation_engine.visual_feedback.show_success_notification("Custom flow completed!")
            else:
                self.logger.error(f"❌ Custom flow failed: {result.errors}")
                self.automation_engine.visual_feedback.show_error_notification("Custom flow failed!")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Error during custom flow: {e}")
            self.automation_engine.visual_feedback.show_error_notification(f"Custom flow error: {str(e)}")
            raise

    def load_flow_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Load automation flow from JSON file"""
        try:
            with open(file_path, 'r') as f:
                flow_data = json.load(f)
            
            # Load form data configuration
            form_data_file = Path(__file__).parent.parent / "config" / "form_data.json"
            form_data = {}
            if form_data_file.exists():
                try:
                    with open(form_data_file, 'r', encoding='utf-8') as f:
                        form_data = json.load(f)
                    self.logger.info(f"Loaded form data configuration from {form_data_file}")
                except Exception as e:
                    self.logger.warning(f"Could not load form data config: {e}")
            
            # Extract variables from flow and merge with config and form data
            flow_variables = flow_data.get('variables', {})
            
            # Merge variables with config (config takes precedence)
            merged_variables = {**flow_variables}
            
            # Add form data if available
            if 'taskRegister' in form_data:
                task_data = form_data['taskRegister']
                merged_variables.update({
                    'transactionDate': task_data.get('transactionDate', '03/06/2025'),
                    'employeeName': task_data.get('employee', {}).get('name', 'Septian Pratama'),
                    'activityCode': task_data.get('activity', {}).get('code', '(OC7240) LABORATORY ANALYSIS'),
                    'labourCode': task_data.get('labour', {}).get('code', 'LAB00000 (LABOUR COST)')
                })
            
            # Add credentials and URLs from main config
            if 'credentials' in self.config:
                merged_variables.update(self.config['credentials'])
            if 'urls' in self.config:
                merged_variables.update(self.config['urls'])
            
            # Get events from flow data
            events = []
            if 'events' in flow_data:
                events = flow_data['events']
            elif 'sampleFlows' in flow_data:
                # Handle extension's sample-flows.json format
                flow_name = list(flow_data['sampleFlows'].keys())[0]
                events = flow_data['sampleFlows'][flow_name]['events']
            elif isinstance(flow_data, list):
                events = flow_data
            else:
                raise ValueError("Invalid flow file format")
            
            # Process variable substitution in events
            events = self._process_flow_variables(events, merged_variables)
            
            self.logger.info(f"Loaded flow with {len(events)} events from {file_path}")
            if form_data:
                self.logger.info(f"Applied form data: Date={merged_variables.get('transactionDate')}, Employee={merged_variables.get('employeeName')}")
            
            return events
                
        except Exception as e:
            self.logger.error(f"Error loading flow from file: {e}")
            raise

    def _process_flow_variables(self, events: List[Dict[str, Any]], variables: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process variable substitution in flow events"""
        def substitute_variables(obj):
            if isinstance(obj, str):
                # Replace variables in format {variableName}
                import re
                pattern = r'\{([^}]+)\}'
                
                def replace_var(match):
                    var_name = match.group(1)
                    return str(variables.get(var_name, f'{{{var_name}}}'))
                
                return re.sub(pattern, replace_var, obj)
            elif isinstance(obj, dict):
                return {key: substitute_variables(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [substitute_variables(item) for item in obj]
            else:
                return obj
        
        return substitute_variables(events)

    async def run_pre_login_flow(self):
        """Run the converted pre-login flow"""
        self.logger.info("🔐 Starting pre-login automation flow")
        
        try:
            # Load the pre-login flow
            flow_file = Path(__file__).parent.parent / "flows" / "pre_login_flow.json"
            flow = self.load_flow_from_file(str(flow_file))
            
            result = await self.automation_engine.execute_automation_flow(flow)
            
            if result.success:
                self.logger.info("✅ Pre-login flow completed successfully")
                self.automation_engine.visual_feedback.show_success_notification("Pre-login flow completed!")
            else:
                self.logger.error(f"❌ Pre-login flow failed: {result.errors}")
                self.automation_engine.visual_feedback.show_error_notification("Pre-login flow failed!")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Error during pre-login flow: {e}")
            self.automation_engine.visual_feedback.show_error_notification(f"Pre-login error: {str(e)}")
            raise

    async def run_post_login_flow(self):
        """Run the converted post-login flow"""
        self.logger.info("📋 Starting post-login automation flow")
        
        try:
            # Load the post-login flow
            flow_file = Path(__file__).parent.parent / "flows" / "post_login_flow.json"
            flow = self.load_flow_from_file(str(flow_file))
            
            result = await self.automation_engine.execute_automation_flow(flow)
            
            if result.success:
                self.logger.info("✅ Post-login flow completed successfully")
                self.automation_engine.visual_feedback.show_success_notification("Post-login flow completed!")
            else:
                self.logger.error(f"❌ Post-login flow failed: {result.errors}")
                self.automation_engine.visual_feedback.show_error_notification("Post-login flow failed!")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Error during post-login flow: {e}")
            self.automation_engine.visual_feedback.show_error_notification(f"Post-login error: {str(e)}")
            raise

    async def run_complete_millware_flow(self):
        """Run complete Millware flow: login + task register in one go"""
        self.logger.info("Starting complete Millware automation flow")
        
        try:
            # Create combined flow: pre-login + post-login
            combined_flow = []
            
            # Load pre-login flow
            pre_login_file = Path(__file__).parent.parent / "flows" / "pre_login_flow.json"
            if pre_login_file.exists():
                pre_flow_data = self.load_flow_from_file(str(pre_login_file))
                combined_flow.extend(pre_flow_data)
            
            # Add transition wait
            combined_flow.append({
                "type": "wait",
                "duration": 3000,
                "description": "Waiting between login and task register navigation"
            })
            
            # Load post-login flow
            post_login_file = Path(__file__).parent.parent / "flows" / "post_login_flow.json"
            if post_login_file.exists():
                post_flow_data = self.load_flow_from_file(str(post_login_file))
                combined_flow.extend(post_flow_data)
            
            # Execute combined flow
            result = await self.automation_engine.execute_automation_flow(combined_flow)
            
            if result.success:
                self.logger.info("Complete Millware flow completed successfully")
                self.automation_engine.visual_feedback.show_success_notification("Automation completed!")
                print("SUCCESS: Complete automation flow finished!")
                print(f"Events executed: {result.events_executed}")
                print(f"Extracted data: {result.extracted_data}")
            else:
                self.logger.error(f"Complete Millware flow failed: {result.errors}")
                self.automation_engine.visual_feedback.show_error_notification("Automation failed!")
                print("FAILED: Automation encountered errors")
                for error in result.errors:
                    print(f"Error: {error}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error during complete Millware flow: {e}")
            self.automation_engine.visual_feedback.show_error_notification(f"Flow error: {str(e)}")
            raise

    async def interactive_mode(self):
        """Run application in interactive mode"""
        self.logger.info("Starting interactive mode")
        
        try:
            while True:
                # Check login status for smart suggestions
                status = await self.check_login_status()
                login_status_icon = "OK" if status['is_logged_in'] else "NEED LOGIN"
                recommended_flow = status['recommended_flow']
                
                print("\n" + "="*60)
                print("SELENIUM AUTOFILL - MILLWARE AUTOMATION")
                print("="*60)
                print(f"Current: {status['current_url'][:50]}...")
                print(f"Login Status: {login_status_icon} - {status['detected_state']}")
                print(f"Recommended: {recommended_flow}")
                print("-" * 60)
                print("QUICK OPTIONS:")
                print("1. AUTO COMPLETE FLOW (Login + Task Register)")
                print("2. Smart Flow Selection (Recommended)")
                print("3. Run Pre-Login Flow (Login only)")
                print("4. Run Post-Login Flow (Task register only)")
                print("")
                print("RECORDING OPTIONS:")
                print("5. 🎬 Start Action Recording")
                print("6. 🛑 Stop Action Recording")
                print("7. 📋 List Recordings") 
                print("8. 🔄 Convert Recording to Flow")
                print("9. ▶️ Run Recorded Flow")
                print("")
                print("MANUAL OPTIONS:")
                print("10. Run Basic Login Flow")
                print("11. Run Attendance Flow")
                print("12. Load Custom Flow from File")
                print("13. Test Element Finding")
                print("14. Take Screenshot")
                print("15. Clear Browser Data")
                print("16. Restart Browser")
                print("17. Refresh Page & Re-analyze")
                print("0. Exit")
                print("-" * 60)
                
                choice = input("Select option (0-17): ").strip()
                
                if choice == "0":
                    print("Exiting application...")
                    break
                elif choice == "1":
                    await self.run_complete_millware_flow()
                elif choice == "2":
                    await self.smart_flow_selection()
                elif choice == "3":
                    await self.run_pre_login_flow()
                elif choice == "4":
                    await self.run_post_login_flow()
                elif choice == "5":
                    await self.start_recording_session()
                elif choice == "6":
                    await self.stop_recording_session()
                elif choice == "7":
                    await self.list_recordings()
                elif choice == "8":
                    await self.convert_recording_to_flow()
                elif choice == "9":
                    await self.run_recorded_flow()
                elif choice == "10":
                    await self.run_login_flow()
                elif choice == "11":
                    await self.run_attendance_flow()
                elif choice == "12":
                    file_path = input("Enter flow file path: ").strip()
                    if file_path and os.path.exists(file_path):
                        flow = self.load_flow_from_file(file_path)
                        await self.run_custom_flow(flow)
                    else:
                        print("File not found!")
                elif choice == "13":
                    await self.test_element_finding()
                elif choice == "14":
                    filename = self.browser_manager.take_screenshot()
                    if filename:
                        print(f"Screenshot saved: {filename}")
                elif choice == "15":
                    self.browser_manager.clear_browser_data()
                    print("Browser data cleared")
                elif choice == "16":
                    print("Restarting browser...")
                    self.driver = self.browser_manager.restart_driver()
                    self.automation_engine = AutomationEngine(self.driver, self.config.get('automation', {}))
                    self.action_recorder = ActionRecorder(self.driver)
                    self.automation_engine.visual_feedback.show_automation_badge()
                    # Re-open Millware URL
                    default_url = self.config["urls"]["login"]
                    self.driver.get(default_url)
                    await self._wait_for_page_stability()
                elif choice == "17":
                    print("Refreshing page...")
                    self.driver.refresh()
                    await self._wait_for_page_stability()
                    print("Page refreshed and re-analyzed")
                else:
                    print("Invalid option!")
                
                input("\nPress Enter to continue...")
                
        except KeyboardInterrupt:
            print("\nApplication interrupted by user")
        except Exception as e:
            self.logger.error(f"Error in interactive mode: {e}")

    async def start_recording_session(self):
        """Start recording user actions"""
        print("\n🎬 ACTION RECORDING")
        print("=" * 40)
        
        if self.action_recorder.recording:
            print("❌ Recording already in progress!")
            return
        
        session_name = input("Enter recording session name (or press Enter for auto-generated): ").strip()
        if not session_name:
            session_name = None
        
        self.action_recorder.start_recording(session_name)
        
        print("\n✅ Recording started!")
        print("💡 Now perform your actions in the browser:")
        print("   - Click elements")
        print("   - Type in input fields")
        print("   - Press keyboard keys")
        print("   - Navigate between pages")
        print("\n🛑 When finished, select option 6 to stop recording")

    async def stop_recording_session(self):
        """Stop recording user actions"""
        print("\n🛑 STOP RECORDING")
        print("=" * 40)
        
        if not self.action_recorder.recording:
            print("❌ No recording in progress!")
            return
        
        recording_data = self.action_recorder.stop_recording()
        
        if recording_data:
            print(f"\n✅ Recording completed!")
            print(f"📊 Session: {recording_data['session_name']}")
            print(f"⏱️ Duration: {recording_data['duration']:.1f} seconds")
            print(f"🎯 Actions recorded: {recording_data['total_actions']}")
            
            # Ask if user wants to convert to automation flow
            convert = input("\nConvert to automation flow now? (y/n): ").strip().lower()
            if convert == 'y':
                flow = self.action_recorder.convert_to_selenium_flow(f"{recording_data['session_name']}.json")
                print(f"✅ Flow generated: {flow['name']}")

    async def list_recordings(self):
        """List all available recordings"""
        print("\n📋 AVAILABLE RECORDINGS")
        print("=" * 40)
        
        recordings = self.action_recorder.list_recordings()
        
        if not recordings:
            print("No recordings found.")
            return
        
        for i, recording in enumerate(recordings, 1):
            info = self.action_recorder.get_recording_info(recording)
            duration = info.get('duration', 0)
            actions = info.get('total_actions', 0)
            print(f"{i}. {recording}")
            print(f"   ⏱️ Duration: {duration:.1f}s | 🎯 Actions: {actions}")
            print(f"   📅 Recorded: {info.get('metadata', {}).get('recorded_at', 'Unknown')}")

    async def convert_recording_to_flow(self):
        """Convert a recording to automation flow"""
        print("\n🔄 CONVERT RECORDING TO FLOW")
        print("=" * 40)
        
        recordings = self.action_recorder.list_recordings()
        
        if not recordings:
            print("No recordings available.")
            return
        
        print("Available recordings:")
        for i, recording in enumerate(recordings, 1):
            print(f"{i}. {recording}")
        
        try:
            choice = int(input("Select recording number: ")) - 1
            if 0 <= choice < len(recordings):
                recording_name = recordings[choice]
                flow = self.action_recorder.convert_to_selenium_flow(f"{recording_name}.json")
                print(f"\n✅ Flow generated: {flow['name']}")
                print(f"📁 Saved to: flows/{recording_name}_flow.json")
            else:
                print("Invalid choice!")
        except ValueError:
            print("Please enter a valid number!")

    async def run_recorded_flow(self):
        """Run a flow generated from recording"""
        print("\n▶️ RUN RECORDED FLOW")
        print("=" * 40)
        
        # List available flow files
        flows_dir = Path("flows")
        if not flows_dir.exists():
            print("No flows directory found.")
            return
        
        flow_files = [f for f in flows_dir.glob("*_flow.json")]
        
        if not flow_files:
            print("No recorded flows available.")
            return
        
        print("Available recorded flows:")
        for i, flow_file in enumerate(flow_files, 1):
            print(f"{i}. {flow_file.stem}")
        
        try:
            choice = int(input("Select flow number: ")) - 1
            if 0 <= choice < len(flow_files):
                flow_file = flow_files[choice]
                print(f"\n▶️ Running flow: {flow_file.stem}")
                
                flow = self.load_flow_from_file(str(flow_file))
                await self.run_custom_flow(flow)
            else:
                print("Invalid choice!")
        except ValueError:
            print("Please enter a valid number!")

    async def test_element_finding(self):
        """Test element finding capabilities"""
        print("\n🔍 Testing Element Finding")
        
        current_url = self.driver.current_url
        print(f"Current URL: {current_url}")
        
        while True:
            selector = input("Enter selector to test (or 'back' to return): ").strip()
            if selector.lower() == 'back':
                break
            
            if not selector:
                continue
            
            try:
                element = await self.automation_engine.element_finder.find_element_with_multiple_methods(selector)
                
                if element:
                    print(f"✅ Element found: {element.tag_name}")
                    print(f"   Text: {element.text[:100]}...")
                    print(f"   Visible: {element.is_displayed()}")
                    
                    # Highlight the element
                    await self.automation_engine.visual_feedback.highlight_element(element, 'default', 2.0)
                    
                    # Generate alternatives
                    alternatives = self.automation_engine.element_finder.generate_alternative_selectors(element)
                    if alternatives:
                        print("   Alternative selectors:")
                        for alt in alternatives[:3]:  # Show first 3
                            print(f"     {alt['type']}: {alt['selector']}")
                else:
                    print("❌ Element not found")
                    
            except Exception as e:
                print(f"❌ Error: {e}")

    async def cleanup(self):
        """Cleanup resources"""
        self.logger.info("Cleaning up resources")
        
        try:
            if hasattr(self, 'automation_engine') and self.automation_engine:
                if hasattr(self.automation_engine, 'visual_feedback'):
                    self.automation_engine.visual_feedback.cleanup()
        except Exception as e:
            self.logger.warning(f"Error cleaning up visual feedback: {e}")
        
        try:
            if hasattr(self, 'browser_manager') and self.browser_manager:
                self.browser_manager.quit_driver()
        except Exception as e:
            self.logger.warning(f"Error closing browser: {e}")
        
        self.logger.info("Cleanup completed")

    async def _wait_for_page_stability(self, timeout: int = 10):
        """Wait for page to be stable (DOM ready and no pending requests)"""
        try:
            from selenium.webdriver.support.ui import WebDriverWait
            
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # Additional wait for any dynamic content
            await asyncio.sleep(1)
            
        except Exception as e:
            self.logger.warning(f"Page stability wait failed: {e}")

    async def run(self):
        """Main application run method"""
        try:
            await self.initialize()
            await self.interactive_mode()
        except Exception as e:
            self.logger.error(f"Application error: {e}")
        finally:
            await self.cleanup()


def create_sample_config():
    """Create sample configuration file"""
    config_dir = Path(__file__).parent.parent / "config"
    config_dir.mkdir(exist_ok=True)
    
    config_file = config_dir / "app_config.json"
    
    if not config_file.exists():
        sample_config = {
            "browser": {
                "headless": False,
                "window_size": [1280, 720],
                "disable_notifications": True,
                "event_delay": 0.5
            },
            "automation": {
                "implicit_wait": 10,
                "page_load_timeout": 30,
                "script_timeout": 30,
                "max_retries": 3
            },
            "credentials": {
                "username": "adm075",
                "password": "adm075"
            },
            "urls": {
                "login": "http://millwarep3.rebinmas.com:8003/",
                "attendance": "http://millwarep3.rebinmas.com:8003/attendance",
                "taskRegister": "http://millwarep3.rebinmas.com:8003/en/PR/trx/frmPrTrxTaskRegisterDet.aspx"
            }
        }
        
        with open(config_file, 'w') as f:
            json.dump(sample_config, f, indent=2)
        
        print(f"📝 Sample configuration created: {config_file}")
        print("Configuration includes Millware system URLs and default credentials")
        print("You can edit the configuration file to customize settings")


async def main():
    """Main entry point"""
    print("SELENIUM AUTOFILL - MILLWARE AUTOMATION SYSTEM")
    print("=" * 60)
    
    # Create sample config if needed
    create_sample_config()
    
    app = SeleniumAutoFillApp()
    
    print("\nSTARTUP OPTIONS:")
    print("1. AUTO RUN (Complete Login + Task Register)")
    print("2. INTERACTIVE MODE (Manual control)")
    print("0. EXIT")
    print("-" * 60)
    
    choice = input("Select startup option (0-2): ").strip()
    
    if choice == "0":
        print("Goodbye!")
        return
    elif choice == "1":
        # Auto run complete flow
        try:
            await app.initialize()
            print("\nStarting automatic complete flow...")
            await app.run_complete_millware_flow()
            print("\nAutomatic flow completed. Keeping browser open for inspection...")
            input("Press Enter to close browser and exit...")
        except Exception as e:
            print(f"Error during automatic flow: {e}")
        finally:
            await app.cleanup()
    elif choice == "2":
        # Interactive mode
        await app.run()
    else:
        print("Invalid choice!")


if __name__ == "__main__":
    # Run the application
    asyncio.run(main())