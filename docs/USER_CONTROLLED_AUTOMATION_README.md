# User-Controlled Automation System

## Overview

This system implements a user-controlled automation workflow where the WebDriver is pre-positioned and waits for user selection before processing records. This provides better control and visibility over the automation process.

## Workflow Architecture

### Phase 1: Initialization (Automatic)
- ✅ WebDriver automatically performs login
- ✅ Navigates to task register page: `http://millwarep3:8004/en/PR/trx/frmPrTrxTaskRegisterDet.aspx`
- ✅ Performs enhanced form detection to ensure readiness
- ✅ Waits in ready state (no automatic data processing)

### Phase 2: User Selection (Manual)
- 👤 Web interface displays available staging data
- 👤 User browses and selects specific records
- 👤 User clicks "Process Selected Records" to trigger automation
- 📊 Selected data is displayed in console/terminal

### Phase 3: Automation Execution (Automatic)
- 🤖 WebDriver begins automated data entry
- 🎯 Processes only user-selected records
- 📈 Real-time progress monitoring in console

## Key Features

### ✅ Pre-Positioned WebDriver
- WebDriver is automatically positioned at the task register page during initialization
- No redundant navigation when processing records
- Enhanced form detection ensures all required elements are ready

### ✅ User-Controlled Selection
- Web interface at `http://localhost:5000` for record selection
- Filter and browse staging data before processing
- Select specific records instead of processing all data

### ✅ Real-Time Feedback
- Console displays selected records before automation starts
- Progress monitoring during automation execution
- Detailed logging of all operations

### ✅ Robust Error Handling
- Enhanced form detection with fallback strategies
- Network connectivity checks
- WebDriver compatibility verification
- Graceful error recovery

## Files and Components

### Main Scripts
- `run_user_controlled_automation.py` - Main script implementing the user-controlled workflow
- `test_user_controlled_workflow.py` - Comprehensive test suite for the workflow

### Core Components
- `src/automation_service.py` - Enhanced automation service with user-controlled workflow
- `src/core/enhanced_staging_automation.py` - Fixed form detection and automation logic
- `src/core/browser_manager.py` - Enhanced WebDriver management with error handling
- `src/data_interface/app.py` - Web interface for user selection

## Usage Instructions

### 1. Start the System
```bash
python run_user_controlled_automation.py
```

### 2. Wait for Initialization
The system will:
- Create WebDriver session
- Perform login automatically
- Navigate to task register page
- Display "SYSTEM READY" message

### 3. Select Records
- Web browser will open automatically to `http://localhost:5000`
- Browse available staging data
- Select specific records to process
- Click "Process Selected Records"

### 4. Monitor Automation
- Selected records will be displayed in console
- WebDriver will begin automated data entry
- Monitor progress in the console window

## Configuration

### Browser Settings
```python
"browser": {
    "headless": False,          # Set to True for headless operation
    "window_size": [1280, 720], # Browser window size
    "disable_notifications": True,
    "event_delay": 0.5          # Delay between actions
}
```

### Automation Settings
```python
"automation": {
    "implicit_wait": 12,        # WebDriver implicit wait (increased for stability)
    "page_load_timeout": 45,    # Page load timeout (increased to prevent renderer timeout)
    "script_timeout": 30,       # Script execution timeout
    "max_retries": 3,           # Maximum retry attempts
    "element_timeout": 15       # Element detection timeout
}
```

### Credentials
```python
"credentials": {
    "username": "adm075",       # Login username
    "password": "adm075"        # Login password
}
```

## Testing

### Run Complete Test Suite
```bash
python test_user_controlled_workflow.py
```

### Test Components
1. **Automation Service Initialization** - Verifies WebDriver positioning
2. **Web Interface Availability** - Tests user selection interface
3. **Mock User Selection** - Simulates user record selection
4. **API Integration** - Tests automation trigger API

## Troubleshooting

### Common Issues

#### 1. WebDriver Initialization Timeout
**Symptoms:** "AUTOMATION ENGINE INITIALIZATION TIMEOUT"
**Solutions:**
- Check network connectivity to `millwarep3:8004`
- Verify Chrome browser is installed and updated
- Check if login credentials are correct

#### 2. Form Detection Issues
**Symptoms:** "Form not ready within timeout"
**Solutions:**
- The system now includes enhanced form detection with fallbacks
- Check browser console for JavaScript errors
- Verify task register page loads correctly

#### 3. Network Connectivity Issues
**Symptoms:** "ERR_NAME_NOT_RESOLVED"
**Solutions:**
- Add `millwarep3` to your hosts file
- Use IP address instead of hostname
- Check firewall settings

#### 4. Web Interface Not Accessible
**Symptoms:** Cannot access `http://localhost:5000`
**Solutions:**
- Check if port 5000 is available
- Verify Flask application started successfully
- Check firewall settings for local connections

## Advantages Over Previous System

### ✅ Better User Control
- Select specific records instead of processing all data
- Preview records before automation starts
- Cancel or modify selection before processing

### ✅ Improved Reliability
- Enhanced form detection with multiple fallback strategies
- Elimination of redundant navigation
- Better error handling and recovery

### ✅ Better Visibility
- Real-time console feedback
- Detailed logging of all operations
- Progress monitoring during automation

### ✅ Faster Execution
- Pre-positioned WebDriver eliminates initialization delays
- No repeated login/navigation cycles
- Optimized for processing selected records only

## API Endpoints

### GET /api/staging-data
Returns available staging data for user selection

### POST /api/process-selected
Triggers automation for selected record IDs
```json
{
    "selected_ids": ["record1", "record2", "record3"]
}
```

### GET /api/job-status/{job_id}
Returns status of a specific automation job

### GET /api/current-job
Returns status of currently running job

## Logging

### Log Files
- `user_controlled_automation.log` - Main system log
- `automation_system.log` - Detailed automation operations
- `test_user_controlled_workflow.log` - Test execution log

### Log Levels
- INFO: General operation information
- WARNING: Non-critical issues
- ERROR: Critical errors requiring attention
- DEBUG: Detailed debugging information

## Support

For issues or questions:
1. Check the log files for detailed error information
2. Run the test suite to identify specific problems
3. Review the troubleshooting section above
4. Check network connectivity and browser compatibility
