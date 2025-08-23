#!/usr/bin/env python3
"""
Venus Desktop Application - Unified Desktop Version
Menggabungkan semua komponen web app menjadi aplikasi desktop Python
"""

import sys
import os
import json
import logging
import asyncio
import threading
import time
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import requests
from concurrent.futures import ThreadPoolExecutor

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import komponen yang diperlukan
try:
    from src.core.api_data_automation import RealAPIDataProcessor
    from src.core.employee_exclusion_validator import EmployeeExclusionValidator
except ImportError as e:
    print(f"Warning: Could not import core modules: {e}")
    RealAPIDataProcessor = None
    EmployeeExclusionValidator = None

# Import enhanced automation system
try:
    from run_user_controlled_automation_enhanced import EnhancedUserControlledAutomationSystem
except ImportError as e:
    print(f"Warning: Could not import enhanced automation: {e}")
    EnhancedUserControlledAutomationSystem = None

# Import enhanced components
try:
    from src.core.enhanced_error_handler import EnhancedErrorHandler
    from src.core.enhanced_automation_manager import EnhancedAutomationManager, AutomationState, AutomationMode
except ImportError as e:
    print(f"Warning: Could not import enhanced components: {e}")
    EnhancedErrorHandler = None
    EnhancedAutomationManager = None
    AutomationState = None
    AutomationMode = None

# Import new desktop components
try:
    from src.core.desktop_error_handler import DesktopErrorHandler, ErrorSeverity
    from src.core.desktop_automation_manager import DesktopAutomationManager, AutomationMode, AutomationState
except ImportError as e:
    print(f"Warning: Could not import desktop components: {e}")
    DesktopErrorHandler = None
    DesktopAutomationManager = None


