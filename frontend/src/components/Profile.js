import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import toast from 'react-hot-toast';

const Profile = () => {
  const { user, token } = useAuth();
  const [settings, setSettings] = useState({
    email: '',
    notifications: {
      email: true,
      telegram: false,
      trade: true,
      market: true,
      security: true
    },
    riskPercentage: 2,
    stopLoss: 5
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user) {
      setSettings(prev => ({
        ...prev,
        email: user.email || ''
      }));
    }
  }, [user]);

  const handleSave = async () => {
    setLoading(true);
    try {
      await axios.put('/api/user/settings', settings, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Settings saved successfully!');
    } catch (error) {
      toast.error('Failed to save settings');
    } finally {
      setLoading(false);
    }
  };

  const handleNotificationChange = (type) => {
    setSettings(prev => ({
      ...prev,
      notifications: {
        ...prev.notifications,
        [type]: !prev.notifications[type]
      }
    }));
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-lg p-6">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-6">
          Profile Settings
        </h1>

        {/* Email Settings */}
        <div className="mb-6">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-3">
            Email Settings
          </h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Email Address
              </label>
              <input
                type="email"
                value={settings.email}
                onChange={(e) => setSettings(prev => ({ ...prev, email: e.target.value }))}
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-md bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100"
              />
            </div>
          </div>
        </div>

        {/* Notification Settings */}
        <div className="mb-6">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-3">
            Notification Settings
          </h2>
          <div className="space-y-3">
            {Object.entries({
              email: 'Email Notifications',
              telegram: 'Telegram Notifications',
              trade: 'Trade Notifications',
              market: 'Market Notifications',
              security: 'Security Notifications'
            }).map(([key, label]) => (
              <div key={key} className="flex items-center justify-between">
                <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                  {label}
                </span>
                <button
                  onClick={() => handleNotificationChange(key)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    settings.notifications[key]
                      ? 'bg-blue-600'
                      : 'bg-slate-200 dark:bg-slate-600'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      settings.notifications[key] ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Risk Management */}
        <div className="mb-6">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-3">
            Risk Management
          </h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Risk Percentage: {settings.riskPercentage}%
              </label>
              <input
                type="range"
                min="1"
                max="10"
                value={settings.riskPercentage}
                onChange={(e) => setSettings(prev => ({ ...prev, riskPercentage: parseInt(e.target.value) }))}
                className="w-full"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Stop Loss: {settings.stopLoss}%
              </label>
              <input
                type="range"
                min="1"
                max="20"
                value={settings.stopLoss}
                onChange={(e) => setSettings(prev => ({ ...prev, stopLoss: parseInt(e.target.value) }))}
                className="w-full"
              />
            </div>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex justify-end">
          <button
            onClick={handleSave}
            disabled={loading}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded-md font-medium transition-colors"
          >
            {loading ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Profile;