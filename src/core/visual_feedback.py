"""
Visual Feedback System - Real-time visual indicators for automation
Provides highlighting and visual feedback during automation execution
"""

import time
import json
from typing import Dict, List, Any, Optional
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.action_chains import ActionChains


class VisualFeedback:
    """Provides visual feedback during automation execution"""
    
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        self.injected_styles = False
        self.active_highlights = []
        
        # Inject CSS styles for visual feedback
        self._inject_visual_styles()

    def _inject_visual_styles(self):
        """Inject CSS styles for visual feedback"""
        if self.injected_styles:
            return
        
        css_styles = """
        <style id="selenium-autofill-styles">
        .selenium-highlight {
            outline: 3px solid #ff6b6b !important;
            outline-offset: 2px !important;
            background-color: rgba(255, 107, 107, 0.1) !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 0 10px rgba(255, 107, 107, 0.5) !important;
        }
        
        .selenium-highlight-click {
            outline: 3px solid #4ecdc4 !important;
            outline-offset: 2px !important;
            background-color: rgba(78, 205, 196, 0.2) !important;
            animation: selenium-click-pulse 0.6s ease !important;
        }
        
        .selenium-highlight-input {
            outline: 3px solid #45b7d1 !important;
            outline-offset: 2px !important;
            background-color: rgba(69, 183, 209, 0.15) !important;
            animation: selenium-input-glow 1s ease !important;
        }
        
        .selenium-highlight-extract {
            outline: 3px solid #96ceb4 !important;
            outline-offset: 2px !important;
            background-color: rgba(150, 206, 180, 0.2) !important;
            animation: selenium-extract-fade 0.8s ease !important;
        }
        
        .selenium-highlight-wait {
            outline: 3px solid #feca57 !important;
            outline-offset: 2px !important;
            background-color: rgba(254, 202, 87, 0.15) !important;
            animation: selenium-wait-blink 2s ease infinite !important;
        }
        
        .selenium-progress-indicator {
            position: fixed !important;
            top: 20px !important;
            right: 20px !important;
            background: rgba(0, 0, 0, 0.8) !important;
            color: white !important;
            padding: 15px 20px !important;
            border-radius: 8px !important;
            font-family: Arial, sans-serif !important;
            font-size: 14px !important;
            z-index: 10000 !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
            min-width: 250px !important;
        }
        
        .selenium-step-indicator {
            position: fixed !important;
            top: 80px !important;
            right: 20px !important;
            background: rgba(52, 152, 219, 0.9) !important;
            color: white !important;
            padding: 10px 15px !important;
            border-radius: 6px !important;
            font-family: Arial, sans-serif !important;
            font-size: 12px !important;
            z-index: 9999 !important;
            max-width: 300px !important;
            word-wrap: break-word !important;
        }
        
        .selenium-error-indicator {
            position: fixed !important;
            top: 140px !important;
            right: 20px !important;
            background: rgba(231, 76, 60, 0.9) !important;
            color: white !important;
            padding: 10px 15px !important;
            border-radius: 6px !important;
            font-family: Arial, sans-serif !important;
            font-size: 12px !important;
            z-index: 9998 !important;
            max-width: 300px !important;
            word-wrap: break-word !important;
        }
        
        @keyframes selenium-click-pulse {
            0% { 
                transform: scale(1); 
                outline-width: 3px; 
            }
            50% { 
                transform: scale(1.02); 
                outline-width: 5px;
                outline-color: #26d0ce;
            }
            100% { 
                transform: scale(1); 
                outline-width: 3px; 
            }
        }
        
        @keyframes selenium-input-glow {
            0% { 
                outline-color: #45b7d1;
                background-color: rgba(69, 183, 209, 0.15);
            }
            50% { 
                outline-color: #74b9ff;
                background-color: rgba(116, 185, 255, 0.25);
            }
            100% { 
                outline-color: #45b7d1;
                background-color: rgba(69, 183, 209, 0.15);
            }
        }
        
        @keyframes selenium-extract-fade {
            0% { 
                background-color: rgba(150, 206, 180, 0.4);
                outline-width: 5px;
            }
            100% { 
                background-color: rgba(150, 206, 180, 0.2);
                outline-width: 3px;
            }
        }
        
        @keyframes selenium-wait-blink {
            0%, 100% { 
                opacity: 1; 
                outline-color: #feca57;
            }
            50% { 
                opacity: 0.6; 
                outline-color: #ff9ff3;
            }
        }
        
        .selenium-automation-badge {
            position: fixed !important;
            top: 10px !important;
            left: 50% !important;
            transform: translateX(-50%) !important;
            background: linear-gradient(45deg, #667eea 0%, #764ba2 100%) !important;
            color: white !important;
            padding: 8px 20px !important;
            border-radius: 20px !important;
            font-family: Arial, sans-serif !important;
            font-size: 13px !important;
            font-weight: bold !important;
            z-index: 10001 !important;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2) !important;
            animation: selenium-badge-float 3s ease-in-out infinite !important;
        }
        
        @keyframes selenium-badge-float {
            0%, 100% { transform: translateX(-50%) translateY(0px); }
            50% { transform: translateX(-50%) translateY(-5px); }
        }
        </style>
        """
        
        # Inject styles into page
        try:
            self.driver.execute_script(f"""
                if (!document.getElementById('selenium-autofill-styles')) {{
                    document.head.insertAdjacentHTML('beforeend', `{css_styles}`);
                }}
            """)
            self.injected_styles = True
        except Exception as e:
            print(f"Failed to inject visual styles: {e}")

    async def highlight_element(self, element: WebElement, action_type: str = "default", duration: float = 1.0):
        """Highlight an element with visual feedback based on action type"""
        if not element:
            return
        
        try:
            # Remove any existing highlights from this element
            self._remove_highlight_from_element(element)
            
            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", element)
            time.sleep(0.3)
            
            # Apply highlight class based on action type
            highlight_class = self._get_highlight_class(action_type)
            
            self.driver.execute_script(f"""
                arguments[0].classList.add('{highlight_class}');
                arguments[0].setAttribute('data-selenium-highlighted', 'true');
            """, element)
            
            # Store for cleanup
            self.active_highlights.append(element)
            
            # Auto-remove highlight after duration
            if duration > 0:
                self.driver.execute_script(f"""
                    setTimeout(function() {{
                        if (arguments[0] && arguments[0].classList) {{
                            arguments[0].classList.remove('{highlight_class}');
                            arguments[0].removeAttribute('data-selenium-highlighted');
                        }}
                    }}, {int(duration * 1000)});
                """, element)
                
        except Exception as e:
            print(f"Error highlighting element: {e}")

    async def highlight_current_action(self, selector: str, action_type: str = "default"):
        """Highlight the current action being performed"""
        try:
            # Show step indicator
            self._show_step_indicator(f"Performing {action_type} on: {selector}")
            
            # If we can find the element, highlight it
            try:
                from selenium.webdriver.common.by import By
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                await self.highlight_element(element, action_type, duration=0.8)
            except:
                # Element might not be found yet, that's okay
                pass
                
        except Exception as e:
            print(f"Error in highlight_current_action: {e}")

    def show_progress_indicator(self, current_step: int, total_steps: int, current_action: str = ""):
        """Show automation progress indicator"""
        progress_percent = (current_step / total_steps) * 100 if total_steps > 0 else 0
        
        progress_html = f"""
        <div id="selenium-progress" class="selenium-progress-indicator">
            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                <div style="width: 20px; height: 20px; border-radius: 50%; background: #4ecdc4; margin-right: 10px; display: flex; align-items: center; justify-content: center;">
                    <span style="color: white; font-size: 10px; font-weight: bold;">✓</span>
                </div>
                <span style="font-weight: bold;">Selenium AutoFill Active</span>
            </div>
            <div style="margin-bottom: 5px;">
                Step {current_step} of {total_steps} ({progress_percent:.1f}%)
            </div>
            <div style="background: rgba(255,255,255,0.2); height: 6px; border-radius: 3px; overflow: hidden;">
                <div style="background: #4ecdc4; height: 100%; width: {progress_percent}%; transition: width 0.3s ease;"></div>
            </div>
            {f'<div style="margin-top: 8px; font-size: 11px; opacity: 0.8;">{current_action}</div>' if current_action else ''}
        </div>
        """
        
        try:
            self.driver.execute_script(f"""
                // Remove existing progress indicator
                var existing = document.getElementById('selenium-progress');
                if (existing) existing.remove();
                
                // Add new progress indicator
                document.body.insertAdjacentHTML('beforeend', `{progress_html}`);
            """)
        except Exception as e:
            print(f"Error showing progress indicator: {e}")

    def _show_step_indicator(self, step_description: str):
        """Show current step indicator"""
        step_html = f"""
        <div id="selenium-step" class="selenium-step-indicator">
            {step_description}
        </div>
        """
        
        try:
            self.driver.execute_script(f"""
                // Remove existing step indicator
                var existing = document.getElementById('selenium-step');
                if (existing) existing.remove();
                
                // Add new step indicator
                document.body.insertAdjacentHTML('beforeend', `{step_html}`);
                
                // Auto-remove after 3 seconds
                setTimeout(function() {{
                    var indicator = document.getElementById('selenium-step');
                    if (indicator) indicator.remove();
                }}, 3000);
            """)
        except Exception as e:
            print(f"Error showing step indicator: {e}")

    def show_error_indicator(self, error_message: str, duration: int = 5000):
        """Show error indicator"""
        error_html = f"""
        <div id="selenium-error" class="selenium-error-indicator">
            <div style="font-weight: bold; margin-bottom: 5px;">⚠️ Automation Error</div>
            <div style="font-size: 11px;">{error_message}</div>
        </div>
        """
        
        try:
            self.driver.execute_script(f"""
                // Remove existing error indicator
                var existing = document.getElementById('selenium-error');
                if (existing) existing.remove();
                
                // Add new error indicator
                document.body.insertAdjacentHTML('beforeend', `{error_html}`);
                
                // Auto-remove after duration
                setTimeout(function() {{
                    var indicator = document.getElementById('selenium-error');
                    if (indicator) indicator.remove();
                }}, {duration});
            """)
        except Exception as e:
            print(f"Error showing error indicator: {e}")

    def show_automation_badge(self):
        """Show automation active badge"""
        badge_html = """
        <div id="selenium-badge" class="selenium-automation-badge">
            🤖 Selenium AutoFill Active
        </div>
        """
        
        try:
            self.driver.execute_script(f"""
                if (!document.getElementById('selenium-badge')) {{
                    document.body.insertAdjacentHTML('beforeend', `{badge_html}`);
                }}
            """)
        except Exception as e:
            print(f"Error showing automation badge: {e}")

    def hide_automation_badge(self):
        """Hide automation badge"""
        try:
            self.driver.execute_script("""
                var badge = document.getElementById('selenium-badge');
                if (badge) badge.remove();
            """)
        except Exception as e:
            print(f"Error hiding automation badge: {e}")

    def clear_all_indicators(self):
        """Clear all visual indicators"""
        try:
            self.driver.execute_script("""
                // Remove all selenium indicators
                ['selenium-progress', 'selenium-step', 'selenium-error', 'selenium-badge'].forEach(function(id) {
                    var element = document.getElementById(id);
                    if (element) element.remove();
                });
                
                // Remove all highlights
                document.querySelectorAll('[data-selenium-highlighted]').forEach(function(element) {
                    element.classList.remove('selenium-highlight', 'selenium-highlight-click', 
                                           'selenium-highlight-input', 'selenium-highlight-extract', 
                                           'selenium-highlight-wait');
                    element.removeAttribute('data-selenium-highlighted');
                });
            """)
            
            self.active_highlights.clear()
            
        except Exception as e:
            print(f"Error clearing indicators: {e}")

    def _get_highlight_class(self, action_type: str) -> str:
        """Get appropriate highlight class for action type"""
        action_class_map = {
            'click': 'selenium-highlight-click',
            'input': 'selenium-highlight-input',
            'extract': 'selenium-highlight-extract',
            'wait': 'selenium-highlight-wait',
            'default': 'selenium-highlight'
        }
        
        return action_class_map.get(action_type.lower(), 'selenium-highlight')

    def _remove_highlight_from_element(self, element: WebElement):
        """Remove highlight classes from specific element"""
        try:
            self.driver.execute_script("""
                arguments[0].classList.remove('selenium-highlight', 'selenium-highlight-click', 
                                           'selenium-highlight-input', 'selenium-highlight-extract', 
                                           'selenium-highlight-wait');
                arguments[0].removeAttribute('data-selenium-highlighted');
            """, element)
        except Exception as e:
            print(f"Error removing highlight: {e}")

    def flash_element(self, element: WebElement, color: str = "#ff6b6b", duration: float = 0.5):
        """Flash an element with a specific color"""
        try:
            original_style = element.get_attribute('style') or ''
            
            # Apply flash effect
            self.driver.execute_script(f"""
                arguments[0].style.cssText = arguments[1] + 
                    '; outline: 3px solid {color}; outline-offset: 2px; ' +
                    'background-color: {color}33; transition: all 0.1s;';
            """, element, original_style)
            
            time.sleep(duration)
            
            # Restore original style
            self.driver.execute_script(f"""
                arguments[0].style.cssText = arguments[1];
            """, element, original_style)
            
        except Exception as e:
            print(f"Error flashing element: {e}")

    def create_element_overlay(self, element: WebElement, text: str, overlay_type: str = "info"):
        """Create a temporary overlay on an element"""
        try:
            # Get element position and size
            location = element.location
            size = element.size
            
            # Create overlay
            overlay_html = f"""
            <div id="selenium-overlay-{int(time.time())}" style="
                position: absolute;
                left: {location['x']}px;
                top: {location['y'] - 30}px;
                background: {'#4ecdc4' if overlay_type == 'info' else '#ff6b6b'};
                color: white;
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 12px;
                font-family: Arial, sans-serif;
                z-index: 10000;
                pointer-events: none;
                animation: fadeInOut 2s ease-in-out;
            ">
                {text}
            </div>
            """
            
            self.driver.execute_script(f"""
                // Add fadeInOut animation if not exists
                if (!document.getElementById('selenium-overlay-styles')) {{
                    document.head.insertAdjacentHTML('beforeend', `
                        <style id="selenium-overlay-styles">
                        @keyframes fadeInOut {{
                            0% {{ opacity: 0; transform: translateY(10px); }}
                            20%, 80% {{ opacity: 1; transform: translateY(0); }}
                            100% {{ opacity: 0; transform: translateY(-10px); }}
                        }}
                        </style>
                    `);
                }}
                
                // Add overlay
                document.body.insertAdjacentHTML('beforeend', `{overlay_html}`);
                
                // Auto-remove after animation
                setTimeout(function() {{
                    var overlay = document.querySelector('[id^="selenium-overlay-"]');
                    if (overlay) overlay.remove();
                }}, 2000);
            """)
            
        except Exception as e:
            print(f"Error creating element overlay: {e}")

    def show_success_notification(self, message: str):
        """Show success notification"""
        self._show_notification(message, "success", "#4ecdc4")

    def show_warning_notification(self, message: str):
        """Show warning notification"""
        self._show_notification(message, "warning", "#feca57")

    def show_error_notification(self, message: str):
        """Show error notification"""
        self._show_notification(message, "error", "#ff6b6b")

    def _show_notification(self, message: str, notification_type: str, color: str):
        """Show a temporary notification"""
        icon_map = {
            "success": "✅",
            "warning": "⚠️",
            "error": "❌"
        }
        
        icon = icon_map.get(notification_type, "ℹ️")
        
        notification_html = f"""
        <div id="selenium-notification" style="
            position: fixed;
            top: 50px;
            left: 50%;
            transform: translateX(-50%);
            background: {color};
            color: white;
            padding: 12px 20px;
            border-radius: 6px;
            font-family: Arial, sans-serif;
            font-size: 14px;
            z-index: 10002;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            animation: slideInOut 3s ease-in-out;
        ">
            {icon} {message}
        </div>
        """
        
        try:
            self.driver.execute_script(f"""
                // Add animation styles if not exists
                if (!document.getElementById('selenium-notification-styles')) {{
                    document.head.insertAdjacentHTML('beforeend', `
                        <style id="selenium-notification-styles">
                        @keyframes slideInOut {{
                            0% {{ opacity: 0; transform: translateX(-50%) translateY(-20px); }}
                            15%, 85% {{ opacity: 1; transform: translateX(-50%) translateY(0); }}
                            100% {{ opacity: 0; transform: translateX(-50%) translateY(-20px); }}
                        }}
                        </style>
                    `);
                }}
                
                // Remove existing notification
                var existing = document.getElementById('selenium-notification');
                if (existing) existing.remove();
                
                // Add new notification
                document.body.insertAdjacentHTML('beforeend', `{notification_html}`);
                
                // Auto-remove
                setTimeout(function() {{
                    var notification = document.getElementById('selenium-notification');
                    if (notification) notification.remove();
                }}, 3000);
            """)
        except Exception as e:
            print(f"Error showing notification: {e}")

    def cleanup(self):
        """Clean up all visual feedback elements"""
        self.clear_all_indicators()
        self.hide_automation_badge()
        
        try:
            # Remove injected styles
            self.driver.execute_script("""
                var styles = document.getElementById('selenium-autofill-styles');
                if (styles) styles.remove();
                
                var overlayStyles = document.getElementById('selenium-overlay-styles');
                if (overlayStyles) overlayStyles.remove();
                
                var notificationStyles = document.getElementById('selenium-notification-styles');
                if (notificationStyles) notificationStyles.remove();
            """)
        except Exception as e:
            print(f"Error during cleanup: {e}") 