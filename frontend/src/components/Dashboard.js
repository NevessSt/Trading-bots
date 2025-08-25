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
  CreditCardIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { format } from 'date-fns';
import BotCard from './BotCard';
import CreateBotModal from './CreateBotModal';
import TradeHistoryModal from './TradeHistoryModal';
import ApiKeysModal from './ApiKeysModal';
import SubscriptionCard from './SubscriptionCard';

const Dashboard = () => {
  const { user, subscription, isVerified } = useAuth();
  const { hasValidLicense, getLicenseType, requiresLicense } = useLicense();
  const { requireRiskAcceptance } = useRiskDisclaimer();
  const [bots, setBots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateBot, setShowCreateBot] = useState(false);
  const [showTradeHistory, setShowTradeHistory] = useState(false);
  const [showApiKeys, setShowApiKeys] = useState(false);
  const [selectedBot, setSelectedBot] = useState(null);
  const [stats, setStats] = useState({
    totalPnL: 0,
    totalTrades: 0,
    activeBots: 0,
    successRate: 0
  });

  useEffect(() => {
    if (isVerified) {
      fetchBots();
      fetchStats();
    }
  }, [isVerified]);

  const fetchBots = async () => {
    try {
      const response = await axios.get('/api/bots');
      setBots(response.data.bots || []);
    } catch (error) {
      console.error('Failed to fetch bots:', error);
      toast.error('Failed to load bots');
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await axios.get('/api/bots/stats');
      setStats(response.data.stats || stats);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const handleStartBot = async (botId) => {
    // Check risk acceptance before starting bot
    if (!requireRiskAcceptance()) {
      return;
    }
    
    try {
      await axios.post(`/api/bots/${botId}/start`);
      toast.success('Bot started successfully');
      fetchBots();
    } catch (error) {
      const message = error.response?.data?.error || 'Failed to start bot';
      toast.error(message);
    }
  };

  const handleStopBot = async (botId) => {
    try {
      await axios.post(`/api/bots/${botId}/stop`);
      toast.success('Bot stopped successfully');
      fetchBots();
    } catch (error) {
      const message = error.response?.data?.error || 'Failed to stop bot';
      toast.error(message);
    }
  };

  const handleDeleteBot = async (botId) => {
    if (!window.confirm('Are you sure you want to delete this bot?')) {
      return;
    }

    try {
      await axios.delete(`/api/bots/${botId}`);
      toast.success('Bot deleted successfully');
      fetchBots();
    } catch (error) {
      const message = error.response?.data?.error || 'Failed to delete bot';
      toast.error(message);
    }
  };

  const handleViewTrades = (bot) => {
    setSelectedBot(bot);
    setShowTradeHistory(true);
  };

  const canCreateBot = () => {
    if (!subscription) return false;
    const maxBots = subscription.features?.max_bots || 1;
    return bots.length < maxBots;
  };

  const handleCreateBotClick = () => {
    // Check risk acceptance before creating bot
    if (!requireRiskAcceptance()) {
      return;
    }
    setShowCreateBot(true);
  };

  if (!isVerified) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md w-full bg-white rounded-lg shadow-md p-6 text-center">
          <ExclamationTriangleIcon className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            Email Verification Required
          </h2>
          <p className="text-gray-600 mb-4">
            Please verify your email address to access the dashboard.
          </p>
          <button
            onClick={() => window.location.href = '/profile'}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
          >
            Go to Profile
          </button>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Welcome back, {user?.first_name || user?.username}!
          </h1>
          <p className="text-gray-600 mt-2">
            Manage your trading bots and monitor performance
          </p>
        </div>

        {/* Subscription Card */}
        <div className="mb-8">
          <SubscriptionCard subscription={subscription} />
        </div>

        {/* License Status Card */}
        <div className="mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <KeyIcon className={`h-8 w-8 ${
                  hasValidLicense ? 'text-green-500' : 'text-red-500'
                }`} />
                <div className="ml-4">
                  <h3 className="text-lg font-medium text-gray-900">License Status</h3>
                  <p className={`text-sm ${
                    hasValidLicense ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {hasValidLicense ? 'Active License' : 'No Valid License'}
                  </p>
                  {hasValidLicense && (
                    <p className="text-xs text-gray-500 mt-1">
                      Type: {getLicenseType() || 'Unknown'}
                    </p>
                  )}
                </div>
              </div>
              <div className="flex space-x-2">
                {!hasValidLicense && (
                  <button
                    onClick={() => window.location.href = '/license'}
                    className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                  >
                    Activate License
                  </button>
                )}
                <button
                  onClick={() => window.location.href = '/license'}
                  className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                >
                  Manage License
                </button>
              </div>
            </div>
            {!hasValidLicense && (
              <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                <p className="text-sm text-yellow-800">
                  <ExclamationTriangleIcon className="h-4 w-4 inline mr-1" />
                  Some features may be limited without a valid license. Activate your license to unlock all trading capabilities.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <ChartBarIcon className="h-8 w-8 text-green-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total P&L</p>
                <p className={`text-2xl font-bold ${
                  (stats.totalPnL || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  ${(stats.totalPnL || 0).toFixed(2)}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <PlayIcon className="h-8 w-8 text-blue-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Active Bots</p>
                <p className="text-2xl font-bold text-gray-900">{stats.activeBots}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <ChartBarIcon className="h-8 w-8 text-purple-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Trades</p>
                <p className="text-2xl font-bold text-gray-900">{stats.totalTrades}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <ChartBarIcon className="h-8 w-8 text-yellow-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Success Rate</p>
                <p className="text-2xl font-bold text-gray-900">
                  {(stats.successRate || 0).toFixed(1)}%
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap gap-4 mb-8">
          <button
            onClick={handleCreateBotClick}
            disabled={!canCreateBot()}
            className={`inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white ${
              canCreateBot()
                ? 'bg-blue-600 hover:bg-blue-700'
                : 'bg-gray-400 cursor-not-allowed'
            }`}
          >
            <PlusIcon className="h-4 w-4 mr-2" />
            Create Bot
          </button>

          <button
            onClick={() => setShowApiKeys(true)}
            className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
          >
            <KeyIcon className="h-4 w-4 mr-2" />
            Manage API Keys
          </button>

          <button
            onClick={() => setShowTradeHistory(true)}
            className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
          >
            <ChartBarIcon className="h-4 w-4 mr-2" />
            Trade History
          </button>
        </div>

        {/* Bot Limit Warning */}
        {!canCreateBot() && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 mb-8">
            <div className="flex">
              <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400" />
              <div className="ml-3">
                <h3 className="text-sm font-medium text-yellow-800">
                  Bot Limit Reached
                </h3>
                <p className="text-sm text-yellow-700 mt-1">
                  You've reached your plan's bot limit ({subscription?.features?.max_bots || 1} bots). 
                  <a href="/billing" className="font-medium underline">
                    Upgrade your plan
                  </a> to create more bots.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Bots Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {bots.length === 0 ? (
            <div className="col-span-full text-center py-12">
              <div className="text-gray-400 mb-4">
                <ChartBarIcon className="h-12 w-12 mx-auto" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No bots created yet
              </h3>
              <p className="text-gray-600 mb-4">
                Create your first trading bot to get started
              </p>
              {canCreateBot() && (
                <button
                  onClick={handleCreateBotClick}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
                >
                  <PlusIcon className="h-4 w-4 mr-2" />
                  Create Your First Bot
                </button>
              )}
            </div>
          ) : (
            bots.map((bot) => (
              <BotCard
                key={bot._id}
                bot={bot}
                onStart={() => handleStartBot(bot._id)}
                onStop={() => handleStopBot(bot._id)}
                onDelete={() => handleDeleteBot(bot._id)}
                onViewTrades={() => handleViewTrades(bot)}
              />
            ))
          )}
        </div>
      </div>

      {/* Modals */}
      {showCreateBot && (
        <CreateBotModal
          isOpen={showCreateBot}
          onClose={() => setShowCreateBot(false)}
          onSuccess={() => {
            setShowCreateBot(false);
            fetchBots();
          }}
        />
      )}

      {showTradeHistory && (
        <TradeHistoryModal
          isOpen={showTradeHistory}
          onClose={() => setShowTradeHistory(false)}
          bot={selectedBot}
        />
      )}

      {showApiKeys && (
        <ApiKeysModal
          isOpen={showApiKeys}
          onClose={() => setShowApiKeys(false)}
        />
      )}
    </div>
  );
};

export default Dashboard;