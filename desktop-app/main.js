const { app, BrowserWindow, ipcMain, dialog, shell } = require('electron');
const path = require('path');
const axios = require('axios');
const Store = require('electron-store');
const { spawn } = require('child_process');

// Initialize electron store for settings
const store = new Store();

// Keep a global reference of the window object
let mainWindow;
let flaskProcess = null;
let isFlaskServerReady = false;

// Flask server configuration
const FLASK_SERVER_URL = store.get('flaskServerUrl', 'http://127.0.0.1:5000');
const FLASK_SERVER_PORT = 5000;

// Function to check external Flask server availability
function startFlaskServer() {
  return new Promise(async (resolve, reject) => {
    console.log('Checking external Flask server availability...');
    
    // Check if external staging API server is available
    let retries = 10;
    let connected = false;
    
    while (retries > 0 && !connected) {
      try {
        console.log(`Flask connection attempt ${11 - retries}/10...`);
        const response = await axios.get(`${FLASK_SERVER_URL}/health`, {
          timeout: 5000
        });
        
        if (response.status === 200) {
          console.log('Successfully connected to external Flask server!');
          isFlaskServerReady = true;
          connected = true;
          resolve();
          return;
        }
      } catch (error) {
        console.log(`Flask connection attempt ${11 - retries}/10 failed: ${error.message}`);
        retries--;
        
        if (retries > 0) {
          // Wait 1 second before retrying
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
      }
    }
    
    if (!connected) {
      console.error('Failed to connect to Flask server after all retries');
      reject(new Error('Cannot connect to external Flask server'));
    }
  });
}

// Function to cleanup Flask server connection
function stopFlaskServer() {
  console.log('Cleaning up Flask server connection...');
  isFlaskServerReady = false;
}

function createWindow() {
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1200,
    minHeight: 700,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, 'assets', 'icon.png'),
    show: false,
    titleBarStyle: 'default',
    autoHideMenuBar: true
  });

  // Load the app
  mainWindow.loadFile('renderer/index.html');

  // Show window when ready to prevent visual flash
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    
    // Enhanced startup sequence: Check connection, fetch data, then initialize browser
    performStartupSequence();
  });

  // Open DevTools in development
  if (process.argv.includes('--dev')) {
    mainWindow.webContents.openDevTools();
  }

  // Handle window closed
  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Handle external links
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });
}

// App event handlers
app.whenReady().then(async () => {
  try {
    // Connect to external Flask server first
    await startFlaskServer();
    console.log('Connected to external Flask server successfully');
    
    // Then create the window
    createWindow();
  } catch (error) {
    console.error('Failed to connect to Flask server:', error);
    
    // Show error dialog and still create window
    dialog.showErrorBox(
      'Server Connection Error',
      `Failed to connect to Flask server: ${error.message}\n\nPlease ensure the staging API server is running on port 5173.\n\nThe application will start but some features may not work.`
    );
    
    createWindow();
  }
});

