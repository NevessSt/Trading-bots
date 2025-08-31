import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useLicense } from '../contexts/LicenseContext';
import { useRiskDisclaimer } from '../contexts/RiskDisclaimerContext';
import axios from 'axios';
import toast from 'react-hot-toast';
import {
  PlayIcon,
  StopIcon,
  PlusIcon,
  CogIcon,
  ChartBarIcon,
  KeyIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  CurrencyDollarIcon,
  TrendingUpIcon,
  TrendingDownIcon,
  QuestionMarkCircleIcon
} from '@heroicons/react/24/outline';
import { format } from 'date-fns';

const UserFriendlyDashboard = () => {
  const { user, subscription, isVerified } = useAuth();
  const { hasValidLicense, getLicenseType } = useLicense();
  const { requireRiskAcceptance } = useRiskDisclaimer();
  const [bots, setBots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateBot, setShowCreateBot] = useState(false);
  const [stats, setStats] = useState({
    totalPnL: 0,
    totalTrades: 0,
    activeBots: 0,
    successRate: 0
  });
  const [marketData, setMarketData] = useState(null);
  const [systemHealth, setSystemHealth] = useState('healthy');

  useEffect(() => {
    if (isVerified) {
      fetchDashboardData();
      const interval = setInterval(fetchDashboardData, 30000); // Update every 30 seconds
      return () => clearInterval(interval);
    }
  }, [isVerified]);

  const fetchDashboardData = async () => {
    try {
      const [botsRes, statsRes, marketRes, healthRes] = await Promise.all([
        axios.get('/api/bots'),
        axios.get('/api/bots/stats'),
        axios.get('/api/market/overview'),
        axios.get('/api/health')
      ]);
      
      setBots(botsRes.data.bots || []);
      setStats(statsRes.data.stats || stats);
      setMarketData(marketRes.data);
      setSystemHealth(healthRes.data.status || 'healthy');
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
      if (loading) {
        toast.error('Failed to load dashboard data');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleBotAction = async (botId, action) => {
    if (action === 'start' && !requireRiskAcceptance()) {
      return;
    }

    try {
      await axios.post(`/api/bots/${botId}/${action}`);
      toast.success(`Bot ${action}ed successfully`);
      fetchDashboardData();
    } catch (error) {
      const message = error.response?.data?.error || `Failed to ${action} bot`;
      toast.error(message);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'running': return 'text-green-600 bg-green-100';
      case 'stopped': return 'text-gray-600 bg-gray-100';
      case 'error': return 'text-red-600 bg-red-100';
      case 'paused': return 'text-yellow-600 bg-yellow-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'running': return <CheckCircleIcon className="h-5 w-5" />;
      case 'stopped': return <XCircleIcon className="h-5 w-5" />;
      case 'error': return <ExclamationTriangleIcon className="h-5 w-5" />;
      case 'paused': return <ClockIcon className="h-5 w-5" />;
      default: return <QuestionMarkCircleIcon className="h-5 w-5" />;
    }
  };

  if (!isVerified) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="max-w-md w-full bg-white rounded-xl shadow-lg p-8 text-center">
          <ExclamationTriangleIcon className="h-16 w-16 text-yellow-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            Email Verification Required
          </h2>
          <p className="text-gray-600 mb-6">
            Please verify your email address to access your trading dashboard.
          </p>
          <button
            onClick={() => window.location.href = '/profile'}
            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Verify Email
          </button>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 text-lg">Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Header */}
        <div className="mb-8">
          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">
                  Welcome back, {user?.first_name || user?.username}! 👋
                </h1>
                <p className="text-gray-600 mt-2">
                  Your automated trading assistant is ready to help you grow your portfolio
                </p>
              </div>
              <div className="flex items-center space-x-2">
                <div className={`flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                  systemHealth === 'healthy' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}>
                  <div className={`w-2 h-2 rounded-full mr-2 ${
                    systemHealth === 'healthy' ? 'bg-green-500' : 'bg-red-500'
                  }`}></div>
                  System {systemHealth === 'healthy' ? 'Online' : 'Issues'}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="flex items-center">
              <div className="p-3 bg-green-100 rounded-lg">
                <CurrencyDollarIcon className="h-8 w-8 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Profit/Loss</p>
                <p className={`text-2xl font-bold flex items-center ${
                  (stats.totalPnL || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  ${Math.abs(stats.totalPnL || 0).toFixed(2)}
                  {(stats.totalPnL || 0) >= 0 ? 
                    <TrendingUpIcon className="h-5 w-5 ml-1" /> : 
                    <TrendingDownIcon className="h-5 w-5 ml-1" />
                  }
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="flex items-center">
              <div className="p-3 bg-blue-100 rounded-lg">
                <PlayIcon className="h-8 w-8 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Active Bots</p>
                <p className="text-2xl font-bold text-gray-900">{stats.activeBots}</p>
                <p className="text-xs text-gray-500">of {bots.length} total</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="flex items-center">
              <div className="p-3 bg-purple-100 rounded-lg">
                <ChartBarIcon className="h-8 w-8 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Trades</p>
                <p className="text-2xl font-bold text-gray-900">{stats.totalTrades}</p>
                <p className="text-xs text-gray-500">executed</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="flex items-center">
              <div className="p-3 bg-yellow-100 rounded-lg">
                <ChartBarIcon className="h-8 w-8 text-yellow-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Success Rate</p>
                <p className="text-2xl font-bold text-gray-900">
                  {(stats.successRate || 0).toFixed(1)}%
                </p>
                <p className="text-xs text-gray-500">win rate</p>
              </div>
            </div>
          </div>
        </div>

        {/* License Status */}
        {!hasValidLicense && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6 mb-8">
            <div className="flex items-start">
              <ExclamationTriangleIcon className="h-6 w-6 text-yellow-600 mt-1" />
              <div className="ml-4">
                <h3 className="text-lg font-medium text-yellow-800">
                  License Required
                </h3>
                <p className="text-yellow-700 mt-1">
                  Some features are limited without a valid license. Activate your license to unlock all trading capabilities.
                </p>
                <button
                  onClick={() => window.location.href = '/license'}
                  className="mt-3 bg-yellow-600 text-white px-4 py-2 rounded-lg hover:bg-yellow-700 transition-colors"
                >
                  Activate License
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Quick Actions */}
        <div className="bg-white rounded-xl shadow-sm p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button
              onClick={() => {
                if (requireRiskAcceptance()) {
                  setShowCreateBot(true);
                }
              }}
              className="flex items-center justify-center p-4 border-2 border-dashed border-blue-300 rounded-lg hover:border-blue-400 hover:bg-blue-50 transition-colors group"
            >
              <PlusIcon className="h-8 w-8 text-blue-600 group-hover:text-blue-700" />
              <span className="ml-2 text-blue-600 group-hover:text-blue-700 font-medium">
                Create New Bot
              </span>
            </button>

            <button
              onClick={() => window.location.href = '/api-keys'}
              className="flex items-center justify-center p-4 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <KeyIcon className="h-8 w-8 text-gray-600" />
              <span className="ml-2 text-gray-600 font-medium">
                Manage API Keys
              </span>
            </button>

            <button
              onClick={() => window.location.href = '/trades'}
              className="flex items-center justify-center p-4 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <ChartBarIcon className="h-8 w-8 text-gray-600" />
              <span className="ml-2 text-gray-600 font-medium">
                View Trade History
              </span>
            </button>
          </div>
        </div>

        {/* Bots Section */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-gray-900">Your Trading Bots</h2>
            <div className="flex items-center space-x-2">
              <InformationCircleIcon className="h-5 w-5 text-gray-400" />
              <span className="text-sm text-gray-500">
                Bots automatically execute trades based on your chosen strategy
              </span>
            </div>
          </div>

          {bots.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-gray-400 mb-4">
                <ChartBarIcon className="h-16 w-16 mx-auto" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No trading bots yet
              </h3>
              <p className="text-gray-600 mb-6">
                Create your first bot to start automated trading. Don't worry - we'll guide you through the process!
              </p>
              <button
                onClick={() => {
                  if (requireRiskAcceptance()) {
                    setShowCreateBot(true);
                  }
                }}
                className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors inline-flex items-center"
              >
                <PlusIcon className="h-5 w-5 mr-2" />
                Create Your First Bot
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {bots.map((bot) => (
                <div key={bot._id} className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-medium text-gray-900">{bot.name}</h3>
                    <div className={`flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                      getStatusColor(bot.status)
                    }`}>
                      {getStatusIcon(bot.status)}
                      <span className="ml-1 capitalize">{bot.status}</span>
                    </div>
                  </div>

                  <div className="space-y-2 mb-4">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Strategy:</span>
                      <span className="font-medium">{bot.strategy}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Balance:</span>
                      <span className="font-medium">${bot.balance?.toFixed(2) || '0.00'}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">P&L:</span>
                      <span className={`font-medium ${
                        (bot.profit_loss || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        ${(bot.profit_loss || 0).toFixed(2)}
                      </span>
                    </div>
                  </div>

                  <div className="flex space-x-2">
                    {bot.status === 'running' ? (
                      <button
                        onClick={() => handleBotAction(bot._id, 'stop')}
                        className="flex-1 bg-red-600 text-white px-3 py-2 rounded-md hover:bg-red-700 transition-colors flex items-center justify-center"
                      >
                        <StopIcon className="h-4 w-4 mr-1" />
                        Stop
                      </button>
                    ) : (
                      <button
                        onClick={() => handleBotAction(bot._id, 'start')}
                        className="flex-1 bg-green-600 text-white px-3 py-2 rounded-md hover:bg-green-700 transition-colors flex items-center justify-center"
                      >
                        <PlayIcon className="h-4 w-4 mr-1" />
                        Start
                      </button>
                    )}
                    <button
                      onClick={() => window.location.href = `/bots/${bot._id}`}
                      className="flex-1 bg-gray-600 text-white px-3 py-2 rounded-md hover:bg-gray-700 transition-colors flex items-center justify-center"
                    >
                      <CogIcon className="h-4 w-4 mr-1" />
                      Settings
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default UserFriendlyDashboard;