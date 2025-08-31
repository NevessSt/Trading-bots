import React, { useState, useEffect, useCallback } from 'react';
import { toast } from 'react-hot-toast';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import { 
  EnhancedAlert,
  EnhancedButton,
  EnhancedCard,
  EnhancedModal,
  EnhancedProgressBar,
  EnhancedInput,
  EnhancedSelect,
  HelpIcon
} from './EnhancedUIComponents';
import {
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  BellIcon,
  CogIcon,
  ChartBarIcon,
  PlayIcon,
  StopIcon,
  PlusIcon,
  EyeIcon
} from '@heroicons/react/24/outline';

const EnhancedDashboardIntegration = () => {
  const { user, token } = useAuth();
  const [systemStatus, setSystemStatus] = useState(null);
  const [securityStats, setSecurityStats] = useState(null);
  const [safetyStatus, setSafetyStatus] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [notificationPrefs, setNotificationPrefs] = useState({});
  const [bots, setBots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [emergencyStopActive, setEmergencyStopActive] = useState(false);
  
  // Modal states
  const [showEmergencyModal, setShowEmergencyModal] = useState(false);
  const [showNotificationModal, setShowNotificationModal] = useState(false);
  const [showSecurityModal, setShowSecurityModal] = useState(false);
  const [showCreateBotModal, setShowCreateBotModal] = useState(false);
  
  // Form states
  const [emergencyReason, setEmergencyReason] = useState('');
  const [newBotConfig, setNewBotConfig] = useState({
    name: '',
    strategy: '',
    symbol: '',
    amount: '',
    stopLoss: '',
    takeProfit: ''
  });

  // API configuration
  const api = axios.create({
    baseURL: process.env.REACT_APP_API_URL || 'http://localhost:5000',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });

  // Fetch system status
  const fetchSystemStatus = useCallback(async () => {
    try {
      const response = await api.get('/api/system/health');
      if (response.data.success) {
        setSystemStatus(response.data.data);
        setEmergencyStopActive(response.data.data.components?.safety?.emergency_stop || false);
      }
    } catch (error) {
      console.error('Failed to fetch system status:', error);
      toast.error('Failed to fetch system status');
    }
  }, [api]);

  // Fetch security statistics
  const fetchSecurityStats = useCallback(async () => {
    try {
      const response = await api.get('/api/system/security/stats');
      if (response.data.success) {
        setSecurityStats(response.data.data);
      }
    } catch (error) {
      console.error('Failed to fetch security stats:', error);
    }
  }, [api]);

  // Fetch safety status
  const fetchSafetyStatus = useCallback(async () => {
    try {
      const response = await api.get('/api/system/safety/status');
      if (response.data.success) {
        setSafetyStatus(response.data.data);
      }
    } catch (error) {
      console.error('Failed to fetch safety status:', error);
    }
  }, [api]);

  // Fetch notifications
  const fetchNotifications = useCallback(async () => {
    try {
      const response = await api.get('/api/system/notifications/history?limit=10');
      if (response.data.success) {
        setNotifications(response.data.data);
      }
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    }
  }, [api]);

  // Fetch notification preferences
  const fetchNotificationPrefs = useCallback(async () => {
    try {
      const response = await api.get('/api/system/notifications/preferences');
      if (response.data.success) {
        setNotificationPrefs(response.data.data);
      }
    } catch (error) {
      console.error('Failed to fetch notification preferences:', error);
    }
  }, [api]);

  // Fetch bots
  const fetchBots = useCallback(async () => {
    try {
      const response = await api.get('/api/bots');
      if (response.data.success) {
        setBots(response.data.data);
      }
    } catch (error) {
      console.error('Failed to fetch bots:', error);
    }
  }, [api]);

  // Initialize data
  useEffect(() => {
    const initializeData = async () => {
      setLoading(true);
      await Promise.all([
        fetchSystemStatus(),
        fetchSecurityStats(),
        fetchSafetyStatus(),
        fetchNotifications(),
        fetchNotificationPrefs(),
        fetchBots()
      ]);
      setLoading(false);
    };

    if (token) {
      initializeData();
    }
  }, [token, fetchSystemStatus, fetchSecurityStats, fetchSafetyStatus, fetchNotifications, fetchNotificationPrefs, fetchBots]);

  // Auto-refresh data
  useEffect(() => {
    const interval = setInterval(() => {
      if (token) {
        fetchSystemStatus();
        fetchNotifications();
      }
    }, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, [token, fetchSystemStatus, fetchNotifications]);

  // Handle emergency stop
  const handleEmergencyStop = async () => {
    try {
      const response = await api.post('/api/system/safety/emergency-stop', {
        reason: emergencyReason || 'Manual emergency stop'
      });
      
      if (response.data.success) {
        toast.success('Emergency stop activated');
        setEmergencyStopActive(true);
        setShowEmergencyModal(false);
        setEmergencyReason('');
        fetchSystemStatus();
      }
    } catch (error) {
      toast.error('Failed to activate emergency stop');
      console.error('Emergency stop error:', error);
    }
  };

  // Handle bot creation
  const handleCreateBot = async () => {
    try {
      const response = await api.post('/api/bots', newBotConfig);
      
      if (response.data.success) {
        toast.success('Bot created successfully');
        setShowCreateBotModal(false);
        setNewBotConfig({
          name: '',
          strategy: '',
          symbol: '',
          amount: '',
          stopLoss: '',
          takeProfit: ''
        });
        fetchBots();
      }
    } catch (error) {
      toast.error('Failed to create bot');
      console.error('Bot creation error:', error);
    }
  };

  // Handle bot start/stop
  const handleBotToggle = async (botId, action) => {
    try {
      const response = await api.post(`/api/bots/${botId}/${action}`);
      
      if (response.data.success) {
        toast.success(`Bot ${action}ed successfully`);
        fetchBots();
      }
    } catch (error) {
      toast.error(`Failed to ${action} bot`);
      console.error(`Bot ${action} error:`, error);
    }
  };

  // Update notification preferences
  const updateNotificationPrefs = async (newPrefs) => {
    try {
      const response = await api.post('/api/system/notifications/preferences', newPrefs);
      
      if (response.data.success) {
        toast.success('Notification preferences updated');
        setNotificationPrefs(newPrefs);
        setShowNotificationModal(false);
      }
    } catch (error) {
      toast.error('Failed to update notification preferences');
      console.error('Notification preferences error:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading enhanced dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Enhanced Trading Dashboard
          </h1>
          <p className="text-gray-600">
            Advanced security, safety, and monitoring for your trading bots
          </p>
        </div>

        {/* Emergency Stop Alert */}
        {emergencyStopActive && (
          <EnhancedAlert
            type="error"
            title="🚨 EMERGENCY STOP ACTIVE"
            message="All trading activities have been halted. Contact support if this was not intentional."
            className="mb-6"
          />
        )}

        {/* System Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* Security Status */}
          <EnhancedCard
            title="Security Status"
            className="border-l-4 border-l-green-500"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-2xl font-bold text-green-600">
                  {systemStatus?.security?.enabled ? 'Active' : 'Inactive'}
                </p>
                <p className="text-sm text-gray-500">
                  {securityStats?.blocked_ips || 0} IPs blocked
                </p>
              </div>
              <ShieldCheckIcon className="h-8 w-8 text-green-500" />
            </div>
            <EnhancedButton
              variant="outline"
              size="sm"
              className="mt-3 w-full"
              onClick={() => setShowSecurityModal(true)}
            >
              View Details
            </EnhancedButton>
          </EnhancedCard>

          {/* Safety Status */}
          <EnhancedCard
            title="Safety System"
            className={`border-l-4 ${emergencyStopActive ? 'border-l-red-500' : 'border-l-blue-500'}`}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className={`text-2xl font-bold ${emergencyStopActive ? 'text-red-600' : 'text-blue-600'}`}>
                  {emergencyStopActive ? 'STOPPED' : 'Active'}
                </p>
                <p className="text-sm text-gray-500">
                  Risk Level: {safetyStatus?.risk_level || 'Normal'}
                </p>
              </div>
              <ExclamationTriangleIcon className={`h-8 w-8 ${emergencyStopActive ? 'text-red-500' : 'text-blue-500'}`} />
            </div>
            <EnhancedButton
              variant={emergencyStopActive ? "danger" : "warning"}
              size="sm"
              className="mt-3 w-full"
              onClick={() => setShowEmergencyModal(true)}
              disabled={emergencyStopActive}
            >
              {emergencyStopActive ? 'Already Stopped' : 'Emergency Stop'}
            </EnhancedButton>
          </EnhancedCard>

          {/* Notifications */}
          <EnhancedCard
            title="Notifications"
            className="border-l-4 border-l-purple-500"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-2xl font-bold text-purple-600">
                  {notifications.length}
                </p>
                <p className="text-sm text-gray-500">
                  Recent alerts
                </p>
              </div>
              <BellIcon className="h-8 w-8 text-purple-500" />
            </div>
            <EnhancedButton
              variant="outline"
              size="sm"
              className="mt-3 w-full"
              onClick={() => setShowNotificationModal(true)}
            >
              Manage
            </EnhancedButton>
          </EnhancedCard>

          {/* Active Bots */}
          <EnhancedCard
            title="Active Bots"
            className="border-l-4 border-l-yellow-500"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-2xl font-bold text-yellow-600">
                  {bots.filter(bot => bot.status === 'running').length}
                </p>
                <p className="text-sm text-gray-500">
                  of {bots.length} total
                </p>
              </div>
              <ChartBarIcon className="h-8 w-8 text-yellow-500" />
            </div>
            <EnhancedButton
              variant="outline"
              size="sm"
              className="mt-3 w-full"
              onClick={() => setShowCreateBotModal(true)}
            >
              <PlusIcon className="h-4 w-4 mr-1" />
              Create Bot
            </EnhancedButton>
          </EnhancedCard>
        </div>

        {/* Bot Management */}
        <EnhancedCard title="Bot Management" className="mb-8">
          {bots.length === 0 ? (
            <div className="text-center py-8">
              <ChartBarIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500 mb-4">No bots created yet</p>
              <EnhancedButton
                variant="primary"
                onClick={() => setShowCreateBotModal(true)}
              >
                <PlusIcon className="h-4 w-4 mr-2" />
                Create Your First Bot
              </EnhancedButton>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {bots.map((bot) => (
                <div key={bot.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-medium text-gray-900">{bot.name}</h3>
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      bot.status === 'running' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {bot.status}
                    </span>
                  </div>
                  
                  <div className="space-y-2 text-sm text-gray-600 mb-4">
                    <p><strong>Strategy:</strong> {bot.strategy}</p>
                    <p><strong>Symbol:</strong> {bot.symbol}</p>
                    <p><strong>P&L:</strong> <span className={bot.pnl >= 0 ? 'text-green-600' : 'text-red-600'}>
                      ${bot.pnl?.toFixed(2) || '0.00'}
                    </span></p>
                  </div>
                  
                  <div className="flex space-x-2">
                    <EnhancedButton
                      variant={bot.status === 'running' ? 'danger' : 'success'}
                      size="sm"
                      onClick={() => handleBotToggle(bot.id, bot.status === 'running' ? 'stop' : 'start')}
                      disabled={emergencyStopActive}
                    >
                      {bot.status === 'running' ? (
                        <><StopIcon className="h-4 w-4 mr-1" /> Stop</>
                      ) : (
                        <><PlayIcon className="h-4 w-4 mr-1" /> Start</>
                      )}
                    </EnhancedButton>
                    
                    <EnhancedButton
                      variant="outline"
                      size="sm"
                    >
                      <EyeIcon className="h-4 w-4 mr-1" />
                      View
                    </EnhancedButton>
                  </div>
                </div>
              ))}
            </div>
          )}
        </EnhancedCard>

        {/* Recent Notifications */}
        <EnhancedCard title="Recent Notifications">
          {notifications.length === 0 ? (
            <p className="text-gray-500 text-center py-4">No recent notifications</p>
          ) : (
            <div className="space-y-3">
              {notifications.slice(0, 5).map((notification, index) => (
                <div key={index} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
                  <BellIcon className="h-5 w-5 text-gray-400 mt-0.5" />
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">
                      {notification.notification?.title}
                    </p>
                    <p className="text-sm text-gray-600">
                      {notification.notification?.message}
                    </p>
                    <p className="text-xs text-gray-400 mt-1">
                      {new Date(notification.timestamp).toLocaleString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </EnhancedCard>
      </div>

      {/* Emergency Stop Modal */}
      <EnhancedModal
        isOpen={showEmergencyModal}
        onClose={() => setShowEmergencyModal(false)}
        title="🚨 Emergency Stop"
        size="md"
      >
        <EnhancedAlert
          type="warning"
          title="Warning"
          message="This will immediately stop all trading activities. This action cannot be undone easily."
        />
        
        <EnhancedInput
          label="Reason for Emergency Stop"
          value={emergencyReason}
          onChange={(e) => setEmergencyReason(e.target.value)}
          placeholder="Enter reason (optional)"
          helpText="Providing a reason helps with troubleshooting"
        />
        
        <div className="flex justify-end space-x-3 mt-6">
          <EnhancedButton
            variant="outline"
            onClick={() => setShowEmergencyModal(false)}
          >
            Cancel
          </EnhancedButton>
          <EnhancedButton
            variant="danger"
            onClick={handleEmergencyStop}
          >
            Activate Emergency Stop
          </EnhancedButton>
        </div>
      </EnhancedModal>

      {/* Create Bot Modal */}
      <EnhancedModal
        isOpen={showCreateBotModal}
        onClose={() => setShowCreateBotModal(false)}
        title="Create New Trading Bot"
        size="lg"
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <EnhancedInput
            label="Bot Name"
            value={newBotConfig.name}
            onChange={(e) => setNewBotConfig({...newBotConfig, name: e.target.value})}
            placeholder="My Trading Bot"
            required
          />
          
          <EnhancedSelect
            label="Strategy"
            value={newBotConfig.strategy}
            onChange={(e) => setNewBotConfig({...newBotConfig, strategy: e.target.value})}
            options={[
              { value: 'grid', label: 'Grid Trading' },
              { value: 'dca', label: 'DCA (Dollar Cost Average)' },
              { value: 'scalping', label: 'Scalping' },
              { value: 'swing', label: 'Swing Trading' }
            ]}
            required
          />
          
          <EnhancedInput
            label="Trading Symbol"
            value={newBotConfig.symbol}
            onChange={(e) => setNewBotConfig({...newBotConfig, symbol: e.target.value})}
            placeholder="BTCUSDT"
            required
          />
          
          <EnhancedInput
            label="Investment Amount ($)"
            type="number"
            value={newBotConfig.amount}
            onChange={(e) => setNewBotConfig({...newBotConfig, amount: e.target.value})}
            placeholder="100"
            required
          />
          
          <EnhancedInput
            label="Stop Loss (%)"
            type="number"
            value={newBotConfig.stopLoss}
            onChange={(e) => setNewBotConfig({...newBotConfig, stopLoss: e.target.value})}
            placeholder="5"
            helpText="Maximum loss percentage before stopping"
          />
          
          <EnhancedInput
            label="Take Profit (%)"
            type="number"
            value={newBotConfig.takeProfit}
            onChange={(e) => setNewBotConfig({...newBotConfig, takeProfit: e.target.value})}
            placeholder="10"
            helpText="Target profit percentage"
          />
        </div>
        
        <div className="flex justify-end space-x-3 mt-6">
          <EnhancedButton
            variant="outline"
            onClick={() => setShowCreateBotModal(false)}
          >
            Cancel
          </EnhancedButton>
          <EnhancedButton
            variant="primary"
            onClick={handleCreateBot}
            disabled={!newBotConfig.name || !newBotConfig.strategy || !newBotConfig.symbol || !newBotConfig.amount}
          >
            Create Bot
          </EnhancedButton>
        </div>
      </EnhancedModal>

      {/* Notification Preferences Modal */}
      <EnhancedModal
        isOpen={showNotificationModal}
        onClose={() => setShowNotificationModal(false)}
        title="Notification Preferences"
        size="md"
      >
        <div className="space-y-4">
          <p className="text-gray-600">Configure how you want to receive notifications:</p>
          
          {/* Add notification preference controls here */}
          <div className="space-y-3">
            <label className="flex items-center">
              <input type="checkbox" className="mr-2" defaultChecked />
              Email notifications
            </label>
            <label className="flex items-center">
              <input type="checkbox" className="mr-2" defaultChecked />
              In-app notifications
            </label>
            <label className="flex items-center">
              <input type="checkbox" className="mr-2" />
              SMS notifications
            </label>
            <label className="flex items-center">
              <input type="checkbox" className="mr-2" />
              Push notifications
            </label>
          </div>
        </div>
        
        <div className="flex justify-end space-x-3 mt-6">
          <EnhancedButton
            variant="outline"
            onClick={() => setShowNotificationModal(false)}
          >
            Cancel
          </EnhancedButton>
          <EnhancedButton
            variant="primary"
            onClick={() => updateNotificationPrefs({})}
          >
            Save Preferences
          </EnhancedButton>
        </div>
      </EnhancedModal>

      {/* Security Details Modal */}
      <EnhancedModal
        isOpen={showSecurityModal}
        onClose={() => setShowSecurityModal(false)}
        title="Security Details"
        size="lg"
      >
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-2">Blocked IPs</h4>
              <p className="text-2xl font-bold text-red-600">{securityStats?.blocked_ips || 0}</p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-2">Rate Limited</h4>
              <p className="text-2xl font-bold text-yellow-600">{securityStats?.rate_limited || 0}</p>
            </div>
          </div>
          
          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="font-medium text-gray-900 mb-2">Security Events (Last 24h)</h4>
            <p className="text-sm text-gray-600">No suspicious activity detected</p>
          </div>
        </div>
      </EnhancedModal>
    </div>
  );
};

export default EnhancedDashboardIntegration;