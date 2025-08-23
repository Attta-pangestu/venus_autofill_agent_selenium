#!/usr/bin/env python3
"""
Desktop Automation Manager for Venus Desktop Application
Integrates with existing automation system and provides enhanced error handling
"""

import logging
import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from enum import Enum

class AutomationMode(Enum):
    """Automation modes"""
    TESTING = "testing"
    REAL = "real"
    DEBUG = "debug"

class AutomationState(Enum):
    """Automation states"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"

class DesktopAutomationManager:
    """Desktop automation manager with enhanced error handling"""
    
    def __init__(self, error_handler=None):
        self.logger = logging.getLogger(__name__)
        self.error_handler = error_handler
        self.state = AutomationState.IDLE
        self.current_progress = {
            'current': 0,
            'total': 0,
            'employee_name': '',
            'status': 'Ready'
        }
        
    async def run_automation(self, 
                           automation_mode: AutomationMode,
                           selected_records: List[Dict],
                           enhanced_automation,
                           progress_callback: Callable = None) -> bool:
        """Run automation with enhanced error handling"""
        
        try:
            self.state = AutomationState.RUNNING
            self.logger.info(f"🚀 Starting automation in {automation_mode.value} mode")
            
            # Set automation mode
            enhanced_automation.automation_mode = automation_mode.value
            
            # Progress tracking
            total_records = len(selected_records)
            processed = 0
            
            # Process records with enhanced error handling
            for i, record in enumerate(selected_records):
                try:
                    # Update progress
                    employee_name = record.get('employee_name', f'Record {i+1}')
                    if progress_callback:
                        progress_callback(
                            current=i+1,
                            total=total_records,
                            employee_name=employee_name,
                            status=f"Processing {employee_name}"
                        )
                    
                    # Process single record with retry logic
                    success = await self._process_record_with_retry(
                        record, enhanced_automation, max_retries=3
                    )
                    
                    if success:
                        processed += 1
                        self.logger.info(f"✅ Successfully processed: {employee_name}")
                    else:
                        self.logger.warning(f"⚠️ Failed to process: {employee_name}")
                        
                        # Continue with next record instead of failing completely
                        if self.error_handler:
                            self.logger.info("🔄 Continuing with next record...")
                        
                except Exception as record_error:
                    self.logger.error(f"❌ Error processing record {i+1}: {record_error}")
                    
                    # Handle individual record errors
                    if self.error_handler:
                        error_info = self.error_handler.handle_error(
                            record_error, 
                            context={'record_index': i+1, 'employee_name': employee_name}
                        )
                        
                        # Decide whether to continue or abort
                        if error_info.severity.value == 'critical':
                            self.logger.error("💥 Critical error detected, aborting automation")
                            self.state = AutomationState.FAILED
                            return False
                    
                    # Continue with next record for non-critical errors
                    continue
                
                # Small delay between records
                await asyncio.sleep(0.5)
            
            # Final progress update
            if progress_callback:
                progress_callback(
                    current=total_records,
                    total=total_records,
                    employee_name="",
                    status=f"Completed: {processed}/{total_records} records"
                )
            
            # Determine final result
            success_rate = (processed / total_records) * 100 if total_records > 0 else 0
            
            if success_rate >= 80:  # Consider 80%+ success rate as successful
                self.state = AutomationState.COMPLETED
                self.logger.info(
                    f"✅ Automation completed successfully. "
                    f"Success rate: {success_rate:.1f}% ({processed}/{total_records})"
                )
                return True
            else:
                self.state = AutomationState.FAILED
                self.logger.warning(
                    f"⚠️ Automation completed with low success rate: "
                    f"{success_rate:.1f}% ({processed}/{total_records})"
                )
                return False
                
        except Exception as e:
            self.state = AutomationState.FAILED
            self.logger.error(f"❌ Automation failed: {e}")
            
            if self.error_handler:
                self.error_handler.handle_error(e, context={
                    'automation_mode': automation_mode.value,
                    'total_records': len(selected_records),
                    'operation': 'run_automation'
                })
            
            return False
    
    async def _process_record_with_retry(self, 
                                       record: Dict, 
                                       enhanced_automation,
                                       max_retries: int = 3) -> bool:
        """Process single record with retry logic"""
        
        for attempt in range(max_retries):
            try:
                # Get the driver from enhanced_automation
                # EnhancedUserControlledAutomationSystem uses processor.browser_manager.get_driver()
                driver = None
                if hasattr(enhanced_automation, 'processor') and enhanced_automation.processor:
                    if hasattr(enhanced_automation.processor, 'browser_manager'):
                        driver = enhanced_automation.processor.browser_manager.get_driver()
                
                if not driver:
                    self.logger.error("❌ No driver available in enhanced_automation")
                    return False
                
                # Call process_single_record_enhanced directly to avoid double loading
                # This prevents the issue where process_selected_records reinitializes browser
                result = await enhanced_automation.process_single_record_enhanced(
                    driver, record, 1, 1  # record_index=1, total_records=1 for single processing
                )
                
                # Check if result indicates success
                if result is not False and result is not None:
                    return True
                    
                # If result is False or None, consider it a failure
                if attempt < max_retries - 1:
                    self.logger.warning(
                        f"⚠️ Attempt {attempt + 1} failed for record, retrying..."
                    )
                    await asyncio.sleep(2)  # Wait before retry
                else:
                    self.logger.error(
                        f"❌ All {max_retries} attempts failed for record"
                    )
                    return False
                    
            except Exception as e:
                self.logger.error(f"❌ Attempt {attempt + 1} error: {e}")
                
                if self.error_handler:
                    error_info = self.error_handler.handle_error(e, context={
                        'attempt': attempt + 1,
                        'max_retries': max_retries,
                        'record': record
                    })
                    
                    # For critical errors, don't retry
                    if error_info.severity.value == 'critical':
                        return False
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    return False
        
        return False
    
    async def cleanup(self):
        """Cleanup automation manager"""
        try:
            self.state = AutomationState.IDLE
            self.logger.info("🧹 Desktop automation manager cleaned up")
        except Exception as e:
            self.logger.error(f"❌ Error during cleanup: {e}")
    
    def get_state(self) -> AutomationState:
        """Get current automation state"""
        return self.state
    
    def get_progress(self) -> Dict[str, Any]:
        """Get current progress information"""
        return self.current_progress.copy()