class DatabaseManager:
    """Manages SQLite database operations for staging data"""
    
    def __init__(self, db_path: str, logger=None):
        self.db_path = db_path
        self.logger = logger or logging.getLogger(__name__)
        self._ensure_database_exists()
    
    def _ensure_database_exists(self):
        """Ensure database file and tables exist"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            # Connect and create tables if they don't exist
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create staging_attendance table if it doesn't exist
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS staging_attendance (
                        id TEXT PRIMARY KEY,
                        employee_id TEXT NOT NULL,
                        employee_name TEXT NOT NULL,
                        date TEXT NOT NULL,
                        day_of_week TEXT,
                        shift TEXT,
                        check_in TEXT,
                        check_out TEXT,
                        regular_hours REAL DEFAULT 0,
                        overtime_hours REAL DEFAULT 0,
                        total_hours REAL DEFAULT 0,
                        task_code TEXT,
                        station_code TEXT,
                        machine_code TEXT,
                        expense_code TEXT,
                        status TEXT DEFAULT 'staged',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        source_record_id TEXT,
                        notes TEXT,
                        raw_charge_job TEXT,
                        leave_type_code TEXT,
                        leave_type_description TEXT,
                        leave_ref_number TEXT,
                        is_alfa BOOLEAN DEFAULT 0,
                        is_on_leave BOOLEAN DEFAULT 0,
                        ptrj_employee_id TEXT DEFAULT 'N/A'
                    )
                ''')
                
                # Create operations_log table if it doesn't exist
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS operations_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        operation_type TEXT NOT NULL,
                        operation_details TEXT,
                        affected_record_ids TEXT,
                        data_volume INTEGER DEFAULT 0,
                        result_status TEXT DEFAULT 'success',
                        error_details TEXT
                    )
                ''')
                
                conn.commit()
                self.logger.info(f"✅ Database initialized: {self.db_path}")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize database: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with sqlite3.connect(self.db_path, timeout=5) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM staging_attendance")
                count = cursor.fetchone()[0]
                self.logger.info(f"✅ Database connection successful - {count} records available")
                return True
        except Exception as e:
            self.logger.error(f"❌ Database connection failed: {e}")
            return False
    
    def fetch_staging_data(self) -> List[Dict[str, Any]]:
        """Fetch all staging data from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row  # Enable dict-like access
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM staging_attendance 
                    ORDER BY employee_name, date
                ''')
                
                rows = cursor.fetchall()
                data = [dict(row) for row in rows]
                
                self.logger.info(f"📊 Fetched {len(data)} records from database")
                return data
                
        except Exception as e:
            self.logger.error(f"❌ Error fetching staging data: {e}")
            return []
    
    def fetch_grouped_staging_data(self) -> List[Dict[str, Any]]:
        """Fetch staging data grouped by employee"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get all data grouped by employee
                cursor.execute('''
                    SELECT employee_id, employee_name, task_code as department,
                           GROUP_CONCAT(id) as record_ids,
                           COUNT(*) as total_records
                    FROM staging_attendance 
                    GROUP BY employee_id, employee_name
                    ORDER BY employee_name
                ''')
                
                employee_groups = cursor.fetchall()
                grouped_data = []
                
                for group in employee_groups:
                    # Get detailed records for this employee
                    cursor.execute('''
                        SELECT * FROM staging_attendance 
                        WHERE employee_id = ? 
                        ORDER BY date
                    ''', (group['employee_id'],))
                    
                    employee_records = cursor.fetchall()
                    data_presensi = [dict(record) for record in employee_records]
                    
                    grouped_data.append({
                        'employee_id': group['employee_id'],
                        'employee_name': group['employee_name'],
                        'department': group['department'],
                        'total_records': group['total_records'],
                        'data_presensi': data_presensi
                    })
                
                total_employees = len(grouped_data)
                total_records = sum(len(emp['data_presensi']) for emp in grouped_data)
                
                self.logger.info(f"📊 Grouped data: {total_employees} employees, {total_records} attendance records")
                return grouped_data
                
        except Exception as e:
            self.logger.error(f"❌ Error fetching grouped staging data: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total records
                cursor.execute("SELECT COUNT(*) FROM staging_attendance")
                total_records = cursor.fetchone()[0]
                
                # Unique employees
                cursor.execute("SELECT COUNT(DISTINCT employee_id) FROM staging_attendance")
                unique_employees = cursor.fetchone()[0]
                
                # Records by status
                cursor.execute("SELECT status, COUNT(*) FROM staging_attendance GROUP BY status")
                status_counts = dict(cursor.fetchall())
                
                return {
                    'total_records': total_records,
                    'unique_employees': unique_employees,
                    'status_counts': status_counts,
                    'database_path': self.db_path
                }
                
        except Exception as e:
            self.logger.error(f"❌ Error getting database stats: {e}")
            return {}


class VenusDesktopApp:
    """
    Aplikasi Desktop Venus yang mengintegrasikan semua komponen:
    - Tkinter GUI untuk interface
    - Flask server internal untuk API
    - Enhanced automation system
    - WebDriver integration
    """
    
    def __init__(self):
        self.logger = self._setup_logging()
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize database manager
        self.db_manager = DatabaseManager(
            db_path=self.config.get('database', {}).get('staging_db_path', 
                'D:\\Gawean Rebinmas\\Autofill Venus Millware\\Selenium Auto Fill _Progress\\Selenium Auto Fill\\Selenium Auto Fill\\data\\staging_attendance.db'),
            logger=self.logger
        )
        
        # Initialize main window
        self.root = tk.Tk()
        self.root.title("Venus AutoFill - Desktop Application")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        
        # Application state
        self.is_browser_ready = False
        self.is_server_running = False
        self.automation_running = False
        self.selected_records = []
        self.staging_data = []
        
        # Components
        self.processor = None
        self.enhanced_automation = None
        self.exclusion_validator = None
        self.flask_thread = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Enhanced components
        self.error_handler = None
        self.automation_manager = None
        
        # Desktop components
        self.desktop_error_handler = None
        self.desktop_automation_manager = None
        
        # Progress tracking
        self.progress_data = {
            'current_employee': '',
            'current_date': '',
            'processed_entries': 0,
            'total_entries': 0,
            'successful_entries': 0,
            'failed_entries': 0,
            'status': 'idle'
        }
        
        # Setup UI
        self._setup_ui()
        self._setup_styles()
        
        # Initialize database status
        self._initialize_database_status()
        
        # Initialize components
        self._initialize_components()
        
        # Start internal server
        self._start_internal_server()
        
        # Load initial data from local database immediately
        self.root.after(500, self._load_initial_staging_data)
        
        # Initialize browser after components are ready
        self.root.after(2000, self._initialize_browser_async)
        
        self.logger.info("Venus Desktop Application initialized")
    
    def _setup_logging(self):
        """Setup logging configuration"""
        log_dir = Path(__file__).parent / "logs"
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'venus_desktop.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        return logging.getLogger(__name__)
    
    def _load_config(self):
        """Load configuration from JSON file"""
        config_path = Path(__file__).parent / "config_venus_desktop_app.json"
        
        # Default configuration
        default_config = {
            "database": {
                "staging_db_path": "D:\\Gawean Rebinmas\\Autofill Venus Millware\\Selenium Auto Fill _Progress\\Selenium Auto Fill\\Selenium Auto Fill\\data\\staging_attendance.db"
            },
            "ui": {
                "auto_refresh_interval": 30,
                "show_progress_details": True,
                "theme": "default"
            },
            "webdriver": {
                "headless": False,
                "timeout": 30,
                "implicit_wait": 10
            },
            "logging": {
                "level": "INFO",
                "max_log_files": 10
            }
        }
        
        try:
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Merge with defaults
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                        elif isinstance(value, dict):
                            for subkey, subvalue in value.items():
                                if subkey not in config[key]:
                                    config[key][subkey] = subvalue
                    return config
            else:
                # Create default config file
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=4, ensure_ascii=False)
                self.logger.info(f"✅ Created default config file: {config_path}")
                return default_config
                
        except Exception as e:
            self.logger.error(f"❌ Error loading config: {e}")
            return default_config
    
    def _initialize_database_status(self):
        """Initialize database status on startup"""
        try:
            if self.db_manager and self.db_manager.test_connection():
                # Database connected successfully
                if hasattr(self, 'db_status_label'):
                    self.db_status_label.config(text="🟢 Database connected", foreground="green")
                
                # Get and log database stats
                stats = self.db_manager.get_stats()
                self.logger.info(f"💾 Database initialized: {stats['total_records']} records, {stats['unique_employees']} unique employees")
            else:
                # Database connection failed
                if hasattr(self, 'db_status_label'):
                    self.db_status_label.config(text="🔴 Database not connected", foreground="red")
                self.logger.warning("⚠️ Database connection failed on startup")
                
        except Exception as e:
            self.logger.error(f"❌ Error initializing database status: {e}")
            if hasattr(self, 'db_status_label'):
                self.db_status_label.config(text="🔴 Database error", foreground="red")
    
    def _setup_ui(self):
        """Setup main UI components"""
        # Create main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(1, weight=1)
        
        # Create UI sections
        self._create_header_section()
        self._create_control_panel()
        self._create_data_section()
        self._create_log_section()
        self._create_status_bar()
    
    def _create_header_section(self):
        """Create header with title and status indicators"""
        header_frame = ttk.LabelFrame(self.main_frame, text="Venus AutoFill Desktop", padding="10")
        header_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        header_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(header_frame, text="🚀 Venus AutoFill Desktop Application", 
                               font=('Segoe UI', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        # Status indicators
        status_frame = ttk.Frame(header_frame)
        status_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E))
        
        # Browser status
        ttk.Label(status_frame, text="Browser:").grid(row=0, column=0, padx=(0, 5))
        self.browser_status_label = ttk.Label(status_frame, text="❌ Not Ready", foreground="red")
        self.browser_status_label.grid(row=0, column=1, padx=(0, 20))
        
        # Server status
        ttk.Label(status_frame, text="Server:").grid(row=0, column=2, padx=(0, 5))
        self.server_status_label = ttk.Label(status_frame, text="❌ Not Running", foreground="red")
        self.server_status_label.grid(row=0, column=3, padx=(0, 20))
        
        # Automation status
        ttk.Label(status_frame, text="Automation:").grid(row=0, column=4, padx=(0, 5))
        self.automation_status_label = ttk.Label(status_frame, text="⏸️ Idle", foreground="gray")
        self.automation_status_label.grid(row=0, column=5)
    
    def _create_control_panel(self):
        """Create control panel with buttons and settings"""
        control_frame = ttk.LabelFrame(self.main_frame, text="Control Panel", padding="10")
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Browser controls
        browser_frame = ttk.LabelFrame(control_frame, text="Browser Control", padding="5")
        browser_frame.pack(fill="x", pady=(0, 10))
        
        self.init_browser_btn = ttk.Button(browser_frame, text="🔧 Initialize Browser", 
                                          command=self._initialize_browser_async)
        self.init_browser_btn.pack(fill="x", pady=2)
        
        self.test_connection_btn = ttk.Button(browser_frame, text="🔗 Test Connection", 
                                             command=self._test_connection)
        self.test_connection_btn.pack(fill="x", pady=2)
        
        # Database Configuration
        db_config_frame = ttk.LabelFrame(control_frame, text="Database Configuration", padding="5")
        db_config_frame.pack(fill="x", pady=(0, 10))
        
        # Database path input
        db_path_frame = ttk.Frame(db_config_frame)
        db_path_frame.pack(fill="x", pady=2)
        
        ttk.Label(db_path_frame, text="DB Path:").pack(side="left")
        self.db_path_var = tk.StringVar(value=self.config.get('database', {}).get('staging_db_path', ''))
        self.db_path_entry = ttk.Entry(db_path_frame, textvariable=self.db_path_var, width=40)
        self.db_path_entry.pack(side="left", padx=(5, 5), fill="x", expand=True)
        
        self.browse_db_btn = ttk.Button(db_path_frame, text="📁 Browse", 
                                       command=self._browse_database_path)
        self.browse_db_btn.pack(side="right", padx=(5, 0))
        
        # Database controls
        db_controls_frame = ttk.Frame(db_config_frame)
        db_controls_frame.pack(fill="x", pady=2)
        
        self.test_db_btn = ttk.Button(db_controls_frame, text="🔍 Test DB Connection", 
                                     command=self._test_database_connection)
        self.test_db_btn.pack(side="left", padx=(0, 5))
        
        self.save_config_btn = ttk.Button(db_controls_frame, text="💾 Save Config", 
                                         command=self._save_config)
        self.save_config_btn.pack(side="left", padx=(0, 5))
        
        # Database status
        self.db_status_label = ttk.Label(db_config_frame, text="🔴 Database not connected", foreground="red")
        self.db_status_label.pack(fill="x", pady=2)
        
        # Data controls
        data_frame = ttk.LabelFrame(control_frame, text="Data Management", padding="5")
        data_frame.pack(fill="x", pady=(0, 10))
        
        self.refresh_data_btn = ttk.Button(data_frame, text="🔄 Refresh Data", 
                                          command=self._refresh_data_async)
        self.refresh_data_btn.pack(fill="x", pady=2)
        
        self.select_all_btn = ttk.Button(data_frame, text="☑️ Select All", 
                                        command=self._select_all_records)
        self.select_all_btn.pack(fill="x", pady=2)
        
        self.clear_selection_btn = ttk.Button(data_frame, text="❌ Clear Selection", 
                                             command=self._clear_selection)
        self.clear_selection_btn.pack(fill="x", pady=2)
        
        # Automation controls
        automation_frame = ttk.LabelFrame(control_frame, text="Automation Control", padding="5")
        automation_frame.pack(fill="x", pady=(0, 10))
        
        # Mode selection
        mode_frame = ttk.Frame(automation_frame)
        mode_frame.pack(fill="x", pady=(0, 5))
        
        ttk.Label(mode_frame, text="Mode:").pack(side="left")
        self.automation_mode = tk.StringVar(value="testing")
        
        mode_radio_frame = ttk.Frame(mode_frame)
        mode_radio_frame.pack(side="right")
        
        ttk.Radiobutton(mode_radio_frame, text="Testing", variable=self.automation_mode, 
                       value="testing").pack(side="left", padx=5)
        ttk.Radiobutton(mode_radio_frame, text="Real", variable=self.automation_mode, 
                       value="real").pack(side="left", padx=5)
        
        self.start_automation_btn = ttk.Button(automation_frame, text="▶️ Start Automation", 
                                              command=self._start_automation_async)
        self.start_automation_btn.pack(fill="x", pady=2)
        
        self.stop_automation_btn = ttk.Button(automation_frame, text="⏹️ Stop Automation", 
                                             command=self._stop_automation, state="disabled")
        self.stop_automation_btn.pack(fill="x", pady=2)
        
        # Enhanced Progress section with data loading indicator
        progress_frame = ttk.LabelFrame(control_frame, text="📊 Progress & Loading Status", padding="5")
        progress_frame.pack(fill="x", pady=(0, 10))
        
        # Data loading progress
        data_loading_frame = ttk.Frame(progress_frame)
        data_loading_frame.pack(fill="x", pady=2)
        
        ttk.Label(data_loading_frame, text="Data Loading:").pack(side="left")
        self.data_loading_var = tk.DoubleVar()
        self.data_loading_bar = ttk.Progressbar(data_loading_frame, variable=self.data_loading_var, 
                                               maximum=100, length=150)
        self.data_loading_bar.pack(side="left", padx=(10, 5))
        
        self.data_loading_label = ttk.Label(data_loading_frame, text="Initializing...")
        self.data_loading_label.pack(side="left", padx=5)
        
        # Automation progress
        automation_frame = ttk.Frame(progress_frame)
        automation_frame.pack(fill="x", pady=2)
        
        ttk.Label(automation_frame, text="Automation:").pack(side="left")
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(automation_frame, variable=self.progress_var, 
                                           maximum=100, length=150)
        self.progress_bar.pack(side="left", padx=(10, 5))
        
        self.progress_label = ttk.Label(automation_frame, text="Ready")
        self.progress_label.pack(side="left", padx=5)
        
        # Statistics
        stats_frame = ttk.LabelFrame(control_frame, text="Statistics", padding="5")
        stats_frame.pack(fill="x")
        
        self.stats_text = tk.Text(stats_frame, height=6, width=30, wrap="word")
        self.stats_text.pack(fill="both", expand=True)
        self._update_statistics()
    
    def _create_data_section(self):
        """Create enhanced data display section with real-time staging data"""
        data_frame = ttk.LabelFrame(self.main_frame, text="📊 Data Staging Real-Time", padding="10")
        data_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        data_frame.columnconfigure(0, weight=1)
        data_frame.rowconfigure(1, weight=1)
        
        # Status and statistics frame
        status_frame = ttk.Frame(data_frame)
        status_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Connection status indicator
        self.connection_status_label = ttk.Label(status_frame, text="🔴 Disconnected", foreground="red")
        self.connection_status_label.grid(row=0, column=0, sticky="w")
        
        # Data statistics
        self.data_stats_label = ttk.Label(status_frame, text="📊 No data loaded")
        self.data_stats_label.grid(row=0, column=1, padx=(20, 0), sticky="w")
        
        # Last update time
        self.last_update_label = ttk.Label(status_frame, text="🕒 Never updated")
        self.last_update_label.grid(row=0, column=2, padx=(20, 0), sticky="w")
        
        # Auto-refresh toggle
        self.auto_refresh_var = tk.BooleanVar(value=True)
        auto_refresh_cb = ttk.Checkbutton(status_frame, text="Auto Refresh", variable=self.auto_refresh_var)
        auto_refresh_cb.grid(row=0, column=3, padx=(20, 0), sticky="e")
        
        # Selection counter
        self.selection_counter_label = ttk.Label(status_frame, text="📋 0 selected")
        self.selection_counter_label.grid(row=0, column=4, padx=(20, 0), sticky="e")
        
        # Configure status frame grid
        status_frame.grid_columnconfigure(4, weight=1)
        
        # Store reference to status frame for later use
        self.status_frame = status_frame
        
        # Create treeview with scrollbars
        tree_frame = ttk.Frame(data_frame)
        tree_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        # Define enhanced columns matching database structure (including hidden record_data column for storing JSON)
        columns = ('employee_name', 'employee_id', 'date', 'day_of_week', 'shift', 'check_in', 'check_out', 'regular_hours', 'overtime_hours', 'total_hours', 'task_code', 'station_code', 'machine_code', 'expense_code', 'raw_charge_job', 'status', 'transfer_status', 'record_data')
        
        self.data_tree = ttk.Treeview(tree_frame, columns=columns, show='tree headings', selectmode='extended')
        
        # Configure enhanced columns
        self.data_tree.heading('#0', text='✓')
        self.data_tree.column('#0', width=30, minwidth=30)
        
        self.data_tree.heading('employee_name', text='Employee Name')
        self.data_tree.column('employee_name', width=180, minwidth=150)
        
        self.data_tree.heading('employee_id', text='Employee ID')
        self.data_tree.column('employee_id', width=100, minwidth=80)
        
        self.data_tree.heading('date', text='Date')
        self.data_tree.column('date', width=90, minwidth=80)
        
        self.data_tree.heading('day_of_week', text='Day')
        self.data_tree.column('day_of_week', width=70, minwidth=60)
        
        self.data_tree.heading('shift', text='Shift')
        self.data_tree.column('shift', width=60, minwidth=50)
        
        self.data_tree.heading('check_in', text='Check In')
        self.data_tree.column('check_in', width=80, minwidth=70)
        
        self.data_tree.heading('check_out', text='Check Out')
        self.data_tree.column('check_out', width=80, minwidth=70)
        
        self.data_tree.heading('regular_hours', text='Regular Hrs')
        self.data_tree.column('regular_hours', width=90, minwidth=80)
        
        self.data_tree.heading('overtime_hours', text='Overtime Hrs')
        self.data_tree.column('overtime_hours', width=90, minwidth=80)
        
        self.data_tree.heading('total_hours', text='Total Hrs')
        self.data_tree.column('total_hours', width=80, minwidth=70)
        
        self.data_tree.heading('task_code', text='Task Code')
        self.data_tree.column('task_code', width=100, minwidth=80)
        
        self.data_tree.heading('station_code', text='Station Code')
        self.data_tree.column('station_code', width=100, minwidth=80)
        
        self.data_tree.heading('machine_code', text='Machine Code')
        self.data_tree.column('machine_code', width=100, minwidth=80)
        
        self.data_tree.heading('expense_code', text='Expense Code')
        self.data_tree.column('expense_code', width=100, minwidth=80)
        
        self.data_tree.heading('raw_charge_job', text='Raw Charge Job')
        self.data_tree.column('raw_charge_job', width=120, minwidth=100)
        
        self.data_tree.heading('status', text='Status')
        self.data_tree.column('status', width=100, minwidth=80)
        
        self.data_tree.heading('transfer_status', text='Transfer Status')
        self.data_tree.column('transfer_status', width=120, minwidth=100)
        
        # Hide the record_data column (used for storing JSON data)
        self.data_tree.column('record_data', width=0, minwidth=0)
        self.data_tree.heading('record_data', text='')
        
        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.data_tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.data_tree.xview)
        
        self.data_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid layout
        self.data_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Bind selection events
        self.data_tree.bind('<<TreeviewSelect>>', self._on_tree_select)
        self.data_tree.bind('<Button-1>', self._on_tree_click)
        self.data_tree.bind('<Double-1>', self._on_data_row_double_click)
        
        # Enhanced keyboard shortcuts for better interaction
        self.data_tree.bind('<Control-a>', self._keyboard_select_all)
        self.data_tree.bind('<Delete>', self._keyboard_clear_selection)
        self.data_tree.bind('<space>', self._keyboard_toggle_selection)
        self.data_tree.bind('<Return>', self._keyboard_show_details)
        
        # Focus handling for keyboard shortcuts
        self.data_tree.focus_set()
    
    def _on_data_row_double_click(self, event):
        """Handle double-click on data row to show details"""
        try:
            item = self.data_tree.identify('item', event.x, event.y)
            if item:
                record_data = self.data_tree.set(item, 'record_data')
                if record_data:
                    record = json.loads(record_data)
                    self._show_record_details(record)
        except Exception as e:
            self._log(f"❌ Error handling double-click: {e}")
    
    def _show_record_details(self, record):
        """Show detailed information about a record"""
        try:
            details_window = tk.Toplevel(self.root)
            details_window.title(f"Record Details - {record.get('employee_name', 'Unknown')}")
            details_window.geometry("500x400")
            details_window.resizable(True, True)
            
            # Create scrolled text widget
            text_widget = scrolledtext.ScrolledText(details_window, wrap="word", padx=10, pady=10)
            text_widget.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Format record details
            details_text = "RECORD DETAILS\n" + "="*50 + "\n\n"
            
            for key, value in record.items():
                details_text += f"{key.replace('_', ' ').title()}: {value}\n"
            
            text_widget.insert("1.0", details_text)
            text_widget.config(state="disabled")
            
            # Add close button
            close_btn = ttk.Button(details_window, text="Close", 
                                 command=details_window.destroy)
            close_btn.pack(pady=10)
            
        except Exception as e:
            self._log(f"❌ Error showing record details: {e}")
    
    def _schedule_initial_data_load(self):
        """Schedule initial data loading after UI is ready"""
        try:
            # Schedule data loading after 2 seconds to allow UI to fully initialize
            self.root.after(2000, self._initial_data_load)
            self._log("📅 Initial data loading scheduled")
        except Exception as e:
            self._log(f"❌ Error scheduling initial data load: {e}")
    
    def _initial_data_load(self):
        """Perform initial data loading"""
        try:
            self._log("🔄 Performing initial data load...")
            
            # Check if auto-refresh is enabled
            if self.auto_refresh_var.get():
                self._refresh_data_async()
            else:
                self._log("⏸️ Auto-refresh disabled, skipping initial data load")
                
        except Exception as e:
            self._log(f"❌ Error in initial data load: {e}")
    
    def _create_log_section(self):
        """Create log display section"""
        log_frame = ttk.LabelFrame(self.main_frame, text="System Log", padding="10")
        log_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Create log text widget with scrollbar
        log_text_frame = ttk.Frame(log_frame)
        log_text_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_text_frame.columnconfigure(0, weight=1)
        log_text_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_text_frame, height=8, wrap="word")
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Log control buttons
        log_btn_frame = ttk.Frame(log_frame)
        log_btn_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        ttk.Button(log_btn_frame, text="Clear Log", command=self._clear_log).pack(side="left", padx=(0, 5))
        ttk.Button(log_btn_frame, text="Save Log", command=self._save_log).pack(side="left")
    
    def _create_status_bar(self):
        """Create status bar at bottom"""
        self.status_bar = ttk.Label(self.root, text="Ready", relief="sunken", anchor="w")
        self.status_bar.grid(row=1, column=0, sticky=(tk.W, tk.E))
    
    def _setup_styles(self):
        """Setup custom styles for ttk widgets"""
        style = ttk.Style()
        
        # Configure button styles
        style.configure('Success.TButton', foreground='green')
        style.configure('Warning.TButton', foreground='orange')
        style.configure('Danger.TButton', foreground='red')
    
    def _initialize_components(self):
        """Initialize application components"""
        try:
            # Initialize enhanced error handler
            if EnhancedErrorHandler:
                self.error_handler = EnhancedErrorHandler()
                self._log("✅ Enhanced error handler initialized")
            
            # Initialize exclusion validator
            if EmployeeExclusionValidator:
                self.exclusion_validator = EmployeeExclusionValidator()
                self._log(f"🔒 Employee exclusion validation: {'Enabled' if self.exclusion_validator.is_enabled() else 'Disabled'}")
            
            # Initialize processor
            if RealAPIDataProcessor:
                self.processor = RealAPIDataProcessor()
                self._log("✅ RealAPIDataProcessor initialized")
            
            # Initialize enhanced automation
            if EnhancedUserControlledAutomationSystem:
                self.enhanced_automation = EnhancedUserControlledAutomationSystem()
                self._log("✅ Enhanced automation system initialized")
            
            # Initialize enhanced automation manager
            if EnhancedAutomationManager and self.error_handler:
                automation_config = {
                    'error_handling': {},
                    'default_mode': 'testing',
                    'batch_size': 10,
                    'delay_between_actions': 1,
                    'health_check_interval': 30,
                    'auto_recovery_enabled': True
                }
                self.automation_manager = EnhancedAutomationManager(automation_config)
                self._log("✅ Enhanced automation manager initialized")
            
            # Initialize desktop components
            if DesktopErrorHandler:
                self.desktop_error_handler = DesktopErrorHandler()
                self._log("✅ Desktop error handler initialized")
            
            if DesktopAutomationManager and self.desktop_error_handler:
                self.desktop_automation_manager = DesktopAutomationManager(self.desktop_error_handler)
                self._log("✅ Desktop automation manager initialized")
            
        except Exception as e:
            self._log(f"❌ Error initializing components: {e}")
            self.logger.error(f"Component initialization error: {e}")
    
    def _start_internal_server(self):
        """Start internal Flask server for API endpoints"""
        try:
            from flask import Flask, jsonify, request
            
            app = Flask(__name__)
            
            @app.route('/api/staging/data-grouped')
            def get_staging_data():
                try:
                    # Fetch data from local database
                    grouped_data = self.db_manager.fetch_grouped_staging_data()
                    
                    # Flatten grouped data to match API format
                    flattened_data = []
                    for group in grouped_data:
                        for record in group.get('data_presensi', []):
                            flattened_data.append(record)
                    
                    # Return data in format matching server port 5173
                    return jsonify({
                        'charge_job_enhancement': {
                            'enabled': True,
                            'records_enhanced': len(flattened_data),
                            'source': 'Local Database'
                        },
                        'data': flattened_data
                    })
                except Exception as e:
                    return jsonify({
                        'error': str(e),
                        'charge_job_enhancement': {
                            'enabled': False,
                            'records_enhanced': 0,
                            'source': 'Local Database'
                        },
                        'data': []
                    }), 500
            
            @app.route('/api/staging/data')
            def get_staging_data_simple():
                try:
                    # Fetch data from local database
                    grouped_data = self.db_manager.fetch_grouped_staging_data()
                    
                    # Flatten grouped data to match API format
                    flattened_data = []
                    for group in grouped_data:
                        for record in group.get('data_presensi', []):
                            flattened_data.append(record)
                    
                    # Return data in format matching server port 5173
                    return jsonify({
                        'charge_job_enhancement': {
                            'enabled': True,
                            'records_enhanced': len(flattened_data),
                            'source': 'Local Database'
                        },
                        'data': flattened_data
                    })
                except Exception as e:
                    return jsonify({
                        'error': str(e),
                        'charge_job_enhancement': {
                            'enabled': False,
                            'records_enhanced': 0,
                            'source': 'Local Database'
                        },
                        'data': []
                    }), 500
            
            @app.route('/api/progress')
            def get_progress():
                return jsonify(self.progress_data)
            
            @app.route('/api/process-selected', methods=['POST'])
            def process_selected():
                try:
                    data = request.get_json()
                    selected_indices = data.get('selected_records', [])
                    mode = data.get('automation_mode', 'testing')
                    
                    # Start automation in background
                    self.executor.submit(self._run_automation_background, selected_indices, mode)
                    
                    return jsonify({
                        'success': True,
                        'message': f'Automation started for {len(selected_indices)} records',
                        'selected_count': len(selected_indices)
                    })
                except Exception as e:
                    return jsonify({
                        'success': False,
                        'error': str(e)
                    }), 500
            
            def run_flask():
                app.run(host='127.0.0.1', port=5174, debug=False, threaded=True, use_reloader=False)
            
            self.flask_thread = threading.Thread(target=run_flask, daemon=True)
            self.flask_thread.start()
            
            time.sleep(1)  # Give server time to start
            self.is_server_running = True
            self._update_server_status()
            self._log("✅ Internal server started on http://127.0.0.1:5174")
            
        except Exception as e:
            self._log(f"❌ Failed to start internal server: {e}")
            self.logger.error(f"Server startup error: {e}")
    
    def _initialize_browser_async(self):
        """Initialize browser in background thread"""
        def init_worker():
            try:
                self._log("🔧 Initializing browser system...")
                self._update_status("Initializing browser...")
                
                if self.processor:
                    # Run async initialization
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    success = loop.run_until_complete(self.processor.initialize_browser())
                    
                    if success:
                        self.is_browser_ready = True
                        
                        # Update enhanced automation
                        if self.enhanced_automation:
                            self.enhanced_automation.processor = self.processor
                            self.enhanced_automation.is_browser_ready = True
                        
                        self._update_browser_status()
                        self._log("✅ Browser initialized successfully")
                        self._update_status("Browser ready")
                        
                        # Show notification that web driver is ready
                        self.root.after(0, self._show_webdriver_ready_notification)
                        
                        # Note: Initial data loading is already handled by _load_initial_staging_data
                        # No need to call _refresh_data_async again to prevent double loading
                    else:
                        self._log("❌ Failed to initialize browser")
                        self._update_status("Browser initialization failed")
                        # Show error notification
                        self.root.after(0, lambda: self._show_notification("error", "Browser initialization failed!"))
                else:
                    self._log("❌ No processor available for browser initialization")
                    self.root.after(0, lambda: self._show_notification("error", "No processor available for browser initialization!"))
                    
            except Exception as e:
                self._log(f"❌ Browser initialization error: {e}")
                self.logger.error(f"Browser init error: {e}")
                self._update_status("Browser initialization error")
                # Show error notification
                self.root.after(0, lambda: self._show_notification("error", f"Browser initialization error: {str(e)[:50]}..."))
        
        self.executor.submit(init_worker)
    
    def _refresh_data_async(self):
        """Refresh staging data in background thread with enhanced progress tracking"""
        def refresh_worker():
            try:
                self._log("🔄 Refreshing staging data...")
                self._update_status("Refreshing data...")
                
                # Update status indicators to show loading
                self.root.after(0, lambda: self._update_status_indicators(connected=None, data_count=None, loading=True))
                self.root.after(0, lambda: self._update_data_loading_progress(10, "Initializing connection..."))
                
                if self.enhanced_automation:
                    start_time = time.time()
                    
                    # Test connection first (30%)
                    self.root.after(0, lambda: self._update_data_loading_progress(30, "Testing API connection..."))
                    connection_ok = self._test_connection_sync()
                    if not connection_ok:
                        self._log("❌ Connection test failed")
                        self.root.after(0, lambda: self._update_data_loading_progress(0, "Connection failed"))
                        self.root.after(0, lambda: self._update_status_indicators(connected=False, data_count=0))
                        return
                    
                    # Run synchronous data fetch (50%)
                    self.root.after(0, lambda: self._update_data_loading_progress(50, "Fetching staging data..."))
                    
                    # Call the synchronous version of fetch_grouped_staging_data
                    grouped_data = self._fetch_grouped_staging_data_sync()
                    
                    if grouped_data:
                        # Apply exclusion filtering (70%)
                        self.root.after(0, lambda: self._update_data_loading_progress(70, "Filtering employee data..."))
                        filtered_data = self.enhanced_automation._filter_excluded_employees_grouped(grouped_data)
                        
                        # Flatten for display (90%)
                        self.root.after(0, lambda: self._update_data_loading_progress(90, "Processing data for display..."))
                        self.staging_data = self.enhanced_automation.flatten_grouped_data_for_selection(filtered_data)
                        
                        # Update UI in main thread (100%)
                        self.root.after(0, lambda: self._update_data_loading_progress(100, "Data loading complete!"))
                        self.root.after(0, self._update_data_display)
                        
                        fetch_time = time.time() - start_time
                        self._log(f"✅ Loaded {len(self.staging_data)} records in {fetch_time:.2f}s")
                        self._update_status(f"Data refreshed - {len(self.staging_data)} records")
                        
                        # Update status indicators
                        self.root.after(0, lambda: self._update_status_indicators(connected=True, data_count=len(self.staging_data)))
                        
                        # Initialize browser after data loading is complete (only if not already initialized)
                        if not self.is_browser_ready:
                            self._log("🚀 Data loading complete, initializing browser...")
                            self.root.after(1000, self._initialize_browser_async)
                        
                        # Reset progress after 2 seconds
                        self.root.after(2000, lambda: self._update_data_loading_progress(0, "Ready for next refresh"))
                        
                        # Schedule next auto-refresh if enabled
                        if self.auto_refresh_var.get():
                            self.root.after(30000, self._refresh_data_async)  # Refresh every 30 seconds
                    else:
                        self._log("❌ No data available")
                        self._update_status("No data available")
                        self.root.after(0, lambda: self._update_data_loading_progress(0, "No data received"))
                        self.root.after(0, lambda: self._update_status_indicators(connected=True, data_count=0))
                else:
                    self._log("❌ Enhanced automation not available")
                    self.root.after(0, lambda: self._update_data_loading_progress(0, "Automation unavailable"))
                    self.root.after(0, lambda: self._update_status_indicators(connected=False, data_count=0))
                    
            except Exception as e:
                self._log(f"❌ Data refresh error: {e}")
                self.logger.error(f"Data refresh error: {e}")
                self._update_status("Data refresh failed")
                self.root.after(0, lambda: self._update_data_loading_progress(0, f"Error: {str(e)[:30]}..."))
                self.root.after(0, lambda: self._update_status_indicators(connected=False, data_count=0))
        
        self.executor.submit(refresh_worker)
    
    def _update_data_display(self, data=None):
        """Update data treeview with current staging data"""
        # Use provided data or fall back to self.staging_data
        display_data = data if data is not None else self.staging_data
        try:
            # Clear existing items
            for item in self.data_tree.get_children():
                self.data_tree.delete(item)
            
            # Add new items
            for i, record in enumerate(display_data):
                employee_name = record.get('employee_name', 'Unknown')
                # Use ptrj_employee_id for display if available, otherwise use employee_id
                employee_id = record.get('ptrj_employee_id', record.get('employee_id', 'Unknown'))
                date = record.get('date', 'Unknown')
                day_of_week = record.get('day_of_week', '')
                shift = record.get('shift', '')
                check_in = record.get('check_in', '')
                check_out = record.get('check_out', '')
                regular_hours = record.get('regular_hours', 0)
                overtime_hours = record.get('overtime_hours', 0)
                total_hours = record.get('total_hours', 0)
                task_code = record.get('task_code', '')
                station_code = record.get('station_code', '')
                machine_code = record.get('machine_code', '')
                expense_code = record.get('expense_code', '')
                raw_charge_job = record.get('raw_charge_job', '')
                status = "Ready" if not record.get('is_transferred', False) else "Transferred"
                transfer_status = record.get('transfer_status', 'Pending')
                
                # Insert item with checkbox-like behavior
                item_id = self.data_tree.insert('', 'end', 
                                               text='☐',  # Unchecked checkbox
                                               values=(employee_name, employee_id, date, day_of_week, 
                                                      shift, check_in, check_out, regular_hours, 
                                                      overtime_hours, total_hours, task_code, 
                                                      station_code, machine_code, expense_code, 
                                                      raw_charge_job, status, transfer_status),
                                               tags=(str(i),))
                
                # Store record data
                self.data_tree.set(item_id, 'record_data', json.dumps(record))
            
            self._update_statistics()
            self._update_selection_counter()
            
        except Exception as e:
            self._log(f"❌ Error updating data display: {e}")
            self.logger.error(f"Data display error: {e}")
    
    def _on_tree_select(self, event):
        """Handle tree selection events"""
        try:
            selected_items = self.data_tree.selection()
            self.selected_records = []
            
            for item in selected_items:
                record_data = self.data_tree.set(item, 'record_data')
                if record_data:
                    record = json.loads(record_data)
                    self.selected_records.append(record)
            
            self._update_statistics()
            
        except Exception as e:
            self._log(f"❌ Error handling selection: {e}")
    
    def _on_tree_click(self, event):
        """Handle tree click events for checkbox behavior"""
        try:
            item = self.data_tree.identify('item', event.x, event.y)
            if item:
                current_text = self.data_tree.item(item, 'text')
                new_text = '☑' if current_text == '☐' else '☐'
                self.data_tree.item(item, text=new_text)
                
                # Update selection
                if new_text == '☑':
                    self.data_tree.selection_add(item)
                else:
                    self.data_tree.selection_remove(item)
                
        except Exception as e:
            self._log(f"❌ Error handling click: {e}")
    
    def _select_all_records(self):
        """Select all records in the tree"""
        try:
            for item in self.data_tree.get_children():
                self.data_tree.item(item, text='☑')
                self.data_tree.selection_add(item)
            
            self._on_tree_select(None)
            self._update_selection_counter()
            self._log(f"✅ Selected all {len(self.data_tree.get_children())} records")
            
        except Exception as e:
            self._log(f"❌ Error selecting all: {e}")
    
    def _clear_selection(self):
        """Clear all selections"""
        try:
            for item in self.data_tree.get_children():
                self.data_tree.item(item, text='☐')
                self.data_tree.selection_remove(item)
            
            self.selected_records = []
            self._update_statistics()
            self._update_selection_counter()
            self._log("✅ Selection cleared")
            
        except Exception as e:
            self._log(f"❌ Error clearing selection: {e}")
    
    def _keyboard_select_all(self, event):
        """Handle Ctrl+A keyboard shortcut for selecting all records"""
        self._select_all_records()
        return 'break'  # Prevent default behavior
    
    def _keyboard_clear_selection(self, event):
        """Handle Delete key for clearing selection"""
        self._clear_selection()
        return 'break'
    
    def _keyboard_toggle_selection(self, event):
        """Handle Space key for toggling current item selection"""
        try:
            current_item = self.data_tree.focus()
            if current_item:
                current_text = self.data_tree.item(current_item, 'text')
                new_text = '☑' if current_text == '☐' else '☐'
                self.data_tree.item(current_item, text=new_text)
                
                # Update selection
                if new_text == '☑':
                    self.data_tree.selection_add(current_item)
                else:
                    self.data_tree.selection_remove(current_item)
                
                self._on_tree_select(None)
                self._update_selection_counter()
            return 'break'
        except Exception as e:
            self._log(f"❌ Error toggling selection: {e}")
    
    def _keyboard_show_details(self, event):
        """Handle Enter key for showing record details"""
        try:
            current_item = self.data_tree.focus()
            if current_item:
                record_data = self.data_tree.set(current_item, 'record_data')
                if record_data:
                    record = json.loads(record_data)
                    self._show_record_details(record)
            return 'break'
        except Exception as e:
            self._log(f"❌ Error showing details: {e}")
    
    def _add_selection_counter_to_ui(self):
        """Add a selection counter to the data section"""
        try:
            # Add selection counter label to status frame
            if hasattr(self, 'status_frame'):
                self.selection_counter_label = ttk.Label(self.status_frame, text="📋 0 selected")
                self.selection_counter_label.grid(row=0, column=4, padx=(20, 0), sticky="e")
                
                # Update grid configuration
                self.status_frame.grid_columnconfigure(4, weight=0)
        except Exception as e:
             self._log(f"❌ Error adding selection counter: {e}")
    
    def _update_selection_counter(self):
        """Update the selection counter display"""
        try:
            if hasattr(self, 'selection_counter_label') and hasattr(self, 'selected_records'):
                count = len(self.selected_records)
                total = len(self.data_tree.get_children()) if hasattr(self, 'data_tree') else 0
                
                if count == 0:
                    text = "📋 0 selected"
                    color = "gray"
                elif count == total and total > 0:
                    text = f"📋 All {count} selected"
                    color = "green"
                else:
                    text = f"📋 {count} of {total} selected"
                    color = "blue"
                
                self.selection_counter_label.config(text=text, foreground=color)
        except Exception as e:
            self._log(f"❌ Error updating selection counter: {e}")
    
    def _start_automation_async(self):
        """Start automation in background thread"""
        if not self.is_browser_ready:
            messagebox.showwarning("Warning", "Please initialize browser first")
            return
        
        if not self.selected_records:
            messagebox.showwarning("Warning", "Please select at least one record")
            return
        
        if self.automation_running:
            messagebox.showwarning("Warning", "Automation is already running")
            return
        
        # Get automation mode
        mode = self.automation_mode.get()
        
        # Confirm automation start
        result = messagebox.askyesno("Confirm Automation", 
                                   f"Start automation for {len(self.selected_records)} records in {mode} mode?")
        if not result:
            return
        
        # Start automation
        self.automation_running = True
        self._update_automation_status()
        self._log(f"🚀 Starting automation for {len(self.selected_records)} records in {mode} mode")
        
        self.executor.submit(self._run_automation_background, self.selected_records, mode)
    
    def _run_automation_background(self, selected_data, mode):
        """Run automation in background thread"""
        try:
            # Use desktop automation manager if available
            if self.desktop_automation_manager and self.enhanced_automation:
                # Set automation mode
                automation_mode = AutomationMode.REAL if mode == 'real' else AutomationMode.TESTING
                
                # Run async automation with desktop manager
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Update progress callback
                def progress_callback(current, total, employee_name="", status=""):
                    self.progress_data.update({
                        'current_employee': employee_name,
                        'processed_entries': current,
                        'total_entries': total,
                        'status': status
                    })
                    self.root.after(0, self._update_statistics)
                
                success = loop.run_until_complete(
                    self.desktop_automation_manager.run_automation(
                        automation_mode=automation_mode,
                        selected_records=selected_data,
                        enhanced_automation=self.enhanced_automation,
                        progress_callback=progress_callback
                    )
                )
                
                if success:
                    self._log("✅ Automation completed successfully")
                    self.root.after(0, lambda: messagebox.showinfo("Success", "Automation completed successfully!"))
                else:
                    self._log("❌ Automation failed")
                    self.root.after(0, lambda: messagebox.showerror("Error", "Automation failed!"))
            elif self.automation_manager and self.enhanced_automation:
                # Fallback to enhanced automation manager
                automation_mode = AutomationMode.REAL if mode == 'real' else AutomationMode.TESTING
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                def progress_callback(current, total, employee_name="", status=""):
                    self.progress_data.update({
                        'current_employee': employee_name,
                        'processed_entries': current,
                        'total_entries': total,
                        'status': status
                    })
                    self.root.after(0, self._update_statistics)
                
                success = loop.run_until_complete(
                    self.automation_manager.run_automation(
                        automation_mode=automation_mode,
                        selected_records=selected_data,
                        enhanced_automation=self.enhanced_automation,
                        progress_callback=progress_callback
                    )
                )
                
                if success:
                    self._log("✅ Automation completed successfully")
                    self.root.after(0, lambda: messagebox.showinfo("Success", "Automation completed successfully!"))
                else:
                    self._log("❌ Automation failed")
                    self.root.after(0, lambda: messagebox.showerror("Error", "Automation failed!"))
            elif self.enhanced_automation:
                # Fallback to original automation
                self.enhanced_automation.automation_mode = mode
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                success = loop.run_until_complete(
                    self.enhanced_automation.process_selected_records(selected_data)
                )
                
                if success:
                    self._log("✅ Automation completed successfully")
                    self.root.after(0, lambda: messagebox.showinfo("Success", "Automation completed successfully!"))
                else:
                    self._log("❌ Automation failed")
                    self.root.after(0, lambda: messagebox.showerror("Error", "Automation failed!"))
            else:
                self._log("❌ Enhanced automation not available")
                
        except Exception as e:
            self._log(f"❌ Automation error: {e}")
            self.logger.error(f"Automation error: {e}")
            
            # Desktop error handling
            if self.desktop_error_handler:
                error_info = self.desktop_error_handler.handle_error(e, {
                    'selected_count': len(selected_data),
                    'mode': mode,
                    'browser_ready': self.is_browser_ready
                })
                error_message = f"Automation error ({error_info.severity.value}): {error_info.message}"
            elif self.error_handler:
                error_info = self.error_handler.handle_automation_error(e, {
                    'selected_count': len(selected_data),
                    'mode': mode,
                    'browser_ready': self.is_browser_ready
                })
                error_message = f"Automation error: {error_info['message']}\n\nSuggested action: {error_info['suggested_action']}"
            else:
                error_message = f"Automation error: {e}"
            
            self.root.after(0, lambda: messagebox.showerror("Error", error_message))
        finally:
            self.automation_running = False
            self.root.after(0, self._update_automation_status)
            self.root.after(0, self._refresh_data_async)  # Refresh data after automation
    
    def _stop_automation(self):
        """Stop running automation"""
        try:
            if self.automation_running:
                # Note: This is a simplified stop - in a real implementation,
                # you'd need to implement proper cancellation in the automation system
                self.automation_running = False
                self._update_automation_status()
                self._log("⏹️ Automation stop requested")
            
        except Exception as e:
            self._log(f"❌ Error stopping automation: {e}")
    
    def _test_connection(self):
        """Test connection to staging server"""
        def test_worker():
            try:
                self._log("🔗 Testing connection to staging server...")
                self._update_status("Testing connection...")
                
                response = requests.get("http://localhost:5173/api/staging/data-grouped", timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        self._log(f"✅ Connection successful - {data.get('count', 0)} records available")
                        self._update_status("Connection successful")
                    else:
                        self._log(f"❌ API error: {data.get('error', 'Unknown error')}")
                        self._update_status("API error")
                else:
                    self._log(f"❌ Connection failed - HTTP {response.status_code}")
                    self._update_status("Connection failed")
                    
            except requests.exceptions.RequestException as e:
                self._log(f"❌ Connection error: {e}")
                self._update_status("Connection error")
            except Exception as e:
                self._log(f"❌ Test error: {e}")
                self._update_status("Test error")
        
        self.executor.submit(test_worker)
    
    def _update_browser_status(self):
        """Update browser status indicator"""
        if self.is_browser_ready:
            self.browser_status_label.config(text="✅ Ready", foreground="green")
        else:
            self.browser_status_label.config(text="❌ Not Ready", foreground="red")
    
    def _update_server_status(self):
        """Update server status indicator"""
        if self.is_server_running:
            self.server_status_label.config(text="✅ Running", foreground="green")
        else:
            self.server_status_label.config(text="❌ Not Running", foreground="red")
    
    def _update_automation_status(self):
        """Update automation status indicator"""
        if self.automation_running:
            self.automation_status_label.config(text="▶️ Running", foreground="blue")
            self.start_automation_btn.config(state="disabled")
            self.stop_automation_btn.config(state="normal")
        else:
            self.automation_status_label.config(text="⏸️ Idle", foreground="gray")
            self.start_automation_btn.config(state="normal")
            self.stop_automation_btn.config(state="disabled")
    
    def _update_statistics(self):
        """Update statistics display"""
        try:
            total_records = len(self.staging_data)
            selected_count = len(self.selected_records)
            
            stats_text = f"""Total Records: {total_records}
Selected: {selected_count}

Progress:
Processed: {self.progress_data['processed_entries']}
Total: {self.progress_data['total_entries']}
Successful: {self.progress_data['successful_entries']}
Failed: {self.progress_data['failed_entries']}

Status: {self.progress_data['status']}"""
            
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(1.0, stats_text)
            
            # Update progress bar
            if self.progress_data['total_entries'] > 0:
                progress = (self.progress_data['processed_entries'] / self.progress_data['total_entries']) * 100
                self.progress_var.set(progress)
                self.progress_label.config(text=f"{self.progress_data['processed_entries']}/{self.progress_data['total_entries']} - {progress:.1f}%")
            else:
                self.progress_var.set(0)
                self.progress_label.config(text="Ready")
            
        except Exception as e:
            self._log(f"❌ Error updating statistics: {e}")
    
    def _update_status_indicators(self, connected=None, data_count=None, loading=False):
        """Update status indicators in data section"""
        try:
            if loading:
                self.connection_status_label.config(text="🔄 Loading...", foreground="blue")
                self.data_stats_label.config(text="📊 Fetching data...")
                self.last_update_label.config(text="🕒 Updating...")
            else:
                if connected is not None:
                    if connected:
                        self.connection_status_label.config(text="🟢 Connected", foreground="green")
                    else:
                        self.connection_status_label.config(text="🔴 Disconnected", foreground="red")
                
                if data_count is not None:
                    self.data_stats_label.config(text=f"📊 {data_count} records loaded")
                
                # Update last update time
                current_time = datetime.now().strftime("%H:%M:%S")
                self.last_update_label.config(text=f"🕒 Last update: {current_time}")
                
        except Exception as e:
            self.logger.error(f"Error updating status indicators: {e}")
    
    def _update_data_loading_progress(self, progress, message):
        """Update data loading progress bar and message"""
        try:
            self.data_loading_var.set(progress)
            self.data_loading_label.config(text=message)
        except Exception as e:
            self.logger.error(f"Error updating data loading progress: {e}")
    
    def _show_notification(self, notification_type, message):
        """Show notification to user"""
        try:
            if notification_type == "success":
                messagebox.showinfo("Success", message)
            elif notification_type == "warning":
                messagebox.showwarning("Warning", message)
            elif notification_type == "error":
                messagebox.showerror("Error", message)
            else:
                messagebox.showinfo("Information", message)
        except Exception as e:
            self.logger.error(f"Error showing notification: {e}")
    
    def _show_webdriver_ready_notification(self):
        """Show specific notification when WebDriver is ready at Task Register"""
        try:
            notification_message = (
                "🎉 WebDriver is Ready!\n\n"
                "✅ Browser has been initialized successfully\n"
                "✅ Navigated to Task Register page\n"
                "✅ Ready for data input automation\n\n"
                "You can now:\n"
                "• Select data records to process\n"
                "• Start automation in Testing or Real mode\n"
                "• Monitor progress in real-time"
            )
            
            messagebox.showinfo("WebDriver Ready - Task Register", notification_message)
            
            # Also log the success
            self._log("🎉 WebDriver ready notification shown to user")
            
        except Exception as e:
            self.logger.error(f"Error showing WebDriver ready notification: {e}")
    
    def _test_connection_sync(self):
        """Test database connection synchronously"""
        try:
            if not self.db_manager:
                return False
            return self.db_manager.test_connection()
        except Exception as e:
            self.logger.error(f"Database connection test failed: {e}")
            return False
    
    def _fetch_grouped_staging_data_sync(self):
        """Fetch grouped staging data from local database synchronously"""
        try:
            self.logger.info("💾 Fetching grouped staging data from local database...")
            
            if not self.db_manager:
                self.logger.error("❌ Database manager not initialized")
                return []
            
            # Test connection first
            if not self.db_manager.test_connection():
                self.logger.error("❌ Database connection failed")
                return []
            
            # Fetch grouped data
            grouped_data = self.db_manager.fetch_grouped_staging_data()
            
            if grouped_data:
                total_employees = len(grouped_data)
                total_records = sum(len(emp.get('data_presensi', [])) for emp in grouped_data)
                
                self.logger.info(f"📊 Grouped data loaded: {total_employees} employees, {total_records} attendance records")
                
                # Log database stats
                stats = self.db_manager.get_stats()
                self.logger.info(f"💾 Database stats: {stats['total_records']} total records, {stats['unique_employees']} unique employees")
                
                return grouped_data
            else:
                self.logger.warning("⚠️ No data found in database")
                return []
                
        except Exception as e:
            self.logger.error(f"❌ Error fetching grouped staging data from database: {e}")
            return []
    
    def _load_initial_staging_data(self):
        """Load initial staging data from local database immediately on startup"""
        try:
            self._log("💾 Loading initial staging data from local database...")
            self._update_status("Loading staging data...")
            
            # Update status indicators to show loading
            self._update_status_indicators(loading=True)
            
            # Fetch data from local database
            grouped_data = self._fetch_grouped_staging_data_sync()
            
            if grouped_data:
                # Convert grouped data to flat list for display
                flat_data = []
                for employee in grouped_data:
                    employee_name = employee.get('employee_name', 'Unknown')
                    employee_id = employee.get('employee_id', 'Unknown')
                    
                    for record in employee.get('data_presensi', []):
                        # Create flat record with actual database columns
                        flat_record = {
                            'employee_name': employee_name,
                            'employee_id': employee_id,
                            'ptrj_employee_id': record.get('ptrj_employee_id', ''),
                            'date': record.get('date', ''),
                            'day_of_week': record.get('day_of_week', ''),
                            'shift': record.get('shift', ''),
                            'check_in': record.get('check_in', ''),
                            'check_out': record.get('check_out', ''),
                            'regular_hours': record.get('regular_hours', ''),
                            'overtime_hours': record.get('overtime_hours', ''),
                            'total_hours': record.get('total_hours', ''),
                            'task_code': record.get('task_code', ''),
                            'station_code': record.get('station_code', ''),
                            'machine_code': record.get('machine_code', ''),
                            'expense_code': record.get('expense_code', ''),
                            'status': record.get('status', 'staged'),
                            'transfer_status': 'pending'  # Default value since column doesn't exist
                        }
                        flat_data.append(flat_record)
                
                # Update staging data and display
                self.staging_data = flat_data
                self._update_data_display(flat_data)
                
                # Update status indicators
                self._update_status_indicators(connected=True, data_count=len(flat_data), loading=False)
                
                self._log(f"✅ Initial staging data loaded: {len(flat_data)} records from {len(grouped_data)} employees")
                self._update_status(f"Staging data loaded: {len(flat_data)} records")
                
            else:
                self.staging_data = []
                self._update_data_display([])
                self._update_status_indicators(connected=True, data_count=0, loading=False)
                self._log("⚠️ No staging data found in local database")
                self._update_status("No staging data found")
                
        except Exception as e:
            self.logger.error(f"❌ Error loading initial staging data: {e}")
            self._log(f"❌ Error loading initial staging data: {e}")
            self._update_status_indicators(connected=False, loading=False)
            self._update_status("Error loading staging data")
    
    def _update_status(self, message):
        """Update status bar"""
        self.status_bar.config(text=message)
    
    def _log(self, message):
        """Add message to log display"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_message = f"[{timestamp}] {message}\n"
            
            self.log_text.insert(tk.END, log_message)
            self.log_text.see(tk.END)
            
            # Also log to file
            self.logger.info(message)
            
        except Exception as e:
            print(f"Logging error: {e}")
    
    def _clear_log(self):
        """Clear log display"""
        self.log_text.delete(1.0, tk.END)
        self._log("Log cleared")
    
    def _save_log(self):
        """Save log to file"""
        try:
            from tkinter import filedialog
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="Save Log File"
            )
            
            if filename:
                log_content = self.log_text.get(1.0, tk.END)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(log_content)
                
                self._log(f"✅ Log saved to {filename}")
                messagebox.showinfo("Success", f"Log saved to {filename}")
            
        except Exception as e:
            self._log(f"❌ Error saving log: {e}")
            messagebox.showerror("Error", f"Failed to save log: {e}")
    
    def _on_closing(self):
        """Handle application closing"""
        try:
            if self.automation_running:
                result = messagebox.askyesno("Confirm Exit", 
                                           "Automation is running. Are you sure you want to exit?")
                if not result:
                    return
            
            self._log("🛑 Shutting down application...")
            
            # Cleanup
            if self.desktop_automation_manager:
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.desktop_automation_manager.cleanup())
                except:
                    pass
            
            if self.automation_manager:
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.automation_manager.cleanup())
                except:
                    pass
            
            if self.enhanced_automation:
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.enhanced_automation.cleanup())
                except:
                    pass
            
            # Shutdown executor
            self.executor.shutdown(wait=False)
            
            self.root.destroy()
            
        except Exception as e:
            self.logger.error(f"Shutdown error: {e}")
            self.root.destroy()
    
    def _browse_database_path(self):
        """Browse for database file"""
        try:
            from tkinter import filedialog
            file_path = filedialog.askopenfilename(
                title="Select Staging Database",
                filetypes=[("SQLite Database", "*.db"), ("All Files", "*.*")],
                initialdir=os.path.dirname(self.db_path_var.get()) if self.db_path_var.get() else os.getcwd()
            )
            
            if file_path:
                self.db_path_var.set(file_path)
                self.logger.info(f"Database path selected: {file_path}")
                
        except Exception as e:
            self.logger.error(f"Error browsing database path: {e}")
            messagebox.showerror("Error", f"Failed to browse database path: {e}")
    
    def _test_database_connection(self):
        """Test database connection"""
        try:
            db_path = self.db_path_var.get().strip()
            if not db_path:
                messagebox.showwarning("Warning", "Please enter a database path first")
                return
            
            # Update database manager with new path
            self.db_manager = DatabaseManager(db_path)
            
            # Test connection
            if self.db_manager.test_connection():
                self.db_status_label.config(text="🟢 Database connected successfully", foreground="green")
                
                # Get database stats
                stats = self.db_manager.get_stats()
                stats_msg = f"Database connected!\nRecords: {stats['total_records']}\nUnique employees: {stats['unique_employees']}"
                messagebox.showinfo("Success", stats_msg)
                
                self.logger.info(f"Database connection successful: {db_path}")
            else:
                self.db_status_label.config(text="🔴 Database connection failed", foreground="red")
                messagebox.showerror("Error", "Failed to connect to database")
                
        except Exception as e:
            self.db_status_label.config(text="🔴 Database connection error", foreground="red")
            self.logger.error(f"Database connection error: {e}")
            messagebox.showerror("Error", f"Database connection error: {e}")
    
    def _save_config(self):
        """Save current configuration to file"""
        try:
            db_path = self.db_path_var.get().strip()
            
            # Update config
            if 'database' not in self.config:
                self.config['database'] = {}
            
            self.config['database']['staging_db_path'] = db_path
            
            # Save to file
            config_path = os.path.join(os.getcwd(), 'config_venus_desktop_app.json')
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            
            messagebox.showinfo("Success", f"Configuration saved to {config_path}")
            self.logger.info(f"Configuration saved: {config_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            messagebox.showerror("Error", f"Failed to save configuration: {e}")
    
    def run(self):
        """Run the desktop application"""
        try:
            # Setup close handler
            self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
            
            # Initial log message
            self._log("🚀 Venus Desktop Application started")
            self._log("💡 Initialize browser to begin automation")
            
            # Start main loop
            self.root.mainloop()
            
        except Exception as e:
            self.logger.error(f"Application error: {e}")
            messagebox.showerror("Application Error", f"An error occurred: {e}")


def main():
    """Main function"""
    try:
        print("🚀 Starting Venus Desktop Application...")
        
        app = VenusDesktopApp()
        app.run()
        
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        logging.exception("Application startup error")


if __name__ == "__main__":
    main()