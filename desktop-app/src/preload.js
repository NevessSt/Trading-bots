const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // App info
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  
  // Settings
  getSettings: () => ipcRenderer.invoke('get-settings'),
  saveSettings: (settings) => ipcRenderer.invoke('save-settings', settings),
  getBackendUrl: () => ipcRenderer.invoke('get-backend-url'),
  setBackendUrl: (url) => ipcRenderer.invoke('set-backend-url', url),
  
  // Dialogs
  showSaveDialog: (options) => ipcRenderer.invoke('show-save-dialog', options),
  showOpenDialog: (options) => ipcRenderer.invoke('show-open-dialog', options),
  showMessageBox: (options) => ipcRenderer.invoke('show-message-box', options),
  
  // External links
  openExternal: (url) => ipcRenderer.invoke('open-external', url),
  
  // App control
  restartApp: () => ipcRenderer.invoke('restart-app'),
  
  // Event listeners
  onWSConnected: (callback) => {
    ipcRenderer.on('ws-connected', callback);
  },
  onWSDisconnected: (callback) => {
    ipcRenderer.on('ws-disconnected', callback);
  },
  onWSMessage: (callback) => {
    ipcRenderer.on('ws-message', (event, data) => callback(data));
  },
  onOpenSettings: (callback) => {
    ipcRenderer.on('open-settings', callback);
  },
  onUpdateAvailable: (callback) => {
    ipcRenderer.on('update-available', (event, info) => callback(info));
  },
  onDownloadProgress: (callback) => {
    ipcRenderer.on('download-progress', (event, progress) => callback(progress));
  },
  onUpdateDownloaded: (callback) => {
    ipcRenderer.on('update-downloaded', (event, info) => callback(info));
  },
  
  // Remove listeners
  removeAllListeners: (channel) => {
    ipcRenderer.removeAllListeners(channel);
  },
  
  // Setup wizard
  getSetupStatus: () => ipcRenderer.invoke('get-setup-status'),
  saveSetupConfig: (config) => ipcRenderer.invoke('save-setup-config', config),
  skipSetup: () => ipcRenderer.invoke('skip-setup'),
  resetSetup: () => ipcRenderer.invoke('reset-setup'),
  testApiConnection: (apiConfig) => ipcRenderer.invoke('test-api-connection', apiConfig)
});

// Expose a limited API for WebSocket communication
contextBridge.exposeInMainWorld('wsAPI', {
  send: (data) => {
    // This would be handled by the main process WebSocket connection
    ipcRenderer.send('ws-send', data);
  }
});

// Expose system information
contextBridge.exposeInMainWorld('systemAPI', {
  platform: process.platform,
  arch: process.arch,
  versions: process.versions
});