#!/usr/bin/env python3
"""
Desktop Error Handler for Venus Desktop Application
Simplified error handling compatible with existing automation system
"""

import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Error categories"""
    BROWSER = "browser"
    NETWORK = "network"
    ELEMENT = "element"
    DATA = "data"
    SYSTEM = "system"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    UNKNOWN = "unknown"

class ErrorInfo:
    """Error information container"""
    
    def __init__(self, 
                 error: Exception,
                 category: ErrorCategory,
                 severity: ErrorSeverity,
                 message: str,
                 context: Dict[str, Any] = None,
                 timestamp: datetime = None):
        self.error = error
        self.category = category
        self.severity = severity
        self.message = message
        self.context = context or {}
        self.timestamp = timestamp or datetime.now()
        self.traceback = traceback.format_exc()

class DesktopErrorHandler:
    """Simplified error handler for desktop application"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.error_count = 0
        self.error_history = []
        
    def handle_error(self, 
                    error: Exception, 
                    context: Dict[str, Any] = None) -> ErrorInfo:
        """Handle and categorize errors"""
        
        try:
            # Categorize error
            category = self._categorize_error(error)
            severity = self._determine_severity(error, category)
            message = self._format_error_message(error, context)
            
            # Create error info
            error_info = ErrorInfo(
                error=error,
                category=category,
                severity=severity,
                message=message,
                context=context
            )
            
            # Log error
            self._log_error(error_info)
            
            # Store error for analysis
            self.error_history.append(error_info)
            self.error_count += 1
            
            # Keep only last 100 errors
            if len(self.error_history) > 100:
                self.error_history = self.error_history[-100:]
            
            return error_info
            
        except Exception as handler_error:
            self.logger.error(f"❌ Error in error handler: {handler_error}")
            # Return a basic error info if handler fails
            return ErrorInfo(
                error=error,
                category=ErrorCategory.UNKNOWN,
                severity=ErrorSeverity.HIGH,
                message=str(error)
            )
    
    def _categorize_error(self, error: Exception) -> ErrorCategory:
        """Categorize error based on type and message"""
        
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # Browser-related errors
        if any(keyword in error_str for keyword in [
            'webdriver', 'selenium', 'chrome', 'browser', 'driver',
            'session', 'window', 'tab'
        ]):
            return ErrorCategory.BROWSER
        
        # Network-related errors
        if any(keyword in error_str for keyword in [
            'connection', 'timeout', 'network', 'http', 'request',
            'response', 'url', 'unreachable'
        ]):
            return ErrorCategory.NETWORK
        
        # Element-related errors
        if any(keyword in error_str for keyword in [
            'element', 'locator', 'xpath', 'css', 'selector',
            'not found', 'no such element', 'stale'
        ]):
            return ErrorCategory.ELEMENT
        
        # Data-related errors
        if any(keyword in error_str for keyword in [
            'data', 'json', 'parse', 'format', 'value',
            'missing', 'invalid', 'empty'
        ]):
            return ErrorCategory.DATA
        
        # Authentication errors
        if any(keyword in error_str for keyword in [
            'login', 'password', 'auth', 'credential',
            'unauthorized', 'forbidden', 'access denied'
        ]):
            return ErrorCategory.AUTHENTICATION
        
        # Validation errors
        if any(keyword in error_str for keyword in [
            'validation', 'validate', 'check', 'verify',
            'assertion', 'expected', 'actual'
        ]):
            return ErrorCategory.VALIDATION
        
        # System errors
        if any(keyword in error_type for keyword in [
            'system', 'os', 'file', 'permission', 'memory',
            'disk', 'process'
        ]):
            return ErrorCategory.SYSTEM
        
        return ErrorCategory.UNKNOWN
    
    def _determine_severity(self, 
                          error: Exception, 
                          category: ErrorCategory) -> ErrorSeverity:
        """Determine error severity"""
        
        error_str = str(error).lower()
        
        # Critical errors that should stop automation
        if any(keyword in error_str for keyword in [
            'critical', 'fatal', 'crash', 'abort',
            'system error', 'memory error', 'disk full'
        ]):
            return ErrorSeverity.CRITICAL
        
        # High severity errors
        if category in [ErrorCategory.BROWSER, ErrorCategory.AUTHENTICATION]:
            return ErrorSeverity.HIGH
        
        if any(keyword in error_str for keyword in [
            'session', 'driver', 'login failed',
            'unauthorized', 'forbidden'
        ]):
            return ErrorSeverity.HIGH
        
        # Medium severity errors
        if category in [ErrorCategory.NETWORK, ErrorCategory.ELEMENT]:
            return ErrorSeverity.MEDIUM
        
        # Low severity errors
        if category in [ErrorCategory.DATA, ErrorCategory.VALIDATION]:
            return ErrorSeverity.LOW
        
        return ErrorSeverity.MEDIUM
    
    def _format_error_message(self, 
                            error: Exception, 
                            context: Dict[str, Any] = None) -> str:
        """Format error message with context"""
        
        base_message = str(error)
        
        if context:
            context_str = ", ".join([f"{k}: {v}" for k, v in context.items()])
            return f"{base_message} (Context: {context_str})"
        
        return base_message
    
    def _log_error(self, error_info: ErrorInfo):
        """Log error with appropriate level"""
        
        log_message = (
            f"[{error_info.category.value.upper()}] "
            f"{error_info.message}"
        )
        
        if error_info.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(f"💥 CRITICAL: {log_message}")
        elif error_info.severity == ErrorSeverity.HIGH:
            self.logger.error(f"❌ HIGH: {log_message}")
        elif error_info.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(f"⚠️ MEDIUM: {log_message}")
        else:
            self.logger.info(f"ℹ️ LOW: {log_message}")
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        
        if not self.error_history:
            return {
                'total_errors': 0,
                'by_category': {},
                'by_severity': {},
                'recent_errors': []
            }
        
        # Count by category
        by_category = {}
        for error_info in self.error_history:
            category = error_info.category.value
            by_category[category] = by_category.get(category, 0) + 1
        
        # Count by severity
        by_severity = {}
        for error_info in self.error_history:
            severity = error_info.severity.value
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        # Recent errors (last 5)
        recent_errors = [
            {
                'timestamp': error_info.timestamp.isoformat(),
                'category': error_info.category.value,
                'severity': error_info.severity.value,
                'message': error_info.message
            }
            for error_info in self.error_history[-5:]
        ]
        
        return {
            'total_errors': self.error_count,
            'by_category': by_category,
            'by_severity': by_severity,
            'recent_errors': recent_errors
        }
    
    def clear_history(self):
        """Clear error history"""
        self.error_history.clear()
        self.error_count = 0
        self.logger.info("🧹 Error history cleared")