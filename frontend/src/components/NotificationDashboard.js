import React, { useState, useEffect } from 'react';
import { Bell, Settings, History, AlertTriangle, CheckCircle, XCircle, TrendingUp, TrendingDown } from 'lucide-react';
import NotificationSettings from './NotificationSettings';
import NotificationHistory from './NotificationHistory';
import api from '../services/api';

const NotificationDashboard = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [recentAlerts, setRecentAlerts] = useState([]);
  const [alertStats, setAlertStats] = useState({
    today: { sent: 0, failed: 0 },
    week: { sent: 0, failed: 0 },
    month: { sent: 0, failed: 0 }
  });
  const [systemHealth, setSystemHealth] = useState({
    email: { status: 'unknown', last_test: null },
    telegram: { status: 'unknown', last_test: null },
    push: { status: 'unknown', last_test: null }
  });
  const [loading, setLoading] = useState(true);

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Bell },
    { id: 'settings', label: 'Settings', icon: Settings },
    { id: 'history', label: 'History', icon: History }
  ];

  useEffect(() => {
    if (activeTab === 'overview') {
      loadOverviewData();
    }
  }, [activeTab]);

  const loadOverviewData = async () => {
    try {
      setLoading(true);
      
      // Load recent alerts
      const recentResponse = await api.get('/notifications/logs', {
        params: { page: 1, per_page: 10 }
      });
      setRecentAlerts(recentResponse.data.notifications || []);
      
      // Load alert statistics
      const statsResponse = await api.get('/notifications/stats');
      setAlertStats({
        today: {
          sent: statsResponse.data.today?.sent || 0,
          failed: statsResponse.data.today?.failed || 0
        },
        week: {
          sent: statsResponse.data.week?.sent || 0,
          failed: statsResponse.data.week?.failed || 0
        },
        month: {
          sent: statsResponse.data.month?.sent || 0,
          failed: statsResponse.data.month?.failed || 0
        }
      });
      
      // Load system health
      const healthResponse = await api.get('/notifications/config-status');
      setSystemHealth({
        email: {
          status: healthResponse.data.email ? 'healthy' : 'error',
          last_test: healthResponse.data.email_last_test || null
        },
        telegram: {
          status: healthResponse.data.telegram ? 'healthy' : 'error',
          last_test: healthResponse.data.telegram_last_test || null
        },
        push: {
          status: healthResponse.data.push ? 'healthy' : 'error',
          last_test: healthResponse.data.push_last_test || null
        }
      });
      
    } catch (error) {
      console.error('Error loading overview data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'error':
        return <XCircle className="w-5 h-5 text-red-600" />;
      default:
        return <AlertTriangle className="w-5 h-5 text-yellow-600" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy':
        return 'text-green-600 bg-green-100';
      case 'error':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-yellow-600 bg-yellow-100';
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleString();
  };

  const getEventTypeColor = (eventType) => {
    const colors = {
      'trade_executed': 'bg-green-100 text-green-800',
      'trade_failed': 'bg-red-100 text-red-800',
      'bot_started': 'bg-blue-100 text-blue-800',
      'bot_stopped': 'bg-gray-100 text-gray-800',
      'bot_error': 'bg-red-100 text-red-800',
      'profit_alert': 'bg-green-100 text-green-800',
      'loss_alert': 'bg-red-100 text-red-800',
      'daily_summary': 'bg-purple-100 text-purple-800'
    };
    return colors[eventType] || 'bg-gray-100 text-gray-800';
  };

  const renderOverview = () => {
    if (loading) {
      return (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-2">Loading dashboard...</span>
        </div>
      );
    }

    return (
      <div className="space-y-6">
        {/* Alert Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-800">Today</h3>
              <TrendingUp className="w-6 h-6 text-blue-600" />
            </div>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Sent:</span>
                <span className="text-sm font-medium text-green-600">{alertStats.today.sent}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Failed:</span>
                <span className="text-sm font-medium text-red-600">{alertStats.today.failed}</span>
              </div>
              <div className="flex justify-between border-t pt-2">
                <span className="text-sm font-medium text-gray-700">Total:</span>
                <span className="text-sm font-bold">{alertStats.today.sent + alertStats.today.failed}</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-800">This Week</h3>
              <TrendingUp className="w-6 h-6 text-green-600" />
            </div>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Sent:</span>
                <span className="text-sm font-medium text-green-600">{alertStats.week.sent}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Failed:</span>
                <span className="text-sm font-medium text-red-600">{alertStats.week.failed}</span>
              </div>
              <div className="flex justify-between border-t pt-2">
                <span className="text-sm font-medium text-gray-700">Total:</span>
                <span className="text-sm font-bold">{alertStats.week.sent + alertStats.week.failed}</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-800">This Month</h3>
              <TrendingDown className="w-6 h-6 text-purple-600" />
            </div>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Sent:</span>
                <span className="text-sm font-medium text-green-600">{alertStats.month.sent}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Failed:</span>
                <span className="text-sm font-medium text-red-600">{alertStats.month.failed}</span>
              </div>
              <div className="flex justify-between border-t pt-2">
                <span className="text-sm font-medium text-gray-700">Total:</span>
                <span className="text-sm font-bold">{alertStats.month.sent + alertStats.month.failed}</span>
              </div>
            </div>
          </div>
        </div>

        {/* System Health */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-medium text-gray-800 mb-4">System Health</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {Object.entries(systemHealth).map(([service, health]) => (
              <div key={service} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700 capitalize">{service}</span>
                  {getStatusIcon(health.status)}
                </div>
                <div className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(health.status)}`}>
                  {health.status === 'healthy' ? 'Operational' : health.status === 'error' ? 'Not Configured' : 'Unknown'}
                </div>
                <div className="mt-2 text-xs text-gray-500">
                  Last test: {formatDate(health.last_test)}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Alerts */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-800">Recent Alerts</h3>
            <button
              onClick={() => setActiveTab('history')}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              View All
            </button>
          </div>
          
          {recentAlerts.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Bell className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p>No recent alerts</p>
            </div>
          ) : (
            <div className="space-y-3">
              {recentAlerts.slice(0, 5).map((alert) => (
                <div key={alert.id} className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50">
                  <div className="flex items-center space-x-3">
                    <div className={`w-2 h-2 rounded-full ${
                      alert.status === 'sent' ? 'bg-green-500' : 'bg-red-500'
                    }`}></div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${
                          getEventTypeColor(alert.event_type)
                        }`}>
                          {alert.event_type.replace('_', ' ').toUpperCase()}
                        </span>
                        <span className="text-sm text-gray-600 capitalize">
                          via {alert.notification_type}
                        </span>
                      </div>
                      <div className="text-sm text-gray-800 mt-1">
                        {alert.subject || 'No subject'}
                      </div>
                    </div>
                  </div>
                  <div className="text-xs text-gray-500">
                    {formatDate(alert.created_at)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-medium text-gray-800 mb-4">Quick Actions</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <button
              onClick={() => setActiveTab('settings')}
              className="flex items-center justify-center p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors"
            >
              <Settings className="w-6 h-6 text-gray-400 mr-2" />
              <span className="text-gray-600">Configure Notifications</span>
            </button>
            
            <button
              onClick={() => setActiveTab('history')}
              className="flex items-center justify-center p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-green-500 hover:bg-green-50 transition-colors"
            >
              <History className="w-6 h-6 text-gray-400 mr-2" />
              <span className="text-gray-600">View Full History</span>
            </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Notification Center</h1>
          <p className="text-gray-600">Manage your trading alerts and notification preferences</p>
        </div>

        {/* Tab Navigation */}
        <div className="bg-white rounded-lg shadow-md mb-6">
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8 px-6">
              {tabs.map((tab) => {
                const IconComponent = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center py-4 px-1 border-b-2 font-medium text-sm ${
                      activeTab === tab.id
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <IconComponent className="w-5 h-5 mr-2" />
                    {tab.label}
                  </button>
                );
              })}
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        <div className="tab-content">
          {activeTab === 'overview' && renderOverview()}
          {activeTab === 'settings' && <NotificationSettings />}
          {activeTab === 'history' && <NotificationHistory />}
        </div>
      </div>
    </div>
  );
};

export default NotificationDashboard;