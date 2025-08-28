import React, { useState, useEffect } from 'react';
import './UpdateManager.css';

const UpdateManager = ({ onClose }) => {
  const [updateInfo, setUpdateInfo] = useState(null);
  const [updateStatus, setUpdateStatus] = useState('idle');
  const [downloadProgress, setDownloadProgress] = useState(0);
  const [autoUpdateEnabled, setAutoUpdateEnabled] = useState(true);
  const [updateChannel, setUpdateChannel] = useState('latest');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Load initial update info
    loadUpdateInfo();

    // Listen for updater messages
    const handleUpdaterMessage = (data) => {
      console.log('Updater message:', data);
      
      switch (data.type) {
        case 'checking':
          setUpdateStatus('checking');
          setError(null);
          break;
        case 'available':
          setUpdateStatus('available');
          setError(null);
          break;
        case 'not-available':
          setUpdateStatus('up-to-date');
          setError(null);
          break;
        case 'download-progress':
          setUpdateStatus('downloading');
          setDownloadProgress(data.percent);
          setError(null);
          break;
        case 'downloaded':
          setUpdateStatus('ready');
          setDownloadProgress(100);
          setError(null);
          break;
        case 'error':
          setUpdateStatus('error');
          setError(data.error || data.message);
          break;
        default:
          break;
      }
    };

    if (window.electronAPI) {
      window.electronAPI.onUpdaterMessage(handleUpdaterMessage);
    }

    return () => {
      if (window.electronAPI) {
        window.electronAPI.removeAllListeners('updater-message');
      }
    };
  }, []);

  const loadUpdateInfo = async () => {
    try {
      if (window.electronAPI) {
        const info = await window.electronAPI.getUpdateInfo();
        setUpdateInfo(info);
        setAutoUpdateEnabled(info.autoUpdateEnabled);
        setUpdateChannel(info.updateChannel);
      }
    } catch (error) {
      console.error('Failed to load update info:', error);
      setError('Failed to load update information');
    }
  };

  const handleCheckForUpdates = async () => {
    setIsLoading(true);
    setError(null);
    setUpdateStatus('checking');
    
    try {
      if (window.electronAPI) {
        const result = await window.electronAPI.checkForUpdates();
        if (result.error) {
          setError(result.error);
          setUpdateStatus('error');
        }
      }
    } catch (error) {
      console.error('Update check failed:', error);
      setError('Failed to check for updates');
      setUpdateStatus('error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownloadUpdate = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      if (window.electronAPI) {
        const result = await window.electronAPI.downloadUpdate();
        if (result.error) {
          setError(result.error);
          setUpdateStatus('error');
        }
      }
    } catch (error) {
      console.error('Update download failed:', error);
      setError('Failed to download update');
      setUpdateStatus('error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleInstallUpdate = async () => {
    try {
      if (window.electronAPI) {
        await window.electronAPI.installUpdate();
      }
    } catch (error) {
      console.error('Update installation failed:', error);
      setError('Failed to install update');
    }
  };

  const handleAutoUpdateToggle = async (enabled) => {
    try {
      if (window.electronAPI) {
        await window.electronAPI.setAutoUpdate(enabled);
        setAutoUpdateEnabled(enabled);
      }
    } catch (error) {
      console.error('Failed to update auto-update setting:', error);
      setError('Failed to update settings');
    }
  };

  const handleChannelChange = async (channel) => {
    try {
      if (window.electronAPI) {
        await window.electronAPI.setUpdateChannel(channel);
        setUpdateChannel(channel);
      }
    } catch (error) {
      console.error('Failed to update channel:', error);
      setError('Failed to update channel');
    }
  };

  const getStatusMessage = () => {
    switch (updateStatus) {
      case 'checking':
        return 'Checking for updates...';
      case 'available':
        return 'Update available!';
      case 'downloading':
        return `Downloading update... ${downloadProgress}%`;
      case 'ready':
        return 'Update ready to install';
      case 'up-to-date':
        return 'You are running the latest version';
      case 'error':
        return 'Update check failed';
      default:
        return 'Ready to check for updates';
    }
  };

  const getStatusIcon = () => {
    switch (updateStatus) {
      case 'checking':
        return '🔄';
      case 'available':
        return '📦';
      case 'downloading':
        return '⬇️';
      case 'ready':
        return '✅';
      case 'up-to-date':
        return '✅';
      case 'error':
        return '❌';
      default:
        return '🔍';
    }
  };

  if (updateInfo?.isDev) {
    return (
      <div className="update-manager">
        <div className="update-header">
          <h2>Update Manager</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
        <div className="update-content">
          <div className="dev-notice">
            <h3>Development Mode</h3>
            <p>Auto-updates are not available in development mode.</p>
            <p>Current version: {updateInfo.currentVersion}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="update-manager">
      <div className="update-header">
        <h2>Update Manager</h2>
        <button className="close-btn" onClick={onClose}>×</button>
      </div>
      
      <div className="update-content">
        <div className="current-version">
          <h3>Current Version</h3>
          <p className="version-number">{updateInfo?.currentVersion || 'Unknown'}</p>
        </div>

        <div className="update-status">
          <div className="status-indicator">
            <span className="status-icon">{getStatusIcon()}</span>
            <span className="status-text">{getStatusMessage()}</span>
          </div>
          
          {updateStatus === 'downloading' && (
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${downloadProgress}%` }}
              ></div>
            </div>
          )}
          
          {error && (
            <div className="error-message">
              <span className="error-icon">⚠️</span>
              <span>{error}</span>
            </div>
          )}
        </div>

        <div className="update-actions">
          <button 
            className="btn btn-primary"
            onClick={handleCheckForUpdates}
            disabled={isLoading || updateStatus === 'checking'}
          >
            {updateStatus === 'checking' ? 'Checking...' : 'Check for Updates'}
          </button>
          
          {updateStatus === 'available' && (
            <button 
              className="btn btn-secondary"
              onClick={handleDownloadUpdate}
              disabled={isLoading}
            >
              Download Update
            </button>
          )}
          
          {updateStatus === 'ready' && (
            <button 
              className="btn btn-success"
              onClick={handleInstallUpdate}
            >
              Install & Restart
            </button>
          )}
        </div>

        <div className="update-settings">
          <h3>Update Settings</h3>
          
          <div className="setting-item">
            <label className="setting-label">
              <input
                type="checkbox"
                checked={autoUpdateEnabled}
                onChange={(e) => handleAutoUpdateToggle(e.target.checked)}
              />
              <span>Enable automatic updates</span>
            </label>
            <p className="setting-description">
              Automatically check for and download updates in the background
            </p>
          </div>
          
          <div className="setting-item">
            <label className="setting-label">
              Update Channel:
              <select 
                value={updateChannel} 
                onChange={(e) => handleChannelChange(e.target.value)}
                className="setting-select"
              >
                <option value="latest">Stable (Recommended)</option>
                <option value="beta">Beta</option>
                <option value="alpha">Alpha (Experimental)</option>
              </select>
            </label>
            <p className="setting-description">
              Choose which type of updates to receive
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UpdateManager;