# Auto-Updater System for Trading Bot Desktop

This document explains the automatic update system implemented in the Trading Bot Desktop application.

## Overview

The auto-updater system provides:
- **Silent background updates** - Checks for updates every 4 hours
- **User-controlled installation** - Users choose when to install updates
- **Progress tracking** - Real-time download progress
- **Rollback safety** - Updates can be deferred or cancelled
- **Cross-platform support** - Works on Windows, macOS, and Linux

## Components

### 1. Main Process (main.js)
- Configures `electron-updater`
- Handles update events
- Manages IPC communication
- Shows native dialogs for user interaction

### 2. Update Manager (update-config.js)
- Centralized update logic
- Periodic update checks
- Error handling and logging
- User notification management

### 3. Renderer Components
- **UpdateManager.jsx** - Settings and manual update interface
- **UpdateNotification.jsx** - Toast notifications for updates
- **UpdateManager.css** & **UpdateNotification.css** - Styling

### 4. Preload Script (preload.js)
- Secure IPC bridge between main and renderer
- Exposes update APIs to React components

## Configuration

### Update Server
Currently configured for GitHub Releases:
```javascript
autoUpdater.setFeedURL({
  provider: 'github',
  owner: 'trading-bot',
  repo: 'desktop-app',
  private: false
});
```

### Update Channels
- **latest** (default) - Stable releases
- **beta** - Beta releases
- **alpha** - Experimental releases

### Check Intervals
- **Automatic**: Every 4 hours
- **Manual**: User-triggered via settings
- **Startup**: 30 seconds after app launch

## User Experience

### Update Flow
1. **Background Check** - App silently checks for updates
2. **Notification** - User sees toast notification if update available
3. **User Choice** - User can download now, later, or view release notes
4. **Download** - Progress shown in real-time
5. **Installation** - User chooses when to restart and install

### Settings
Users can control:
- Enable/disable automatic updates
- Choose update channel (stable/beta/alpha)
- Manual update checks
- View current version info

## Development

### Testing Updates
```bash
# Development mode (updates disabled)
npm run electron-dev

# Production mode (updates enabled)
npm run electron
```

### Building Releases
```bash
# Build for current platform
npm run dist

# Build for specific platforms
npm run dist-win
npm run dist-mac
npm run dist-linux
```

### Publishing Updates
1. Update version in `package.json`
2. Build distributables: `npm run dist`
3. Create GitHub release with built files
4. Tag release with version number
5. Auto-updater will detect new release

## Security

### Code Signing
- **Windows**: Authenticode signing (configure in `package.json`)
- **macOS**: Apple Developer ID signing
- **Linux**: GPG signing for repositories

### Update Verification
- Checksums verified automatically
- Signature validation on signed builds
- HTTPS-only update downloads

## Error Handling

### Common Issues
1. **Network errors** - Retry mechanism with exponential backoff
2. **Insufficient permissions** - Clear error messages
3. **Corrupted downloads** - Automatic re-download
4. **Disk space** - Pre-download space check

### Logging
Update events logged to:
- Console (development)
- Application logs (production)
- User-visible error messages

## API Reference

### IPC Handlers (Main Process)
```javascript
// Check for updates manually
ipcMain.handle('check-for-updates')

// Download available update
ipcMain.handle('download-update')

// Install downloaded update
ipcMain.handle('install-update')

// Get current update info
ipcMain.handle('get-update-info')

// Enable/disable auto-updates
ipcMain.handle('set-auto-update', enabled)

// Set update channel
ipcMain.handle('set-update-channel', channel)
```

### Renderer APIs (via electronAPI)
```javascript
// Check for updates
const result = await window.electronAPI.checkForUpdates();

// Download update
const result = await window.electronAPI.downloadUpdate();

// Install update
const result = await window.electronAPI.installUpdate();

// Get update info
const info = await window.electronAPI.getUpdateInfo();

// Listen for update events
window.electronAPI.onUpdaterMessage((data) => {
  console.log('Update event:', data);
});
```

### Update Events
```javascript
// Event types sent to renderer
{
  type: 'checking' | 'available' | 'not-available' | 'download-progress' | 'downloaded' | 'error',
  message: string,
  version?: string,
  percent?: number,
  error?: string
}
```

## Deployment Checklist

### Before Release
- [ ] Update version in `package.json`
- [ ] Test update flow in staging
- [ ] Verify code signing certificates
- [ ] Check update server configuration
- [ ] Test rollback scenarios

### Release Process
- [ ] Build distributables for all platforms
- [ ] Upload to GitHub Releases
- [ ] Tag release with semantic version
- [ ] Test auto-update detection
- [ ] Monitor update adoption

### Post-Release
- [ ] Monitor error logs
- [ ] Check update success rates
- [ ] Respond to user feedback
- [ ] Plan next release cycle

## Troubleshooting

### Updates Not Working
1. Check internet connection
2. Verify GitHub repository access
3. Check code signing certificates
4. Review application logs
5. Test with manual update check

### Performance Issues
1. Adjust check intervals
2. Optimize download size
3. Use delta updates if available
4. Monitor bandwidth usage

### User Experience Issues
1. Review notification timing
2. Improve error messages
3. Add progress indicators
4. Simplify user choices

## Future Enhancements

### Planned Features
- [ ] Delta updates for smaller downloads
- [ ] Update scheduling (install at specific times)
- [ ] Rollback to previous version
- [ ] Update statistics and analytics
- [ ] Custom update servers
- [ ] Offline update packages

### Performance Optimizations
- [ ] Compressed update packages
- [ ] CDN distribution
- [ ] Bandwidth throttling
- [ ] Background download prioritization

## Support

For issues with the auto-updater system:
1. Check this documentation
2. Review application logs
3. Test in development mode
4. Contact development team
5. File GitHub issue with logs

---

**Note**: This auto-updater system is designed for production use with proper code signing and release management. Always test updates thoroughly before deploying to users.