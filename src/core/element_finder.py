"""
Element Finder - Enhanced element targeting system
Replicates the sophisticated element finding capabilities from the Chrome extension
"""

import time
import re
from typing import Dict, List, Any, Optional, Union, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup


class ElementFinder:
    """Advanced element finding with multiple targeting strategies"""
    
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        self.default_timeout = 15  # Increased from 10 to 15 for better stability

    async def find_element_with_multiple_methods(
        self, 
        primary_selector: str, 
        selector_type: str = 'css',
        alternatives: List[Dict[str, str]] = None,
        timeout: int = None
    ) -> Optional[WebElement]:
        """
        Find element using multiple targeting methods with fallbacks
        Replicates the extension's findElementWithMultipleMethods function
        """
        timeout = timeout or self.default_timeout
        alternatives = alternatives or []
        
        # Try primary selector first
        element = await self._try_find_element(primary_selector, selector_type, timeout)
        if element:
            return element
        
        # Try alternative selectors
        for alt in alternatives:
            alt_selector = alt.get('selector', '')
            alt_type = alt.get('type', 'css')
            
            if alt_selector:
                element = await self._try_find_element(alt_selector, alt_type, timeout)
                if element:
                    return element
        
        # Try text-based search if the selector looks like text
        if self._looks_like_text_search(primary_selector):
            element = await self.find_element_by_text_advanced(primary_selector)
            if element:
                return element
        
        # Try attribute-based search
        if '=' in primary_selector:
            element = await self._try_attribute_search(primary_selector, timeout)
            if element:
                return element
        
        return None

    async def _try_find_element(
        self, 
        selector: str, 
        selector_type: str, 
        timeout: int
    ) -> Optional[WebElement]:
        """Try to find element with specific selector type"""
        try:
            if selector_type.lower() == 'css':
                return await self.find_element_by_css_selector(selector, timeout)
            elif selector_type.lower() == 'xpath':
                return await self.find_element_by_xpath(selector, timeout)
            elif selector_type.lower() == 'text':
                return await self.find_element_by_text_content(selector, timeout)
            elif selector_type.lower() == 'attribute':
                return await self._parse_and_find_by_attribute(selector, timeout)
            else:
                # Default to CSS
                return await self.find_element_by_css_selector(selector, timeout)
        except Exception:
            return None

    async def find_element_by_css_selector(self, selector: str, timeout: int = None) -> Optional[WebElement]:
        """Find element by CSS selector with wait"""
        timeout = timeout or self.default_timeout
        
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            return element
        except TimeoutException:
            return None

    async def find_element_by_xpath(self, xpath: str, timeout: int = None) -> Optional[WebElement]:
        """Find element by XPath with wait"""
        timeout = timeout or self.default_timeout
        
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            return element
        except TimeoutException:
            return None

    async def find_element_by_text_content(
        self, 
        text_config: Union[str, Dict[str, Any]], 
        timeout: int = None
    ) -> Optional[WebElement]:
        """Find element by text content with advanced matching"""
        timeout = timeout or self.default_timeout
        
        if isinstance(text_config, str):
            search_text = text_config
            exact_match = False
            case_sensitive = False
        else:
            search_text = text_config.get('text', '')
            exact_match = text_config.get('exactMatch', False)
            case_sensitive = text_config.get('caseSensitive', False)
        
        if not search_text:
            return None
        
        # Try different text-based XPath strategies
        xpaths = self._generate_text_xpaths(search_text, exact_match, case_sensitive)
        
        for xpath in xpaths:
            try:
                element = WebDriverWait(self.driver, timeout // len(xpaths)).until(
                    EC.presence_of_element_located((By.XPATH, xpath))
                )
                if element and element.is_displayed():
                    return element
            except TimeoutException:
                continue
        
        return None

    async def find_element_by_text_advanced(
        self, 
        search_text: str, 
        options: Dict[str, Any] = None
    ) -> Optional[WebElement]:
        """
        Advanced text search similar to the extension's findElementByTextAdvanced
        """
        options = options or {}
        timeout = options.get('timeout', 3000) / 1000
        exact_match = options.get('exactMatch', False)
        case_sensitive = options.get('caseSensitive', False)
        include_buttons = options.get('includeButtons', True)
        include_links = options.get('includeLinks', True)
        include_inputs = options.get('includeInputs', True)
        
        # Process search text
        if not case_sensitive:
            search_text = search_text.lower()
        
        # Get page source and parse with BeautifulSoup for better text matching
        page_source = self.driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Define target tags based on options
        target_tags = []
        if include_buttons:
            target_tags.extend(['button', 'input[type="button"]', 'input[type="submit"]'])
        if include_links:
            target_tags.append('a')
        if include_inputs:
            target_tags.extend(['input', 'textarea', 'select'])
        
        # Add common interactive elements
        target_tags.extend(['span', 'div', 'p', 'td', 'th', 'li'])
        
        # Search for elements
        candidates = []
        
        for tag in target_tags:
            elements = soup.select(tag) if '[' not in tag else soup.select(tag.split('[')[0])
            
            for elem in elements:
                text_content = elem.get_text().strip()
                if not case_sensitive:
                    text_content = text_content.lower()
                
                if exact_match:
                    if text_content == search_text:
                        candidates.append(elem)
                else:
                    if search_text in text_content:
                        candidates.append(elem)
        
        # Convert BeautifulSoup elements back to Selenium elements
        for candidate in candidates:
            # Generate XPath for the candidate
            xpath = self._generate_xpath_for_soup_element(candidate)
            if xpath:
                try:
                    selenium_element = self.driver.find_element(By.XPATH, xpath)
                    if selenium_element and selenium_element.is_displayed():
                        return selenium_element
                except NoSuchElementException:
                    continue
        
        return None

    async def find_elements_by_text(
        self, 
        search_text: str, 
        options: Dict[str, Any] = None
    ) -> List[WebElement]:
        """Find multiple elements by text content"""
        options = options or {}
        max_results = options.get('maxResults', 10)
        
        elements = []
        xpaths = self._generate_text_xpaths(search_text, 
                                          options.get('exactMatch', False),
                                          options.get('caseSensitive', False))
        
        for xpath in xpaths:
            try:
                found_elements = self.driver.find_elements(By.XPATH, xpath)
                for elem in found_elements:
                    if elem.is_displayed() and len(elements) < max_results:
                        elements.append(elem)
            except Exception:
                continue
        
        return elements

    async def quick_text_search(self, search_text: str, timeout: int = 1) -> Optional[WebElement]:
        """Quick text search for immediate feedback"""
        if not search_text:
            return None
        
        # Simple XPath for quick search
        xpath = f"//*[contains(text(), '{search_text}')]"
        
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            return element if element.is_displayed() else None
        except TimeoutException:
            return None

    def _generate_text_xpaths(
        self, 
        search_text: str, 
        exact_match: bool = False, 
        case_sensitive: bool = False
    ) -> List[str]:
        """Generate various XPath expressions for text searching"""
        xpaths = []
        
        # Escape quotes in search text
        escaped_text = search_text.replace("'", "\\'").replace('"', '\\"')
        
        if exact_match:
            if case_sensitive:
                xpaths.extend([
                    f"//*[text()='{escaped_text}']",
                    f"//button[text()='{escaped_text}']",
                    f"//a[text()='{escaped_text}']",
                    f"//input[@value='{escaped_text}']",
                    f"//span[text()='{escaped_text}']"
                ])
            else:
                # Case insensitive exact match
                lower_text = escaped_text.lower()
                xpaths.extend([
                    f"//*[translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')='{lower_text}']",
                    f"//button[translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')='{lower_text}']"
                ])
        else:
            if case_sensitive:
                xpaths.extend([
                    f"//*[contains(text(), '{escaped_text}')]",
                    f"//button[contains(text(), '{escaped_text}')]",
                    f"//a[contains(text(), '{escaped_text}')]",
                    f"//input[contains(@value, '{escaped_text}')]",
                    f"//span[contains(text(), '{escaped_text}')]",
                    f"//div[contains(text(), '{escaped_text}')]",
                    f"//td[contains(text(), '{escaped_text}')]",
                    f"//th[contains(text(), '{escaped_text}')]"
                ])
            else:
                # Case insensitive contains
                lower_text = escaped_text.lower()
                xpaths.extend([
                    f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{lower_text}')]",
                    f"//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{lower_text}')]"
                ])
        
        return xpaths

    def _generate_xpath_for_soup_element(self, soup_element) -> Optional[str]:
        """Generate XPath for a BeautifulSoup element"""
        try:
            # Simple approach: use tag name and attributes
            tag = soup_element.name
            if not tag:
                return None
            
            # Build XPath based on element attributes
            xpath_parts = [f"//{tag}"]
            
            # Add ID if present
            if soup_element.get('id'):
                xpath_parts = [f"//{tag}[@id='{soup_element['id']}']"]
                return xpath_parts[0]
            
            # Add class if present
            if soup_element.get('class'):
                classes = ' '.join(soup_element['class'])
                xpath_parts = [f"//{tag}[@class='{classes}']"]
                return xpath_parts[0]
            
            # Use text content for identification
            text = soup_element.get_text().strip()
            if text and len(text) < 100:  # Avoid very long text
                escaped_text = text.replace("'", "\\'")
                xpath_parts = [f"//{tag}[text()='{escaped_text}']"]
                return xpath_parts[0]
            
            return None
        except Exception:
            return None

    async def _try_attribute_search(self, selector: str, timeout: int) -> Optional[WebElement]:
        """Try to find element by attribute value"""
        if '=' not in selector:
            return None
        
        try:
            # Parse attribute search (e.g., "data-id=123" or "name=username")
            if selector.startswith('[') and selector.endswith(']'):
                # CSS attribute selector format
                xpath = f"//*{selector}"
            else:
                # Simple attribute=value format
                parts = selector.split('=', 1)
                if len(parts) == 2:
                    attr_name = parts[0].strip()
                    attr_value = parts[1].strip().strip('"\'')
                    xpath = f"//*[@{attr_name}='{attr_value}']"
                else:
                    return None
            
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            return element
        except Exception:
            return None

    async def _parse_and_find_by_attribute(self, selector: str, timeout: int) -> Optional[WebElement]:
        """Parse attribute selector and find element"""
        # This method can be enhanced to parse complex attribute selectors
        return await self._try_attribute_search(selector, timeout)

    def _looks_like_text_search(self, selector: str) -> bool:
        """Determine if selector looks like a text search rather than CSS/XPath"""
        # Simple heuristics to detect text searches
        text_indicators = [
            ' ',  # Contains spaces (likely text)
            not selector.startswith(('#', '.', '//', '[', '*')),  # Doesn't start with CSS/XPath indicators
            len(selector) > 1 and selector.isalnum() == False and '#' not in selector  # Complex text
        ]
        
        return any(text_indicators) and not any([
            selector.startswith('//'),  # XPath
            selector.startswith('#'),   # CSS ID
            selector.startswith('.'),   # CSS class
            selector.startswith('['),   # CSS attribute
            '>' in selector,            # CSS descendant
            '+' in selector,            # CSS sibling
            '~' in selector             # CSS general sibling
        ])

    def generate_alternative_selectors(self, element: WebElement) -> List[Dict[str, str]]:
        """Generate alternative selectors for an element"""
        alternatives = []
        
        try:
            # Get element attributes
            tag_name = element.tag_name
            element_id = element.get_attribute('id')
            class_names = element.get_attribute('class')
            name = element.get_attribute('name')
            text = element.text.strip()
            
            # ID-based selector
            if element_id:
                alternatives.append({
                    'type': 'css',
                    'selector': f'#{element_id}',
                    'description': 'ID selector'
                })
            
            # Class-based selector
            if class_names:
                class_list = class_names.strip().split()
                if class_list:
                    class_selector = '.' + '.'.join(class_list)
                    alternatives.append({
                        'type': 'css',
                        'selector': f'{tag_name}{class_selector}',
                        'description': 'Tag + class selector'
                    })
            
            # Name attribute selector
            if name:
                alternatives.append({
                    'type': 'css',
                    'selector': f'{tag_name}[name="{name}"]',
                    'description': 'Name attribute selector'
                })
            
            # Text-based selector
            if text and len(text) < 50:
                alternatives.append({
                    'type': 'text',
                    'selector': text,
                    'description': 'Text content selector'
                })
            
            # XPath selector
            xpath = self._generate_xpath_for_element(element)
            if xpath:
                alternatives.append({
                    'type': 'xpath',
                    'selector': xpath,
                    'description': 'Generated XPath'
                })
            
        except Exception as e:
            print(f"Error generating alternatives: {e}")
        
        return alternatives

    def _generate_xpath_for_element(self, element: WebElement) -> Optional[str]:
        """Generate XPath for a Selenium WebElement"""
        try:
            # Use JavaScript to generate XPath
            xpath = self.driver.execute_script("""
                function getXPathForElement(element) {
                    var idx = function(sib, name) {
                        var count = 1;
                        for (var prev = sib.previousSibling; prev; prev = prev.previousSibling) {
                            if (prev.nodeType == 1 && prev.tagName == name) count++;
                        }
                        return count;
                    };
                    
                    var segs = [];
                    for (; element && element.nodeType == 1; element = element.parentNode) {
                        if (element.hasAttribute('id')) {
                            segs.unshift('id("' + element.getAttribute('id') + '")');
                            return segs.join('/');
                        } else if (element.hasAttribute('class')) {
                            segs.unshift(element.tagName.toLowerCase() + '[@class="' + element.getAttribute('class') + '"]');
                        } else {
                            segs.unshift(element.tagName.toLowerCase() + '[' + idx(element, element.tagName) + ']');
                        }
                    }
                    return segs.length ? '/' + segs.join('/') : null;
                }
                return getXPathForElement(arguments[0]);
            """, element)
            
            return xpath
        except Exception:
            return None