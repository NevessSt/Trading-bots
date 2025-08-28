const { app, BrowserWindow, Menu, ipcMain, dialog, shell } = require('electron');
const { autoUpdater } = require('electron-updater');
const path = require('path');
const isDev = process.argv.includes('--dev');

let mainWindow;
let splashWindow;

// Store for app settings
const settings = {
  theme: 'dark',
  autoStart: false,
  notifications: true,
  autoUpdate: true,
  updateChannel: 'latest'
};

// Auto-updater configuration
if (!isDev) {
  // Configure auto-updater
  autoUpdater.checkForUpdatesAndNotify();
  
  // Set update feed URL (replace with your actual update server)
  autoUpdater.setFeedURL({
    provider: 'github',
    owner: 'trading-bot',
    repo: 'desktop-app',
    private: false
  });
  
  // Auto-updater event handlers
  autoUpdater.on('checking-for-update', () => {
    console.log('Checking for update...');
    if (mainWindow) {
      mainWindow.webContents.send('updater-message', {
        type: 'checking',
        message: 'Checking for updates...'
      });
    }
  });
  
  autoUpdater.on('update-available', (info) => {
    console.log('Update available:', info.version);
    if (mainWindow) {
      mainWindow.webContents.send('updater-message', {
        type: 'available',
        message: `Update available: v${info.version}`,
        version: info.version
      });
    }
  });
  
  autoUpdater.on('update-not-available', (info) => {
    console.log('Update not available');
    if (mainWindow) {
      mainWindow.webContents.send('updater-message', {
        type: 'not-available',
        message: 'You are running the latest version'
      });
    }
  });
  
  autoUpdater.on('error', (err) => {
    console.error('Update error:', err);
    if (mainWindow) {
      mainWindow.webContents.send('updater-message', {
        type: 'error',
        message: 'Update check failed',
        error: err.message
      });
    }
  });
  
  autoUpdater.on('download-progress', (progressObj) => {
    const percent = Math.round(progressObj.percent);
    console.log(`Download progress: ${percent}%`);
    if (mainWindow) {
      mainWindow.webContents.send('updater-message', {
        type: 'download-progress',
        message: `Downloading update: ${percent}%`,
        percent: percent,
        bytesPerSecond: progressObj.bytesPerSecond,
        total: progressObj.total,
        transferred: progressObj.transferred
      });
    }
  });
  
  autoUpdater.on('update-downloaded', (info) => {
    console.log('Update downloaded:', info.version);
    if (mainWindow) {
      mainWindow.webContents.send('updater-message', {
        type: 'downloaded',
        message: `Update v${info.version} downloaded. Restart to apply.`,
        version: info.version
      });
    }
    
    // Show notification to user
    if (settings.notifications) {
      dialog.showMessageBox(mainWindow, {
        type: 'info',
        title: 'Update Ready',
        message: `Trading Bot Desktop v${info.version} is ready to install.`,
        detail: 'The application will restart to apply the update.',
        buttons: ['Restart Now', 'Later'],
        defaultId: 0
      }).then((result) => {
        if (result.response === 0) {
          autoUpdater.quitAndInstall();
        }
      });
    }
  });
}

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

  splashWindow.loadFile('splash.html');
  
  setTimeout(() => {
    if (splashWindow) {
      splashWindow.close();
      splashWindow = null;
    }
    createMainWindow();
  }, 3000);
}

function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1200,
    minHeight: 700,
    show: false,
    icon: path.join(__dirname, 'assets', 'icon.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    }
  });

  mainWindow.loadFile('index.html');

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    if (isDev) {
      mainWindow.webContents.openDevTools();
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Create application menu
  createMenu();
}

