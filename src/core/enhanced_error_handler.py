#!/usr/bin/env python3
"""
Enhanced Error Handler for Venus Desktop Application
Handles automation errors with advanced recovery mechanisms
"""

import logging
import time
import traceback
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
from selenium.common.exceptions import (
    WebDriverException,
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
    ElementNotInteractableException,
    ElementClickInterceptedException,
    SessionNotCreatedException,
    InvalidSessionIdException,
    NoSuchWindowException,
    UnexpectedAlertPresentException
)
from selenium.webdriver.remote.webdriver import WebDriver
from requests.exceptions import RequestException, ConnectionError, Timeout

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Error categories for better handling"""
    BROWSER = "browser"
    NETWORK = "network"
    ELEMENT = "element"
    DATA = "data"
    SYSTEM = "system"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"

class RecoveryAction(Enum):
    """Available recovery actions"""
    RETRY = "retry"
    REFRESH_PAGE = "refresh_page"
    RESTART_BROWSER = "restart_browser"
    SKIP_RECORD = "skip_record"
    ABORT_AUTOMATION = "abort_automation"
    WAIT_AND_RETRY = "wait_and_retry"
    CLEAR_CACHE = "clear_cache"
    SWITCH_WINDOW = "switch_window"

class ErrorInfo:
    """Container for error information"""
    def __init__(self, 
                 error: Exception,
                 category: ErrorCategory,
                 severity: ErrorSeverity,
                 context: Dict[str, Any] = None,
                 suggested_actions: List[RecoveryAction] = None):
        self.error = error
        self.category = category
        self.severity = severity
        self.context = context or {}
        self.suggested_actions = suggested_actions or []
        self.timestamp = datetime.now()
        self.error_id = f"{category.value}_{int(time.time())}"
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert error info to dictionary"""
        return {
            'error_id': self.error_id,
            'timestamp': self.timestamp.isoformat(),
            'category': self.category.value,
            'severity': self.severity.value,
            'error_type': type(self.error).__name__,
            'error_message': str(self.error),
            'context': self.context,
            'suggested_actions': [action.value for action in self.suggested_actions],
            'traceback': traceback.format_exc()
        }

