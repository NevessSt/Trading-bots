import React, { useState, useEffect } from 'react';
import { Bell, Mail, MessageCircle, Smartphone, Check, X, Settings, Save, RefreshCw } from 'lucide-react';
import api from '../services/api';

const NotificationSettings = () => {
  const [preferences, setPreferences] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testingNotifications, setTestingNotifications] = useState({});
  const [message, setMessage] = useState({ type: '', text: '' });
  const [configStatus, setConfigStatus] = useState({
    email: false,
    telegram: false,
    push: false
  });

  const eventTypes = [
    { key: 'trade_executed', label: 'Trade Executed', description: 'When a trade is successfully executed' },
    { key: 'trade_failed', label: 'Trade Failed', description: 'When a trade fails to execute' },
    { key: 'bot_started', label: 'Bot Started', description: 'When a trading bot is started' },
    { key: 'bot_stopped', label: 'Bot Stopped', description: 'When a trading bot is stopped' },
    { key: 'bot_error', label: 'Bot Error', description: 'When a bot encounters an error' },
    { key: 'profit_alert', label: 'Profit Alert', description: 'When profit targets are reached' },
    { key: 'loss_alert', label: 'Loss Alert', description: 'When loss thresholds are exceeded' },
    { key: 'daily_summary', label: 'Daily Summary', description: 'Daily trading performance summary' }
  ];

  const notificationTypes = [
    { key: 'email', label: 'Email', icon: Mail, color: 'text-blue-600' },
    { key: 'telegram', label: 'Telegram', icon: MessageCircle, color: 'text-green-600' },
    { key: 'push', label: 'Push', icon: Smartphone, color: 'text-purple-600' }
  ];

  useEffect(() => {
    loadPreferences();
    checkConfigStatus();
  }, []);

  const loadPreferences = async () => {
    try {
      setLoading(true);
      const response = await api.get('/notifications/preferences');
      
      // Convert array to nested object structure
      const prefsMap = {};
      response.data.forEach(pref => {
        if (!prefsMap[pref.event_type]) {
          prefsMap[pref.event_type] = {};
        }
        prefsMap[pref.event_type][pref.notification_type] = pref.enabled;
      });
      
      setPreferences(prefsMap);
    } catch (error) {
      console.error('Error loading preferences:', error);
      setMessage({ type: 'error', text: 'Failed to load notification preferences' });
    } finally {
      setLoading(false);
    }
  };

  const checkConfigStatus = async () => {
    try {
      const response = await api.get('/notifications/config-status');
      setConfigStatus(response.data);
    } catch (error) {
      console.error('Error checking config status:', error);
    }
  };

  const handlePreferenceChange = (eventType, notificationType, enabled) => {
    setPreferences(prev => ({
      ...prev,
      [eventType]: {
        ...prev[eventType],
        [notificationType]: enabled
      }
    }));
  };

  const savePreferences = async () => {
    try {
      setSaving(true);
      
      // Convert nested object back to array format
      const prefsArray = [];
      Object.entries(preferences).forEach(([eventType, notificationTypes]) => {
        Object.entries(notificationTypes).forEach(([notificationType, enabled]) => {
          prefsArray.push({
            event_type: eventType,
            notification_type: notificationType,
            enabled: enabled
          });
        });
      });
      
      await api.put('/notifications/preferences/bulk', { preferences: prefsArray });
      setMessage({ type: 'success', text: 'Notification preferences saved successfully!' });
      
      setTimeout(() => setMessage({ type: '', text: '' }), 3000);
    } catch (error) {
      console.error('Error saving preferences:', error);
      setMessage({ type: 'error', text: 'Failed to save notification preferences' });
    } finally {
      setSaving(false);
    }
  };

  const testNotification = async (notificationType) => {
    try {
      setTestingNotifications(prev => ({ ...prev, [notificationType]: true }));
      
      await api.post(`/notifications/test/${notificationType}`);
      setMessage({ 
        type: 'success', 
        text: `Test ${notificationType} notification sent successfully!` 
      });
      
      setTimeout(() => setMessage({ type: '', text: '' }), 3000);
    } catch (error) {
      console.error(`Error testing ${notificationType} notification:`, error);
      setMessage({ 
        type: 'error', 
        text: `Failed to send test ${notificationType} notification` 
      });
    } finally {
      setTestingNotifications(prev => ({ ...prev, [notificationType]: false }));
    }
  };

  const getNotificationIcon = (notificationType, enabled, configured) => {
    const IconComponent = notificationTypes.find(nt => nt.key === notificationType)?.icon || Bell;
    const colorClass = notificationTypes.find(nt => nt.key === notificationType)?.color || 'text-gray-600';
    
    if (!configured) {
      return <IconComponent className="w-5 h-5 text-gray-400" />;
    }
    
    return (
      <IconComponent 
        className={`w-5 h-5 ${
          enabled ? colorClass : 'text-gray-400'
        }`} 
      />
    );
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-center py-8">
          <RefreshCw className="w-6 h-6 animate-spin text-blue-600 mr-2" />
          <span>Loading notification settings...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <Settings className="w-6 h-6 text-gray-700 mr-2" />
          <h2 className="text-xl font-semibold text-gray-800">Notification Settings</h2>
        </div>
        <button
          onClick={savePreferences}
          disabled={saving}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {saving ? (
            <RefreshCw className="w-4 h-4 animate-spin mr-2" />
          ) : (
            <Save className="w-4 h-4 mr-2" />
          )}
          {saving ? 'Saving...' : 'Save Settings'}
        </button>
      </div>

      {message.text && (
        <div className={`mb-4 p-3 rounded-lg ${
          message.type === 'success' 
            ? 'bg-green-100 text-green-800 border border-green-200' 
            : 'bg-red-100 text-red-800 border border-red-200'
        }`}>
          {message.text}
        </div>
      )}

      {/* Configuration Status */}
      <div className="mb-6 p-4 bg-gray-50 rounded-lg">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Configuration Status</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {notificationTypes.map(({ key, label, icon: Icon, color }) => {
            const configured = configStatus[key];
            return (
              <div key={key} className="flex items-center justify-between p-3 bg-white rounded border">
                <div className="flex items-center">
                  <Icon className={`w-5 h-5 mr-2 ${configured ? color : 'text-gray-400'}`} />
                  <span className="text-sm font-medium">{label}</span>
                </div>
                <div className="flex items-center">
                  {configured ? (
                    <>
                      <Check className="w-4 h-4 text-green-600 mr-2" />
                      <button
                        onClick={() => testNotification(key)}
                        disabled={testingNotifications[key]}
                        className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 disabled:opacity-50"
                      >
                        {testingNotifications[key] ? 'Testing...' : 'Test'}
                      </button>
                    </>
                  ) : (
                    <>
                      <X className="w-4 h-4 text-red-600 mr-2" />
                      <span className="text-xs text-gray-500">Not configured</span>
                    </>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Notification Preferences Table */}
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-3 px-4 font-medium text-gray-700">Event Type</th>
              {notificationTypes.map(({ key, label, icon: Icon, color }) => (
                <th key={key} className="text-center py-3 px-4 font-medium text-gray-700">
                  <div className="flex items-center justify-center">
                    <Icon className={`w-4 h-4 mr-1 ${color}`} />
                    {label}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {eventTypes.map(({ key, label, description }) => (
              <tr key={key} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="py-4 px-4">
                  <div>
                    <div className="font-medium text-gray-800">{label}</div>
                    <div className="text-sm text-gray-500">{description}</div>
                  </div>
                </td>
                {notificationTypes.map(({ key: notifKey }) => {
                  const enabled = preferences[key]?.[notifKey] || false;
                  const configured = configStatus[notifKey];
                  
                  return (
                    <td key={notifKey} className="py-4 px-4 text-center">
                      <label className="inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={enabled}
                          disabled={!configured}
                          onChange={(e) => handlePreferenceChange(key, notifKey, e.target.checked)}
                          className="sr-only"
                        />
                        <div className={`relative w-10 h-6 rounded-full transition-colors ${
                          !configured 
                            ? 'bg-gray-200 cursor-not-allowed' 
                            : enabled 
                              ? 'bg-blue-600' 
                              : 'bg-gray-300'
                        }`}>
                          <div className={`absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-transform ${
                            enabled && configured ? 'translate-x-4' : 'translate-x-0'
                          }`} />
                        </div>
                      </label>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-6 p-4 bg-blue-50 rounded-lg">
        <h4 className="text-sm font-medium text-blue-800 mb-2">💡 Tips</h4>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>• Configure your notification channels in the system settings before enabling notifications</li>
          <li>• Use the "Test" button to verify your notification setup is working correctly</li>
          <li>• Critical events like trade failures and loss alerts are recommended to be enabled</li>
          <li>• You can customize notification templates for each event type</li>
        </ul>
      </div>
    </div>
  );
};

export default NotificationSettings;