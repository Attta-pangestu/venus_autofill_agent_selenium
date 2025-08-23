# Automated Data Entry System

A comprehensive automation system that consists of two main components:
1. **Data Interface** - Web-based UI for viewing and selecting staging data
2. **Selenium Automation** - Automated data entry into Millware Task Register system

## Features

### Component 1: Data Interface
- 🌐 Web-based interface accessible at `http://localhost:5000`
- 📊 Fetches staging data from API endpoint: `http://localhost:5173/api/staging/data`
- 🔍 Advanced filtering capabilities:
  - Filter by employee name
  - Filter by date range
  - Filter by status
- ✅ Multi-select functionality for batch processing
- 📋 Real-time job status monitoring
- 🎯 Process selected records with one click

### Component 2: Selenium Automation
- 🤖 Automated login to Millware system (`http://millwarep3:8004/`)
- 📝 Automated data entry for each selected staging record
- 🔄 Robust page load detection (no fixed time delays)
- 🎯 Intelligent form field targeting
- 📊 Detailed processing results and error handling
- 🔁 Sequential processing with proper delays

## System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Browser   │    │   Flask Web App  │    │ Automation      │
│   (User)        │◄──►│   (Data Interface│◄──►│ Service         │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   Staging API    │    │ Selenium        │
                       │   (Data Source)  │    │ WebDriver       │
                       └──────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │ Millware System │
                                               │ (Target)        │
                                               └─────────────────┘
```

## Installation

### Prerequisites
- Python 3.8 or higher
- Chrome browser (for Selenium WebDriver)
- Access to Millware system
- Access to staging data API

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Required Packages
- `selenium==4.15.2` - Web automation
- `webdriver-manager==4.0.1` - Chrome driver management
- `flask==3.0.0` - Web interface
- `flask-cors==4.0.0` - CORS support
- `requests==2.31.0` - API communication
- `pandas==2.1.4` - Data processing

## Configuration

### 1. Application Configuration
Edit `config/app_config.json`:

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
    "username": "adm075",
    "password": "adm075"
  },
  "urls": {
    "login": "http://millwarep3:8004/",
    "taskRegister": "http://millwarep3:8004/en/PR/trx/frmPrTrxTaskRegisterDet.aspx"
  },
  "api": {
    "staging_data_url": "http://localhost:5173/api/staging/data"
  },
  "web_interface": {
    "host": "0.0.0.0",
    "port": 5000,
    "debug": false
  }
}
```

### 2. Staging Data API
Ensure your staging data API returns data in this format:

```json
{
  "data": [
    {
      "id": "unique_record_id",
      "employee_name": "SEPTIAN ADE PRATAMA",
      "employee_id": "POM00132",
      "date": "2025-06-10",
      "task_code": "OC7190",
      "station_code": "STN-BLR",
      "raw_charge_job": "(OC7190) BOILER OPERATION / STN-BLR (STATION BOILER) / BLR00000 (LABOUR COST) / L (LABOUR)",
      "status": "staged"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 50
}
```

## Usage

### Quick Start
```bash
# Run the complete system
python run_automation_system.py

# Access web interface
# Open browser to: http://localhost:5000
```

### Command Line Options
```bash
# Run only web interface
python run_automation_system.py --mode web

# Run only automation service
python run_automation_system.py --mode automation

# Run in headless mode (no browser window)
python run_automation_system.py --headless

# Run with debug enabled
python run_automation_system.py --debug
```

### Web Interface Usage

1. **Access the Interface**
   - Open browser to `http://localhost:5000`
   - The interface will automatically load staging data

2. **Filter Data**
   - Use the filter section to narrow down records
   - Filter by employee name, date range, or status
   - Click "Apply Filters" to update the table

3. **Select Records**
   - Use checkboxes to select individual records
   - Use "Select All" to select all visible records
   - Selected count is displayed in real-time

4. **Process Records**
   - Click "Process Selected Records" button
   - Confirm the automation in the popup
   - Monitor progress in real-time

5. **Monitor Jobs**
   - View current job status
   - Check job history
   - Cancel running jobs if needed

## Automation Flow

### Login Flow
1. Navigate to `http://millwarep3:8004/`
2. Find username input: `<input name="txtUsername" type="text" id="txtUsername">`
3. Enter username: `adm075`
4. Find password input: `<input name="txtPassword" type="password" id="txtPassword">`
5. Enter password: `adm075`
6. Click login button: `<input type="submit" name="btnLogin" id="btnLogin">`
7. Handle any login popups
8. Navigate to Task Register page

### Data Entry Flow (for each record)
1. **Date Input**: Enter date in `MainContent_txtTrxDate` field (DD/MM/YYYY format)
2. **Employee Selection**: Use autocomplete field to select employee
3. **Charge Job Processing**: Parse `raw_charge_job` field and fill sequentially:
   - Task Code (e.g., "(OC7190) BOILER OPERATION")
   - Station Code (e.g., "STN-BLR (STATION BOILER)")
   - Machine Code (e.g., "BLR00000 (LABOUR COST)")
   - Expense Code (e.g., "L (LABOUR)")
4. **Form Submission**: Send Arrow Down + Enter keys
5. **Wait for Completion**: Dynamic page load detection

## API Endpoints

### Data Interface API
- `GET /api/staging-data` - Get staging data with filters
- `POST /api/process-selected` - Start automation for selected records
- `GET /api/job-status/<job_id>` - Get specific job status
- `GET /api/jobs` - Get all jobs
- `GET /api/current-job` - Get currently running job
- `POST /api/cancel-job/<job_id>` - Cancel a job
- `GET /api/employees` - Get unique employee names

### Request/Response Examples

#### Process Selected Records
```bash
POST /api/process-selected
Content-Type: application/json

{
  "selected_ids": ["POM00132_2025-06-10", "POM00181_2025-06-10"]
}
```

Response:
```json
{
  "success": true,
  "message": "Started automation for 2 records",
  "selected_count": 2,
  "automation_id": "auto_20250610_143022"
}
```

#### Job Status
```bash
GET /api/job-status/auto_20250610_143022
```

Response:
```json
{
  "job_id": "auto_20250610_143022",
  "status": "completed",
  "created_at": "2025-06-10T14:30:22",
  "started_at": "2025-06-10T14:30:23",
  "completed_at": "2025-06-10T14:32:15",
  "selected_records_count": 2,
  "results": [
    {
      "success": true,
      "record_id": "POM00132_2025-06-10",
      "message": "Record processed successfully",
      "processing_time": 45.2
    }
  ]
}
```

## Troubleshooting

### Common Issues

1. **Chrome Driver Issues**
   ```bash
   # Update webdriver-manager
   pip install --upgrade webdriver-manager
   ```

2. **API Connection Issues**
   - Verify staging data API is running on `http://localhost:5173`
   - Check network connectivity
   - Verify API response format

3. **Millware Login Issues**
   - Verify credentials in config
   - Check Millware system availability
   - Ensure correct URLs in configuration

4. **Automation Failures**
   - Check browser console for JavaScript errors
   - Verify HTML structure matches selectors
   - Enable debug mode for detailed logging

### Logs
- Application logs: `automation_system.log`
- Automation service logs: `automation_service.log`
- Selenium logs: `selenium_autofill.log`

## Development

### Project Structure
```
├── src/
│   ├── core/                    # Core automation modules
│   │   ├── automation_engine.py
│   │   ├── staging_automation.py
│   │   └── browser_manager.py
│   ├── data_interface/          # Web interface
│   │   ├── app.py              # Flask application
│   │   └── templates/
│   │       └── index.html      # Main UI template
│   └── automation_service.py    # Automation service coordinator
├── config/                      # Configuration files
├── flows/                       # Automation flow definitions
├── requirements.txt             # Python dependencies
└── run_automation_system.py     # Main startup script
```

### Adding New Features
1. **New API Endpoints**: Add to `src/data_interface/app.py`
2. **Automation Logic**: Extend `src/core/staging_automation.py`
3. **UI Components**: Modify `src/data_interface/templates/index.html`
4. **Configuration**: Update `config/app_config.json`

## Security Considerations

- Credentials are stored in configuration files
- Web interface runs on all interfaces (0.0.0.0) by default
- No authentication implemented (suitable for internal networks)
- Consider adding HTTPS and authentication for production use

## License

This project is part of the Venus AutoFill Selenium automation system.