class EnhancedErrorHandler:
    """Enhanced error handler with recovery mechanisms"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        self.error_history: List[ErrorInfo] = []
        self.recovery_attempts: Dict[str, int] = {}
        self.max_recovery_attempts = self.config.get('max_recovery_attempts', 3)
        self.recovery_delay = self.config.get('recovery_delay', 2)
        self.screenshot_on_error = self.config.get('screenshot_on_error', True)
        self.save_page_source = self.config.get('save_page_source_on_error', True)
        self.error_log_file = self.config.get('error_log_file', './logs/errors.json')
        
        # Ensure error log directory exists
        os.makedirs(os.path.dirname(self.error_log_file), exist_ok=True)
        
        # Error classification mapping
        self.error_classification = {
            # Browser errors
            SessionNotCreatedException: (ErrorCategory.BROWSER, ErrorSeverity.CRITICAL),
            InvalidSessionIdException: (ErrorCategory.BROWSER, ErrorSeverity.HIGH),
            NoSuchWindowException: (ErrorCategory.BROWSER, ErrorSeverity.HIGH),
            WebDriverException: (ErrorCategory.BROWSER, ErrorSeverity.MEDIUM),
            
            # Element errors
            NoSuchElementException: (ErrorCategory.ELEMENT, ErrorSeverity.MEDIUM),
            StaleElementReferenceException: (ErrorCategory.ELEMENT, ErrorSeverity.MEDIUM),
            ElementNotInteractableException: (ErrorCategory.ELEMENT, ErrorSeverity.MEDIUM),
            ElementClickInterceptedException: (ErrorCategory.ELEMENT, ErrorSeverity.MEDIUM),
            TimeoutException: (ErrorCategory.ELEMENT, ErrorSeverity.MEDIUM),
            
            # Network errors
            ConnectionError: (ErrorCategory.NETWORK, ErrorSeverity.HIGH),
            Timeout: (ErrorCategory.NETWORK, ErrorSeverity.MEDIUM),
            RequestException: (ErrorCategory.NETWORK, ErrorSeverity.MEDIUM),
            
            # Alert errors
            UnexpectedAlertPresentException: (ErrorCategory.BROWSER, ErrorSeverity.MEDIUM),
        }
        
        # Recovery strategies
        self.recovery_strategies = {
            ErrorCategory.BROWSER: {
                ErrorSeverity.CRITICAL: [RecoveryAction.RESTART_BROWSER, RecoveryAction.ABORT_AUTOMATION],
                ErrorSeverity.HIGH: [RecoveryAction.RESTART_BROWSER, RecoveryAction.WAIT_AND_RETRY],
                ErrorSeverity.MEDIUM: [RecoveryAction.REFRESH_PAGE, RecoveryAction.RETRY],
                ErrorSeverity.LOW: [RecoveryAction.RETRY]
            },
            ErrorCategory.ELEMENT: {
                ErrorSeverity.HIGH: [RecoveryAction.REFRESH_PAGE, RecoveryAction.WAIT_AND_RETRY],
                ErrorSeverity.MEDIUM: [RecoveryAction.WAIT_AND_RETRY, RecoveryAction.RETRY],
                ErrorSeverity.LOW: [RecoveryAction.RETRY]
            },
            ErrorCategory.NETWORK: {
                ErrorSeverity.HIGH: [RecoveryAction.WAIT_AND_RETRY, RecoveryAction.RESTART_BROWSER],
                ErrorSeverity.MEDIUM: [RecoveryAction.WAIT_AND_RETRY, RecoveryAction.RETRY],
                ErrorSeverity.LOW: [RecoveryAction.RETRY]
            },
            ErrorCategory.DATA: {
                ErrorSeverity.HIGH: [RecoveryAction.SKIP_RECORD, RecoveryAction.ABORT_AUTOMATION],
                ErrorSeverity.MEDIUM: [RecoveryAction.SKIP_RECORD, RecoveryAction.RETRY],
                ErrorSeverity.LOW: [RecoveryAction.RETRY]
            },
            ErrorCategory.SYSTEM: {
                ErrorSeverity.CRITICAL: [RecoveryAction.ABORT_AUTOMATION],
                ErrorSeverity.HIGH: [RecoveryAction.RESTART_BROWSER, RecoveryAction.ABORT_AUTOMATION],
                ErrorSeverity.MEDIUM: [RecoveryAction.WAIT_AND_RETRY],
                ErrorSeverity.LOW: [RecoveryAction.RETRY]
            }
        }
    
    def classify_error(self, error: Exception, context: Dict[str, Any] = None) -> ErrorInfo:
        """Classify error and determine recovery strategy"""
        error_type = type(error)
        
        # Get classification from mapping
        if error_type in self.error_classification:
            category, severity = self.error_classification[error_type]
        else:
            # Default classification for unknown errors
            category = ErrorCategory.SYSTEM
            severity = ErrorSeverity.MEDIUM
            
        # Adjust severity based on context
        if context:
            if context.get('retry_count', 0) > 2:
                severity = ErrorSeverity.HIGH
            if context.get('critical_operation', False):
                severity = ErrorSeverity.HIGH
                
        # Get suggested recovery actions
        suggested_actions = self.recovery_strategies.get(category, {}).get(
            severity, [RecoveryAction.RETRY]
        )
        
        return ErrorInfo(
            error=error,
            category=category,
            severity=severity,
            context=context,
            suggested_actions=suggested_actions
        )
    
    def handle_error(self, 
                    error: Exception, 
                    context: Dict[str, Any] = None,
                    driver: Optional[WebDriver] = None) -> ErrorInfo:
        """Handle error with classification and logging"""
        error_info = self.classify_error(error, context)
        
        # Log error
        self.logger.error(
            f"🚨 {error_info.category.value.upper()} ERROR [{error_info.severity.value}]: "
            f"{error_info.error_message}"
        )
        
        # Add to error history
        self.error_history.append(error_info)
        
        # Save error details
        self._save_error_details(error_info)
        
        # Capture diagnostics if driver available
        if driver and error_info.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            self._capture_diagnostics(driver, error_info)
        
        # Log suggested recovery actions
        if error_info.suggested_actions:
            actions_str = ", ".join([action.value for action in error_info.suggested_actions])
            self.logger.info(f"💡 Suggested recovery actions: {actions_str}")
        
        return error_info
    
    def attempt_recovery(self, 
                        error_info: ErrorInfo,
                        driver: Optional[WebDriver] = None,
                        recovery_callbacks: Dict[RecoveryAction, Callable] = None) -> bool:
        """Attempt to recover from error"""
        recovery_callbacks = recovery_callbacks or {}
        
        # Check if we've exceeded max attempts for this error type
        error_key = f"{error_info.category.value}_{type(error_info.error).__name__}"
        current_attempts = self.recovery_attempts.get(error_key, 0)
        
        if current_attempts >= self.max_recovery_attempts:
            self.logger.warning(
                f"⚠️ Max recovery attempts ({self.max_recovery_attempts}) "
                f"exceeded for {error_key}"
            )
            return False
        
        # Increment attempt counter
        self.recovery_attempts[error_key] = current_attempts + 1
        
        # Try each suggested recovery action
        for action in error_info.suggested_actions:
            self.logger.info(f"🔄 Attempting recovery action: {action.value}")
            
            try:
                success = self._execute_recovery_action(
                    action, driver, recovery_callbacks
                )
                
                if success:
                    self.logger.info(f"✅ Recovery successful with action: {action.value}")
                    # Reset attempt counter on success
                    self.recovery_attempts[error_key] = 0
                    return True
                    
            except Exception as recovery_error:
                self.logger.error(
                    f"❌ Recovery action {action.value} failed: {recovery_error}"
                )
                continue
        
        self.logger.error("❌ All recovery attempts failed")
        return False
    
    def _execute_recovery_action(self, 
                                action: RecoveryAction,
                                driver: Optional[WebDriver] = None,
                                callbacks: Dict[RecoveryAction, Callable] = None) -> bool:
        """Execute specific recovery action"""
        
        # Use custom callback if available
        if callbacks and action in callbacks:
            return callbacks[action]()
        
        # Default recovery implementations
        if action == RecoveryAction.RETRY:
            time.sleep(self.recovery_delay)
            return True
            
        elif action == RecoveryAction.WAIT_AND_RETRY:
            time.sleep(self.recovery_delay * 2)
            return True
            
        elif action == RecoveryAction.REFRESH_PAGE and driver:
            driver.refresh()
            time.sleep(3)
            return True
            
        elif action == RecoveryAction.CLEAR_CACHE and driver:
            driver.delete_all_cookies()
            return True
            
        elif action == RecoveryAction.SWITCH_WINDOW and driver:
            if len(driver.window_handles) > 1:
                driver.switch_to.window(driver.window_handles[-1])
                return True
            return False
            
        elif action == RecoveryAction.SKIP_RECORD:
            self.logger.info("⏭️ Skipping current record")
            return True
            
        elif action in [RecoveryAction.RESTART_BROWSER, RecoveryAction.ABORT_AUTOMATION]:
            # These require external handling
            self.logger.warning(f"⚠️ Action {action.value} requires external handling")
            return False
        
        return False
    
    def _capture_diagnostics(self, driver: WebDriver, error_info: ErrorInfo):
        """Capture diagnostic information"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Take screenshot
            if self.screenshot_on_error:
                screenshot_path = f"./logs/screenshots/error_{error_info.error_id}_{timestamp}.png"
                os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                driver.save_screenshot(screenshot_path)
                self.logger.info(f"📸 Screenshot saved: {screenshot_path}")
            
            # Save page source
            if self.save_page_source:
                source_path = f"./logs/page_sources/error_{error_info.error_id}_{timestamp}.html"
                os.makedirs(os.path.dirname(source_path), exist_ok=True)
                with open(source_path, 'w', encoding='utf-8') as f:
                    f.write(driver.page_source)
                self.logger.info(f"📄 Page source saved: {source_path}")
                
        except Exception as diag_error:
            self.logger.warning(f"⚠️ Failed to capture diagnostics: {diag_error}")
    
    def _save_error_details(self, error_info: ErrorInfo):
        """Save error details to file"""
        try:
            # Load existing errors
            errors = []
            if os.path.exists(self.error_log_file):
                with open(self.error_log_file, 'r', encoding='utf-8') as f:
                    errors = json.load(f)
            
            # Add new error
            errors.append(error_info.to_dict())
            
            # Keep only last 1000 errors
            if len(errors) > 1000:
                errors = errors[-1000:]
            
            # Save back to file
            with open(self.error_log_file, 'w', encoding='utf-8') as f:
                json.dump(errors, f, indent=2, ensure_ascii=False)
                
        except Exception as save_error:
            self.logger.warning(f"⚠️ Failed to save error details: {save_error}")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics"""
        if not self.error_history:
            return {}
        
        stats = {
            'total_errors': len(self.error_history),
            'by_category': {},
            'by_severity': {},
            'recent_errors': len([e for e in self.error_history 
                                if (datetime.now() - e.timestamp).seconds < 3600])
        }
        
        for error_info in self.error_history:
            # Count by category
            category = error_info.category.value
            stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
            
            # Count by severity
            severity = error_info.severity.value
            stats['by_severity'][severity] = stats['by_severity'].get(severity, 0) + 1
        
        return stats
    
    def clear_error_history(self):
        """Clear error history"""
        self.error_history.clear()
        self.recovery_attempts.clear()
        self.logger.info("🧹 Error history cleared")
    
    def is_critical_error_pattern(self) -> bool:
        """Check if there's a critical error pattern"""
        recent_errors = [e for e in self.error_history 
                        if (datetime.now() - e.timestamp).seconds < 300]  # Last 5 minutes
        
        if len(recent_errors) >= 5:
            return True
        
        critical_errors = [e for e in recent_errors 
                          if e.severity == ErrorSeverity.CRITICAL]
        
        return len(critical_errors) >= 2