function createMenu() {
  const template = [
    {
      label: 'File',
      submenu: [
        {
          label: 'Settings',
          accelerator: 'CmdOrCtrl+,',
          click: () => {
            mainWindow.webContents.send('show-settings');
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
        {
          label: 'Dashboard',
          accelerator: 'CmdOrCtrl+1',
          click: () => {
            mainWindow.webContents.send('navigate-to', 'dashboard');
          }
        },
        {
          label: 'Trading',
          accelerator: 'CmdOrCtrl+2',
          click: () => {
            mainWindow.webContents.send('navigate-to', 'trading');
          }
        },
        {
          label: 'Portfolio',
          accelerator: 'CmdOrCtrl+3',
          click: () => {
            mainWindow.webContents.send('navigate-to', 'portfolio');
          }
        },
        { type: 'separator' },
        {
          label: 'Reload',
          accelerator: 'CmdOrCtrl+R',
          click: () => {
            mainWindow.reload();
          }
        },
        {
          label: 'Toggle Developer Tools',
          accelerator: process.platform === 'darwin' ? 'Alt+Cmd+I' : 'Ctrl+Shift+I',
          click: () => {
            mainWindow.webContents.toggleDevTools();
          }
        }
      ]
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'About',
          click: () => {
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: 'About Trading Bot Desktop',
              message: 'Trading Bot Desktop v1.0.0',
              detail: 'Professional desktop trading application for cryptocurrency markets.'
            });
          }
        },
        {
          label: 'Documentation',
          click: () => {
            shell.openExternal('https://github.com/your-repo/trading-bot');
          }
        }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

// IPC handlers
ipcMain.handle('get-app-version', () => {
  return app.getVersion();
});

ipcMain.handle('get-settings', () => {
  return settings;
});

ipcMain.handle('save-settings', (event, newSettings) => {
  Object.assign(settings, newSettings);
  return settings;
});

ipcMain.handle('show-message-box', async (event, options) => {
  const result = await dialog.showMessageBox(mainWindow, options);
  return result;
});

ipcMain.handle('show-open-dialog', async (event, options) => {
  const result = await dialog.showOpenDialog(mainWindow, options);
  return result;
});

ipcMain.handle('show-save-dialog', async (event, options) => {
  const result = await dialog.showSaveDialog(mainWindow, options);
  return result;
});

ipcMain.handle('open-external', (event, url) => {
  shell.openExternal(url);
});

ipcMain.handle('quit-app', () => {
  app.quit();
});

ipcMain.handle('minimize-app', () => {
  mainWindow.minimize();
});

ipcMain.handle('maximize-app', () => {
  if (mainWindow.isMaximized()) {
    mainWindow.unmaximize();
  } else {
    mainWindow.maximize();
  }
});

// Auto-updater IPC handlers
ipcMain.handle('check-for-updates', async () => {
  if (isDev) {
    return { error: 'Updates not available in development mode' };
  }
  
  try {
    const result = await autoUpdater.checkForUpdates();
    return { success: true, updateInfo: result };
  } catch (error) {
    console.error('Manual update check failed:', error);
    return { error: error.message };
  }
});

ipcMain.handle('download-update', async () => {
  if (isDev) {
    return { error: 'Updates not available in development mode' };
  }
  
  try {
    await autoUpdater.downloadUpdate();
    return { success: true };
  } catch (error) {
    console.error('Update download failed:', error);
    return { error: error.message };
  }
});

ipcMain.handle('install-update', () => {
  if (isDev) {
    return { error: 'Updates not available in development mode' };
  }
  
  autoUpdater.quitAndInstall();
  return { success: true };
});

ipcMain.handle('get-update-info', () => {
  return {
    currentVersion: app.getVersion(),
    autoUpdateEnabled: settings.autoUpdate,
    updateChannel: settings.updateChannel,
    isDev: isDev
  };
});

ipcMain.handle('set-auto-update', (event, enabled) => {
  settings.autoUpdate = enabled;
  
  if (!isDev) {
    if (enabled) {
      autoUpdater.checkForUpdatesAndNotify();
    }
  }
  
  return settings;
});

ipcMain.handle('set-update-channel', (event, channel) => {
  settings.updateChannel = channel;
  
  if (!isDev) {
    // Update the feed URL with new channel if needed
    autoUpdater.setFeedURL({
      provider: 'github',
      owner: 'trading-bot',
      repo: 'desktop-app',
      private: false,
      channel: channel
    });
  }
  
  return settings;
});

// App event handlers
app.whenReady().then(() => {
  createSplashWindow();

  // Set up periodic update checks (every 4 hours)
  if (!isDev && settings.autoUpdate) {
    setInterval(() => {
      autoUpdater.checkForUpdatesAndNotify();
    }, 4 * 60 * 60 * 1000); // 4 hours in milliseconds
  }

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  // Save any pending data
  console.log('App is quitting...');
});

// Security: Prevent new window creation
app.on('web-contents-created', (event, contents) => {
  contents.on('new-window', (navigationEvent, navigationURL) => {
    navigationEvent.preventDefault();
    shell.openExternal(navigationURL);
  });
});