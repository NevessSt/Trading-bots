import React, { useState, useEffect } from 'react';
import './UpdateNotification.css';

const UpdateNotification = ({ onOpenUpdateManager, onDismiss }) => {
  const [notification, setNotification] = useState(null);
  const [isVisible, setIsVisible] = useState(false);
  const [autoHideTimer, setAutoHideTimer] = useState(null);

  useEffect(() => {
    // Listen for updater messages
    const handleUpdaterMessage = (data) => {
      console.log('Update notification received:', data);
      
      switch (data.type) {
        case 'available':
          showNotification({
            type: 'info',
            title: 'Update Available',
            message: `Version ${data.version} is available for download`,
            action: 'Download',
            persistent: true
          });
          break;
        case 'downloaded':
          showNotification({
            type: 'success',
            title: 'Update Ready',
            message: `Version ${data.version} is ready to install`,
            action: 'Install & Restart',
            persistent: true
          });
          break;
        case 'error':
          showNotification({
            type: 'error',
            title: 'Update Failed',
            message: data.message || 'Failed to check for updates',
            action: 'Retry',
            persistent: false,
            autoHide: 5000
          });
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
      if (autoHideTimer) {
        clearTimeout(autoHideTimer);
      }
    };
  }, [autoHideTimer]);

  const showNotification = (notificationData) => {
    setNotification(notificationData);
    setIsVisible(true);

    // Auto-hide if specified
    if (notificationData.autoHide && !notificationData.persistent) {
      const timer = setTimeout(() => {
        hideNotification();
      }, notificationData.autoHide);
      setAutoHideTimer(timer);
    }
  };

  const hideNotification = () => {
    setIsVisible(false);
    setTimeout(() => {
      setNotification(null);
      if (onDismiss) {
        onDismiss();
      }
    }, 300); // Wait for animation to complete
  };

  const handleActionClick = () => {
    if (notification?.type === 'error') {
      // Retry update check
      if (window.electronAPI) {
        window.electronAPI.checkForUpdates();
      }
    } else {
      // Open update manager
      if (onOpenUpdateManager) {
        onOpenUpdateManager();
      }
    }
    hideNotification();
  };

  const getNotificationIcon = () => {
    switch (notification?.type) {
      case 'info':
        return '📦';
      case 'success':
        return '✅';
      case 'error':
        return '❌';
      case 'warning':
        return '⚠️';
      default:
        return 'ℹ️';
    }
  };

  if (!notification || !isVisible) {
    return null;
  }

  return (
    <div className={`update-notification ${notification.type} ${isVisible ? 'visible' : ''}`}>
      <div className="notification-content">
        <div className="notification-icon">
          {getNotificationIcon()}
        </div>
        
        <div className="notification-text">
          <div className="notification-title">
            {notification.title}
          </div>
          <div className="notification-message">
            {notification.message}
          </div>
        </div>
        
        <div className="notification-actions">
          {notification.action && (
            <button 
              className="notification-action-btn"
              onClick={handleActionClick}
            >
              {notification.action}
            </button>
          )}
          
          <button 
            className="notification-close-btn"
            onClick={hideNotification}
            title="Dismiss"
          >
            ×
          </button>
        </div>
      </div>
      
      {!notification.persistent && notification.autoHide && (
        <div 
          className="notification-progress"
          style={{
            animationDuration: `${notification.autoHide}ms`
          }}
        ></div>
      )}
    </div>
  );
};

export default UpdateNotification;