# Selenium AutoFill - Standalone Browser Automation

A powerful standalone browser automation application built with Selenium WebDriver that replicates and extends the functionality of the Ekstensi_auto_fill Chrome extension. This application provides visual feedback, sophisticated element targeting, and JSON-based flow definitions for complex automation scenarios.

## 🚀 Features

### Core Automation Capabilities
- **Visual Browser Automation**: Visible browser window with real-time highlighting and feedback
- **JSON-Based Flow Definitions**: Define complex automation flows using structured JSON
- **Advanced Element Targeting**: Multiple selector strategies with intelligent fallbacks
- **Real-Time Visual Feedback**: Progress indicators, element highlighting, and status notifications
- **Conditional Logic**: Support for if-then-else conditions and loops
- **Data Extraction**: Extract and store data from web pages
- **Error Handling**: Robust error handling with retry mechanisms
- **Keyboard Events**: Full keyboard interaction support including special keys
- **Redirect Prevention**: Prevent unwanted page redirects during automation

### Advanced Features
- **Pre/Post-Login Sequences**: Automated login and navigation flows
- **Popup Handling**: Automatic detection and handling of modal dialogs
- **Text Search Engine**: Advanced text-based element finding
- **Screenshot Capture**: Automated screenshot functionality
- **Browser Profile Management**: Support for custom Chrome profiles
- **Interactive Mode**: User-friendly command-line interface
- **Flow Validation**: Pre-execution validation of automation flows
- **Chrome Extension Compatibility**: Load and execute flows from Ekstensi_auto_fill extension

## 📋 System Requirements

- **Python**: 3.8 or higher
- **Chrome Browser**: Latest version recommended
- **Operating System**: Windows, macOS, or Linux

## 🛠️ Installation