app.on('window-all-closed', () => {
  // Stop Flask server when app is closing
  stopFlaskServer();
  
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  // Ensure Flask server is stopped before quitting
  stopFlaskServer();
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// IPC handlers for communication with renderer process

// Check Flask server connection with extended timeout
ipcMain.handle('check-flask-connection', async () => {
  try {
    const response = await axios.get(`${FLASK_SERVER_URL}/health`, {
      timeout: 15000 // Increased from 5s to 15s for better connection stability
    });
    return { success: true, data: response.data };
  } catch (error) {
    return { 
      success: false, 
      error: error.message,
      code: error.code
    };
  }
})

// Get staging data from Flask API with extended timeout for better data loading
ipcMain.handle('get-staging-data', async (event, filters = {}) => {
  try {
    const response = await axios.get(`${FLASK_SERVER_URL}/api/staging-data`, {
      params: filters,
      timeout: 30000 // Increased from 10s to 30s for better data loading
    });
    return { success: true, data: response.data };
  } catch (error) {
    return { 
      success: false, 
      error: error.message,
      status: error.response?.status
    };
  }
});

// Initialize browser and login
ipcMain.handle('initialize-browser', async () => {
  try {
    const response = await axios.post(`${FLASK_SERVER_URL}/api/initialize-browser`, {}, {
      timeout: 60000 // Longer timeout for browser initialization
    });
    return { success: true, data: response.data };
  } catch (error) {
    return { 
      success: false, 
      error: error.message,
      status: error.response?.status
    };
  }
});

// Enhanced automation endpoints
ipcMain.handle('start-automation', async (event, selectedIds) => {
  try {
    const response = await axios.post(`${FLASK_SERVER_URL}/api/process-data`, {
      selected_ids: selectedIds
    }, {
      timeout: 30000
    });
    return { success: true, data: response.data };
  } catch (error) {
    return { 
      success: false, 
      error: error.message,
      status: error.response?.status
    };
  }
});

// Enhanced data processing endpoint
ipcMain.handle('process-selected-data', async (event, selectedData) => {
  try {
    const response = await axios.post(`${FLASK_SERVER_URL}/api/process-data`, selectedData, {
      timeout: 30000
    });
    return { success: true, data: response.data };
  } catch (error) {
    return { 
      success: false, 
      error: error.message,
      status: error.response?.status
    };
  }
});

// Get grouped staging data with extended timeout
ipcMain.handle('get-grouped-staging-data', async (event, filters = {}) => {
  try {
    const response = await axios.get(`${FLASK_SERVER_URL}/api/staging-data-grouped`, {
      params: filters,
      timeout: 30000 // Increased from 10s to 30s for better data loading
    });
    return { success: true, data: response.data.data || [] };
  } catch (error) {
    return { 
      success: false, 
      error: error.message,
      status: error.response?.status
    };
  }
});

// Get browser status
ipcMain.handle('get-browser-status', async (event) => {
  try {
    const response = await axios.get(`${FLASK_SERVER_URL}/api/browser-status`, {
      timeout: 10000
    });
    return { success: true, data: response.data };
  } catch (error) {
    return { 
      success: false, 
      error: error.message,
      status: error.response?.status
    };
  }
});

// Get processing progress
ipcMain.handle('get-processing-progress', async (event) => {
  try {
    const response = await axios.get(`${FLASK_SERVER_URL}/api/processing-progress`, {
      timeout: 5000
    });
    return { success: true, data: response.data };
  } catch (error) {
    return { 
      success: false, 
      error: error.message,
      status: error.response?.status
    };
  }
});

// Stop processing
ipcMain.handle('stop-processing', async (event) => {
  try {
    const response = await axios.post(`${FLASK_SERVER_URL}/api/stop-processing`, {}, {
      timeout: 5000
    });
    return { success: true, data: response.data };
  } catch (error) {
    return { 
      success: false, 
      error: error.message,
      status: error.response?.status
    };
  }
});

// Get automation status
ipcMain.handle('get-automation-status', async (event) => {
  try {
    const response = await axios.get(`${FLASK_SERVER_URL}/api/automation-status`, {
      timeout: 5000
    });
    return { success: true, data: response.data };
  } catch (error) {
    return { 
      success: false, 
      error: error.message,
      status: error.response?.status
    };
  }
});

// Stop automation process
ipcMain.handle('stop-automation', async () => {
  try {
    const response = await axios.post(`${FLASK_SERVER_URL}/api/stop-automation`, {}, {
      timeout: 10000
    });
    return { success: true, data: response.data };
  } catch (error) {
    return { 
      success: false, 
      error: error.message
    };
  }
});

// Get crosscheck results
ipcMain.handle('get-crosscheck-results', async () => {
  try {
    const response = await axios.get(`${FLASK_SERVER_URL}/api/crosscheck-results`, {
      timeout: 10000
    });
    return { success: true, data: response.data };
  } catch (error) {
    return { 
      success: false, 
      error: error.message
    };
  }
});

// Settings management
ipcMain.handle('get-settings', () => {
  return {
    flaskServerUrl: store.get('flaskServerUrl', 'http://127.0.0.1:5000'),
    autoRefresh: store.get('autoRefresh', true),
    refreshInterval: store.get('refreshInterval', 5000)
  };
});

ipcMain.handle('save-settings', (event, settings) => {
  try {
    store.set('flaskServerUrl', settings.flaskServerUrl);
    store.set('autoRefresh', settings.autoRefresh);
    store.set('refreshInterval', settings.refreshInterval);
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// Show error dialog
ipcMain.handle('show-error-dialog', async (event, title, content) => {
  const result = await dialog.showMessageBox(mainWindow, {
    type: 'error',
    title: title,
    message: content,
    buttons: ['OK']
  });
  return result;
});

// Show info dialog
ipcMain.handle('show-info-dialog', async (event, title, content) => {
  const result = await dialog.showMessageBox(mainWindow, {
    type: 'info',
    title: title,
    message: content,
    buttons: ['OK']
  });
  return result;
});

// Enhanced startup sequence function
async function performStartupSequence() {
  console.log('Starting enhanced startup sequence...');
  
  try {
    // Step 1: Check Flask server connection with retry
    console.log('Step 1: Checking Flask server connection...');
    const connectionEstablished = await checkFlaskConnectionWithRetry();
    
    if (connectionEstablished) {
      // Step 2: Automatically fetch staging data
      console.log('Step 2: Fetching staging data...');
      await fetchInitialStagingData();
      
      // Step 3: Initialize browser and navigate to task register
      console.log('Step 3: Initializing browser...');
      await initializeBrowserOnStartup();
      
      console.log('Startup sequence completed successfully!');
    } else {
      console.warn('Startup sequence incomplete due to connection failure');
    }
  } catch (error) {
    console.error('Error during startup sequence:', error);
    dialog.showErrorBox(
      'Startup Error',
      `An error occurred during startup: ${error.message}`
    );
  }
}

// Function to fetch initial staging data on startup
async function fetchInitialStagingData() {
  try {
    console.log('Fetching initial staging data...');
    const response = await axios.get(`${FLASK_SERVER_URL}/api/staging-data-grouped`, {
      params: { limit: 50 }, // Load first 50 records for initial display
      timeout: 30000
    });
    
    if (response.data && response.data.data) {
      console.log(`Successfully fetched ${response.data.data.length} staging records`);
      
      // Notify renderer process about the data
      if (mainWindow && mainWindow.webContents) {
        mainWindow.webContents.send('initial-data-loaded', {
          success: true,
          data: response.data,
          message: `Loaded ${response.data.data.length} staging records from database`
        });
      }
    }
  } catch (error) {
    console.error('Failed to fetch initial staging data:', error);
    
    // Notify renderer about the error
    if (mainWindow && mainWindow.webContents) {
      mainWindow.webContents.send('initial-data-loaded', {
        success: false,
        error: error.message,
        message: 'Failed to load staging data from database on startup'
      });
    }
  }
}

// Function to initialize browser on startup
async function initializeBrowserOnStartup() {
  try {
    console.log('Initializing browser on startup...');
    
    // Notify renderer that browser initialization is starting
    if (mainWindow && mainWindow.webContents) {
      mainWindow.webContents.send('browser-initialization-started');
    }
    
    const response = await axios.post(`${FLASK_SERVER_URL}/api/initialize-browser`, {}, {
      timeout: 60000
    });
    
    if (response.data) {
      console.log('Browser initialized successfully:', response.data);
      
      // Notify renderer about successful browser initialization
      if (mainWindow && mainWindow.webContents) {
        mainWindow.webContents.send('browser-initialization-completed', {
          success: true,
          data: response.data,
          message: 'Browser initialized and navigated to task register'
        });
      }
    }
  } catch (error) {
    console.error('Failed to initialize browser on startup:', error);
    
    // Notify renderer about the error
    if (mainWindow && mainWindow.webContents) {
      mainWindow.webContents.send('browser-initialization-completed', {
        success: false,
        error: error.message,
        message: 'Failed to initialize browser on startup'
      });
    }
  }
}

// Helper function to check Flask connection with retry
async function checkFlaskConnectionWithRetry(maxRetries = 10, delay = 1000) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      await axios.get(`${FLASK_SERVER_URL}/health`, { timeout: 5000 });
      console.log('Flask server connection established');
      return true;
    } catch (error) {
      console.log(`Flask connection attempt ${i + 1}/${maxRetries} failed:`, error.message);
      
      if (i < maxRetries - 1) {
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }
  
  console.error('Failed to connect to Flask server after all retries');
  
  // Show connection error dialog only if integrated server failed
  if (isFlaskServerReady) {
    dialog.showMessageBox(mainWindow, {
      type: 'warning',
      title: 'Server Connection Warning',
      message: 'Cannot connect to integrated Flask server',
      detail: 'The Flask server is running but not responding to health checks.',
      buttons: ['OK']
    });
  }
  
  return false;
}

// Helper function to check Flask connection (legacy)
async function checkFlaskConnection() {
  try {
    await axios.get(`${FLASK_SERVER_URL}/health`, { timeout: 5000 });
    console.log('Flask server connection established');
  } catch (error) {
    console.error('Failed to connect to Flask server:', error.message);
  }
}

// Handle app errors
process.on('uncaughtException', (error) => {
  console.error('Uncaught Exception:', error);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
});