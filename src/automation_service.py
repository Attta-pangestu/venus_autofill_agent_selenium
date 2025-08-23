"""
Automation Service - Enhanced service with persistent browser sessions
"""

import asyncio
import json
import logging
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

from core.enhanced_staging_automation import EnhancedStagingAutomationEngine, AutomationResult

@dataclass
class AutomationJob:
    """Represents an automation job"""
    job_id: str
    selected_records: List[str]
    status: str  # 'pending', 'running', 'completed', 'failed'
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    results: List[AutomationResult] = None
    error_message: Optional[str] = None

class AutomationService:
    """Enhanced service with persistent browser sessions and pre-initialization"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Job management
        self.jobs: Dict[str, AutomationJob] = {}
        self.current_job: Optional[AutomationJob] = None
        
        # Enhanced automation engine with persistence
        self.automation_engine: Optional[EnhancedStagingAutomationEngine] = None
        self.is_engine_initialized = False
        
        # Threading
        self.automation_thread: Optional[threading.Thread] = None
        self.initialization_lock = threading.Lock()
        
        # Setup logging
        self.setup_logging()
        
        # Start pre-initialization in background
        self._start_pre_initialization()
    
    def setup_logging(self):
        """Setup logging for the automation service"""
        log_file = Path("automation_service.log")
        
        # Create file handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        self.logger.addHandler(file_handler)
        self.logger.setLevel(logging.INFO)
    
    def _start_pre_initialization(self):
        """Start pre-initialization of automation engine in background"""
        def init_worker():
            try:
                self.logger.info("🚀 Starting pre-initialization of automation engine...")
                
                # Run initialization in async context
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Create and initialize the enhanced automation engine
                self.automation_engine = EnhancedStagingAutomationEngine(self.config)
                
                # Initialize (this will pre-login and set up persistent session)
                success = loop.run_until_complete(self.automation_engine.initialize())
                
                if success:
                    # Additional step: Ensure we're positioned at task register and ready
                    print("🎯 Positioning WebDriver at task register page...")
                    await_success = loop.run_until_complete(self._ensure_ready_state())

                    if await_success:
                        with self.initialization_lock:
                            self.is_engine_initialized = True
                        self.logger.info("✅ Automation engine pre-initialized successfully")
                        print("\n" + "="*60)
                        print("✅ AUTOMATION ENGINE READY")
                        print("🌐 WebDriver is positioned at task register page")
                        print("⏳ Waiting for user to select records via web interface")
                        print("🎯 Ready to process user-selected records")
                        print("📱 Open http://localhost:5000 to select records")
                        print("="*60)
                    else:
                        self.logger.error("❌ Failed to reach ready state")
                        print("❌ FAILED TO REACH READY STATE")
                else:
                    self.logger.error("❌ Failed to pre-initialize automation engine")
                    print("❌ AUTOMATION ENGINE INITIALIZATION FAILED")
                
            except Exception as e:
                self.logger.error(f"❌ Pre-initialization failed: {e}")
            finally:
                loop.close()
        
        # Start initialization thread
        init_thread = threading.Thread(target=init_worker, daemon=True)
        init_thread.start()

    async def _ensure_ready_state(self):
        """Ensure the automation engine is in ready state at task register page"""
        try:
            # Get the driver from the automation engine
            driver = self.automation_engine.browser_manager.get_driver()
            if not driver:
                self.logger.error("No WebDriver available")
                return False

            # Check current URL
            current_url = driver.current_url
            self.logger.info(f"Current URL: {current_url}")

            # Ensure we're at the task register page
            if "frmPrTrxTaskRegisterDet.aspx" not in current_url:
                self.logger.info("Navigating to task register page...")
                await self.automation_engine.browser_manager.navigate_to_task_register()

                # Verify navigation
                final_url = driver.current_url
                if "frmPrTrxTaskRegisterDet.aspx" not in final_url:
                    self.logger.error(f"Failed to reach task register page: {final_url}")
                    return False

            # Perform enhanced form detection to ensure readiness
            self.logger.info("Verifying form readiness...")
            form_ready = await self.automation_engine._wait_for_form_ready_enhanced()

            if form_ready:
                self.logger.info("✅ Automation engine is in ready state")
                return True
            else:
                self.logger.error("❌ Form not ready")
                return False

        except Exception as e:
            self.logger.error(f"Error ensuring ready state: {e}")
            return False

    def start_automation_job(self, selected_record_ids: List[str]) -> str:
        """Start a new automation job using pre-initialized engine"""
        try:
            # Immediate console feedback when user clicks process
            print("\n" + "🚀" + "="*60)
            print("🤖 STARTING AUTOMATION PROCESS")
            print("="*62)
            print(f"📊 Selected Records: {len(selected_record_ids)}")
            print(f"🆔 Record IDs: {', '.join(selected_record_ids)}")
            print("="*62)
            
            # Show staging data preview immediately (even if engine not ready)
            try:
                print("\n📋 STAGING DATA PREVIEW:")
                preview_records = self._create_preview_records(selected_record_ids)
                for i, record in enumerate(preview_records, 1):
                    print(f"   {i}. {record.get('employee_name', 'Unknown')} - {record.get('date', 'N/A')}")
                    print(f"      Task: {record.get('task_code', 'N/A')} | Raw Job: {record.get('raw_charge_job', 'N/A')[:50]}...")
                print("="*62)
            except Exception as e:
                print(f"⚠️ Could not load staging data preview: {e}")
                print("="*62)
            
            # Check if engine is ready
            if not self.is_engine_initialized:
                print("⚠️ Automation engine still initializing - waiting for completion...")
                self.logger.warning("⚠️ Automation engine not yet ready, will wait for initialization...")
                
                # Increased timeout for location page handling
                max_wait_time = 60  # increased from 30 to 60 seconds
                wait_start = time.time()
                
                while not self.is_engine_initialized and (time.time() - wait_start) < max_wait_time:
                    elapsed = int(time.time() - wait_start)
                    print(f"⏳ Waiting for engine initialization... ({elapsed}s)")
                    time.sleep(2)
                
                if not self.is_engine_initialized:
                    print("❌ AUTOMATION ENGINE INITIALIZATION TIMEOUT")
                    print("   This usually means the browser couldn't navigate past the login/location page")
                    print("   Please check the browser window and logs for more details")
                    raise Exception("Automation engine initialization timeout")
                else:
                    print("✅ Automation engine is now ready!")
            
            # Generate job ID
            job_id = f"auto_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Create job
            job = AutomationJob(
                job_id=job_id,
                selected_records=selected_record_ids,
                status='pending',
                created_at=datetime.now().isoformat(),
                results=[]
            )
            
            # Store job
            self.jobs[job_id] = job
            
            # Start automation in background thread (using pre-initialized engine)
            self.automation_thread = threading.Thread(
                target=self._run_automation_job_fast,
                args=(job_id,),
                daemon=True
            )
            self.automation_thread.start()
            
            self.logger.info(f"🚀 Started automation job {job_id} for {len(selected_record_ids)} records (using pre-initialized engine)")
            return job_id
            
        except Exception as e:
            self.logger.error(f"Failed to start automation job: {e}")
            raise
    
    def _run_automation_job_fast(self, job_id: str):
        """Run automation job using pre-initialized engine for fast execution"""
        try:
            job = self.jobs.get(job_id)
            if not job:
                self.logger.error(f"Job {job_id} not found")
                return
            
            # Update job status
            job.status = 'running'
            job.started_at = datetime.now().isoformat()
            self.current_job = job
            
            self.logger.info(f"🏃 Starting fast automation job {job_id}")
            
            # Run the automation using the pre-initialized engine
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                loop.run_until_complete(self._execute_automation_job_fast(job))
            finally:
                loop.close()
            
        except Exception as e:
            self.logger.error(f"Error in automation job {job_id}: {e}")
            if job_id in self.jobs:
                self.jobs[job_id].status = 'failed'
                self.jobs[job_id].error_message = str(e)
                self.jobs[job_id].completed_at = datetime.now().isoformat()
        finally:
            self.current_job = None
    
    async def _execute_automation_job_fast(self, job: AutomationJob):
        """Execute automation job using pre-initialized engine"""
        try:
            # Fetch staging records for the selected IDs
            staging_records = await self._fetch_staging_records(job.selected_records)
            
            if not staging_records:
                raise Exception("No staging records found for selected IDs")
            
            # Enhanced debug logging for staging data
            self._log_staging_data_details(staging_records, job.job_id)
            
            self.logger.info(f"⚡ Processing {len(staging_records)} staging records with pre-initialized engine")
            
            # Process the records using the pre-initialized engine
            # No need to initialize here - engine is already ready!
            results = await self.automation_engine.process_staging_records(staging_records)
            
            # Update job with results
            job.results = results
            job.status = 'completed'
            job.completed_at = datetime.now().isoformat()
            
            # Log summary
            successful = sum(1 for r in results if r.success)
            failed = len(results) - successful
            
            self.logger.info(f"✅ Job {job.job_id} completed: {successful} successful, {failed} failed")
            
        except Exception as e:
            self.logger.error(f"❌ Automation job {job.job_id} failed: {e}")
            job.status = 'failed'
            job.error_message = str(e)
            job.completed_at = datetime.now().isoformat()
            raise
    
    def _log_staging_data_details(self, staging_records: List[Dict[str, Any]], job_id: str):
        """Log comprehensive details about staging data records before automation"""
        try:
            print("\n" + "="*80)
            print(f"🔍 DETAILED STAGING DATA ANALYSIS - Job {job_id}")
            print("="*80)
            
            for i, record in enumerate(staging_records, 1):
                print(f"\n📋 RECORD {i}/{len(staging_records)}")
                print("-" * 50)
                print(f"🆔 Record ID: {record.get('id', 'N/A')}")
                print(f"👤 Employee ID: {record.get('employee_id', 'N/A')}")
                print(f"👨‍💼 Employee Name: {record.get('employee_name', 'N/A')}")
                print(f"📅 Date: {record.get('date', 'N/A')}")
                print(f"📊 Status: {record.get('status', 'N/A')}")
                print(f"⏰ Hours: {record.get('hours', 'N/A')}")
                print(f"🔢 Unit: {record.get('unit', 'N/A')}")
                print(f"🏢 Task Code: {record.get('task_code', 'N/A')}")
                print(f"📍 Station Code: {record.get('station_code', 'N/A')}")
                
                # Raw charge job
                raw_charge_job = record.get('raw_charge_job', '')
                print(f"🏗️ Raw Charge Job: {raw_charge_job}")
                
                # Parse charge job components
                if raw_charge_job:
                    parsed_components = self._parse_charge_job_debug(raw_charge_job)
                    print("🔧 Parsed Charge Job Components:")
                    for component_name, component_value in parsed_components.items():
                        print(f"   • {component_name}: {component_value}")
                else:
                    print("⚠️ No charge job data to parse")
                    
                print("-" * 50)
            
            print(f"\n📊 SUMMARY:")
            print(f"   • Total Records: {len(staging_records)}")
            print(f"   • Unique Employees: {len(set(r.get('employee_name', '') for r in staging_records))}")
            print(f"   • Date Range: {self._get_date_range(staging_records)}")
            print(f"   • Total Hours: {sum(r.get('hours', 0) for r in staging_records)}")
            print("="*80 + "\n")
            
            # Also log to file
            self.logger.info(f"📋 Staging Data Summary for Job {job_id}:")
            for i, record in enumerate(staging_records, 1):
                self.logger.info(f"Record {i}: {record.get('employee_name', 'N/A')} - {record.get('date', 'N/A')} - {record.get('raw_charge_job', 'N/A')[:50]}...")
                
        except Exception as e:
            self.logger.error(f"Error logging staging data details: {e}")
            print(f"⚠️ Error displaying staging data details: {e}")
    
    def _parse_charge_job_debug(self, raw_charge_job: str) -> Dict[str, str]:
        """Parse charge job for debug display"""
        try:
            components = {
                "Task Code": "Not found",
                "Location": "Not found", 
                "Sub Location": "Not found",
                "Type": "Not found"
            }
            
            # Split by " / " to get the main parts
            parts = raw_charge_job.split(" / ")
            
            if len(parts) >= 4:
                # Extract task code from first part (remove parentheses)
                task_part = parts[0].strip()
                if task_part.startswith("(") and ")" in task_part:
                    components["Task Code"] = task_part.split(")", 1)[0][1:]
                else:
                    components["Task Code"] = task_part
                
                # Extract other parts
                components["Location"] = parts[1].strip()
                components["Sub Location"] = parts[2].split("(")[0].strip()
                components["Type"] = parts[3].split("(")[0].strip()
            else:
                components["Raw Format"] = raw_charge_job
                components["Parse Status"] = f"Could not parse - only {len(parts)} parts found"
            
            return components
            
        except Exception as e:
            return {
                "Parse Error": str(e),
                "Raw Data": raw_charge_job[:100] + "..." if len(raw_charge_job) > 100 else raw_charge_job
            }
    
    def _get_date_range(self, staging_records: List[Dict[str, Any]]) -> str:
        """Get date range from staging records"""
        try:
            dates = [r.get('date', '') for r in staging_records if r.get('date')]
            if not dates:
                return "No dates found"
            
            unique_dates = sorted(set(dates))
            if len(unique_dates) == 1:
                return unique_dates[0]
            else:
                return f"{unique_dates[0]} to {unique_dates[-1]}"
                
        except Exception:
            return "Error calculating date range"
    
    async def _fetch_staging_records(self, record_ids: List[str]) -> List[Dict[str, Any]]:
        """Fetch staging records from API or create mock data"""
        try:
            # Create mock data based on the record IDs
            mock_records = []
            for record_id in record_ids:
                # Parse record ID to extract employee info
                parts = record_id.split('_')
                if len(parts) >= 2:
                    employee_id = parts[0]
                    date = parts[1] if len(parts) > 1 else '2025-06-10'
                else:
                    employee_id = record_id
                    date = '2025-06-10'
                
                # Create mock record
                mock_record = {
                    'id': record_id,
                    'employee_id': employee_id,
                    'employee_name': self._get_employee_name(employee_id),
                    'date': date,
                    'task_code': 'OC7190',
                    'station_code': 'STN-BLR',
                    'raw_charge_job': '(OC7190) BOILER OPERATION / STN-BLR (STATION BOILER) / BLR00000 (LABOUR COST) / L (LABOUR)',
                    'status': 'staged',
                    'hours': 7.0,
                    'unit': 1.0
                }
                
                mock_records.append(mock_record)
            
            self.logger.info(f"Created {len(mock_records)} mock staging records")
            return mock_records
            
        except Exception as e:
            self.logger.error(f"Failed to fetch staging records: {e}")
            return []
    
    def _create_preview_records(self, record_ids: List[str]) -> List[Dict[str, Any]]:
        """Create preview records synchronously for immediate display"""
        try:
            preview_records = []
            for record_id in record_ids:
                # Parse record ID to extract employee info
                parts = record_id.split('_')
                if len(parts) >= 2:
                    employee_id = parts[0]
                    date = parts[1] if len(parts) > 1 else '2025-06-11'
                else:
                    employee_id = record_id
                    date = '2025-06-11'
                
                # Create preview record
                preview_record = {
                    'id': record_id,
                    'employee_id': employee_id,
                    'employee_name': self._get_employee_name(employee_id),
                    'date': date,
                    'task_code': 'OC7190',
                    'station_code': 'STN-BLR',
                    'raw_charge_job': '(OC7190) BOILER OPERATION / STN-BLR (STATION BOILER) / BLR00000 (LABOUR COST) / L (LABOUR)',
                    'status': 'staged',
                    'hours': 7.0,
                    'unit': 1.0
                }
                
                preview_records.append(preview_record)
            
            return preview_records
            
        except Exception as e:
            self.logger.error(f"Failed to create preview records: {e}")
            return []
    
    def _get_employee_name(self, employee_id: str) -> str:
        """Get employee name from ID (mock implementation)"""
        # Mock employee names
        employee_names = {
            'c1e595b4-d498-4320-bce3-8d0f0cf52060': 'Employee Test User',
            'emp001': 'John Doe',
            'emp002': 'Jane Smith',
            'emp003': 'Bob Johnson'
        }
        return employee_names.get(employee_id, f'Employee {employee_id}')
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific job"""
        try:
            job = self.jobs.get(job_id)
            if not job:
                return None
            
            # Convert results to serializable format
            serializable_results = []
            if job.results:
                for result in job.results:
                    serializable_results.append({
                        'success': result.success,
                        'record_id': result.record_id,
                        'message': result.message,
                        'error_details': result.error_details,
                        'processing_time': result.processing_time
                    })
            
            return {
                'job_id': job.job_id,
                'status': job.status,
                'selected_records': job.selected_records,
                'created_at': job.created_at,
                'started_at': job.started_at,
                'completed_at': job.completed_at,
                'results': serializable_results,
                'error_message': job.error_message,
                'total_records': len(job.selected_records),
                'successful_records': len([r for r in serializable_results if r['success']]) if serializable_results else 0,
                'failed_records': len([r for r in serializable_results if not r['success']]) if serializable_results else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error getting job status: {e}")
            return None
    
    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """Get all jobs"""
        return [self.get_job_status(job_id) for job_id in self.jobs.keys()]
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job"""
        try:
            job = self.jobs.get(job_id)
            if not job:
                return False
            
            if job.status == 'running':
                job.status = 'cancelled'
                job.completed_at = datetime.now().isoformat()
                job.error_message = "Job cancelled by user"
                
                # Stop current job if it's the one being cancelled
                if self.current_job and self.current_job.job_id == job_id:
                    self.current_job = None
                
                self.logger.info(f"Job {job_id} cancelled")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error cancelling job: {e}")
            return False
    
    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """Clean up old completed jobs"""
        try:
            current_time = datetime.now()
            cutoff_time = current_time.timestamp() - (max_age_hours * 3600)
            
            jobs_to_remove = []
            for job_id, job in self.jobs.items():
                try:
                    job_time = datetime.fromisoformat(job.created_at).timestamp()
                    if job_time < cutoff_time and job.status in ['completed', 'failed', 'cancelled']:
                        jobs_to_remove.append(job_id)
                except:
                    pass
            
            for job_id in jobs_to_remove:
                del self.jobs[job_id]
            
            if jobs_to_remove:
                self.logger.info(f"Cleaned up {len(jobs_to_remove)} old jobs")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up old jobs: {e}")
    
    def get_current_job_status(self) -> Optional[Dict[str, Any]]:
        """Get status of currently running job"""
        if self.current_job:
            return self.get_job_status(self.current_job.job_id)
        return None
    
    def is_automation_running(self) -> bool:
        """Check if automation is currently running"""
        return self.current_job is not None
    
    def get_engine_status(self) -> Dict[str, Any]:
        """Get status of the automation engine"""
        return {
            'initialized': self.is_engine_initialized,
            'engine_available': self.automation_engine is not None,
            'current_job_running': self.is_automation_running()
        }
    
    def initialize_browser(self) -> Dict[str, Any]:
        """Initialize browser for desktop app with enhanced error handling and connection stability"""
        try:
            self.logger.info("🚀 Initializing browser for desktop app with enhanced stability...")
            
            # Check if already initialized
            if self.is_engine_initialized and self.automation_engine:
                self.logger.info("✅ Browser already initialized")
                return {
                    'success': True,
                    'message': 'Browser already initialized and ready',
                    'status': 'ready'
                }
            
            # Initialize the automation engine with retry mechanism for connection issues
            max_init_attempts = 3
            last_error = None
            
            for attempt in range(max_init_attempts):
                try:
                    self.logger.info(f"Browser initialization attempt {attempt + 1}/{max_init_attempts}")
                    
                    # Create automation engine instance if needed
                    if not self.automation_engine:
                        from core.enhanced_staging_automation import EnhancedStagingAutomationEngine
                        self.automation_engine = EnhancedStagingAutomationEngine(self.config)
                    
                    # Initialize browser and perform login
                    success = asyncio.run(self.automation_engine.initialize())
                    
                    if success:
                        self.is_engine_initialized = True
                        self.logger.info("✅ Browser initialization completed successfully")
                        return {
                            'success': True,
                            'message': 'Browser initialized and logged in successfully',
                            'status': 'ready',
                            'attempt': attempt + 1
                        }
                    else:
                        last_error = "Engine initialization returned False"
                        self.logger.warning(f"Attempt {attempt + 1} failed: {last_error}")
                        
                except Exception as init_error:
                    last_error = str(init_error)
                    self.logger.warning(f"Attempt {attempt + 1} failed with error: {last_error}")
                    
                    # If not the last attempt, wait before retrying
                    if attempt < max_init_attempts - 1:
                        self.logger.info(f"Waiting 5 seconds before retry...")
                        time.sleep(5)
            
            # All attempts failed
            self.logger.error(f"❌ Browser initialization failed after {max_init_attempts} attempts")
            return {
                'success': False,
                'message': f'Browser initialization failed after {max_init_attempts} attempts: {last_error}',
                'status': 'failed',
                'last_error': last_error
            }
                
        except Exception as e:
            self.logger.error(f"❌ Critical error during browser initialization: {e}")
            return {
                'success': False,
                'message': f'Critical browser initialization error: {str(e)}',
                'status': 'error',
                'error': str(e)
            }
    
    async def cleanup(self):
        """Clean up automation service resources"""
        try:
            self.logger.info("Cleaning up automation service...")
            
            # Cancel any running jobs
            for job_id, job in self.jobs.items():
                if job.status == 'running':
                    self.cancel_job(job_id)
            
            # Clean up automation engine
            if self.automation_engine:
                await self.automation_engine.cleanup()
                self.automation_engine = None
            
            self.is_engine_initialized = False
            
        except Exception as e:
            self.logger.error(f"Error during automation service cleanup: {e}")

# Global automation service instance with thread safety
_automation_service_instance: Optional[AutomationService] = None
_service_creation_lock = threading.Lock()

def get_automation_service(config: Dict[str, Any] = None) -> AutomationService:
    """Get or create the global automation service instance with thread safety"""
    global _automation_service_instance
    
    # Double-checked locking pattern for thread safety
    if _automation_service_instance is None:
        with _service_creation_lock:
            # Check again inside the lock
            if _automation_service_instance is None:
                if config is None:
                    raise ValueError("Configuration required for first-time service creation")
                print("🔧 Creating new AutomationService instance (singleton pattern)")
                _automation_service_instance = AutomationService(config)
            else:
                print("✅ Using existing AutomationService instance (singleton pattern)")
    else:
        print("✅ Using existing AutomationService instance (singleton pattern)")
    
    return _automation_service_instance

def cleanup_automation_service():
    """Clean up the global automation service instance"""
    global _automation_service_instance
    
    if _automation_service_instance:
        # Run cleanup in async context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_automation_service_instance.cleanup())
        finally:
            loop.close()
        
        _automation_service_instance = None
