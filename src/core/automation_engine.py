"""
Selenium AutoFill - Core Automation Engine
Replicates the functionality of Venus-Millware AutoFill Chrome Extension
"""

import time
import json
import re
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, 
    ElementNotInteractableException, StaleElementReferenceException
)

from .element_finder import ElementFinder
from .visual_feedback import VisualFeedback
from .data_manager import DataManager
from .flow_validator import FlowValidator

@dataclass
class ExecutionResult:
    success: bool
    events_executed: int
    errors: List[str]
    extracted_data: Dict[str, Any]
    start_time: str
    end_time: Optional[str]
    execution_id: str

class AutomationEngine:
    """Core automation engine that executes flows using Selenium WebDriver"""
    
    def __init__(self, driver: webdriver.Chrome, config: Dict[str, Any]):
        self.driver = driver
        self.config = config
        self.is_executing = False
        self.is_paused = False
        self.current_execution = None
        self.automation_data = None
        self.flow_events = []
        self.extracted_data = {}
        self.loop_context = {}
        self.variables = {}
        
        # Initialize helper components
        self.element_finder = ElementFinder(driver)
        self.visual_feedback = VisualFeedback(driver)
        self.data_manager = DataManager()
        self.flow_validator = FlowValidator()
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Execution results tracking
        self.execution_results = ExecutionResult(
            success=False,
            events_executed=0,
            errors=[],
            extracted_data={},
            start_time="",
            end_time=None,
            execution_id=""
        )

    async def execute_automation_flow(self, flow_events: List[Dict], automation_data: List[Dict] = None, metadata: Dict = None) -> ExecutionResult:
        """Execute a complete automation flow"""
        if self.is_executing:
            raise Exception("Automation already running")

        self.logger.info("🚀 Starting automation flow execution")
        
        self.is_executing = True
        self.is_paused = False
        self.flow_events = flow_events
        self.automation_data = automation_data or []
        
        # Initialize execution results
        self.execution_results = ExecutionResult(
            success=False,
            events_executed=0,
            errors=[],
            extracted_data={},
            start_time=datetime.now().isoformat(),
            end_time=None,
            execution_id=metadata.get('executionId', self._generate_execution_id()) if metadata else self._generate_execution_id()
        )

        try:
            # Validate flow before execution
            validation_result = self.flow_validator.validate_flow(flow_events)
            if not validation_result.is_valid:
                raise Exception(f"Flow validation failed: {validation_result.errors}")

            # Execute the flow sequence
            await self._run_flow_sequence()

            # Mark as successful
            self.execution_results.success = True
            self.execution_results.end_time = datetime.now().isoformat()
            
            self.logger.info("✅ Automation flow completed successfully")
            return self.execution_results

        except Exception as error:
            self.logger.error(f"❌ Automation flow execution failed: {error}")
            self.execution_results.success = False
            self.execution_results.end_time = datetime.now().isoformat()
            self.execution_results.errors.append({
                'message': str(error),
                'timestamp': datetime.now().isoformat(),
                'event_index': len(self.execution_results.errors)
            })
            return self.execution_results
        finally:
            self.is_executing = False

    async def _run_flow_sequence(self):
        """Execute the sequence of flow events"""
        for index, event in enumerate(self.flow_events):
            if not self.is_executing:
                break
                
            while self.is_paused:
                time.sleep(0.1)
                
            try:
                self.logger.info(f"Executing event {index + 1}/{len(self.flow_events)}: {event.get('type', 'unknown')}")
                
                # Highlight current event visually
                if event.get('selector'):
                    await self.visual_feedback.highlight_current_action(event['selector'], event.get('type', 'unknown'))
                
                # Execute the event
                await self._execute_event(event, index)
                
                self.execution_results.events_executed += 1
                
                # Add delay between events for visual feedback
                time.sleep(self.config.get('event_delay', 0.5))
                
            except Exception as error:
                self.logger.error(f"Error executing event {index}: {error}")
                self.execution_results.errors.append({
                    'event_index': index,
                    'event_type': event.get('type', 'unknown'),
                    'message': str(error),
                    'timestamp': datetime.now().isoformat()
                })
                
                # Check if this is a critical error
                if self._is_critical_error(error):
                    raise error
                
                # Continue with next event for non-critical errors
                continue

    async def _execute_event(self, event: Dict[str, Any], index: int):
        """Execute a single automation event"""
        event_type = event.get('type', '').lower()
        
        # Map event types to execution methods
        execution_map = {
            'click': self._execute_click_event,
            'input': self._execute_input_event,
            'wait': self._execute_wait_event,
            'navigate': self._execute_navigate_event,
            'extract': self._execute_extract_event,
            'scroll': self._execute_scroll_event,
            'hover': self._execute_hover_event,
            'select_option': self._execute_select_option_event,
            'form_fill': self._execute_form_fill_event,
            'screenshot': self._execute_screenshot_event,
            'wait_for_element': self._execute_wait_for_element_event,
            'if_then_else': self._execute_if_then_else_event,
            'loop': self._execute_loop_event,
            'variable_set': self._execute_variable_set_event,
            'data_extract_multiple': self._execute_data_extract_multiple_event,
            'text_search_click': self._execute_text_search_click_event,
            'popup_handler': self._execute_popup_handler_event,
            'wait_for_page_stability': self._execute_wait_for_page_stability_event,
            'open_to': self._execute_open_to_event,
            'alert_handle': self._execute_alert_handle_event,
            'post_login_sequence': self._execute_post_login_sequence_event,
            'text_search': self._execute_text_search_event,
            'text_search_navigate': self._execute_text_search_navigate_event,
            'keyboard': self._execute_keyboard_event,
            'prevent_redirect': self._execute_prevent_redirect_event
        }
        
        execution_method = execution_map.get(event_type)
        if execution_method:
            await execution_method(event)
        else:
            self.logger.warning(f"Unknown event type: {event_type}")

    async def _execute_click_event(self, event: Dict[str, Any]):
        """Execute a click event"""
        selector = event.get('selector')
        if not selector:
            raise Exception("Click event requires a selector")
        
        # Find element using enhanced targeting
        element = await self.element_finder.find_element_with_multiple_methods(
            selector, 
            event.get('selectorType', 'css'),
            event.get('alternatives', [])
        )
        
        if not element:
            raise Exception(f"Element not found: {selector}")
        
        # Ensure element is clickable
        await self._ensure_element_clickable(element)
        
        # Perform click with visual feedback
        await self.visual_feedback.highlight_element(element, 'click')
        
        # Handle different click types
        click_type = event.get('clickType', 'normal')
        if click_type == 'right':
            ActionChains(self.driver).context_click(element).perform()
        elif click_type == 'double':
            ActionChains(self.driver).double_click(element).perform()
        else:
            element.click()
        
        self.logger.info(f"Clicked element: {selector}")

    async def _execute_input_event(self, event: Dict[str, Any]):
        """Execute an input event"""
        selector = event.get('selector')
        value = event.get('value', '')
        
        if not selector:
            raise Exception("Input event requires a selector")
        
        # Process data mapping if present
        if event.get('dataMapping'):
            value = self._get_data_value(event['dataMapping'])
        
        # Process variable substitution
        value = self._process_variables(value)
        
        # Find element
        element = await self.element_finder.find_element_with_multiple_methods(selector)
        
        if not element:
            raise Exception(f"Input element not found: {selector}")
        
        # Clear existing value if specified
        if event.get('clearFirst', True):
            element.clear()
        
        # Visual feedback
        await self.visual_feedback.highlight_element(element, 'input')
        
        # Input the value with optional typing simulation
        if event.get('simulateTyping', False):
            await self._simulate_typing(element, value, event.get('typingDelay', 100))
        else:
            element.send_keys(value)
        
        self.logger.info(f"Input value '{value}' to element: {selector}")

    async def _execute_wait_event(self, event: Dict[str, Any]):
        """Execute a wait event"""
        duration = event.get('duration', 1000) / 1000  # Convert ms to seconds
        
        self.logger.info(f"Waiting for {duration} seconds")
        time.sleep(duration)

    async def _execute_navigate_event(self, event: Dict[str, Any]):
        """Execute a navigate event"""
        url = event.get('url')
        if not url:
            raise Exception("Navigate event requires a URL")
        
        # Process variable substitution
        url = self._process_variables(url)
        
        self.logger.info(f"Navigating to: {url}")
        self.driver.get(url)
        
        # Wait for page load if specified
        if event.get('waitForLoad', True):
            await self._wait_for_page_stability()

    async def _execute_open_to_event(self, event: Dict[str, Any]):
        """Execute an open_to event (same as navigate)"""
        await self._execute_navigate_event(event)

    async def _execute_extract_event(self, event: Dict[str, Any]):
        """Execute a data extraction event"""
        selector = event.get('selector')
        extraction_name = event.get('name', f'extract_{int(time.time())}')
        
        if not selector:
            raise Exception("Extract event requires a selector")
        
        element = await self.element_finder.find_element_with_multiple_methods(selector)
        if not element:
            raise Exception(f"Element not found for extraction: {selector}")
        
        # Extract data based on attribute
        attribute = event.get('attribute', 'text')
        if attribute == 'text':
            extracted_value = element.text
        elif attribute == 'value':
            extracted_value = element.get_attribute('value')
        else:
            extracted_value = element.get_attribute(attribute)
        
        # Apply transformations if specified
        if event.get('transform'):
            extracted_value = self._transform_value(extracted_value, event['transform'])
        
        # Store extracted data
        self.extracted_data[extraction_name] = extracted_value
        self.execution_results.extracted_data[extraction_name] = extracted_value
        
        # Store globally if specified
        if event.get('storeGlobally', False):
            self.variables[extraction_name] = extracted_value
        
        self.logger.info(f"Extracted data '{extraction_name}': {extracted_value}")

    async def _execute_if_then_else_event(self, event: Dict[str, Any]):
        """Execute conditional logic event"""
        condition = event.get('condition')
        if not condition:
            raise Exception("if_then_else event requires a condition")
        
        # Evaluate condition
        condition_result = await self._evaluate_condition(condition)
        
        # Execute appropriate branch
        if condition_result:
            then_events = event.get('thenEvents', [])
            if then_events:
                await self._execute_events(then_events, 0)
        else:
            else_events = event.get('elseEvents', [])
            if else_events:
                await self._execute_events(else_events, 0)

    async def _execute_loop_event(self, event: Dict[str, Any]):
        """Execute loop event"""
        iterations = event.get('iterations', 1)
        iteration_delay = event.get('iterationDelay', 0) / 1000
        continue_on_error = event.get('continueOnError', False)
        events = event.get('events', [])
        
        for i in range(iterations):
            self.loop_context['loopIndex'] = i
            self.variables['loopIndex'] = i
            
            try:
                await self._execute_events(events, 0)
                
                if iteration_delay > 0:
                    time.sleep(iteration_delay)
                    
            except Exception as error:
                if not continue_on_error:
                    raise error
                self.logger.warning(f"Loop iteration {i} failed: {error}")
                continue

    # Helper methods
    async def _ensure_element_clickable(self, element: WebElement):
        """Ensure element is clickable by scrolling into view and waiting"""
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.2)
        
        # Wait for element to be clickable
        try:
            WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(element)
            )
        except TimeoutException:
            # Element might still be clickable even if not detected as such
            pass

    async def _simulate_typing(self, element: WebElement, text: str, delay_ms: int = 100):
        """Simulate human typing with delays between keystrokes"""
        for char in text:
            element.send_keys(char)
            time.sleep(delay_ms / 1000)

    async def _wait_for_page_stability(self, timeout: int = 10):
        """Wait for page to be stable (DOM ready and no pending requests)"""
        WebDriverWait(self.driver, timeout).until(
            lambda driver: driver.execute_script("return document.readyState") == "complete"
        )
        
        # Additional wait for any dynamic content
        time.sleep(1)

    def _process_variables(self, value: str) -> str:
        """Process variable substitution in string values"""
        if not isinstance(value, str):
            return value
        
        # Replace variables in format {variableName}
        import re
        pattern = r'\{([^}]+)\}'
        
        def replace_var(match):
            var_name = match.group(1)
            return str(self.variables.get(var_name, f'{{{var_name}}}'))
        
        return re.sub(pattern, replace_var, value)

    def _get_data_value(self, path: str) -> Any:
        """Get value from automation data using dot notation path"""
        if not self.automation_data:
            return ""
        
        # Simple implementation - can be enhanced for complex paths
        parts = path.split('.')
        data = self.automation_data
        
        for part in parts:
            if '[' in part and ']' in part:
                # Handle array indexing
                array_name, index_part = part.split('[')
                index = int(index_part.rstrip(']'))
                data = data[array_name][index] if array_name else data[index]
            else:
                data = data.get(part, "") if isinstance(data, dict) else ""
        
        return data

    def _transform_value(self, value: Any, transform: Dict[str, Any]) -> Any:
        """Apply transformation to extracted value"""
        transform_type = transform.get('type', '')
        
        if transform_type == 'trim':
            return str(value).strip()
        elif transform_type == 'upper':
            return str(value).upper()
        elif transform_type == 'lower':
            return str(value).lower()
        elif transform_type == 'regex':
            pattern = transform.get('pattern', '')
            replacement = transform.get('replacement', '')
            return re.sub(pattern, replacement, str(value))
        
        return value

    async def _evaluate_condition(self, condition: Dict[str, Any]) -> bool:
        """Evaluate a condition for conditional logic"""
        condition_type = condition.get('type', '')
        
        if condition_type == 'element_exists':
            selector = condition.get('selector', '')
            try:
                element = await self.element_finder.find_element_with_multiple_methods(selector)
                if condition.get('visible', False):
                    return element is not None and element.is_displayed()
                return element is not None
            except:
                return False
        
        elif condition_type == 'url_contains':
            value = condition.get('value', '')
            return value in self.driver.current_url
        
        elif condition_type == 'element_text_contains':
            selector = condition.get('selector', '')
            value = condition.get('value', '')
            try:
                element = await self.element_finder.find_element_with_multiple_methods(selector)
                return value in element.text if element else False
            except:
                return False
        
        return False

    async def _execute_events(self, events: List[Dict], base_index: int):
        """Execute a list of events (used for loops and conditionals)"""
        for i, event in enumerate(events):
            await self._execute_event(event, base_index + i)

    def _is_critical_error(self, error: Exception) -> bool:
        """Determine if an error should stop execution"""
        critical_errors = [
            TimeoutException,
            NoSuchElementException
        ]
        return any(isinstance(error, err_type) for err_type in critical_errors)

    def _generate_execution_id(self) -> str:
        """Generate unique execution ID"""
        return f"exec_{int(time.time())}_{hash(str(self.flow_events)) % 10000}"

    def pause_automation(self):
        """Pause automation execution"""
        self.is_paused = True
        self.logger.info("Automation paused")

    def resume_automation(self):
        """Resume automation execution"""
        self.is_paused = False
        self.logger.info("Automation resumed")

    def stop_automation(self):
        """Stop automation execution"""
        self.is_executing = False
        self.is_paused = False
        self.logger.info("Automation stopped")

    # Additional event execution methods to be implemented...
    async def _execute_scroll_event(self, event: Dict[str, Any]):
        """Execute scroll event - placeholder for implementation"""
        pass

    async def _execute_hover_event(self, event: Dict[str, Any]):
        """Execute hover event - placeholder for implementation"""
        pass

    async def _execute_select_option_event(self, event: Dict[str, Any]):
        """Execute select option event - placeholder for implementation"""
        pass

    async def _execute_form_fill_event(self, event: Dict[str, Any]):
        """Execute form fill event - placeholder for implementation"""
        pass

    async def _execute_screenshot_event(self, event: Dict[str, Any]):
        """Execute screenshot event - placeholder for implementation"""
        pass

    async def _execute_wait_for_element_event(self, event: Dict[str, Any]):
        """Execute wait for element event - wait for element to appear or disappear"""
        selector = event.get('selector')
        timeout = event.get('timeout', 10000) / 1000  # Convert ms to seconds
        expect_visible = event.get('expectVisible', True)
        
        if not selector:
            raise Exception("wait_for_element event requires a selector")
        
        self.logger.info(f"Waiting for element: {selector} (visible: {expect_visible})")
        
        try:
            if expect_visible:
                # Wait for element to be visible
                element = WebDriverWait(self.driver, timeout).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, selector))
                )
                await self.visual_feedback.highlight_element(element, 'wait', 1.0)
            else:
                # Wait for element to be invisible or not present
                WebDriverWait(self.driver, timeout).until(
                    EC.invisibility_of_element_located((By.CSS_SELECTOR, selector))
                )
            
            self.logger.info(f"Element condition met: {selector}")
            
        except TimeoutException:
            raise Exception(f"Element condition not met within {timeout}s: {selector}")

    async def _execute_variable_set_event(self, event: Dict[str, Any]):
        """Execute variable set event - placeholder for implementation"""
        pass

    async def _execute_data_extract_multiple_event(self, event: Dict[str, Any]):
        """Execute multiple data extraction event - placeholder for implementation"""
        pass

    async def _execute_text_search_click_event(self, event: Dict[str, Any]):
        """Execute text search click event - placeholder for implementation"""
        pass

    async def _execute_popup_handler_event(self, event: Dict[str, Any]):
        """Execute popup handler event - handle modal dialogs and popups"""
        timeout = event.get('timeout', 10000) / 1000
        popup_selectors = event.get('popupSelectors', [])
        ok_button_selectors = event.get('okButtonSelectors', [])
        stabilize_delay = event.get('popupStabilizeDelay', 1000) / 1000
        dismissal_timeout = event.get('dismissalTimeout', 5000) / 1000
        
        self.logger.info("Handling popup dialogs")
        
        try:
            # First, wait for popup to appear
            popup_element = None
            for selector in popup_selectors:
                try:
                    popup_element = WebDriverWait(self.driver, timeout).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    self.logger.info(f"Popup found with selector: {selector}")
                    break
                except TimeoutException:
                    continue
            
            if popup_element:
                # Wait for popup to stabilize
                if stabilize_delay > 0:
                    time.sleep(stabilize_delay)
                
                # Highlight the popup
                await self.visual_feedback.highlight_element(popup_element, 'wait', 1.0)
                
                # Try to find and click OK button
                ok_button = None
                for ok_selector in ok_button_selectors:
                    try:
                        ok_button = WebDriverWait(self.driver, dismissal_timeout).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, ok_selector))
                        )
                        self.logger.info(f"OK button found with selector: {ok_selector}")
                        break
                    except TimeoutException:
                        continue
                
                if ok_button:
                    # Highlight and click OK button
                    await self.visual_feedback.highlight_element(ok_button, 'click', 0.5)
                    ok_button.click()
                    self.logger.info("Popup dismissed by clicking OK button")
                    
                    # Wait a bit for popup to close
                    time.sleep(0.5)
                else:
                    self.logger.warning("Could not find OK button to dismiss popup")
            else:
                self.logger.info("No popup found within timeout period")
                
        except Exception as e:
            self.logger.warning(f"Error handling popup: {e}")

    async def _execute_wait_for_page_stability_event(self, event: Dict[str, Any]):
        """Execute wait for page stability event - placeholder for implementation"""
        pass

    async def _execute_alert_handle_event(self, event: Dict[str, Any]):
        """Execute alert handle event - placeholder for implementation"""
        pass

    async def _execute_post_login_sequence_event(self, event: Dict[str, Any]):
        """Execute post login sequence event - placeholder for implementation"""
        pass

    async def _execute_text_search_event(self, event: Dict[str, Any]):
        """Execute text search event - placeholder for implementation"""
        pass

    async def _execute_text_search_navigate_event(self, event: Dict[str, Any]):
        """Execute text search navigate event - placeholder for implementation"""
        pass

    async def _execute_keyboard_event(self, event: Dict[str, Any]):
        """Execute keyboard event - send keys to an element"""
        selector = event.get('selector')
        key = event.get('key', '')
        wait_after_key = event.get('waitAfterKey', 0) / 1000  # Convert ms to seconds
        prevent_default = event.get('preventDefault', False)
        
        if not selector or not key:
            raise Exception("Keyboard event requires both selector and key")
        
        # Find element
        element = await self.element_finder.find_element_with_multiple_methods(
            selector, 
            event.get('selectorType', 'css')
        )
        
        if not element:
            raise Exception(f"Element not found for keyboard input: {selector}")
        
        # Visual feedback
        await self.visual_feedback.highlight_element(element, 'input')
        
        # Map key names to Selenium key constants
        key_mapping = {
            'Enter': Keys.ENTER,
            'Return': Keys.RETURN,
            'Tab': Keys.TAB,
            'Space': Keys.SPACE,
            'Escape': Keys.ESCAPE,
            'Backspace': Keys.BACKSPACE,
            'Delete': Keys.DELETE,
            'ArrowUp': Keys.ARROW_UP,
            'ArrowDown': Keys.ARROW_DOWN,
            'ArrowLeft': Keys.ARROW_LEFT,
            'ArrowRight': Keys.ARROW_RIGHT,
            'Home': Keys.HOME,
            'End': Keys.END,
            'PageUp': Keys.PAGE_UP,
            'PageDown': Keys.PAGE_DOWN,
            'F1': Keys.F1, 'F2': Keys.F2, 'F3': Keys.F3, 'F4': Keys.F4,
            'F5': Keys.F5, 'F6': Keys.F6, 'F7': Keys.F7, 'F8': Keys.F8,
            'F9': Keys.F9, 'F10': Keys.F10, 'F11': Keys.F11, 'F12': Keys.F12,
            'Shift': Keys.SHIFT,
            'Control': Keys.CONTROL,
            'Alt': Keys.ALT,
            'Meta': Keys.META
        }
        
        # Get the key to send
        selenium_key = key_mapping.get(key, key)
        
        # If prevent_default is enabled, we might need to use JavaScript to prevent default behavior
        if prevent_default:
            try:
                self.driver.execute_script("""
                    arguments[0].addEventListener('keydown', function(e) {
                        if (e.key === arguments[1]) {
                            e.preventDefault();
                        }
                    }, {once: true});
                """, element, key)
            except Exception as e:
                self.logger.warning(f"Could not set preventDefault for key event: {e}")
        
        # Send the key
        try:
            element.send_keys(selenium_key)
            self.logger.info(f"Sent key '{key}' to element: {selector}")
        except Exception as e:
            # If direct send_keys fails, try using ActionChains
            try:
                ActionChains(self.driver).click(element).send_keys(selenium_key).perform()
                self.logger.info(f"Sent key '{key}' to element using ActionChains: {selector}")
            except Exception as e2:
                raise Exception(f"Failed to send key '{key}' to element: {e2}")
        
        # Wait after key if specified
        if wait_after_key > 0:
            time.sleep(wait_after_key)

    async def _execute_prevent_redirect_event(self, event: Dict[str, Any]):
        """Execute prevent redirect event - block page navigation temporarily"""
        timeout = event.get('timeout', 3000) / 1000  # Convert ms to seconds
        block_methods = event.get('blockMethods', [])
        allow_manual_navigation = event.get('allowManualNavigation', False)
        
        self.logger.info(f"Setting up redirect prevention for {timeout} seconds")
        
        # JavaScript to prevent various types of redirects
        prevent_redirect_script = """
        window.seleniumAutoFillPreventRedirect = {
            originalMethods: {},
            blockMethods: arguments[0],
            allowManual: arguments[1],
            startTime: Date.now(),
            timeout: arguments[2] * 1000,
            
            init: function() {
                var self = this;
                
                // Block location changes
                if (this.blockMethods.includes('location.href')) {
                    this.originalMethods.locationHref = Object.getOwnPropertyDescriptor(Location.prototype, 'href');
                    Object.defineProperty(location, 'href', {
                        get: function() { return self.originalMethods.locationHref.get.call(this); },
                        set: function(value) {
                            if (!self.shouldAllow()) {
                                console.log('Selenium AutoFill: Blocked location.href redirect to', value);
                                return;
                            }
                            self.originalMethods.locationHref.set.call(this, value);
                        }
                    });
                }
                
                // Block location.assign
                if (this.blockMethods.includes('location.assign')) {
                    this.originalMethods.locationAssign = location.assign;
                    location.assign = function(url) {
                        if (!self.shouldAllow()) {
                            console.log('Selenium AutoFill: Blocked location.assign to', url);
                            return;
                        }
                        self.originalMethods.locationAssign.call(this, url);
                    };
                }
                
                // Block location.replace
                if (this.blockMethods.includes('location.replace')) {
                    this.originalMethods.locationReplace = location.replace;
                    location.replace = function(url) {
                        if (!self.shouldAllow()) {
                            console.log('Selenium AutoFill: Blocked location.replace to', url);
                            return;
                        }
                        self.originalMethods.locationReplace.call(this, url);
                    };
                }
                
                // Block form submissions
                if (this.blockMethods.includes('form_submit')) {
                    document.addEventListener('submit', function(e) {
                        if (!self.shouldAllow()) {
                            console.log('Selenium AutoFill: Blocked form submission');
                            e.preventDefault();
                            e.stopPropagation();
                        }
                    }, true);
                }
                
                // Block meta refresh
                if (this.blockMethods.includes('meta_refresh')) {
                    var metaTags = document.querySelectorAll('meta[http-equiv="refresh"]');
                    metaTags.forEach(function(meta) {
                        if (!self.shouldAllow()) {
                            console.log('Selenium AutoFill: Blocked meta refresh');
                            meta.remove();
                        }
                    });
                }
                
                // Auto-cleanup after timeout
                setTimeout(function() {
                    self.cleanup();
                }, this.timeout);
            },
            
            shouldAllow: function() {
                var elapsed = Date.now() - this.startTime;
                if (elapsed > this.timeout) {
                    this.cleanup();
                    return true;
                }
                return this.allowManual;
            },
            
            cleanup: function() {
                console.log('Selenium AutoFill: Cleaning up redirect prevention');
                
                // Restore original methods
                if (this.originalMethods.locationHref) {
                    Object.defineProperty(location, 'href', this.originalMethods.locationHref);
                }
                if (this.originalMethods.locationAssign) {
                    location.assign = this.originalMethods.locationAssign;
                }
                if (this.originalMethods.locationReplace) {
                    location.replace = this.originalMethods.locationReplace;
                }
                
                delete window.seleniumAutoFillPreventRedirect;
            }
        };
        
        window.seleniumAutoFillPreventRedirect.init();
        """
        
        try:
            # Execute the script to set up redirect prevention
            self.driver.execute_script(
                prevent_redirect_script, 
                block_methods, 
                allow_manual_navigation, 
                timeout
            )
            
            self.logger.info(f"Redirect prevention active for {timeout} seconds")
            
        except Exception as e:
            self.logger.warning(f"Failed to set up redirect prevention: {e}") 