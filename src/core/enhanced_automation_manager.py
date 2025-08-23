#!/usr/bin/env python3
"""
Enhanced Automation Manager for Venus Desktop Application
Provides robust automation control with advanced error handling and recovery
"""

import logging
import time
import threading
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any, Tuple
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, Future
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from .enhanced_error_handler import (
    EnhancedErrorHandler, ErrorCategory, ErrorSeverity, RecoveryAction,
    handle_automation_errors
)

class AutomationState(Enum):
    """Automation states"""
    IDLE = "idle"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    COMPLETED = "completed"

class AutomationMode(Enum):
    """Automation modes"""
    TESTING = "testing"
    PRODUCTION = "production"
    DEBUG = "debug"

class ProgressInfo:
    """Progress tracking information"""
    def __init__(self):
        self.total_records = 0
        self.processed_records = 0
        self.successful_records = 0
        self.failed_records = 0
        self.skipped_records = 0
        self.start_time = None
        self.end_time = None
        self.current_record = None
        self.estimated_completion = None
        
    @property
    def completion_percentage(self) -> float:
        if self.total_records == 0:
            return 0.0
        return (self.processed_records / self.total_records) * 100
    
    @property
    def success_rate(self) -> float:
        if self.processed_records == 0:
            return 0.0
        return (self.successful_records / self.processed_records) * 100
    
    @property
    def elapsed_time(self) -> float:
        if not self.start_time:
            return 0.0
        end_time = self.end_time or datetime.now()
        return (end_time - self.start_time).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_records': self.total_records,
            'processed_records': self.processed_records,
            'successful_records': self.successful_records,
            'failed_records': self.failed_records,
            'skipped_records': self.skipped_records,
            'completion_percentage': self.completion_percentage,
            'success_rate': self.success_rate,
            'elapsed_time': self.elapsed_time,
            'current_record': self.current_record,
            'estimated_completion': self.estimated_completion.isoformat() if self.estimated_completion else None
        }

