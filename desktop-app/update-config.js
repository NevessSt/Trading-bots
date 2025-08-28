/**
 * Auto-updater configuration for Trading Bot Desktop
 * This file contains configuration for electron-updater
 */

const { autoUpdater } = require('electron-updater');
const { app, dialog } = require('electron');
const isDev = process.env.NODE_ENV === 'development';

class UpdateManager {
  constructor(mainWindow) {
    this.mainWindow = mainWindow;
    this.updateCheckInterval = null;
    this.isUpdateInProgress = false;
    
    if (!isDev) {
      this.setupAutoUpdater();
    }
  }

  setupAutoUpdater() {
    // Configure auto-updater
    autoUpdater.autoDownload = false; // Don't auto-download, let user choose
    autoUpdater.autoInstallOnAppQuit = true;
    
    // Set update server configuration
    autoUpdater.setFeedURL({
      provider: 'github',
      owner: 'trading-bot',
      repo: 'desktop-app',
      private: false,
      releaseType: 'release' // or 'prerelease' for beta versions
    });

    // Event handlers
    autoUpdater.on('checking-for-update', () => {
      this.log('Checking for update...');
      this.sendStatusToRenderer('checking', 'Checking for updates...');
    });

    autoUpdater.on('update-available', (info) => {
      this.log('Update available:', info.version);
      this.sendStatusToRenderer('available', `Update available: v${info.version}`, info);
      
      // Show user notification
      this.showUpdateAvailableDialog(info);
    });

    autoUpdater.on('update-not-available', (info) => {
      this.log('Update not available');
      this.sendStatusToRenderer('not-available', 'You are running the latest version');
    });

    autoUpdater.on('error', (err) => {
      this.log('Update error:', err);
      this.sendStatusToRenderer('error', 'Update check failed', { error: err.message });
      this.isUpdateInProgress = false;
    });

    autoUpdater.on('download-progress', (progressObj) => {
      const percent = Math.round(progressObj.percent);
      this.log(`Download progress: ${percent}%`);
      this.sendStatusToRenderer('download-progress', `Downloading update: ${percent}%`, {
        percent,
        bytesPerSecond: progressObj.bytesPerSecond,
        total: progressObj.total,
        transferred: progressObj.transferred
      });
    });

    autoUpdater.on('update-downloaded', (info) => {
      this.log('Update downloaded:', info.version);
      this.sendStatusToRenderer('downloaded', `Update v${info.version} downloaded. Restart to apply.`, info);
      this.isUpdateInProgress = false;
      
      // Show restart dialog
      this.showUpdateReadyDialog(info);
    });
  }

  async checkForUpdates(showNoUpdateDialog = false) {
    if (isDev) {
      return { error: 'Updates not available in development mode' };
    }

    if (this.isUpdateInProgress) {
      return { error: 'Update check already in progress' };
    }

    try {
      this.isUpdateInProgress = true;
      const result = await autoUpdater.checkForUpdates();
      
      if (showNoUpdateDialog && !result.updateInfo.version) {
        dialog.showMessageBox(this.mainWindow, {
          type: 'info',
          title: 'No Updates',
          message: 'You are running the latest version of Trading Bot Desktop.',
          buttons: ['OK']
        });
      }
      
      return { success: true, updateInfo: result };
    } catch (error) {
      this.isUpdateInProgress = false;
      this.log('Manual update check failed:', error);
      return { error: error.message };
    }
  }

  async downloadUpdate() {
    if (isDev) {
      return { error: 'Updates not available in development mode' };
    }

    try {
      await autoUpdater.downloadUpdate();
      return { success: true };
    } catch (error) {
      this.log('Update download failed:', error);
      return { error: error.message };
    }
  }

  quitAndInstall() {
    if (isDev) {
      return { error: 'Updates not available in development mode' };
    }

    autoUpdater.quitAndInstall();
    return { success: true };
  }

  startPeriodicChecks(intervalHours = 4) {
    if (isDev || this.updateCheckInterval) {
      return;
    }

    const intervalMs = intervalHours * 60 * 60 * 1000;
    this.updateCheckInterval = setInterval(() => {
      this.checkForUpdates(false);
    }, intervalMs);

    // Initial check after 30 seconds
    setTimeout(() => {
      this.checkForUpdates(false);
    }, 30000);
  }

  stopPeriodicChecks() {
    if (this.updateCheckInterval) {
      clearInterval(this.updateCheckInterval);
      this.updateCheckInterval = null;
    }
  }

  showUpdateAvailableDialog(info) {
    if (!this.mainWindow) return;

    dialog.showMessageBox(this.mainWindow, {
      type: 'info',
      title: 'Update Available',
      message: `Trading Bot Desktop v${info.version} is available.`,
      detail: `Current version: v${app.getVersion()}\nNew version: v${info.version}\n\nWould you like to download the update now?`,
      buttons: ['Download Now', 'Download Later', 'View Release Notes'],
      defaultId: 0,
      cancelId: 1
    }).then((result) => {
      switch (result.response) {
        case 0: // Download Now
          this.downloadUpdate();
          break;
        case 2: // View Release Notes
          require('electron').shell.openExternal(`https://github.com/trading-bot/desktop-app/releases/tag/v${info.version}`);
          break;
        default:
          // Download Later - do nothing
          break;
      }
    });
  }

  showUpdateReadyDialog(info) {
    if (!this.mainWindow) return;

    dialog.showMessageBox(this.mainWindow, {
      type: 'info',
      title: 'Update Ready',
      message: `Trading Bot Desktop v${info.version} is ready to install.`,
      detail: 'The application will restart to apply the update. Any unsaved work will be lost.',
      buttons: ['Restart Now', 'Restart Later'],
      defaultId: 0,
      cancelId: 1
    }).then((result) => {
      if (result.response === 0) {
        this.quitAndInstall();
      }
    });
  }

  sendStatusToRenderer(type, message, data = {}) {
    if (this.mainWindow && this.mainWindow.webContents) {
      this.mainWindow.webContents.send('updater-message', {
        type,
        message,
        ...data
      });
    }
  }

  log(...args) {
    console.log('[UpdateManager]', ...args);
  }

  // Getters for current state
  get currentVersion() {
    return app.getVersion();
  }

  get isDevMode() {
    return isDev;
  }

  get isCheckingForUpdates() {
    return this.isUpdateInProgress;
  }
}

module.exports = UpdateManager;