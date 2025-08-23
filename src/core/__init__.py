# Venus Desktop Application - Core Components

from .desktop_error_handler import DesktopErrorHandler, ErrorSeverity, ErrorCategory
from .desktop_automation_manager import DesktopAutomationManager, AutomationMode, AutomationState

__all__ = [
    'DesktopErrorHandler',
    'ErrorSeverity', 
    'ErrorCategory',
    'DesktopAutomationManager',
    'AutomationMode',
    'AutomationState'
]