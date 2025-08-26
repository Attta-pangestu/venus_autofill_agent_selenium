"""
Data Interface - Flask Web Application
Provides a web interface for viewing and selecting staging data for automation
"""

import json
import logging
import requests
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
import asyncio
import threading

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from automation_service import get_automation_service
from core.employee_exclusion_validator import EmployeeExclusionValidator

# Import enhanced system components
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.core.database_manager import DatabaseManager

# Set up logging with UTF-8 support
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('flask_app.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins=['http://localhost:*', 'file://*'], supports_credentials=True)

# Configure Flask for better connection handling
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
app.config['JSON_SORT_KEYS'] = False

# Configuration
# Database-based configuration - no longer using API endpoints

class StagingDataManager:
    """Manages staging data operations"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.cached_data = None
        self.cache_timestamp = None
        self.cache_duration = 300  # 5 minutes
    
    def fetch_staging_data(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Fetch staging data from database with optional filters"""
        try:
            # Check cache first
            if self._is_cache_valid():
                logger.info("Using cached staging data")
                return self._apply_filters(self.cached_data, filters)
            
            # Fetch fresh data from database
            logger.info("Fetching staging data from database")
            
            # Build SQL query with filters
            query = "SELECT * FROM staging_attendance WHERE 1=1"
            params = []
            
            if filters:
                if filters.get('employee_name'):
                    query += " AND employee_name LIKE ?"
                    params.append(f"%{filters['employee_name']}%")
                if filters.get('date_from'):
                    query += " AND date >= ?"
                    params.append(filters['date_from'])
                if filters.get('date_to'):
                    query += " AND date <= ?"
                    params.append(filters['date_to'])
                if filters.get('status'):
                    query += " AND status = ?"
                    params.append(filters['status'])
            
            # Add ordering
            query += " ORDER BY date DESC, employee_name"
            
            # Add limit and offset
            limit = filters.get('limit', 50) if filters else 50
            offset = filters.get('offset', 0) if filters else 0
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            # Execute query
            records = self.db_manager.execute_query(query, params)
            
            # Get total count for pagination
            count_query = "SELECT COUNT(*) as total FROM staging_attendance WHERE 1=1"
            count_params = []
            
            if filters:
                if filters.get('employee_name'):
                    count_query += " AND employee_name LIKE ?"
                    count_params.append(f"%{filters['employee_name']}%")
                if filters.get('date_from'):
                    count_query += " AND date >= ?"
                    count_params.append(filters['date_from'])
                if filters.get('date_to'):
                    count_query += " AND date <= ?"
                    count_params.append(filters['date_to'])
                if filters.get('status'):
                    count_query += " AND status = ?"
                    count_params.append(filters['status'])
            
            total_result = self.db_manager.execute_query(count_query, count_params)
            total = total_result[0]['total'] if total_result else 0
            
            # Format response
            data = {
                'data': records,
                'total': total,
                'page': (offset // limit) + 1,
                'per_page': limit,
                'success': True
            }
            
            # Cache the data
            self.cached_data = data
            self.cache_timestamp = datetime.now()
            
            logger.info(f"Successfully fetched {len(records)} staging records from database")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching staging data from database: {e}")
            return {
                'error': f'Failed to fetch data from database: {str(e)}',
                'data': [],
                'total': 0,
                'page': 1,
                'per_page': 50,
                'success': False
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
            logger.warning(f"Invalid date format: {record_date}")
            return False

# Load default configuration for automation service
def load_default_config():
    """Load default configuration for automation service"""
    return {
        "browser": {
            "headless": False,
            "window_size": [1280, 720],
            "disable_notifications": True,
            "event_delay": 0.5,
            "chrome_options": [
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--start-maximized"
            ],
            "page_load_timeout": 30,
            "implicit_wait": 10
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
            "login_url": "http://10.0.0.7:8080/venus/",
            "task_register_url": "http://10.0.0.7:8080/venus/task_register.jsp"
        }
    }

# Initialize database manager first
database_manager = DatabaseManager()

# Initialize data manager, automation service, and exclusion validator
staging_manager = StagingDataManager(database_manager)
automation_service = get_automation_service(load_default_config())
exclusion_validator = EmployeeExclusionValidator()
is_browser_ready = False
automation_mode = 'testing'
current_progress = {
    'current_employee': '',
    'current_date': '',
    'processed_entries': 0,
    'total_entries': 0,
    'successful_entries': 0,
    'failed_entries': 0,
    'status': 'idle'
}
processed_data = []

# Helper functions for enhanced functionality
async def fetch_grouped_staging_data():
    """Fetch grouped staging data from database"""
    try:
        logger.info("🗄️ Fetching grouped staging data from database...")
        
        grouped_data = database_manager.fetch_grouped_staging_data()
        
        if grouped_data:
            total_employees = len(grouped_data)
            total_records = sum(len(emp.get('data_presensi', [])) for emp in grouped_data)
            
            logger.info(f"📊 Grouped data received: {total_employees} employees, {total_records} attendance records")
            
            return grouped_data
        else:
            logger.error("❌ No data found in database")
            return []
            
    except Exception as e:
        logger.error(f"❌ Error fetching grouped staging data: {e}")
        return []

def filter_excluded_employees_grouped(grouped_data):
    """Filter out excluded employees from grouped staging data"""
    try:
        logger.info(f"🔍 Starting filtering process for {len(grouped_data)} employee groups")
        
        if not exclusion_validator.is_enabled():
            logger.info("🔓 Exclusion filtering disabled - returning all data")
            return grouped_data
        
        filtered_data = []
        excluded_employees = []
        
        for i, employee_group in enumerate(grouped_data):
            # Use the correct structure from DatabaseManager
            employee_name = employee_group.get('employee_name', '')
            
            logger.info(f"🔍 Processing group {i+1}: employee_name='{employee_name}'")
            
            if not employee_name:
                # Keep groups without employee name
                logger.info(f"⚠️ Group {i+1}: No employee name found, keeping group")
                filtered_data.append(employee_group)
                continue
            
            # Check if employee is in exclusion list
            is_excluded = is_employee_excluded(employee_name)
            
            if is_excluded:
                excluded_employees.append(employee_name)
                logger.info(f"🚫 FILTERED OUT: {employee_name}")
            else:
                filtered_data.append(employee_group)
                logger.info(f"✅ ALLOWED: {employee_name}")
        
        logger.info(f"📊 Filtering complete: {len(excluded_employees)} excluded, {len(filtered_data)} allowed")
        
        if excluded_employees:
            logger.info(f"🚫 EXCLUDED EMPLOYEES: {excluded_employees}")
        
        return filtered_data
        
    except Exception as e:
        logger.error(f"❌ Error filtering excluded employees: {e}")
        return grouped_data

def is_employee_excluded(employee_name):
    """Check if employee name matches any exclusion list entry"""
    try:
        if not employee_name:
            logger.info(f"🔍 is_employee_excluded: Empty employee name, returning False")
            return False
        
        excluded_list = exclusion_validator.get_excluded_employees_list()
        settings = exclusion_validator.config.get('exclusion_settings', {})
        
        logger.info(f"🔍 is_employee_excluded: Checking '{employee_name}' against {len(excluded_list)} excluded names")
        logger.info(f"🔍 Settings: case_sensitive={settings.get('case_sensitive', False)}, partial_match={settings.get('partial_match', True)}")
        
        # Normalize employee name
        normalized_name = employee_name.strip()
        if not settings.get('case_sensitive', False):
            normalized_name = normalized_name.lower()
        
        logger.info(f"🔍 Normalized name: '{normalized_name}'")
        
        # Check against normalized exclusion list
        for excluded_name in excluded_list:
            normalized_excluded = excluded_name.strip()
            if not settings.get('case_sensitive', False):
                normalized_excluded = normalized_excluded.lower()
            
            # Exact match (primary check)
            if normalized_name == normalized_excluded:
                logger.info(f"🚫 EXACT MATCH: '{normalized_name}' == '{normalized_excluded}'")
                return True
            
            # Partial match with word overlap
            if settings.get('partial_match', True):
                name_words = set(normalized_name.split())
                excluded_words = set(normalized_excluded.split())
                
                if name_words and excluded_words:
                    overlap = len(name_words.intersection(excluded_words))
                    total_words = len(name_words.union(excluded_words))
                    similarity = overlap / total_words if total_words > 0 else 0
                    
                    if similarity >= 0.7:
                        logger.info(f"🚫 PARTIAL MATCH: '{normalized_name}' vs '{normalized_excluded}' (similarity: {similarity:.2f})")
                        return True
        
        logger.info(f"✅ NO MATCH: '{employee_name}' is not excluded")
        return False
        
    except Exception as e:
        logger.error(f"❌ Error checking employee exclusion: {e}")
        return False

def flatten_grouped_data_for_selection(grouped_data):
    """Flatten grouped data for selection interface"""
    try:
        logger.info(f"🔍 Starting flattening process for {len(grouped_data)} employee groups")
        flattened_data = []
        
        for i, employee_group in enumerate(grouped_data):
            # Use the correct structure from DatabaseManager
            employee_name = employee_group.get('employee_name', 'Unknown')
            employee_id = employee_group.get('employee_id', '')
            ptrj_employee_id = employee_group.get('ptrj_employee_id', '')
            
            logger.info(f"🔍 Group {i+1}: employee_name='{employee_name}', employee_id='{employee_id}', ptrj_employee_id='{ptrj_employee_id}'")
            
            data_presensi = employee_group.get('data_presensi', [])
            logger.info(f"🔍 Group {i+1}: Found {len(data_presensi)} attendance records")
            
            if not data_presensi:
                logger.info(f"⚠️ Group {i+1}: No attendance data found, skipping")
                continue
            
            for j, entry in enumerate(data_presensi):
                logger.info(f"🔍 Group {i+1}, Entry {j+1}: {entry}")
                flattened_entry = {
                    'employee_name': employee_name,
                    'employee_id': employee_id,
                    'ptrj_employee_id': ptrj_employee_id,
                    'date': entry.get('date', ''),
                    'regular_hours': entry.get('regular_hours', 0),
                    'overtime_hours': entry.get('overtime_hours', 0),
                    'total_hours': entry.get('total_hours', 0),
                    'task_code': entry.get('task_code', ''),
                    'station_code': entry.get('station_code', ''),
                    'raw_charge_job': entry.get('raw_charge_job', ''),
                    'status': entry.get('status', 'staged'),
                    'is_overtime': entry.get('is_overtime', False),
                    'hours': entry.get('hours', 0),
                    'original_data': entry  # Keep original for processing
                }
                flattened_data.append(flattened_entry)
                logger.info(f"✅ Group {i+1}, Entry {j+1}: Added flattened entry")
        
        logger.info(f"📋 Flattened {len(flattened_data)} records from {len(grouped_data)} employee groups")
        return flattened_data
        
    except Exception as e:
        logger.error(f"❌ Error flattening grouped data: {e}")
        return []

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/staging-data')
def get_staging_data():
    """API endpoint to get staging data with filters"""
    try:
        # Get filter parameters
        filters = {
            'employee_name': request.args.get('employee_name'),
            'date_from': request.args.get('date_from'),
            'date_to': request.args.get('date_to'),
            'status': request.args.get('status', 'staged'),
            'limit': request.args.get('limit', 50, type=int),
            'offset': request.args.get('offset', 0, type=int)
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        # Fetch data
        data = staging_manager.fetch_staging_data(filters)
        
        return jsonify(data)
        
    except Exception as e:
        logger.error(f"Error in get_staging_data: {e}")
        return jsonify({
            'error': str(e),
            'data': [],
            'total': 0
        }), 500

@app.route('/api/staging-data-grouped')
def get_staging_data_grouped():
    """Get staging data grouped by employee for enhanced interface"""
    try:
        # Fetch grouped data and flatten for interface
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Use the correct function that maintains grouped structure
            grouped_data = loop.run_until_complete(fetch_grouped_staging_data())
            logger.info(f"📊 Fetched {len(grouped_data)} employee groups from database")
            
            # Apply exclusion filtering
            filtered_grouped_data = filter_excluded_employees_grouped(grouped_data)
            
            # Flatten for interface
            flattened_data = flatten_grouped_data_for_selection(filtered_grouped_data)
            logger.info(f"✅ API response: {len(flattened_data)} flattened records")
            
            return jsonify({
                'success': True,
                'data': flattened_data,
                'total': len(flattened_data)
            })
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error getting grouped staging data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/browser-status')
def get_browser_status():
    """Get current browser status for desktop app"""
    global is_browser_ready
    try:
        return jsonify({
            'is_ready': is_browser_ready,
            'status': 'ready' if is_browser_ready else 'not_ready',
            'mode': automation_mode
        })
    except Exception as e:
        logger.error(f"Error getting browser status: {e}")
        return jsonify({
            'is_ready': False,
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/process-data', methods=['POST'])
def process_data():
    """Process selected data with web driver"""
    global current_progress, processed_data, is_browser_ready
    
    try:
        data = request.get_json()
        selected_data = data.get('selected_data', [])
        
        if not selected_data:
            return jsonify({'error': 'No data selected for processing'}), 400
        
        if not is_browser_ready:
            return jsonify({'error': 'Browser not initialized. Please initialize browser first.'}), 400
        
        # Reset progress
        current_progress = {
            'current_employee': '',
            'current_date': '',
            'processed_entries': 0,
            'total_entries': len(selected_data),
            'successful_entries': 0,
            'failed_entries': 0,
            'status': 'processing'
        }
        
        processed_data = []
        
        # Start processing in background thread
        def process_in_background():
            global current_progress, processed_data
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Process the data
                loop.run_until_complete(processor.process_selected_data_with_progress(
                    selected_data, current_progress, processed_data
                ))
                
                current_progress['status'] = 'completed'
                logger.info(f"✅ Processing completed: {current_progress['successful_entries']} successful, {current_progress['failed_entries']} failed")
                
            except Exception as e:
                logger.error(f"❌ Error in background processing: {e}")
                current_progress['status'] = 'error'
                current_progress['error'] = str(e)
            finally:
                loop.close()
        
        # Start background thread
        thread = threading.Thread(target=process_in_background)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': f'Started processing {len(selected_data)} entries',
            'total_entries': len(selected_data)
        })
        
    except Exception as e:
        logger.error(f"❌ Error starting data processing: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/processing-progress')
def get_processing_progress():
    """Get current processing progress"""
    global current_progress
    return jsonify(current_progress)

@app.route('/api/processed-data')
def get_processed_data():
    """Get processed data results"""
    global processed_data
    return jsonify({
        'success': True,
        'data': processed_data,
        'total': len(processed_data)
    })

@app.route('/api/stop-processing', methods=['POST'])
def stop_processing():
    """Stop current processing"""
    global current_progress
    try:
        current_progress['status'] = 'stopped'
        logger.info("🛑 Processing stopped by user")
        
        return jsonify({
            'success': True,
            'message': 'Processing stopped'
        })
        
    except Exception as e:
        logger.error(f"❌ Error stopping processing: {e}")
        return jsonify({'error': str(e)}), 500

# Background processing function
def process_selected_data_background(selected_data):
    """Process selected data in background using web driver"""
    global current_progress, processed_data, automation_mode
    
    try:
        logger.info(f"🚀 Starting background processing for {len(selected_data)} records")
        automation_mode = True
        current_progress = {
            'total': len(selected_data),
            'processed': 0,
            'success': 0,
            'failed': 0,
            'current_employee': '',
            'status': 'processing'
        }
        
        # Initialize browser if not ready
        if not browser_ready:
            logger.info("🌐 Initializing browser for automation...")
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(api_processor.initialize_browser_system())
                globals()['browser_ready'] = True
                logger.info("✅ Browser initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize browser: {e}")
                current_progress['status'] = 'error'
                current_progress['error'] = f"Browser initialization failed: {str(e)}"
                automation_mode = False
                return
        
        # Group data by employee for processing
        employee_groups = {}
        for record in selected_data:
            employee_name = record.get('employee_name', 'Unknown')
            if employee_name not in employee_groups:
                employee_groups[employee_name] = {
                    'identitas_karyawan': {
                        'employee_name': employee_name,
                        'ptrj_employee_id': record.get('ptrj_employee_id', ''),
                        'employee_id': record.get('employee_id', '')
                    },
                    'data_presensi': []
                }
            employee_groups[employee_name]['data_presensi'].append(record.get('original_data', record))
        
        # Process each employee group
        for employee_name, employee_data in employee_groups.items():
            if not automation_mode:  # Check if stopped
                break
                
            current_progress['current_employee'] = employee_name
            logger.info(f"👤 Processing employee: {employee_name}")
            
            try:
                # Process employee data using the automation system
                # This would integrate with the actual automation logic
                result = {
                    'employee_name': employee_name,
                    'records_processed': len(employee_data['data_presensi']),
                    'status': 'success',
                    'timestamp': datetime.now().isoformat()
                }
                
                processed_data.append(result)
                current_progress['processed'] += len(employee_data['data_presensi'])
                current_progress['success'] += len(employee_data['data_presensi'])
                
                logger.info(f"✅ Successfully processed {employee_name}")
                
            except Exception as e:
                logger.error(f"❌ Error processing {employee_name}: {e}")
                result = {
                    'employee_name': employee_name,
                    'records_processed': 0,
                    'status': 'failed',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                processed_data.append(result)
                current_progress['failed'] += len(employee_data['data_presensi'])
                current_progress['processed'] += len(employee_data['data_presensi'])
        
        # Update final status
        if automation_mode:
            current_progress['status'] = 'completed'
            logger.info(f"🎉 Processing completed: {current_progress['success']} success, {current_progress['failed']} failed")
        else:
            current_progress['status'] = 'stopped'
            logger.info("⏹️ Processing stopped by user")
        
        automation_mode = False
        
    except Exception as e:
        logger.error(f"❌ Error in background processing: {e}")
        current_progress['status'] = 'error'
        current_progress['error'] = str(e)
        automation_mode = False

@app.route('/api/validate-exclusions', methods=['POST'])
def validate_exclusions():
    """Validate selected records against exclusion list"""
    try:
        data = request.get_json()
        selected_indices = data.get('selected_indices', [])
        
        if not selected_indices:
            return jsonify({'error': 'No records selected for validation'}), 400
        
        # Fetch current staging data
        staging_data = staging_manager.fetch_staging_data()
        records = staging_data.get('data', [])
        
        if not records:
            return jsonify({'error': 'No staging data available'}), 400
        
        # Validate against exclusion list
        validation_result = exclusion_validator.validate_records(records, selected_indices)
        
        # Get confirmation dialog data
        dialog_data = exclusion_validator.get_confirmation_dialog_data(validation_result)
        
        logger.info(f"🔍 Exclusion validation completed: {len(validation_result.excluded_matches)} exclusions found")
        
        return jsonify({
            'success': True,
            'validation_result': {
                'has_exclusions': validation_result.has_exclusions,
                'excluded_count': len(validation_result.excluded_matches),
                'clean_count': len(validation_result.clean_records),
                'total_count': validation_result.total_records,
                'summary': validation_result.summary,
                'clean_indices': validation_result.clean_indices,
                'excluded_indices': validation_result.excluded_indices
            },
            'dialog_data': dialog_data
        })
        
    except Exception as e:
        logger.error(f"❌ Error validating exclusions: {e}")
        return jsonify({'error': f'Validation failed: {str(e)}'}), 500

@app.route('/api/process-selected', methods=['POST'])
def process_selected_records():
    """API endpoint to trigger automation for selected records with exclusion validation"""
    try:
        data = request.get_json()
        selected_ids = data.get('selected_ids', [])
        selected_indices = data.get('selected_indices', [])
        bypass_exclusion = data.get('bypass_exclusion', False)

        if not selected_ids:
            return jsonify({'error': 'No records selected'}), 400

        # Perform exclusion validation if not bypassed
        if not bypass_exclusion and exclusion_validator.is_enabled():
            # Fetch current staging data for validation
            staging_data = staging_manager.fetch_staging_data()
            records = staging_data.get('data', [])
            
            if records and selected_indices:
                validation_result = exclusion_validator.validate_records(records, selected_indices)
                
                if validation_result.has_exclusions:
                    # Return exclusion validation results for user confirmation
                    dialog_data = exclusion_validator.get_confirmation_dialog_data(validation_result)
                    
                    return jsonify({
                        'success': False,
                        'requires_confirmation': True,
                        'validation_result': {
                            'has_exclusions': validation_result.has_exclusions,
                            'excluded_count': len(validation_result.excluded_matches),
                            'clean_count': len(validation_result.clean_records),
                            'total_count': validation_result.total_records,
                            'summary': validation_result.summary,
                            'clean_indices': validation_result.clean_indices,
                            'excluded_indices': validation_result.excluded_indices
                        },
                        'dialog_data': dialog_data,
                        'message': 'Excluded employees detected in selection. Please confirm to proceed with cleaned dataset.'
                    })

        logger.info(f"Processing {len(selected_ids)} selected records")

        # Check if automation is already running
        if automation_service.is_automation_running():
            return jsonify({'error': 'Automation is already running'}), 409

        # Start automation job
        job_id = automation_service.start_automation_job(selected_ids)

        result = {
            'success': True,
            'message': f'Started automation for {len(selected_ids)} records',
            'selected_count': len(selected_ids),
            'automation_id': job_id
        }

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error processing selected records: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/employees')
def get_employees():
    """Get unique employee names for filter dropdown"""
    try:
        # Get data directly from database
        grouped_data = database_manager.fetch_grouped_staging_data()
        
        # Extract unique employee names
        employees = set()
        for employee_group in grouped_data:
            if employee_group.get('employee_name'):
                employees.add(employee_group['employee_name'])
        
        return jsonify(sorted(list(employees)))
        
    except Exception as e:
        logger.error(f"Error getting employees: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/job-status/<job_id>')
def get_job_status(job_id):
    """Get status of a specific automation job"""
    try:
        status = automation_service.get_job_status(job_id)

        if not status:
            return jsonify({'error': 'Job not found'}), 404

        return jsonify(status)

    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/jobs')
def get_all_jobs():
    """Get status of all automation jobs"""
    try:
        jobs = automation_service.get_all_jobs()
        return jsonify(jobs)

    except Exception as e:
        logger.error(f"Error getting jobs: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/current-job')
def get_current_job():
    """Get status of currently running job"""
    try:
        current_job = automation_service.get_current_job_status()

        if not current_job:
            return jsonify({'message': 'No job currently running'}), 200

        return jsonify(current_job)

    except Exception as e:
        logger.error(f"Error getting current job: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cancel-job/<job_id>', methods=['POST'])
def cancel_job(job_id):
    """Cancel a running automation job"""
    try:
        success = automation_service.cancel_job(job_id)

        if success:
            return jsonify({'message': f'Job {job_id} cancelled successfully'})
        else:
            return jsonify({'error': 'Job not found or cannot be cancelled'}), 400

    except Exception as e:
        logger.error(f"Error cancelling job: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/automation-status')
def get_automation_status():
    """Get current automation status for desktop app"""
    try:
        # Check if automation is currently running
        is_running = automation_service.is_automation_running()
        current_job = automation_service.get_current_job_status()
        engine_status = automation_service.get_engine_status()
        
        return jsonify({
            'success': True,
            'is_running': is_running,
            'current_job': current_job,
            'engine_status': engine_status,
            'browser_ready': is_browser_ready
        })
    except Exception as e:
        logger.error(f"Error getting automation status: {e}")
        return jsonify({
            'success': False,
            'message': str(e),
            'is_running': False,
            'current_job': None,
            'engine_status': {'initialized': False, 'ready': False},
            'browser_ready': False
        }), 500

@app.route('/api/stop-automation', methods=['POST'])
def stop_automation():
    """Stop current automation process for desktop app"""
    try:
        # Get current job and cancel it
        current_job = automation_service.get_current_job_status()
        if current_job and current_job.get('job_id'):
            success = automation_service.cancel_job(current_job['job_id'])
            if success:
                logger.info(f"✅ Automation stopped successfully: {current_job['job_id']}")
                return jsonify({
                    'success': True,
                    'message': 'Automation stopped successfully',
                    'stopped_job_id': current_job['job_id']
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to stop automation'
                }), 500
        else:
            return jsonify({
                'success': True,
                'message': 'No automation currently running'
            })
    except Exception as e:
        logger.error(f"Error stopping automation: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/crosscheck-results')
def get_crosscheck_results():
    """Get crosscheck results for desktop app"""
    try:
        # Get processed data from automation service
        global processed_data
        
        # Format crosscheck results
        crosscheck_results = []
        for item in processed_data:
            crosscheck_results.append({
                'id': item.get('id', ''),
                'employee_name': item.get('employee_name', ''),
                'date': item.get('date', ''),
                'status': item.get('status', 'unknown'),
                'message': item.get('message', ''),
                'processed_at': item.get('processed_at', ''),
                'success': item.get('success', False)
            })
        
        return jsonify({
            'success': True,
            'results': crosscheck_results,
            'total_processed': len(crosscheck_results),
            'successful': len([r for r in crosscheck_results if r['success']]),
            'failed': len([r for r in crosscheck_results if not r['success']])
        })
    except Exception as e:
        logger.error(f"Error getting crosscheck results: {e}")
        return jsonify({
            'success': False,
            'message': str(e),
            'results': [],
            'total_processed': 0,
            'successful': 0,
            'failed': 0
        }), 500

@app.route('/api/initialize-browser', methods=['POST'])
def initialize_browser():
    """Initialize browser and perform login for desktop app"""
    global is_browser_ready
    try:
        logger.info("🚀 Browser initialization requested from desktop app")
        
        # Call the synchronous initialize_browser method directly
        result = automation_service.initialize_browser()
        
        # Update global browser ready status
        if result.get('success', False):
            is_browser_ready = True
            logger.info("✅ Browser ready status updated to True")
        else:
            is_browser_ready = False
            logger.warning("⚠️ Browser initialization failed, status remains False")
        
        return jsonify(result)
            
    except Exception as e:
        logger.error(f"❌ Error in browser initialization endpoint: {e}")
        is_browser_ready = False
        return jsonify({
            'success': False,
            'message': f'Browser initialization failed: {str(e)}',
            'status': 'error'
        }), 500

@app.route('/health')
def health_check():
    """Health check endpoint for desktop app"""
    try:
        # Basic health check - verify staging manager is working
        staging_manager.fetch_staging_data({'limit': 1})
        return jsonify({
            'status': 'healthy',
            'message': 'Flask server is running',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

if __name__ == '__main__':
    logger.info("Starting Data Interface Web Application")
    logger.info("Using direct database access to staging_attendance.db")
    
    # Run the Flask app with improved connection handling
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True,
        use_reloader=False,  # Disable reloader to avoid issues with threading
        request_handler=None,  # Use default request handler
        processes=1  # Single process to avoid conflicts
    )
