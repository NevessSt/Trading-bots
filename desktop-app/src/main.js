const { app, BrowserWindow, Menu, ipcMain, dialog, shell, Notification } = require('electron');
const { autoUpdater } = require('electron-updater');
const Store = require('electron-store');
const path = require('path');
const isDev = require('electron-is-dev');
const axios = require('axios');
const WebSocket = require('ws');

// Initialize electron store for settings
const store = new Store();

let mainWindow;
let splashWindow;
let backendProcess;
let wsConnection;

// Backend API configuration
const BACKEND_URL = store.get('backend_url', 'http://localhost:5000');
const WS_URL = store.get('ws_url', 'ws://localhost:8765');

function createSplashWindow() {
  splashWindow = new BrowserWindow({
    width: 400,
    height: 300,
    frame: false,
    alwaysOnTop: true,
    transparent: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    }
  });

  splashWindow.loadFile(path.join(__dirname, '../assets/splash.html'));
  
  splashWindow.on('closed', () => {
    splashWindow = null;
  });
}

function createMainWindow() {
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1200,
    minHeight: 800,
    show: false,
    icon: path.join(__dirname, '../assets/icon.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      preload: path.join(__dirname, 'preload.js')
    }
  });

  // Load the app
  const startUrl = isDev 
    ? 'http://localhost:3000' 
    : `file://${path.join(__dirname, '../build/index.html')}`;
  
  mainWindow.loadURL(startUrl);

  // Show window when ready
  mainWindow.once('ready-to-show', () => {
    if (splashWindow) {
      splashWindow.close();
    }
    mainWindow.show();
    
    // Focus on window
    if (isDev) {
      mainWindow.webContents.openDevTools();
    }
  });

  // Handle window closed
  mainWindow.on('closed', () => {
    mainWindow = null;
    if (wsConnection) {
      wsConnection.close();
    }
  });

  // Handle external links
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });
}

// App event handlers
app.whenReady().then(() => {
  createSplashWindow();
  
  // Check backend connection
  setTimeout(() => {
    checkBackendConnection();
  }, 2000);
  
  // Setup auto updater
  if (!isDev) {
    autoUpdater.checkForUpdatesAndNotify();
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createMainWindow();
  }
});

// Backend connection check
async function checkBackendConnection() {
  try {
    const response = await axios.get(`${BACKEND_URL}/api/health`, {
      timeout: 5000
    });
    
    if (response.status === 200) {
      createMainWindow();
      connectWebSocket();
    } else {
      showBackendError();
    }
  } catch (error) {
    console.error('Backend connection failed:', error.message);
    showBackendError();
  }
}

function showBackendError() {
  dialog.showErrorBox(
    'Backend Connection Failed',
    'Could not connect to TradingBot Pro backend.\n\nPlease ensure the backend server is running or check your connection settings.'
  );
  
  // Still create main window but show connection error
  createMainWindow();
}

// WebSocket connection
function connectWebSocket() {
  try {
    wsConnection = new WebSocket(WS_URL);
    
    wsConnection.on('open', () => {
      console.log('WebSocket connected');
      if (mainWindow) {
        mainWindow.webContents.send('ws-connected');
      }
    });
    
    wsConnection.on('message', (data) => {
      try {
        const message = JSON.parse(data);
        if (mainWindow) {
          mainWindow.webContents.send('ws-message', message);
        }
        
        // Show notifications for important events
        if (message.type === 'trade_executed' || message.type === 'alert') {
          showNotification(message);
        }
      } catch (error) {
        console.error('WebSocket message parse error:', error);
      }
    });
    
    wsConnection.on('close', () => {
      console.log('WebSocket disconnected');
      if (mainWindow) {
        mainWindow.webContents.send('ws-disconnected');
      }
      
      // Attempt to reconnect after 5 seconds
      setTimeout(connectWebSocket, 5000);
    });
    
    wsConnection.on('error', (error) => {
      console.error('WebSocket error:', error);
    });
  } catch (error) {
    console.error('WebSocket connection failed:', error);
  }
}

// Notification system
function showNotification(message) {
  if (Notification.isSupported()) {
    const notification = new Notification({
      title: 'TradingBot Pro',
      body: message.message || message.text || 'Trading update',
      icon: path.join(__dirname, '../assets/icon.png')
    });
    
    notification.show();
    
    notification.on('click', () => {
      if (mainWindow) {
        mainWindow.focus();
      }
    });
  }
}

// IPC handlers
ipcMain.handle('get-app-version', () => {
  return app.getVersion();
});

ipcMain.handle('get-backend-url', () => {
  return store.get('backend_url', 'http://localhost:5000');
});

ipcMain.handle('set-backend-url', (event, url) => {
  store.set('backend_url', url);
  return true;
});

ipcMain.handle('get-settings', () => {
  return {
    backend_url: store.get('backend_url', 'http://localhost:5000'),
    ws_url: store.get('ws_url', 'ws://localhost:8765'),
    notifications: store.get('notifications', true),
    auto_start: store.get('auto_start', false),
    theme: store.get('theme', 'dark')
  };
});

