import React, { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useNotificationContext } from '../contexts/NotificationContext';
import { formatDistanceToNow } from 'date-fns';

const NotificationBell = ({ className = '' }) => {
  const {
    recentNotifications,
    unreadCount,
    markAsRead,
    markAllAsRead,
    isConnected
  } = useNotificationContext();
  
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);
  const buttonRef = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && 
          !dropdownRef.current.contains(event.target) &&
          !buttonRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const toggleDropdown = () => {
    setIsOpen(!isOpen);
  };

  const handleNotificationClick = (notification) => {
    if (!notification.read) {
      markAsRead([notification.id]);
    }
  };

  const handleMarkAllRead = () => {
    markAllAsRead();
  };

  const getEventTypeIcon = (eventType) => {
    const icons = {
      'trade_executed': '💰',
      'trade_failed': '❌',
      'bot_started': '🚀',
      'bot_stopped': '⏹️',
      'bot_error': '⚠️',
      'profit_alert': '📈',
      'loss_alert': '📉',
      'daily_summary': '📊',
      'market_alert': '📢',
      'system_alert': '🔔'
    };
    return icons[eventType] || '📬';
  };

  const getEventTypeColor = (eventType) => {
    const colors = {
      'trade_executed': 'text-green-600',
      'trade_failed': 'text-red-600',
      'bot_started': 'text-blue-600',
      'bot_stopped': 'text-gray-600',
      'bot_error': 'text-red-600',
      'profit_alert': 'text-green-600',
      'loss_alert': 'text-red-600',
      'daily_summary': 'text-blue-600',
      'market_alert': 'text-yellow-600',
      'system_alert': 'text-purple-600'
    };
    return colors[eventType] || 'text-gray-600';
  };

  const recentItems = recentNotifications.slice(0, 5);

  return (
    <div className={`relative ${className}`}>
      {/* Bell Button */}
      <button
        ref={buttonRef}
        onClick={toggleDropdown}
        className={`relative p-2 text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white transition-colors duration-200 ${
          !isConnected ? 'opacity-50' : ''
        }`}
        title={isConnected ? 'Notifications' : 'Disconnected from notification service'}
      >
        <svg
          className="w-6 h-6"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
          />
        </svg>
        
        {/* Unread Count Badge */}
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center font-medium">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
        
        {/* Connection Status Indicator */}
        <span className={`absolute -bottom-1 -right-1 w-3 h-3 rounded-full ${
          isConnected ? 'bg-green-400' : 'bg-red-400'
        }`} />
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div
          ref={dropdownRef}
          className="absolute right-0 mt-2 w-80 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50"
        >
          {/* Header */}
          <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Notifications
            </h3>
            <div className="flex items-center space-x-2">
              {unreadCount > 0 && (
                <button
                  onClick={handleMarkAllRead}
                  className="text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                >
                  Mark all read
                </button>
              )}
              <Link
                to="/notifications"
                onClick={() => setIsOpen(false)}
                className="text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
              >
                View all
              </Link>
            </div>
          </div>

          {/* Connection Status */}
          <div className={`px-4 py-2 text-sm flex items-center space-x-2 ${
            isConnected 
              ? 'text-green-600 bg-green-50 dark:bg-green-900/20 dark:text-green-400'
              : 'text-red-600 bg-red-50 dark:bg-red-900/20 dark:text-red-400'
          }`}>
            <span className={`w-2 h-2 rounded-full ${
              isConnected ? 'bg-green-400' : 'bg-red-400'
            }`} />
            <span>
              {isConnected ? 'Connected to notification service' : 'Disconnected from notification service'}
            </span>
          </div>

          {/* Notifications List */}
          <div className="max-h-96 overflow-y-auto">
            {recentItems.length === 0 ? (
              <div className="px-4 py-8 text-center text-gray-500 dark:text-gray-400">
                <svg className="w-12 h-12 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2M4 13h2m13-8l-4 4m0 0l-4-4m4 4V3" />
                </svg>
                <p>No recent notifications</p>
              </div>
            ) : (
              recentItems.map((notification) => (
                <div
                  key={notification.id}
                  onClick={() => handleNotificationClick(notification)}
                  className={`px-4 py-3 border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer transition-colors duration-150 ${
                    !notification.read ? 'bg-blue-50 dark:bg-blue-900/20' : ''
                  }`}
                >
                  <div className="flex items-start space-x-3">
                    {/* Event Icon */}
                    <div className="flex-shrink-0 mt-1">
                      <span className="text-lg">
                        {getEventTypeIcon(notification.event_type)}
                      </span>
                    </div>
                    
                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <p className={`text-sm font-medium truncate ${
                          notification.read 
                            ? 'text-gray-900 dark:text-gray-100' 
                            : 'text-gray-900 dark:text-white'
                        }`}>
                          {notification.subject}
                        </p>
                        {!notification.read && (
                          <span className="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0 ml-2" />
                        )}
                      </div>
                      
                      <p className="text-sm text-gray-600 dark:text-gray-400 truncate mt-1">
                        {notification.content}
                      </p>
                      
                      <div className="flex items-center justify-between mt-2">
                        <span className={`text-xs px-2 py-1 rounded-full ${
                          getEventTypeColor(notification.event_type)
                        } bg-opacity-10`}>
                          {notification.event_type.replace('_', ' ')}
                        </span>
                        
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {formatDistanceToNow(new Date(notification.timestamp), { addSuffix: true })}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          {recentItems.length > 0 && (
            <div className="px-4 py-3 border-t border-gray-200 dark:border-gray-700">
              <Link
                to="/notifications"
                onClick={() => setIsOpen(false)}
                className="block w-full text-center text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 font-medium"
              >
                View all notifications
              </Link>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default NotificationBell;