# Venus AutoFill Desktop Application

Desktop version of the Venus AutoFill web application built with Electron. This application provides the same functionality as the web interface but as a standalone desktop application.

## Features

- **Desktop Application**: Standalone desktop app that doesn't require a web browser
- **Same UI/UX**: Identical interface and functionality as the web version
- **Real-time Data**: Live connection to Flask backend server
- **Progress Tracking**: Real-time automation progress monitoring
- **Database Crosscheck**: Automated verification of processed data
- **Settings Management**: Configurable server connection and refresh settings
- **Auto-refresh**: Automatic data updates with configurable intervals
- **Offline Notifications**: Connection status indicators and error handling

## Prerequisites

- Node.js (version 16 or higher)
- npm (comes with Node.js)
- Running Flask backend server (Venus AutoFill web application)

## Installation

1. **Navigate to the desktop app directory:**
   ```bash
   cd desktop-app
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Install Electron globally (optional but recommended):**
   ```bash
   npm install -g electron
   ```

## Running the Application

### Development Mode
```bash
npm start
# or
npm run dev
```

### Production Mode
```bash
electron .
```

## Building Executable

### Build for Windows
```bash
npm run build-win
```

### Build for all platforms
```bash
npm run build
```

The built application will be available in the `dist` folder.

## Configuration

### Flask Server Connection

1. Click the **Settings** button in the application
2. Configure the Flask Server URL (default: `http://localhost:5000`)
3. Enable/disable auto-refresh
4. Set refresh interval (5-300 seconds)

### Default Settings
- **Flask Server URL**: `http://localhost:5000`
- **Auto Refresh**: Enabled
- **Refresh Interval**: 30 seconds

## Application Structure

```
desktop-app/
├── main.js              # Main Electron process
├── preload.js           # Preload script for secure IPC
├── package.json         # Dependencies and build config
├── renderer/
│   ├── index.html       # Main UI template
│   ├── styles.css       # Application styles
│   └── app.js          # Frontend application logic
└── assets/
    └── icon.png        # Application icon
```

## Key Components

### Main Process (`main.js`)
- Window management
- IPC communication with Flask backend
- Settings storage
- Error handling

### Renderer Process (`renderer/`)
- User interface
- Data visualization
- User interactions
- Real-time updates

### Preload Script (`preload.js`)
- Secure bridge between main and renderer processes
- Exposes safe APIs to the frontend

## API Integration

The desktop app communicates with the Flask backend through these endpoints:

- `GET /api/health` - Server health check
- `GET /api/staging-data` - Fetch staging data with filters
- `POST /api/start-automation` - Start automation process
- `GET /api/automation-status` - Get automation progress
- `POST /api/stop-automation` - Stop automation process
- `GET /api/crosscheck-results` - Get database crosscheck results

## Features Overview

### Data Management
- **Real-time Data Loading**: Fetch and display staging data from Flask backend
- **Advanced Filtering**: Filter by date range, status, and search text
- **Bulk Selection**: Select all or clear selection with one click
- **Auto-refresh**: Configurable automatic data updates

### Automation Control
- **Start/Stop Automation**: Control automation process with selected records
- **Progress Monitoring**: Real-time progress tracking with visual indicators
- **Status Updates**: Live status updates during automation
- **Error Handling**: Comprehensive error reporting and recovery

### Database Crosscheck
- **Automatic Verification**: Post-automation data verification
- **Visual Results**: Color-coded crosscheck results display
- **Manual Refresh**: On-demand crosscheck result updates

### Settings & Configuration
- **Server Configuration**: Configurable Flask server connection
- **Auto-refresh Settings**: Customizable refresh intervals
- **Persistent Settings**: Settings saved between application sessions

## Troubleshooting

### Connection Issues
1. **Check Flask Server**: Ensure the Flask backend is running
2. **Verify URL**: Check the Flask server URL in settings
3. **Network Access**: Ensure network connectivity to the server
4. **Firewall**: Check firewall settings for the application

### Performance Issues
1. **Reduce Refresh Interval**: Increase the auto-refresh interval
2. **Limit Data Range**: Use date filters to reduce data load
3. **Close Other Applications**: Free up system resources

### Application Errors
1. **Restart Application**: Close and reopen the application
2. **Clear Settings**: Reset settings to default values
3. **Check Logs**: Review console logs for error details
4. **Update Dependencies**: Ensure all dependencies are up to date

## Development

### Adding New Features
1. **Backend Integration**: Add new IPC handlers in `main.js`
2. **Frontend Logic**: Implement UI logic in `app.js`
3. **Styling**: Add styles in `styles.css`
4. **Security**: Expose new APIs through `preload.js`

### Debugging
- Use `npm run dev` to open DevTools
- Check console logs for errors
- Monitor network requests in DevTools
- Use Electron's built-in debugging tools

## Security

- **Context Isolation**: Enabled for security
- **Node Integration**: Disabled in renderer process
- **Secure IPC**: All communication through preload script
- **No Remote Module**: Remote module disabled for security

## License

MIT License - See the main project license for details.

## Support

For issues and support:
1. Check the troubleshooting section
2. Review console logs for errors
3. Ensure Flask backend is properly configured
4. Contact the development team for assistance

---

**Note**: This desktop application requires the Venus AutoFill Flask backend to be running. Ensure the web application is properly set up and accessible before using the desktop version.