# Decorator for automatic error handling
def handle_automation_errors(error_handler: EnhancedErrorHandler, 
                           driver_getter: Callable = None,
                           recovery_callbacks: Dict[RecoveryAction, Callable] = None):
    """Decorator for automatic error handling in automation functions"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            max_attempts = 3
            attempt = 0
            
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                    
                except Exception as e:
                    attempt += 1
                    context = {
                        'function': func.__name__,
                        'attempt': attempt,
                        'max_attempts': max_attempts,
                        'args': str(args)[:100],  # Truncate for logging
                        'kwargs': str(kwargs)[:100]
                    }
                    
                    error_info = error_handler.handle_error(
                        e, context, 
                        driver_getter() if driver_getter else None
                    )
                    
                    if attempt < max_attempts:
                        recovery_success = error_handler.attempt_recovery(
                            error_info,
                            driver_getter() if driver_getter else None,
                            recovery_callbacks
                        )
                        
                        if not recovery_success and error_info.severity == ErrorSeverity.CRITICAL:
                            break
                    else:
                        # Final attempt failed
                        error_handler.logger.error(
                            f"❌ Function {func.__name__} failed after {max_attempts} attempts"
                        )
                        raise e
            
            # If we get here, all attempts failed
            raise Exception(f"Function {func.__name__} failed after {max_attempts} attempts")
        
        return wrapper
    return decorator