1. **Clone or download the project:**
   ```bash
   git clone <repository-url>
   cd "Selenium Auto Fill"
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **ChromeDriver will be automatically downloaded** when you first run the application.

## 🎯 Quick Start

1. **Run the application:**
   ```bash
   python src/main.py
   ```

2. **Configure your settings:**
   - On first run, a sample configuration file will be created at `config/app_config.json`
   - Edit this file with your actual credentials and URLs

3. **Use the interactive menu:**
   - Choose from pre-defined flows (login, attendance)
   - Use converted Chrome extension flows
   - Load custom flows from JSON files
   - Test element finding capabilities

## 📁 Project Structure

```
Selenium Auto Fill/
├── src/
│   ├── core/
│   │   ├── automation_engine.py    # Main automation execution engine
│   │   ├── browser_manager.py      # Chrome WebDriver management
│   │   ├── element_finder.py       # Advanced element targeting
│   │   ├── visual_feedback.py      # Real-time visual indicators
│   │   ├── data_manager.py         # Data handling utilities
│   │   └── flow_validator.py       # Flow validation system
│   └── main.py                     # Application entry point
├── flows/
│   ├── sample_login_flow.json      # Example flow definition
│   ├── pre_login_flow.json         # Converted Chrome extension pre-login
│   └── post_login_flow.json        # Converted Chrome extension post-login
├── examples/
│   ├── basic_usage.py              # Basic usage examples
│   └── chrome_extension_flows.py   # Chrome extension flow tests
├── config/
│   └── app_config.json            # Application configuration
├── requirements.txt               # Python dependencies
└── README.md                     # This file
```

## ⚙️ Configuration

### Application Configuration (`config/app_config.json`)

```json
{
  "browser": {
    "headless": false,
    "window_size": [1280, 720],
    "disable_notifications": true,
    "event_delay": 0.5
  },
  "automation": {
    "implicit_wait": 10,
    "page_load_timeout": 30,
    "script_timeout": 30,
    "max_retries": 3
  },
  "credentials": {
    "username": "your_username",
    "password": "your_password"
  },
  "urls": {
    "login": "http://your-server.com/login",
    "attendance": "http://your-server.com/attendance"
  }
}
```

## 📝 Flow Definition Format

Automation flows are defined using JSON with support for complex logic:

### Basic Structure
```json
{
  "name": "Flow Name",
  "description": "Flow description",
  "variables": {
    "username": "admin",
    "loginUrl": "http://example.com/login"
  },
  "events": [
    {
      "id": 1,
      "type": "open_to",
      "url": "{loginUrl}",
      "description": "Navigate to login page"
    }
  ]
}
```

### Supported Event Types

#### Navigation Events
- **`open_to`**: Navigate to URL
- **`navigate`**: Alternative navigation syntax
- **`wait_for_page_stability`**: Wait for page to fully load

#### Interaction Events
- **`click`**: Click elements with multiple targeting strategies
- **`input`**: Enter text with typing simulation options
- **`hover`**: Hover over elements
- **`scroll`**: Scroll to elements or positions
- **`keyboard`**: Send keyboard keys (new feature)

#### Wait Events
- **`wait`**: Simple time-based wait
- **`wait_for_element`**: Wait for element to appear/disappear

#### Data Events
- **`extract`**: Extract text or attribute values
- **`data_extract_multiple`**: Extract multiple data points
- **`variable_set`**: Set variables for later use

#### Control Flow Events
- **`if_then_else`**: Conditional execution
- **`loop`**: Repeat actions with iteration control
- **`prevent_redirect`**: Prevent page redirects (new feature)

#### Utility Events
- **`screenshot`**: Capture page screenshots
- **`popup_handler`**: Handle modal dialogs
- **`form_fill`**: Fill multiple form fields

### New Event Types

#### Keyboard Event
Send keyboard keys to elements with full key mapping support:

```json
{
  "type": "keyboard",
  "selector": "input.search-field",
  "key": "Enter",
  "description": "Press Enter to search",
  "waitAfterKey": 500,
  "preventDefault": false
}
```

**Supported Keys:**
- Navigation: `ArrowUp`, `ArrowDown`, `ArrowLeft`, `ArrowRight`, `Home`, `End`, `PageUp`, `PageDown`
- Action: `Enter`, `Return`, `Tab`, `Space`, `Escape`, `Backspace`, `Delete`
- Function: `F1` through `F12`
- Modifiers: `Shift`, `Control`, `Alt`, `Meta`

#### Prevent Redirect Event
Temporarily block page navigation to prevent unwanted redirects:

```json
{
  "type": "prevent_redirect",
  "timeout": 3000,
  "description": "Prevent page redirects during form interaction",
  "blockMethods": [
    "location.href",
    "location.assign",
    "location.replace",
    "meta_refresh",
    "form_submit"
  ],
  "allowManualNavigation": false
}
```

### Example: Advanced Chrome Extension Flow

```json
{
  "name": "Autocomplete Interaction Flow",
  "variables": {
    "employee": "John Doe",
    "activityCode": "(OC7240) LABORATORY ANALYSIS"
  },
  "events": [
    {
      "type": "input",
      "selector": "input.ui-autocomplete-input",
      "value": "{employee}",
      "simulateTyping": true,
      "typingDelay": 50
    },
    {
      "type": "keyboard",
      "selector": "input.ui-autocomplete-input",
      "key": "Space",
      "description": "Trigger autocomplete dropdown"
    },
    {
      "type": "wait_for_element",
      "selector": ".ui-autocomplete:not([style*='display: none'])",
      "expectVisible": true,
      "timeout": 1000
    },
    {
      "type": "keyboard",
      "selector": "input.ui-autocomplete-input",
      "key": "ArrowDown",
      "description": "Navigate dropdown options"
    },
    {
      "type": "prevent_redirect",
      "timeout": 3000,
      "blockMethods": ["location.href", "form_submit"]
    },
    {
      "type": "keyboard",
      "selector": "input.ui-autocomplete-input",
      "key": "Enter",
      "description": "Select option",
      "preventDefault": true
    }
  ]
}
```

## 🎮 Interactive Mode Features

The application provides an interactive command-line interface with the following options:

### Basic Flows
1. **Run Login Flow**: Execute automated login sequence
2. **Run Attendance Flow**: Execute attendance entry automation
3. **Run Complete Flow**: Combined login + attendance automation

### Chrome Extension Converted Flows
4. **Run Pre-Login Flow**: Converted pre-login sequence from Chrome extension
5. **Run Post-Login Flow**: Converted post-login sequence with autocomplete interactions
6. **Run Complete Chrome Extension Flow**: Full converted flow sequence

### Advanced Options
7. **Load Custom Flow**: Load and execute flows from JSON files
8. **Test Element Finding**: Interactive element testing and highlighting
9. **Take Screenshot**: Capture current browser state
10. **Clear Browser Data**: Clear cookies, cache, and storage
11. **Restart Browser**: Restart the browser session

## 🔍 Advanced Element Targeting

The application uses sophisticated element finding strategies:

### Multiple Selector Types
- **CSS Selectors**: Standard CSS selector syntax
- **XPath**: Full XPath expression support
- **Text Content**: Find elements by visible text
- **Attribute Matching**: Find by attribute values

### Intelligent Fallbacks
```json
{
  "type": "click",
  "selector": "#primary-button",
  "alternatives": [
    {"type": "css", "selector": ".btn-primary"},
    {"type": "text", "selector": "Submit"},
    {"type": "xpath", "selector": "//button[contains(@class, 'submit')]"}
  ]
}
```

### Text-Based Finding
```json
{
  "type": "click",
  "selector": "Login to Continue",
  "selectorType": "text",
  "options": {
    "exactMatch": false,
    "caseSensitive": false,
    "includeButtons": true
  }
}
```

## 🎨 Visual Feedback System

### Real-Time Indicators
- **Progress Bar**: Shows automation progress
- **Element Highlighting**: Visual element identification
- **Action Indicators**: Real-time action feedback
- **Status Notifications**: Success/error notifications
- **Step Descriptions**: Current action descriptions

### Customizable Visual Effects
- **Color-coded Actions**: Different colors for different action types
- **Animation Effects**: Smooth highlighting animations
- **Overlay Information**: Contextual element information
- **Screenshot Integration**: Automatic visual documentation

## 🛡️ Error Handling & Recovery

### Robust Error Management
- **Element Not Found**: Automatic retry with alternative selectors
- **Timeout Handling**: Configurable timeout strategies
- **Page Load Issues**: Automatic page stability detection
- **Network Errors**: Connection retry mechanisms
- **Keyboard Event Failures**: Fallback to ActionChains for key sending

### Recovery Strategies
- **Alternative Selectors**: Multiple targeting strategies per element
- **Graceful Degradation**: Continue on non-critical errors
- **State Validation**: Verify expected page states
- **Automatic Screenshots**: Capture failure states for debugging

## 🔧 Chrome Extension Integration

### Converting Extension Flows
The application can load flows from the original Ekstensi_auto_fill Chrome extension format and includes pre-converted flows:

- **Pre-Login Flow**: Complete login sequence with popup handling
- **Post-Login Flow**: Complex autocomplete interactions with keyboard events
- **Variable Substitution**: Automatic merging of flow variables with config

### Flow Compatibility
- **Event Type Mapping**: Automatic conversion of extension event types
- **Selector Translation**: Support for extension selector formats
- **Variable Processing**: Merge extension variables with application config

## 🚨 Troubleshooting

### Common Issues

**Chrome Driver Issues:**
- ChromeDriver is automatically managed by webdriver-manager
- If issues persist, manually delete cached drivers and restart

**Element Not Found:**
- Use the interactive element testing feature
- Check alternative selectors
- Verify page load timing

**Keyboard Events Not Working:**
- Check if element is focused before sending keys
- Try using `preventDefault: true` for special handling
- Use ActionChains fallback for complex key combinations

**Redirect Prevention Issues:**
- Ensure timeout is sufficient for the operation
- Check if the page uses unsupported redirect methods
- Monitor browser console for blocked redirect messages

### Debug Mode
```python
# Enable verbose logging
logging.getLogger().setLevel(logging.DEBUG)

# Take screenshots on errors
automation_engine.visual_feedback.show_error_notification("Debug info")
```

## 🔗 Integration with Existing Flows

The application can load and execute flows from the original Ekstensi_auto_fill extension:

```bash
# Load extension's sample flows
python src/main.py
# Choose option 7: Load and Run Custom Flow from File
# Enter path: ../Ekstensi_auto_fill/sample-flows.json
```

## 📊 Testing New Features

Use the test script to verify keyboard and redirect prevention functionality:

```bash
python examples/chrome_extension_flows.py
```

This includes:
- Keyboard event testing on sample forms
- Redirect prevention demonstration
- Chrome extension flow analysis

---

For more information, issues, or feature requests, please refer to the project repository or contact the development team. 