ipcMain.handle('save-settings', (event, settings) => {
  Object.keys(settings).forEach(key => {
    store.set(key, settings[key]);
  });
  return true;
});

ipcMain.handle('show-save-dialog', async (event, options) => {
  const result = await dialog.showSaveDialog(mainWindow, options);
  return result;
});

ipcMain.handle('show-open-dialog', async (event, options) => {
  const result = await dialog.showOpenDialog(mainWindow, options);
  return result;
});

ipcMain.handle('show-message-box', async (event, options) => {
  const result = await dialog.showMessageBox(mainWindow, options);
  return result;
});

ipcMain.handle('open-external', (event, url) => {
  shell.openExternal(url);
});

ipcMain.handle('restart-app', () => {
  app.relaunch();
  app.exit();
});

// Setup wizard IPC handlers
ipcMain.handle('get-setup-status', () => {
  return {
    completed: store.get('setup_completed', false),
    skipped: store.get('setup_skipped', false)
  };
});

ipcMain.handle('save-setup-config', (event, config) => {
  // Save API configuration
  if (config.apiConfig) {
    store.set('api_config', config.apiConfig);
  }
  
  // Save trading preferences
  if (config.tradingPrefs) {
    store.set('trading_preferences', config.tradingPrefs);
  }
  
  // Save risk settings
  if (config.riskSettings) {
    store.set('risk_settings', config.riskSettings);
  }
  
  // Mark setup as completed
  store.set('setup_completed', true);
  store.set('setup_skipped', false);
  
  return true;
});

ipcMain.handle('skip-setup', () => {
  store.set('setup_skipped', true);
  store.set('setup_completed', false);
  return true;
});

ipcMain.handle('reset-setup', () => {
  store.delete('setup_completed');
  store.delete('setup_skipped');
  store.delete('api_config');
  store.delete('trading_preferences');
  store.delete('risk_settings');
  return true;
});

ipcMain.handle('test-api-connection', async (event, apiConfig) => {
  try {
    // Simulate API connection test
    // In a real implementation, this would test the actual API connection
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Mock validation - in real app, validate actual API credentials
    if (apiConfig.apiKey && apiConfig.apiSecret && apiConfig.exchange) {
      return { success: true, message: 'API connection successful' };
    } else {
      return { success: false, message: 'Invalid API credentials' };
    }
  } catch (error) {
    return { success: false, message: error.message };
  }
});

// Auto updater events
autoUpdater.on('checking-for-update', () => {
  console.log('Checking for update...');
});

autoUpdater.on('update-available', (info) => {
  console.log('Update available.');
  if (mainWindow) {
    mainWindow.webContents.send('update-available', info);
  }
});

autoUpdater.on('update-not-available', (info) => {
  console.log('Update not available.');
});

autoUpdater.on('error', (err) => {
  console.log('Error in auto-updater. ' + err);
});

autoUpdater.on('download-progress', (progressObj) => {
  if (mainWindow) {
    mainWindow.webContents.send('download-progress', progressObj);
  }
});

autoUpdater.on('update-downloaded', (info) => {
  console.log('Update downloaded');
  if (mainWindow) {
    mainWindow.webContents.send('update-downloaded', info);
  }
});

// Menu template
const menuTemplate = [
  {
    label: 'File',
    submenu: [
      {
        label: 'Settings',
        accelerator: 'CmdOrCtrl+,',
        click: () => {
          if (mainWindow) {
            mainWindow.webContents.send('open-settings');
          }
        }
      },
      { type: 'separator' },
      {
        label: 'Exit',
        accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
        click: () => {
          app.quit();
        }
      }
    ]
  },
  {
    label: 'View',
    submenu: [
      { role: 'reload' },
      { role: 'forceReload' },
      { role: 'toggleDevTools' },
      { type: 'separator' },
      { role: 'resetZoom' },
      { role: 'zoomIn' },
      { role: 'zoomOut' },
      { type: 'separator' },
      { role: 'togglefullscreen' }
    ]
  },
  {
    label: 'Window',
    submenu: [
      { role: 'minimize' },
      { role: 'close' }
    ]
  },
  {
    label: 'Help',
    submenu: [
      {
        label: 'About TradingBot Pro',
        click: () => {
          dialog.showMessageBox(mainWindow, {
            type: 'info',
            title: 'About TradingBot Pro',
            message: 'TradingBot Pro',
            detail: `Version: ${app.getVersion()}\nProfessional Cryptocurrency Trading Bot\n\n© 2024 TradingBot Pro. All rights reserved.`
          });
        }
      },
      {
        label: 'Documentation',
        click: () => {
          shell.openExternal('https://github.com/NevessSt/Trading-bots');
        }
      }
    ]
  }
];

// Set application menu
Menu.setApplicationMenu(Menu.buildFromTemplate(menuTemplate));