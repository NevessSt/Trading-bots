import React, { useState, useEffect } from 'react';
import {
  BuildingStorefrontIcon,
  CheckCircleIcon,
  XCircleIcon,
  CogIcon,
  TrashIcon,
  StarIcon,
  EyeIcon,
  EyeSlashIcon
} from '@heroicons/react/24/outline';
import { CheckCircleIcon as CheckCircleIconSolid } from '@heroicons/react/24/solid';
import axios from 'axios';

const ExchangeManager = () => {
  const [exchanges, setExchanges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [configuring, setConfiguring] = useState(null);
  const [showCredentials, setShowCredentials] = useState({});
  const [formData, setFormData] = useState({
    api_key: '',
    api_secret: '',
    passphrase: '',
    testnet: true,
    enabled: true
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const exchangeInfo = {
    binance: {
      name: 'Binance',
      description: 'World\'s largest cryptocurrency exchange',
      requiresPassphrase: false,
      testnetSupported: true,
      icon: '🟡'
    },
    coinbase: {
      name: 'Coinbase Pro',
      description: 'Professional trading platform by Coinbase',
      requiresPassphrase: true,
      testnetSupported: true,
      icon: '🔵'
    },
    kucoin: {
      name: 'KuCoin',
      description: 'Global cryptocurrency exchange',
      requiresPassphrase: true,
      testnetSupported: true,
      icon: '🟢'
    },
    bybit: {
      name: 'Bybit',
      description: 'Derivatives and spot trading platform',
      requiresPassphrase: false,
      testnetSupported: true,
      icon: '🟠'
    },
    kraken: {
      name: 'Kraken',
      description: 'Established US-based exchange',
      requiresPassphrase: false,
      testnetSupported: false,
      icon: '🟣'
    },
    okx: {
      name: 'OKX',
      description: 'Global crypto exchange and Web3 ecosystem',
      requiresPassphrase: true,
      testnetSupported: true,
      icon: '⚫'
    }
  };

  useEffect(() => {
    fetchExchanges();
  }, []);

  const fetchExchanges = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('/api/exchanges', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setExchanges(response.data.exchanges);
    } catch (error) {
      setError('Failed to fetch exchanges');
      console.error('Error fetching exchanges:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleConfigure = (exchangeName) => {
    setConfiguring(exchangeName);
    setFormData({
      api_key: '',
      api_secret: '',
      passphrase: '',
      testnet: true,
      enabled: true
    });
    setError('');
    setSuccess('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `/api/exchanges/${configuring}/configure`,
        formData,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      setSuccess(response.data.message);
      setConfiguring(null);
      fetchExchanges();
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to configure exchange');
    }
  };

  const handleTestConnection = async (exchangeName) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `/api/exchanges/${exchangeName}/test`,
        {},
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setSuccess(response.data.message);
    } catch (error) {
      setError(error.response?.data?.error || 'Connection test failed');
    }
  };

  const handleRemove = async (exchangeName) => {
    if (!window.confirm(`Are you sure you want to remove ${exchangeName}?`)) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      await axios.delete(`/api/exchanges/${exchangeName}/remove`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSuccess(`${exchangeName} removed successfully`);
      fetchExchanges();
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to remove exchange');
    }
  };

  const handleSetPrimary = async (exchangeName) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `/api/exchanges/${exchangeName}/set-primary`,
        {},
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setSuccess(`${exchangeName} set as primary exchange`);
      fetchExchanges();
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to set primary exchange');
    }
  };

  const toggleShowCredentials = (field) => {
    setShowCredentials(prev => ({
      ...prev,
      [field]: !prev[field]
    }));
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Exchange Management
        </h1>
        <p className="text-gray-600">
          Configure and manage your cryptocurrency exchange connections
        </p>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex">
            <XCircleIcon className="h-5 w-5 text-red-400 mr-2" />
            <p className="text-red-800">{error}</p>
          </div>
        </div>
      )}

      {success && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex">
            <CheckCircleIcon className="h-5 w-5 text-green-400 mr-2" />
            <p className="text-green-800">{success}</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {exchanges.map((exchange) => {
          const info = exchangeInfo[exchange.name] || {};
          return (
            <div
              key={exchange.name}
              className="bg-white rounded-lg shadow-md border border-gray-200 p-6"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center">
                  <span className="text-2xl mr-3">{info.icon}</span>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                      {info.name || exchange.display_name}
                    </h3>
                    <p className="text-sm text-gray-500">{info.description}</p>
                  </div>
                </div>
                {exchange.is_primary && (
                  <StarIcon className="h-5 w-5 text-yellow-500 fill-current" />
                )}
              </div>

              <div className="mb-4">
                <div className="flex items-center mb-2">
                  {exchange.status === 'connected' ? (
                    <CheckCircleIconSolid className="h-5 w-5 text-green-500 mr-2" />
                  ) : (
                    <XCircleIcon className="h-5 w-5 text-red-500 mr-2" />
                  )}
                  <span className="text-sm font-medium">
                    {exchange.status === 'connected' ? 'Connected' : 'Disconnected'}
                  </span>
                </div>
                {exchange.testnet && (
                  <span className="inline-block px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded">
                    Testnet
                  </span>
                )}
              </div>

              <div className="space-y-2">
                {!exchange.configured ? (
                  <button
                    onClick={() => handleConfigure(exchange.name)}
                    className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    <CogIcon className="h-4 w-4 inline mr-2" />
                    Configure
                  </button>
                ) : (
                  <div className="space-y-2">
                    <button
                      onClick={() => handleTestConnection(exchange.name)}
                      className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                    >
                      Test Connection
                    </button>
                    {!exchange.is_primary && (
                      <button
                        onClick={() => handleSetPrimary(exchange.name)}
                        className="w-full px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors"
                      >
                        <StarIcon className="h-4 w-4 inline mr-2" />
                        Set as Primary
                      </button>
                    )}
                    <button
                      onClick={() => handleRemove(exchange.name)}
                      className="w-full px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                    >
                      <TrashIcon className="h-4 w-4 inline mr-2" />
                      Remove
                    </button>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Configuration Modal */}
      {configuring && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
            <h2 className="text-xl font-bold mb-4">
              Configure {exchangeInfo[configuring]?.name || configuring}
            </h2>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  API Key
                </label>
                <div className="relative">
                  <input
                    type={showCredentials.api_key ? 'text' : 'password'}
                    value={formData.api_key}
                    onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent pr-10"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => toggleShowCredentials('api_key')}
                    className="absolute right-2 top-2 text-gray-400 hover:text-gray-600"
                  >
                    {showCredentials.api_key ? (
                      <EyeSlashIcon className="h-5 w-5" />
                    ) : (
                      <EyeIcon className="h-5 w-5" />
                    )}
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  API Secret
                </label>
                <div className="relative">
                  <input
                    type={showCredentials.api_secret ? 'text' : 'password'}
                    value={formData.api_secret}
                    onChange={(e) => setFormData({ ...formData, api_secret: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent pr-10"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => toggleShowCredentials('api_secret')}
                    className="absolute right-2 top-2 text-gray-400 hover:text-gray-600"
                  >
                    {showCredentials.api_secret ? (
                      <EyeSlashIcon className="h-5 w-5" />
                    ) : (
                      <EyeIcon className="h-5 w-5" />
                    )}
                  </button>
                </div>
              </div>

              {exchangeInfo[configuring]?.requiresPassphrase && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Passphrase
                  </label>
                  <div className="relative">
                    <input
                      type={showCredentials.passphrase ? 'text' : 'password'}
                      value={formData.passphrase}
                      onChange={(e) => setFormData({ ...formData, passphrase: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent pr-10"
                      required
                    />
                    <button
                      type="button"
                      onClick={() => toggleShowCredentials('passphrase')}
                      className="absolute right-2 top-2 text-gray-400 hover:text-gray-600"
                    >
                      {showCredentials.passphrase ? (
                        <EyeSlashIcon className="h-5 w-5" />
                      ) : (
                        <EyeIcon className="h-5 w-5" />
                      )}
                    </button>
                  </div>
                </div>
              )}

              {exchangeInfo[configuring]?.testnetSupported && (
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="testnet"
                    checked={formData.testnet}
                    onChange={(e) => setFormData({ ...formData, testnet: e.target.checked })}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="testnet" className="ml-2 text-sm text-gray-700">
                    Use Testnet (Recommended for testing)
                  </label>
                </div>
              )}

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="enabled"
                  checked={formData.enabled}
                  onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="enabled" className="ml-2 text-sm text-gray-700">
                  Enable this exchange
                </label>
              </div>

              <div className="flex space-x-3 pt-4">
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Configure
                </button>
                <button
                  type="button"
                  onClick={() => setConfiguring(null)}
                  className="flex-1 px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default ExchangeManager;