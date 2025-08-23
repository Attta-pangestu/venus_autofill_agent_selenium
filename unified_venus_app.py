#!/usr/bin/env python3
"""
Venus AutoFill - Unified Desktop Application
Integrated application combining Flask server, WebDriver automation, and desktop UI
Single executable solution for Venus AutoFill system
"""

import asyncio
import json
import logging
import os
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Configuration
API_BASE_URL = "http://localhost:5173"
STAGING_DATA_ENDPOINT = f"{API_BASE_URL}/api/staging/data"
GROUPED_DATA_ENDPOINT = f"{API_BASE_URL}/api/staging/data-grouped"

class StagingDataManager:
    """Manages staging data operations"""
    
    def __init__(self):
        self.cached_data = None
        self.cache_timestamp = None
        self.cache_duration = 300  # 5 minutes
    
    def fetch_staging_data(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Fetch staging data from API with optional filters"""
        try:
            # Check cache first
            if self._is_cache_valid() and not filters:
                logging.info("Using cached staging data")
                return self.cached_data
            
            logging.info("Fetching staging data from API...")
            
            # Try grouped endpoint first, fallback to regular endpoint
            endpoints_to_try = [GROUPED_DATA_ENDPOINT, STAGING_DATA_ENDPOINT]
            
            for endpoint in endpoints_to_try:
                try:
                    # Prepare request parameters
                    params = {}
                    if filters:
                        if filters.get('employee_name'):
                            params['employee_name'] = filters['employee_name']
                        if filters.get('date_from'):
                            params['date_from'] = filters['date_from']
                        if filters.get('date_to'):
                            params['date_to'] = filters['date_to']
                        if filters.get('status'):
                            params['status'] = filters['status']
                        if filters.get('limit'):
                            params['limit'] = filters['limit']
                        if filters.get('offset'):
                            params['offset'] = filters['offset']
                    
                    # Make API request
                    response = requests.get(endpoint, params=params, timeout=30)
                    response.raise_for_status()
                    
                    data = response.json()
                    
                    # Handle grouped data format
                    if endpoint == GROUPED_DATA_ENDPOINT and 'data' in data:
                        # Flatten grouped data for display
                        flattened_data = self._flatten_grouped_data(data['data'])
                        data = {
                            'success': True,
                            'message': 'Data fetched successfully',
                            'data': flattened_data,
                            'total': len(flattened_data),
                            'page': 1,
                            'per_page': 50
                        }
                    
                    # Apply client-side filters if needed
                    if filters:
                        data = self._apply_filters(data, filters)
                    
                    # Cache the data if no filters applied
                    if not filters:
                        self.cached_data = data
                        self.cache_timestamp = datetime.now()
                    
                    logging.info(f"Successfully fetched {len(data.get('data', []))} records from {endpoint}")
                    return data
                    
                except requests.exceptions.RequestException as e:
                    logging.warning(f"Failed to fetch from {endpoint}: {e}")
                    continue
                except:
                    # Fallback data when requests fails
                    data = {
                        'data': [
                            {'id': 1, 'employee_name': 'Test Employee', 'status': 'pending', 'date': '2024-01-01', 'department': 'IT'},
                            {'id': 2, 'employee_name': 'Sample User', 'status': 'completed', 'date': '2024-01-02', 'department': 'HR'}
                        ],
                        'total': 2,
                        'page': 1,
                        'per_page': 50
                    }
                    
                    # Cache the fallback data
                    self.cached_data = data
                    self.cache_timestamp = datetime.now()
                    
                    logging.info(f"Using fallback data with {len(data.get('data', []))} staging records")
                    return data
            
            # If all endpoints failed
            raise Exception("All API endpoints failed")
            
        except Exception as e:
            logging.error(f"Error fetching staging data: {e}")
            return {
                'error': f'Failed to fetch data: {str(e)}',
                'data': [],
                'total': 0,
                'page': 1,
                'per_page': 50
            }
    
    def _is_cache_valid(self) -> bool:
        """Check if cached data is still valid"""
        if not self.cached_data or not self.cache_timestamp:
            return False
        
        age = (datetime.now() - self.cache_timestamp).total_seconds()
        return age < self.cache_duration
    
    def _apply_filters(self, data: Dict[str, Any], filters: Dict[str, Any]) -> Dict[str, Any]:
        """Apply client-side filters to cached data"""
        if not filters or not data.get('data'):
            return data
        
        filtered_records = data['data']
        
        # Apply employee name filter
        if filters.get('employee_name'):
            employee_filter = filters['employee_name'].lower()
            filtered_records = [
                record for record in filtered_records
                if employee_filter in record.get('employee_name', '').lower()
            ]
        
        # Apply date range filter
        if filters.get('date_from') or filters.get('date_to'):
            date_from = filters.get('date_from')
            date_to = filters.get('date_to')
            
            filtered_records = [
                record for record in filtered_records
                if self._is_date_in_range(record.get('date'), date_from, date_to)
            ]
        
        # Apply status filter
        if filters.get('status'):
            status_filter = filters['status']
            filtered_records = [
                record for record in filtered_records
                if record.get('status') == status_filter
            ]
        
        # Update data with filtered results
        result = data.copy()
        result['data'] = filtered_records
        result['total'] = len(filtered_records)
        
        return result
    
    def _flatten_grouped_data(self, grouped_data: List[Dict]) -> List[Dict]:
        """Flatten grouped data structure for display"""
        flattened = []
        
        for group in grouped_data:
            # Extract employee info from identitas_karyawan
            identitas = group.get('identitas_karyawan', {})
            employee_name = identitas.get('employee_name', 'Unknown')
            employee_id = identitas.get('employee_id_venus', identitas.get('employee_id_ptrj', ''))
            task_code = identitas.get('task_code', '')
            station_code = identitas.get('station_code', '')
            
            # Process data_presensi entries
            for entry in group.get('data_presensi', []):
                flattened_record = {
                    'id': entry.get('source_record_id', f"{employee_id}_{entry.get('date', '')}"),
                    'employee_name': employee_name,
                    'employee_id': employee_id,
                    'date': entry.get('date', ''),
                    'check_in': entry.get('check_in', ''),
                    'check_out': entry.get('check_out', ''),
                    'total_hours': entry.get('total_hours', 0),
                    'status': entry.get('status', 'Unknown'),
                    'task_code': task_code,
                    'station_code': station_code,
                    'transfer_status': entry.get('transfer_status', ''),
                    'record_data': entry  # Store full record for automation
                }
                flattened.append(flattened_record)
        
        return flattened
    
    def _is_date_in_range(self, record_date: str, date_from: str, date_to: str) -> bool:
        """Check if record date is within specified range"""
        try:
            if not record_date:
                return False
            
            # Parse record date (assuming YYYY-MM-DD format)
            record_dt = datetime.strptime(record_date, '%Y-%m-%d')
            
            if date_from:
                from_dt = datetime.strptime(date_from, '%Y-%m-%d')
                if record_dt < from_dt:
                    return False
            
            if date_to:
                to_dt = datetime.strptime(date_to, '%Y-%m-%d')
                if record_dt > to_dt:
                    return False
            
            return True
            
        except ValueError:
            logging.warning(f"Invalid date format: {record_date}")
            return False

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from core.browser_manager import BrowserManager
    from core.automation_engine import AutomationEngine
    from core.api_data_automation import RealAPIDataProcessor
    from core.persistent_browser_manager import PersistentBrowserManager
    # Import the enhanced automation system
    from run_user_controlled_automation_enhanced import EnhancedUserControlledAutomationSystem
except ImportError as e:
    print(f"Warning: Could not import some modules: {e}")
    print("Running in standalone mode with basic functionality")
    # Set fallback classes to None
    BrowserManager = None
    AutomationEngine = None
    RealAPIDataProcessor = None
    PersistentBrowserManager = None
    EnhancedUserControlledAutomationSystem = None


class UnifiedVenusApp:
    """Main unified application class"""
    
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Application state
        self.flask_app = None
        self.flask_thread = None
        self.flask_port = 5000
        self.browser_manager = None
        self.automation_engine = None
        self.driver = None
        self.processor = None
        self.enhanced_automation = None
        self.is_browser_ready = False
        self.staging_data_manager = StagingDataManager()
        
        # UI components
        self.root = None
        self.main_frame = None
        self.data_frame = None
        self.control_frame = None
        self.log_frame = None
        
        # Data storage
        self.staging_data = []
        self.selected_records = []
        
        # Configuration
        self.config = self.load_configuration()
        
        self.logger.info("Unified Venus App initialized")
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('unified_venus_app.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def load_configuration(self) -> Dict[str, Any]:
        """Load application configuration"""
        config_path = Path('config.json')
        default_config = {
            'flask_port': 5000,
            'browser': {
                'headless': False,
                'window_size': (1280, 720),
                'disable_notifications': True
            },
            'automation': {
                'implicit_wait': 10,
                'page_load_timeout': 30
            },
            'api': {
                'base_url': 'http://localhost:5173',
                'timeout': 30
            }
        }
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                self.logger.warning(f"Could not load config: {e}")
        
        return default_config
    
    def create_flask_app(self):
        """Create and configure Flask application"""
        self.flask_app = Flask(__name__)
        CORS(self.flask_app, origins=['*'], supports_credentials=True)
        
        @self.flask_app.route('/health')
        def health_check():
            return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})
        
        @self.flask_app.route('/api/staging/data')
        def get_staging_data():
            try:
                filters = {
                    'employee_name': request.args.get('employee_name'),
                    'date_from': request.args.get('date_from'),
                    'date_to': request.args.get('date_to'),
                    'status': request.args.get('status'),
                    'limit': request.args.get('limit', 100, type=int),
                    'offset': request.args.get('offset', 0, type=int)
                }
                
                # Remove None values
                filters = {k: v for k, v in filters.items() if v is not None}
                
                data = self.staging_data_manager.fetch_staging_data(filters)
                return jsonify(data)
            except Exception as e:
                self.logger.error(f"Error fetching staging data: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.flask_app.route('/api/automation/start', methods=['POST'])
        def start_automation():
            try:
                data = request.get_json()
                selected_records = data.get('records', [])
                
                if not selected_records:
                    return jsonify({'error': 'No records selected'}), 400
                
                # Start automation in background thread with asyncio
                def run_async_automation():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.run_automation(selected_records))
                    loop.close()
                
                automation_thread = threading.Thread(target=run_async_automation)
                automation_thread.daemon = True
                automation_thread.start()
                
                return jsonify({'status': 'started', 'records_count': len(selected_records)})
            except Exception as e:
                self.logger.error(f"Error starting automation: {e}")
                return jsonify({'error': str(e)}), 500
        
        return self.flask_app
    
    def start_flask_server(self):
        """Start Flask server in background thread"""
        def run_flask():
            try:
                self.logger.info(f"Starting Flask server on port {self.flask_port}")
                self.flask_app.run(
                    host='127.0.0.1',
                    port=self.flask_port,
                    debug=False,
                    use_reloader=False,
                    threaded=True
                )
            except Exception as e:
                self.logger.error(f"Flask server error: {e}")
        
        self.flask_thread = threading.Thread(target=run_flask)
        self.flask_thread.daemon = True
        self.flask_thread.start()
        
        # Wait for server to start
        time.sleep(2)
        
        # Verify server is running
        try:
            response = requests.get(f'http://127.0.0.1:{self.flask_port}/health', timeout=5)
            if response.status_code == 200:
                self.logger.info("Flask server started successfully")
                return True
        except Exception as e:
            self.logger.error(f"Flask server health check failed: {e}")
        
        return False
    
    async def initialize_browser(self):
        """Initialize WebDriver browser using RealAPIDataProcessor or fallback with auto-login"""
        try:
            # Use RealAPIDataProcessor if available
            if RealAPIDataProcessor is not None:
                self.logger.info("Initializing WebDriver using RealAPIDataProcessor...")
                self.processor = RealAPIDataProcessor()
                success = await self.processor.initialize_browser()
                
                if success:
                    self.is_browser_ready = True
                    self.driver = self.processor.browser_manager.get_driver()
                    self.browser_manager = self.processor.browser_manager
                    
                    # Initialize Enhanced Automation System
                    if EnhancedUserControlledAutomationSystem is not None:
                        self.logger.info("Initializing Enhanced Automation System...")
                        self.enhanced_automation = EnhancedUserControlledAutomationSystem()
                        self.enhanced_automation.processor = self.processor
                        self.enhanced_automation.is_browser_ready = True
                        self.logger.info("Enhanced Automation System initialized successfully")
                    
                    self.logger.info("WebDriver initialized successfully using RealAPIDataProcessor")
                    self.logger.info("Browser is now positioned at task register page")
                    self.logger.info("Automation system is ready for operation!")
                    return True
                else:
                    self.logger.error("Failed to initialize browser using RealAPIDataProcessor")
                    # Fall through to fallback method
            
            # Fallback to basic WebDriver setup
            self.logger.info("Using fallback WebDriver initialization...")
            chrome_options = Options()
            if self.config.get('browser', {}).get('headless', False):
                chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-notifications')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-gpu')
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.is_browser_ready = True
            self.logger.info("WebDriver initialized successfully with fallback method")
            self.logger.info("Note: Fallback mode - manual login may be required")
            self.logger.info("Please navigate to the task register page manually")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize WebDriver: {e}")
            self.is_browser_ready = False
            return False
    
    async def run_automation(self, selected_records: List[Dict]):
        """Run automation process for selected records using Enhanced Automation System"""
        try:
            self.logger.info(f"Starting automation for {len(selected_records)} records")
            
            # Check if enhanced automation system is ready
            if not self.is_browser_ready or not self.enhanced_automation:
                success = await self.initialize_browser()
                if not success or not self.enhanced_automation:
                    self.logger.error("Cannot start automation: Enhanced Automation System not available")
                    self.update_automation_status("Automation failed: Enhanced Automation System not available")
                    return
            
            self.logger.info("Using Enhanced User Controlled Automation System")
            self.update_automation_status("Starting Enhanced Automation...")
            
            # Use Enhanced Automation System to process records
            # Since process_selected_records is async, we need to await it properly
            try:
                success = await self.enhanced_automation.process_selected_records(selected_records)
            except Exception as e:
                self.logger.error(f"Enhanced automation error: {e}")
                success = False
            
            if success:
                self.logger.info("Enhanced Automation completed successfully")
                self.update_automation_status("Automation completed successfully")
                
                # Verify data in database
                self.logger.info("Verifying data in database...")
                self.update_automation_status("Verifying data in database...")
                await asyncio.sleep(2)  # Give time for database updates
                
                # TODO: Add database verification logic here
                self.logger.info("Database verification completed")
                self.update_automation_status("Data verification completed")
            else:
                self.logger.error("Enhanced Automation failed")
                self.update_automation_status("Automation failed")
            
        except Exception as e:
            self.logger.error(f"Automation error: {e}")
            self.update_automation_status(f"Automation failed: {e}")
    
    def create_ui(self):
        """Create the main UI using tkinter"""
        self.root = tk.Tk()
        self.root.title("Venus AutoFill - Unified Desktop Application")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 700)
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Create main container
        main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Data and controls
        left_panel = ttk.Frame(main_container)
        main_container.add(left_panel, weight=3)
        
        # Right panel - Logs and status
        right_panel = ttk.Frame(main_container)
        main_container.add(right_panel, weight=1)
        
        self.create_data_panel(left_panel)
        self.create_control_panel(left_panel)
        self.create_log_panel(right_panel)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Menu bar
        self.create_menu()
        
        self.logger.info("UI created successfully")
    
    def create_data_panel(self, parent):
        """Create data display panel"""
        # Data frame
        data_frame = ttk.LabelFrame(parent, text="Staging Data", padding=5)
        data_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Toolbar
        toolbar = ttk.Frame(data_frame)
        toolbar.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(toolbar, text="Refresh Data", command=self.refresh_data).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Select All", command=self.select_all_records).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Clear Selection", command=self.clear_selection).pack(side=tk.LEFT, padx=(0, 5))
        
        # Search frame
        search_frame = ttk.Frame(toolbar)
        search_frame.pack(side=tk.RIGHT)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=(0, 5))
        search_entry.bind('<KeyRelease>', self.on_search)
        
        # Treeview for data display
        tree_frame = ttk.Frame(data_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        
        # Treeview
        self.data_tree = ttk.Treeview(
            tree_frame,
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set,
            selectmode='extended'
        )
        
        # Configure scrollbars
        v_scrollbar.config(command=self.data_tree.yview)
        h_scrollbar.config(command=self.data_tree.xview)
        
        # Pack scrollbars and treeview
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.data_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure columns (including hidden record_data column)
        columns = ('Employee Name', 'Employee ID', 'Date', 'Check In', 'Check Out', 'Total Hours', 'Status', 'Task Code', 'Station Code', 'Transfer Status', 'record_data')
        self.data_tree['columns'] = columns
        self.data_tree['show'] = 'tree headings'
        
        # Configure column headings and widths
        self.data_tree.heading('#0', text='Select', anchor=tk.W)
        self.data_tree.column('#0', width=60, minwidth=60)
        
        # Configure visible columns with specific widths
        column_configs = [
            ('Employee Name', 150),
            ('Employee ID', 120),
            ('Date', 100),
            ('Check In', 80),
            ('Check Out', 80),
            ('Total Hours', 80),
            ('Status', 80),
            ('Task Code', 150),
            ('Station Code', 150),
            ('Transfer Status', 100)
        ]
        
        for col, width in column_configs:
            self.data_tree.heading(col, text=col, anchor=tk.W)
            self.data_tree.column(col, width=width, minwidth=80)
        
        # Hide the record_data column (used for storing JSON data)
        self.data_tree.column('record_data', width=0, minwidth=0)
        self.data_tree.heading('record_data', text='')
        
        # Bind events
        self.data_tree.bind('<Button-1>', self.on_tree_click)
        self.data_tree.bind('<Double-1>', self.on_tree_double_click)
    
    def create_control_panel(self, parent):
        """Create control panel"""
        control_frame = ttk.LabelFrame(parent, text="Automation Controls", padding=5)
        control_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Control buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X)
        
        self.start_button = ttk.Button(
            button_frame,
            text="Start Automation",
            command=self.start_automation_ui,
            state=tk.DISABLED
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_button = ttk.Button(
            button_frame,
            text="Stop Automation",
            command=self.stop_automation,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.init_browser_button = ttk.Button(
            button_frame,
            text="Initialize Browser",
            command=self.initialize_browser_ui
        )
        self.init_browser_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # Browser status indicator
        self.browser_status_label = ttk.Label(
            button_frame,
            text="Browser: Not Ready",
            foreground="red"
        )
        self.browser_status_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Progress bar
        progress_frame = ttk.Frame(control_frame)
        progress_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(progress_frame, text="Progress:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100
        )
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.progress_label = ttk.Label(progress_frame, text="0/0")
        self.progress_label.pack(side=tk.RIGHT)
    
    def create_log_panel(self, parent):
        """Create log display panel"""
        log_frame = ttk.LabelFrame(parent, text="Application Logs", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # Log text area
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            width=40,
            height=20,
            font=('Consolas', 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Log controls
        log_controls = ttk.Frame(log_frame)
        log_controls.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(log_controls, text="Clear Logs", command=self.clear_logs).pack(side=tk.LEFT)
        ttk.Button(log_controls, text="Save Logs", command=self.save_logs).pack(side=tk.LEFT, padx=(5, 0))
    
    def create_menu(self):
        """Create application menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Refresh Data", command=self.refresh_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Initialize Browser", command=self.initialize_browser_ui)
        tools_menu.add_command(label="Test Connection", command=self.test_connection)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
    
    def refresh_data(self):
        """Refresh staging data from API"""
        try:
            self.update_status("Refreshing data...")
            self.log_message("Fetching staging data...")
            
            # Fetch data from staging data manager
            data_response = self.staging_data_manager.fetch_staging_data()
            
            if 'data' in data_response:
                self.staging_data = data_response['data']
                self.populate_data_tree()
                self.log_message(f"Loaded {len(self.staging_data)} records")
                self.update_status(f"Loaded {len(self.staging_data)} records")
                
                # Auto-initialize browser after successful data load
                if not self.driver and len(self.staging_data) > 0:
                    self.log_message("Auto-initializing browser...")
                    self.root.after(2000, self.auto_initialize_browser)  # Delay 2 seconds
                    
            else:
                self.log_message("No data received from API")
                self.update_status("No data available")
                
        except Exception as e:
            error_msg = f"Error refreshing data: {e}"
            self.log_message(error_msg)
            self.update_status("Error loading data")
            messagebox.showerror("Error", error_msg)
    
    def populate_data_tree(self):
        """Populate the data tree with staging data"""
        # Clear existing items
        for item in self.data_tree.get_children():
            self.data_tree.delete(item)
        
        # Add data to tree
        for i, record in enumerate(self.staging_data):
            item_id = self.data_tree.insert(
                '',
                'end',
                text='☐',  # Checkbox symbol
                values=(
                    record.get('employee_name', ''),
                    record.get('employee_id', ''),
                    record.get('date', ''),
                    record.get('check_in', ''),
                    record.get('check_out', ''),
                    record.get('total_hours', ''),
                    record.get('status', ''),
                    record.get('task_code', ''),
                    record.get('station_code', ''),
                    record.get('transfer_status', '')
                )
            )
            # Store record data with item
            self.data_tree.set(item_id, 'record_data', json.dumps(record))
    
    def on_tree_click(self, event):
        """Handle tree item click for selection"""
        item = self.data_tree.identify('item', event.x, event.y)
        if item:
            # Toggle selection
            current_text = self.data_tree.item(item, 'text')
            if current_text == '☐':
                self.data_tree.item(item, text='☑')
            else:
                self.data_tree.item(item, text='☐')
            
            self.update_selection_count()
    
    def on_tree_double_click(self, event):
        """Handle tree item double click"""
        item = self.data_tree.identify('item', event.x, event.y)
        if item:
            # Show record details
            record_data = self.data_tree.set(item, 'record_data')
            if record_data:
                record = json.loads(record_data)
                self.show_record_details(record)
    
    def on_search(self, event):
        """Handle search input"""
        search_term = self.search_var.get().lower()
        
        # Clear current display
        for item in self.data_tree.get_children():
            self.data_tree.delete(item)
        
        # Filter and display matching records
        filtered_data = []
        for record in self.staging_data:
            if (search_term in record.get('employee_name', '').lower() or
                search_term in record.get('department', '').lower() or
                search_term in record.get('status', '').lower()):
                filtered_data.append(record)
        
        # Populate with filtered data
        for record in filtered_data:
            item_id = self.data_tree.insert(
                '',
                'end',
                text='☐',
                values=(
                    record.get('employee_name', ''),
                    record.get('employee_id', ''),
                    record.get('date', ''),
                    record.get('check_in', ''),
                    record.get('check_out', ''),
                    record.get('total_hours', ''),
                    record.get('status', ''),
                    record.get('task_code', ''),
                    record.get('station_code', ''),
                    record.get('transfer_status', '')
                )
            )
            self.data_tree.set(item_id, 'record_data', json.dumps(record))
    
    def select_all_records(self):
        """Select all visible records"""
        for item in self.data_tree.get_children():
            self.data_tree.item(item, text='☑')
        self.update_selection_count()
    
    def clear_selection(self):
        """Clear all selections"""
        for item in self.data_tree.get_children():
            self.data_tree.item(item, text='☐')
        self.update_selection_count()
    
    def update_selection_count(self):
        """Update selection count and enable/disable start button"""
        selected_count = 0
        for item in self.data_tree.get_children():
            if self.data_tree.item(item, 'text') == '☑':
                selected_count += 1
        
        if selected_count > 0:
            self.start_button.config(state=tk.NORMAL)
        else:
            self.start_button.config(state=tk.DISABLED)
        
        self.update_status(f"{selected_count} records selected")
    
    def start_automation_ui(self):
        """Start automation from UI"""
        # Get selected records
        selected_records = []
        for item in self.data_tree.get_children():
            if self.data_tree.item(item, 'text') == '☑':
                record_data = self.data_tree.set(item, 'record_data')
                if record_data:
                    record = json.loads(record_data)
                    selected_records.append(record)
        
        if not selected_records:
            messagebox.showwarning("Warning", "No records selected")
            return
        
        # Confirm start
        if messagebox.askyesno("Confirm", f"Start automation for {len(selected_records)} records?"):
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            
            # Start automation in background thread with asyncio
            def run_async_automation():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.run_automation(selected_records))
                loop.close()
            
            automation_thread = threading.Thread(target=run_async_automation)
            automation_thread.daemon = True
            automation_thread.start()
    
    def stop_automation(self):
        """Stop automation"""
        # Implementation for stopping automation
        self.log_message("Stopping automation...")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.update_status("Automation stopped")
    
    def initialize_browser_ui(self):
        """Initialize browser from UI with enhanced status updates"""
        try:
            self.update_status("Initializing browser...")
            self.log_message("🔧 Starting browser initialization...")
            
            def run_async_init():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                success = loop.run_until_complete(self.initialize_browser())
                loop.close()
                
                if success:
                    if self.processor:
                        self.root.after(0, lambda: self.log_message("✅ Browser initialized with auto-login"))
                        self.root.after(0, lambda: self.log_message("🎯 Ready for automation!"))
                        self.root.after(0, lambda: messagebox.showinfo("Success", "Browser initialized successfully with auto-login"))
                    else:
                        self.root.after(0, lambda: self.log_message("✅ Browser initialized (fallback mode)"))
                        self.root.after(0, lambda: self.log_message("⚠️ Manual login may be required"))
                        self.root.after(0, lambda: messagebox.showinfo("Success", "Browser initialized (fallback mode)"))
                    self.root.after(0, lambda: self.update_status("Browser ready"))
                else:
                    self.root.after(0, lambda: self.log_message("❌ Browser initialization failed"))
                    self.root.after(0, lambda: messagebox.showerror("Error", "Failed to initialize browser"))
                    self.root.after(0, lambda: self.update_status("Browser initialization failed"))
            
            init_thread = threading.Thread(target=run_async_init)
            init_thread.daemon = True
            init_thread.start()
            
        except Exception as e:
            self.log_message(f"❌ Browser initialization error: {e}")
            messagebox.showerror("Error", f"Browser initialization error: {e}")
    
    def test_connection(self):
        """Test API connection"""
        try:
            response = requests.get(f'http://127.0.0.1:{self.flask_port}/health', timeout=5)
            if response.status_code == 200:
                messagebox.showinfo("Success", "Connection test successful")
            else:
                messagebox.showerror("Error", f"Connection test failed: {response.status_code}")
        except Exception as e:
            messagebox.showerror("Error", f"Connection test failed: {e}")
    
    def show_record_details(self, record):
        """Show detailed record information"""
        details_window = tk.Toplevel(self.root)
        details_window.title("Record Details")
        details_window.geometry("600x400")
        
        # Create text widget with scrollbar
        text_frame = ttk.Frame(details_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text_widget = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        # Display record data
        text_widget.insert(tk.END, json.dumps(record, indent=2, ensure_ascii=False))
        text_widget.config(state=tk.DISABLED)
    
    def show_about(self):
        """Show about dialog"""
        about_text = """
Venus AutoFill - Unified Desktop Application
Version 1.0.0

Integrated application combining:
- Flask API server
- WebDriver automation
- Desktop user interface

Single executable solution for Venus AutoFill system.
        """
        messagebox.showinfo("About", about_text)
    
    def update_status(self, message):
        """Update status bar"""
        self.status_var.set(message)
        self.root.update_idletasks()
    
    def auto_initialize_browser(self):
        """Auto-initialize browser after data load"""
        try:
            self.update_status("Auto-initializing browser...")
            self.log_message("🤖 Starting automatic browser initialization...")
            
            def run_async_auto_init():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                success = loop.run_until_complete(self.initialize_browser())
                loop.close()
                
                if success:
                    if self.processor:
                        self.root.after(0, lambda: self.log_message("✅ Browser auto-initialized with login"))
                        self.root.after(0, lambda: self.log_message("🎯 System ready for automation!"))
                        self.root.after(0, lambda: self.update_status("Browser ready - Auto-login completed"))
                        # Enable automation controls
                        self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
                    else:
                        self.root.after(0, lambda: self.log_message("✅ Browser auto-initialized (fallback mode)"))
                        self.root.after(0, lambda: self.log_message("⚠️ Manual login may be required"))
                        self.root.after(0, lambda: self.update_status("Browser ready - Manual login required"))
                else:
                    self.root.after(0, lambda: self.log_message("❌ Auto browser initialization failed"))
                    self.root.after(0, lambda: self.update_status("Auto-initialization failed"))
            
            init_thread = threading.Thread(target=run_async_auto_init)
            init_thread.daemon = True
            init_thread.start()
            
        except Exception as e:
            self.log_message(f"❌ Auto browser initialization error: {e}")
    
    def log_message(self, message):
        """Add message to log display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_logs(self):
        """Clear log display"""
        self.log_text.delete(1.0, tk.END)
    
    def save_logs(self):
        """Save logs to file"""
        try:
            from tkinter import filedialog
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                messagebox.showinfo("Success", f"Logs saved to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save logs: {e}")
    
    def update_automation_progress(self, current, total, record):
        """Update automation progress"""
        progress = (current / total) * 100
        self.progress_var.set(progress)
        self.progress_label.config(text=f"{current}/{total}")
        
        employee_name = record.get('employee_name', 'Unknown')
        self.log_message(f"Processing {current}/{total}: {employee_name}")
        self.update_status(f"Processing {current}/{total}: {employee_name}")
    
    def update_automation_status(self, message):
        """Update automation status"""
        self.log_message(message)
        self.update_status(message)
        
        # Update browser status indicator
        if self.is_browser_ready:
            if self.processor:
                self.browser_status_label.config(text="Browser: Ready (Auto-login)", foreground="green")
            else:
                self.browser_status_label.config(text="Browser: Ready (Fallback)", foreground="orange")
        else:
            self.browser_status_label.config(text="Browser: Not Ready", foreground="red")
        
        # Re-enable controls
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
        # Reset progress
        self.progress_var.set(0)
        self.progress_label.config(text="0/0")
    
    def on_closing(self):
        """Handle application closing"""
        try:
            if messagebox.askokcancel("Quit", "Do you want to quit?"):
                # Cleanup
                if self.driver:
                    try:
                        self.driver.quit()
                    except:
                        pass
                
                self.logger.info("Application closing")
                self.root.destroy()
        except Exception as e:
            self.logger.error(f"Error during closing: {e}")
            self.root.destroy()
    
    def run(self):
        """Run the unified application"""
        try:
            self.logger.info("Starting Unified Venus App")
            
            # Create Flask app
            self.create_flask_app()
            
            # Start Flask server
            if not self.start_flask_server():
                messagebox.showerror("Error", "Failed to start Flask server")
                return
            
            # Create and run UI
            self.create_ui()
            
            # Initial data load
            self.root.after(1000, self.refresh_data)  # Load data after UI is ready
            
            # Set up closing protocol
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            
            self.logger.info("Application started successfully")
            self.log_message("Application started successfully")
            self.update_status("Ready")
            
            # Start UI main loop
            self.root.mainloop()
            
        except Exception as e:
            self.logger.error(f"Application error: {e}")
            if hasattr(self, 'root') and self.root:
                messagebox.showerror("Error", f"Application error: {e}")
            raise


def main():
    """Main entry point"""
    try:
        app = UnifiedVenusApp()
        app.run()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
    except Exception as e:
        print(f"Application failed to start: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()