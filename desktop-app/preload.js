const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // Data operations
  getStagingData: (filters) => ipcRenderer.invoke('get-staging-data', filters),
  getGroupedStagingData: () => ipcRenderer.invoke('get-grouped-staging-data'),
  
  // Enhanced automation operations
  startAutomation: (selectedIds) => ipcRenderer.invoke('start-automation', selectedIds),
  processSelectedData: (selectedData) => ipcRenderer.invoke('process-selected-data', selectedData),
  stopAutomation: () => ipcRenderer.invoke('stop-automation'),
  stopProcessing: () => ipcRenderer.invoke('stop-processing'),
  getAutomationStatus: () => ipcRenderer.invoke('get-automation-status'),
  getProcessingProgress: () => ipcRenderer.invoke('get-processing-progress'),
  getCrosscheckResults: () => ipcRenderer.invoke('get-crosscheck-results'),
  
  // Browser operations
  initializeBrowser: () => ipcRenderer.invoke('initialize-browser'),
  getBrowserStatus: () => ipcRenderer.invoke('get-browser-status'),
  
  // Settings operations
  getSettings: () => ipcRenderer.invoke('get-settings'),
  saveSettings: (settings) => ipcRenderer.invoke('save-settings', settings),
  
  // Connection operations
  checkFlaskConnection: () => ipcRenderer.invoke('check-flask-connection'),
  
  // Dialog operations
  showInfoDialog: (title, message) => ipcRenderer.invoke('show-info-dialog', title, message),
  showErrorDialog: (title, message) => ipcRenderer.invoke('show-error-dialog', title, message),
  
  // Startup sequence event listeners
  onInitialDataLoaded: (callback) => {
    ipcRenderer.on('initial-data-loaded', callback);
    // Return cleanup function
    return () => ipcRenderer.removeListener('initial-data-loaded', callback);
  },
  
  onBrowserInitializationStarted: (callback) => {
    ipcRenderer.on('browser-initialization-started', callback);
    return () => ipcRenderer.removeListener('browser-initialization-started', callback);
  },
  
  onBrowserInitializationCompleted: (callback) => {
    ipcRenderer.on('browser-initialization-completed', callback);
    return () => ipcRenderer.removeListener('browser-initialization-completed', callback);
  },
  
  // Utility methods
  platform: process.platform,
  versions: process.versions
});

// Log that preload script has loaded
console.log('Preload script loaded successfully');