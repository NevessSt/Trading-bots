import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { useAuth } from './AuthContext';
import { useNotifications, NotificationContainer } from '../components/AlertNotification';
import io from 'socket.io-client';

const NotificationContext = createContext();

export const useNotificationContext = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotificationContext must be used within a NotificationProvider');
  }
  return context;
};

export const NotificationProvider = ({ children }) => {
  const { user, isAuthenticated } = useAuth();
  const {
    notifications,
    addNotification,
    removeNotification,
    clearAllNotifications,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    showTrade
  } = useNotifications();
  
  const [socket, setSocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [recentNotifications, setRecentNotifications] = useState([]);

  // Initialize WebSocket connection
  useEffect(() => {
    if (isAuthenticated && user) {
      const newSocket = io(process.env.REACT_APP_WEBSOCKET_URL || 'http://localhost:5000', {
        auth: {
          token: localStorage.getItem('token')
        },
        transports: ['websocket', 'polling']
      });

      newSocket.on('connect', () => {
        console.log('Connected to notification service');
        setIsConnected(true);
      });

      newSocket.on('disconnect', () => {
        console.log('Disconnected from notification service');
        setIsConnected(false);
      });

      newSocket.on('connect_error', (error) => {
        console.error('WebSocket connection error:', error);
        setIsConnected(false);
      });

      // Listen for real-time notifications
      newSocket.on('notification', (data) => {
        handleRealtimeNotification(data);
      });

      // Listen for trade notifications
      newSocket.on('trade_notification', (data) => {
        handleTradeNotification(data);
      });

      // Listen for system alerts
      newSocket.on('system_alert', (data) => {
        handleSystemAlert(data);
      });

      setSocket(newSocket);

      return () => {
        newSocket.close();
      };
    }
  }, [isAuthenticated, user]);

  // Handle real-time notifications
  const handleRealtimeNotification = useCallback((data) => {
    const { event_type, notification_type, subject, content, status } = data;
    
    // Add to recent notifications list
    const newNotification = {
      id: Date.now(),
      event_type,
      notification_type,
      subject,
      content,
      status,
      timestamp: new Date().toISOString(),
      read: false
    };
    
    setRecentNotifications(prev => [newNotification, ...prev.slice(0, 49)]); // Keep last 50
    setUnreadCount(prev => prev + 1);
    
    // Show toast notification based on event type
    const notificationConfig = getNotificationConfig(event_type);
    
    if (notificationConfig.showToast) {
      const toastMethod = getToastMethod(event_type);
      toastMethod(subject || notificationConfig.defaultTitle, content, {
        autoClose: notificationConfig.autoClose,
        duration: notificationConfig.duration
      });
    }
  }, [showSuccess, showError, showWarning, showInfo, showTrade]);

  // Handle trade-specific notifications
  const handleTradeNotification = useCallback((data) => {
    const { trade_id, symbol, side, quantity, price, status, profit_loss } = data;
    
    let title, message, type;
    
    if (status === 'executed') {
      title = `Trade Executed: ${symbol}`;
      message = `${side.toUpperCase()} ${quantity} at $${price}`;
      type = 'trade';
      
      if (profit_loss) {
        message += ` (P/L: ${profit_loss > 0 ? '+' : ''}$${profit_loss.toFixed(2)})`;
        type = profit_loss > 0 ? 'success' : 'error';
      }
    } else if (status === 'failed') {
      title = `Trade Failed: ${symbol}`;
      message = `Failed to ${side.toLowerCase()} ${quantity} at $${price}`;
      type = 'error';
    }
    
    const toastMethod = type === 'success' ? showSuccess : 
                       type === 'error' ? showError : showTrade;
    
    toastMethod(title, message, { duration: 8000 });
    
    // Add to recent notifications
    const newNotification = {
      id: Date.now(),
      event_type: 'trade_' + status,
      notification_type: 'realtime',
      subject: title,
      content: message,
      status: 'sent',
      timestamp: new Date().toISOString(),
      read: false,
      trade_data: { trade_id, symbol, side, quantity, price, status, profit_loss }
    };
    
    setRecentNotifications(prev => [newNotification, ...prev.slice(0, 49)]);
    setUnreadCount(prev => prev + 1);
  }, [showSuccess, showError, showTrade]);

  // Handle system alerts
  const handleSystemAlert = useCallback((data) => {
    const { alert_type, title, message, severity } = data;
    
    const toastMethod = severity === 'high' ? showError :
                       severity === 'medium' ? showWarning : showInfo;
    
    toastMethod(title, message, { 
      duration: severity === 'high' ? 10000 : 6000,
      autoClose: severity !== 'high' // High severity alerts require manual dismissal
    });
    
    // Add to recent notifications
    const newNotification = {
      id: Date.now(),
      event_type: 'system_alert',
      notification_type: 'realtime',
      subject: title,
      content: message,
      status: 'sent',
      timestamp: new Date().toISOString(),
      read: false,
      alert_data: { alert_type, severity }
    };
    
    setRecentNotifications(prev => [newNotification, ...prev.slice(0, 49)]);
    setUnreadCount(prev => prev + 1);
  }, [showError, showWarning, showInfo]);

  // Get notification configuration based on event type
  const getNotificationConfig = (eventType) => {
    const configs = {
      'trade_executed': {
        showToast: true,
        defaultTitle: 'Trade Executed',
        autoClose: true,
        duration: 6000
      },
      'trade_failed': {
        showToast: true,
        defaultTitle: 'Trade Failed',
        autoClose: true,
        duration: 8000
      },
      'bot_started': {
        showToast: true,
        defaultTitle: 'Bot Started',
        autoClose: true,
        duration: 4000
      },
      'bot_stopped': {
        showToast: true,
        defaultTitle: 'Bot Stopped',
        autoClose: true,
        duration: 4000
      },
      'bot_error': {
        showToast: true,
        defaultTitle: 'Bot Error',
        autoClose: false,
        duration: 10000
      },
      'profit_alert': {
        showToast: true,
        defaultTitle: 'Profit Alert',
        autoClose: true,
        duration: 6000
      },
      'loss_alert': {
        showToast: true,
        defaultTitle: 'Loss Alert',
        autoClose: false,
        duration: 10000
      },
      'daily_summary': {
        showToast: true,
        defaultTitle: 'Daily Summary',
        autoClose: true,
        duration: 8000
      }
    };
    
    return configs[eventType] || {
      showToast: true,
      defaultTitle: 'Notification',
      autoClose: true,
      duration: 5000
    };
  };

  // Get appropriate toast method based on event type
  const getToastMethod = (eventType) => {
    const methodMap = {
      'trade_executed': showTrade,
      'trade_failed': showError,
      'bot_started': showSuccess,
      'bot_stopped': showInfo,
      'bot_error': showError,
      'profit_alert': showSuccess,
      'loss_alert': showError,
      'daily_summary': showInfo
    };
    
    return methodMap[eventType] || showInfo;
  };

  // Mark notifications as read
  const markAsRead = useCallback((notificationIds) => {
    setRecentNotifications(prev => 
      prev.map(notif => 
        notificationIds.includes(notif.id) 
          ? { ...notif, read: true }
          : notif
      )
    );
    
    const unreadIds = notificationIds.filter(id => 
      recentNotifications.find(n => n.id === id && !n.read)
    );
    
    setUnreadCount(prev => Math.max(0, prev - unreadIds.length));
  }, [recentNotifications]);

  // Mark all as read
  const markAllAsRead = useCallback(() => {
    setRecentNotifications(prev => 
      prev.map(notif => ({ ...notif, read: true }))
    );
    setUnreadCount(0);
  }, []);

  // Clear recent notifications
  const clearRecentNotifications = useCallback(() => {
    setRecentNotifications([]);
    setUnreadCount(0);
  }, []);

  // Send test notification
  const sendTestNotification = useCallback((type = 'info') => {
    const testMessages = {
      success: { title: 'Test Success', message: 'This is a test success notification' },
      error: { title: 'Test Error', message: 'This is a test error notification' },
      warning: { title: 'Test Warning', message: 'This is a test warning notification' },
      info: { title: 'Test Info', message: 'This is a test info notification' },
      trade: { title: 'Test Trade', message: 'BUY 100 BTC at $45,000' }
    };
    
    const { title, message } = testMessages[type] || testMessages.info;
    const toastMethod = {
      success: showSuccess,
      error: showError,
      warning: showWarning,
      info: showInfo,
      trade: showTrade
    }[type] || showInfo;
    
    toastMethod(title, message);
  }, [showSuccess, showError, showWarning, showInfo, showTrade]);

  const value = {
    // WebSocket connection
    socket,
    isConnected,
    
    // Toast notifications
    notifications,
    addNotification,
    removeNotification,
    clearAllNotifications,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    showTrade,
    
    // Recent notifications
    recentNotifications,
    unreadCount,
    markAsRead,
    markAllAsRead,
    clearRecentNotifications,
    
    // Utilities
    sendTestNotification
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
      <NotificationContainer 
        notifications={notifications} 
        onRemove={removeNotification}
        position="top-right"
      />
    </NotificationContext.Provider>
  );
};

export default NotificationContext;