class EnhancedAutomationManager:
    """Enhanced automation manager with robust error handling"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # Initialize error handler
        error_config = self.config.get('error_handling', {})
        self.error_handler = EnhancedErrorHandler(error_config)
        
        # State management
        self.state = AutomationState.IDLE
        self.mode = AutomationMode(self.config.get('default_mode', 'testing'))
        self.progress = ProgressInfo()
        
        # Browser management
        self.driver: Optional[WebDriver] = None
        self.browser_healthy = False
        self.last_health_check = None
        
        # Threading
        self.automation_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        
        # Callbacks
        self.progress_callbacks: List[Callable[[ProgressInfo], None]] = []
        self.state_callbacks: List[Callable[[AutomationState], None]] = []
        self.error_callbacks: List[Callable[[Exception], None]] = []
        
        # Configuration
        self.batch_size = self.config.get('batch_size', 10)
        self.delay_between_actions = self.config.get('delay_between_actions', 1)
        self.health_check_interval = self.config.get('health_check_interval', 30)
        self.auto_recovery = self.config.get('auto_recovery_enabled', True)
        
        # Recovery callbacks
        self.recovery_callbacks = {
            RecoveryAction.RESTART_BROWSER: self._restart_browser,
            RecoveryAction.REFRESH_PAGE: self._refresh_page,
            RecoveryAction.CLEAR_CACHE: self._clear_cache,
            RecoveryAction.SKIP_RECORD: self._skip_current_record,
            RecoveryAction.ABORT_AUTOMATION: self._abort_automation
        }
        
        # Start health monitoring
        self._start_health_monitoring()
        
        self.logger.info("🚀 Enhanced Automation Manager initialized")
    
    def set_driver(self, driver: WebDriver):
        """Set the WebDriver instance"""
        self.driver = driver
        self.browser_healthy = True
        self.last_health_check = datetime.now()
        self.logger.info("🌐 WebDriver set and marked as healthy")
    
    def add_progress_callback(self, callback: Callable[[ProgressInfo], None]):
        """Add progress update callback"""
        self.progress_callbacks.append(callback)
    
    def add_state_callback(self, callback: Callable[[AutomationState], None]):
        """Add state change callback"""
        self.state_callbacks.append(callback)
    
    def add_error_callback(self, callback: Callable[[Exception], None]):
        """Add error callback"""
        self.error_callbacks.append(callback)
    
    def set_mode(self, mode: AutomationMode):
        """Set automation mode"""
        self.mode = mode
        self.logger.info(f"🔧 Automation mode set to: {mode.value}")
    
    def start_automation(self, 
                        records: List[Dict[str, Any]], 
                        automation_function: Callable,
                        **kwargs) -> bool:
        """Start automation process"""
        if self.state != AutomationState.IDLE:
            self.logger.warning(f"⚠️ Cannot start automation. Current state: {self.state.value}")
            return False
        
        if not self.driver or not self.browser_healthy:
            self.logger.error("❌ Browser not available or unhealthy")
            return False
        
        # Reset progress
        self.progress = ProgressInfo()
        self.progress.total_records = len(records)
        self.progress.start_time = datetime.now()
        
        # Reset stop/pause events
        self.stop_event.clear()
        self.pause_event.clear()
        
        # Start automation in separate thread
        self.automation_thread = threading.Thread(
            target=self._run_automation,
            args=(records, automation_function),
            kwargs=kwargs,
            daemon=True
        )
        
        self._set_state(AutomationState.INITIALIZING)
        self.automation_thread.start()
        
        self.logger.info(f"🚀 Automation started with {len(records)} records")
        return True
    
    def stop_automation(self, force: bool = False) -> bool:
        """Stop automation process"""
        if self.state not in [AutomationState.RUNNING, AutomationState.PAUSED]:
            self.logger.warning(f"⚠️ Cannot stop automation. Current state: {self.state.value}")
            return False
        
        self._set_state(AutomationState.STOPPING)
        self.stop_event.set()
        
        if force and self.automation_thread:
            # Force termination (not recommended)
            self.logger.warning("⚠️ Force stopping automation thread")
            # Note: Python doesn't have thread.terminate(), so we rely on stop_event
        
        self.logger.info("🛑 Automation stop requested")
        return True
    
    def pause_automation(self) -> bool:
        """Pause automation process"""
        if self.state != AutomationState.RUNNING:
            return False
        
        self._set_state(AutomationState.PAUSED)
        self.pause_event.set()
        self.logger.info("⏸️ Automation paused")
        return True
    
    def resume_automation(self) -> bool:
        """Resume automation process"""
        if self.state != AutomationState.PAUSED:
            return False
        
        self._set_state(AutomationState.RUNNING)
        self.pause_event.clear()
        self.logger.info("▶️ Automation resumed")
        return True
    
    def _run_automation(self, 
                       records: List[Dict[str, Any]], 
                       automation_function: Callable,
                       **kwargs):
        """Main automation loop"""
        try:
            self._set_state(AutomationState.RUNNING)
            
            for i, record in enumerate(records):
                # Check for stop/pause
                if self.stop_event.is_set():
                    self.logger.info("🛑 Automation stopped by user")
                    break
                
                while self.pause_event.is_set():
                    time.sleep(0.5)
                    if self.stop_event.is_set():
                        break
                
                if self.stop_event.is_set():
                    break
                
                # Update progress
                self.progress.current_record = record
                self._notify_progress()
                
                # Process record with error handling
                success = self._process_record_with_recovery(
                    record, automation_function, **kwargs
                )
                
                # Update counters
                self.progress.processed_records += 1
                if success:
                    self.progress.successful_records += 1
                else:
                    self.progress.failed_records += 1
                
                # Update estimated completion
                self._update_estimated_completion()
                
                # Notify progress
                self._notify_progress()
                
                # Delay between actions
                if self.delay_between_actions > 0:
                    time.sleep(self.delay_between_actions)
                
                # Health check
                if i % 10 == 0:  # Check every 10 records
                    self._check_browser_health()
            
            # Automation completed
            self.progress.end_time = datetime.now()
            
            if self.stop_event.is_set():
                self._set_state(AutomationState.STOPPED)
            else:
                self._set_state(AutomationState.COMPLETED)
                
            self.logger.info(
                f"✅ Automation completed. "
                f"Success: {self.progress.successful_records}/{self.progress.total_records} "
                f"({self.progress.success_rate:.1f}%)"
            )
            
        except Exception as e:
            self.logger.error(f"❌ Automation failed: {e}")
            self._set_state(AutomationState.ERROR)
            self._notify_error(e)
    
    def _process_record_with_recovery(self, 
                                     record: Dict[str, Any], 
                                     automation_function: Callable,
                                     **kwargs) -> bool:
        """Process single record with error recovery"""
        max_attempts = 3
        attempt = 0
        
        while attempt < max_attempts:
            try:
                # Create decorated function with error handling
                @handle_automation_errors(
                    self.error_handler,
                    lambda: self.driver,
                    self.recovery_callbacks
                )
                def safe_automation():
                    return automation_function(record, **kwargs)
                
                result = safe_automation()
                return result is not False  # Consider None as success
                
            except Exception as e:
                attempt += 1
                context = {
                    'record': record,
                    'attempt': attempt,
                    'max_attempts': max_attempts
                }
                
                error_info = self.error_handler.handle_error(e, context, self.driver)
                
                # Check if we should continue or abort
                if error_info.severity == ErrorSeverity.CRITICAL:
                    self.logger.error("💥 Critical error detected, aborting record")
                    self.progress.failed_records += 1
                    return False
                
                if attempt < max_attempts and self.auto_recovery:
                    recovery_success = self.error_handler.attempt_recovery(
                        error_info, self.driver, self.recovery_callbacks
                    )
                    
                    if not recovery_success:
                        self.logger.warning(f"⚠️ Recovery failed for attempt {attempt}")
                        continue
                else:
                    self.logger.error(f"❌ Record processing failed after {max_attempts} attempts")
                    return False
        
        return False
    
    def _check_browser_health(self) -> bool:
        """Check browser health"""
        if not self.driver:
            self.browser_healthy = False
            return False
        
        try:
            # Simple health check
            self.driver.current_url
            self.browser_healthy = True
            self.last_health_check = datetime.now()
            return True
            
        except WebDriverException as e:
            self.logger.warning(f"⚠️ Browser health check failed: {e}")
            self.browser_healthy = False
            
            if self.auto_recovery:
                self.logger.info("🔄 Attempting browser recovery...")
                return self._restart_browser()
            
            return False
    
    def _start_health_monitoring(self):
        """Start background health monitoring"""
        def health_monitor():
            while True:
                time.sleep(self.health_check_interval)
                if self.driver and self.state == AutomationState.RUNNING:
                    self._check_browser_health()
        
        monitor_thread = threading.Thread(target=health_monitor, daemon=True)
        monitor_thread.start()
    
    def _restart_browser(self) -> bool:
        """Restart browser (requires external implementation)"""
        self.logger.warning("🔄 Browser restart requested - requires external handling")
        # This should be implemented by the calling application
        return False
    
    def _refresh_page(self) -> bool:
        """Refresh current page"""
        if not self.driver:
            return False
        
        try:
            self.driver.refresh()
            time.sleep(3)
            self.logger.info("🔄 Page refreshed")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to refresh page: {e}")
            return False
    
    def _clear_cache(self) -> bool:
        """Clear browser cache"""
        if not self.driver:
            return False
        
        try:
            self.driver.delete_all_cookies()
            self.logger.info("🧹 Browser cache cleared")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to clear cache: {e}")
            return False
    
    def _skip_current_record(self) -> bool:
        """Skip current record"""
        self.progress.skipped_records += 1
        self.logger.info("⏭️ Skipping current record")
        return True
    
    def _abort_automation(self) -> bool:
        """Abort automation"""
        self.logger.warning("🚨 Aborting automation due to critical error")
        self.stop_event.set()
        return True
    
    def _update_estimated_completion(self):
        """Update estimated completion time"""
        if self.progress.processed_records > 0 and self.progress.start_time:
            elapsed = (datetime.now() - self.progress.start_time).total_seconds()
            avg_time_per_record = elapsed / self.progress.processed_records
            remaining_records = self.progress.total_records - self.progress.processed_records
            estimated_remaining_time = remaining_records * avg_time_per_record
            
            self.progress.estimated_completion = datetime.now() + \
                                               timedelta(seconds=estimated_remaining_time)
    
    def _set_state(self, new_state: AutomationState):
        """Set automation state and notify callbacks"""
        if self.state != new_state:
            old_state = self.state
            self.state = new_state
            self.logger.info(f"🔄 State changed: {old_state.value} → {new_state.value}")
            
            # Notify callbacks
            for callback in self.state_callbacks:
                try:
                    callback(new_state)
                except Exception as e:
                    self.logger.error(f"❌ State callback error: {e}")
    
    def _notify_progress(self):
        """Notify progress callbacks"""
        for callback in self.progress_callbacks:
            try:
                callback(self.progress)
            except Exception as e:
                self.logger.error(f"❌ Progress callback error: {e}")
    
    def _notify_error(self, error: Exception):
        """Notify error callbacks"""
        for callback in self.error_callbacks:
            try:
                callback(error)
            except Exception as e:
                self.logger.error(f"❌ Error callback error: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current automation status"""
        return {
            'state': self.state.value,
            'mode': self.mode.value,
            'browser_healthy': self.browser_healthy,
            'last_health_check': self.last_health_check.isoformat() if self.last_health_check else None,
            'progress': self.progress.to_dict(),
            'error_stats': self.error_handler.get_error_statistics(),
            'is_critical_pattern': self.error_handler.is_critical_error_pattern()
        }
    
    def cleanup(self):
        """Cleanup resources"""
        self.stop_automation(force=True)
        
        if self.automation_thread and self.automation_thread.is_alive():
            self.automation_thread.join(timeout=5)
        
        self.error_handler.clear_error_history()
        self.logger.info("🧹 Automation manager cleaned up")

from datetime import timedelta