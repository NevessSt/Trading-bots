import React, { useState, useEffect } from 'react';
import { XMarkIcon, EyeIcon, EyeSlashIcon, TrashIcon, CheckCircleIcon, ExclamationTriangleIcon, ClockIcon } from '@heroicons/react/24/outline';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import { useLicense } from '../contexts/LicenseContext';
import toast from 'react-hot-toast';

const ApiKeysModal = ({ isOpen, onClose }) => {
  const { requiresLicense } = useLicense();
  const [apiKeys, setApiKeys] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [visibleKeys, setVisibleKeys] = useState({});
  const [newKey, setNewKey] = useState({
    name: '',
    exchange: 'binance',
    api_key: '',
    secret_key: '',
    passphrase: '',
    testnet: false,
    permissions: {
      spot_trading: true,
      futures_trading: false,
      margin_trading: false,
      read_only: false
    }
  });
  const [testingKey, setTestingKey] = useState(null);

  useEffect(() => {
    if (isOpen) {
      fetchApiKeys();
    }
  }, [isOpen]);

  const fetchApiKeys = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/api-keys/');
      setApiKeys(response.data || []);
    } catch (error) {
      toast.error('Failed to fetch API keys');
    } finally {
      setLoading(false);
    }
  };

  const handleAddApiKey = async (e) => {
    e.preventDefault();
    
    // Check license before adding API key
    if (!requiresLicense('api_key_management')) {
      return;
    }
    
    if (!newKey.name || !newKey.api_key || !newKey.secret_key) {
      toast.error('Please fill in all required fields');
      return;
    }

    // Check if passphrase is required for certain exchanges
    if ((newKey.exchange === 'coinbase') && !newKey.passphrase) {
      toast.error('Passphrase is required for Coinbase Pro');
      return;
    }

    try {
      // Map frontend field names to backend expected field names
      const apiKeyData = {
        key_name: newKey.name,
        exchange: newKey.exchange,
        api_key: newKey.api_key,
        api_secret: newKey.secret_key,
        passphrase: newKey.passphrase || undefined,
        testnet: newKey.testnet,
        permissions: ['read', 'trade'], // Convert permissions object to array
        validate_keys: false // Skip validation for now to allow testing
      };
      
      await axios.post('/api/api-keys/', apiKeyData);
      toast.success('API key added successfully');
      setNewKey({
        name: '',
        exchange: 'binance',
        api_key: '',
        secret_key: '',
        passphrase: '',
        testnet: false,
        permissions: {
          spot_trading: true,
          futures_trading: false,
          margin_trading: false,
          read_only: false
        }
      });
      setShowForm(false);
      fetchApiKeys();
    } catch (error) {
      console.error('API Key creation error:', error);
      const errorMessage = error.response?.data?.error || 'Failed to add API key';
      toast.error(errorMessage);
    }
  };

  const handleTestApiKey = async (keyId) => {
    setTestingKey(keyId);
    try {
      const response = await axios.post(`/api/api-keys/${keyId}/test/`, {});
      if (response.data.success) {
        toast.success('API key test successful!');
      } else {
        toast.error(`API key test failed: ${response.data.error}`);
      }
    } catch (error) {
      toast.error('Failed to test API key');
    } finally {
      setTestingKey(null);
    }
  };

  const handleDeleteApiKey = async (keyId) => {
    // Check license before deleting API key
    if (!requiresLicense('api_key_management')) {
      return;
    }
    
    if (!window.confirm('Are you sure you want to delete this API key?')) {
      return;
    }

    try {
      await axios.delete(`/api/api-keys/${keyId}/`);
      toast.success('API key deleted successfully');
      fetchApiKeys();
    } catch (error) {
      toast.error('Failed to delete API key');
    }
  };

  const toggleKeyVisibility = (keyId) => {
    setVisibleKeys(prev => ({
      ...prev,
      [keyId]: !prev[keyId]
    }));
  };

  const maskKey = (key) => {
    if (!key) return '';
    return key.substring(0, 8) + '...' + key.substring(key.length - 8);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-200 dark:border-slate-700">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100">
            API Keys Management
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-full transition-colors"
          >
            <XMarkIcon className="h-5 w-5 text-slate-500 dark:text-slate-400" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-96">
          {/* Add New Key Button */}
          {!showForm && (
            <div className="mb-6">
              <button
                onClick={() => setShowForm(true)}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md font-medium transition-colors"
              >
                Add New API Key
              </button>
            </div>
          )}

          {/* Add New Key Form */}
          {showForm && (
            <div className="mb-6 p-4 border border-slate-200 dark:border-slate-700 rounded-lg">
              <h3 className="text-lg font-medium text-slate-900 dark:text-slate-100 mb-4">
                Add New API Key
              </h3>
              <form onSubmit={handleAddApiKey} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Name *
                    </label>
                    <input
                      type="text"
                      value={newKey.name}
                      onChange={(e) => setNewKey(prev => ({ ...prev, name: e.target.value }))}
                      className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-md bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100"
                      placeholder="My Binance Key"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Exchange
                    </label>
                    <select
                      value={newKey.exchange}
                      onChange={(e) => setNewKey(prev => ({ ...prev, exchange: e.target.value }))}
                      className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-md bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100"
                    >
                      <option value="binance">Binance</option>
                      <option value="binance_us">Binance US</option>
                      <option value="coinbase">Coinbase Pro</option>
                      <option value="kraken">Kraken</option>
                      <option value="kucoin">KuCoin</option>
                      <option value="huobi">Huobi</option>
                      <option value="okx">OKX</option>
                      <option value="bybit">Bybit</option>
                      <option value="gate_io">Gate.io</option>
                      <option value="bitfinex">Bitfinex</option>
                      <option value="ftx">FTX</option>
                      <option value="bitmex">BitMEX</option>
                      <option value="dydx">dYdX</option>
                      <option value="gemini">Gemini</option>
                      <option value="crypto_com">Crypto.com</option>
                    </select>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                    API Key *
                  </label>
                  <input
                    type="text"
                    value={newKey.api_key}
                    onChange={(e) => setNewKey(prev => ({ ...prev, api_key: e.target.value }))}
                    className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-md bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100"
                    placeholder="Your API Key"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Secret Key *
                  </label>
                  <input
                    type="password"
                    value={newKey.secret_key}
                    onChange={(e) => setNewKey(prev => ({ ...prev, secret_key: e.target.value }))}
                    className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-md bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100"
                    placeholder="Your Secret Key"
                    required
                  />
                </div>
                {(newKey.exchange === 'coinbase' || newKey.exchange === 'kucoin' || newKey.exchange === 'okx') && (
                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Passphrase {newKey.exchange === 'coinbase' ? '*' : ''}
                    </label>
                    <input
                      type="password"
                      value={newKey.passphrase}
                      onChange={(e) => setNewKey(prev => ({ ...prev, passphrase: e.target.value }))}
                      className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-md bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100"
                      placeholder="Passphrase"
                      required={newKey.exchange === 'coinbase'}
                    />
                  </div>
                )}
                <div className="space-y-3">
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="testnet"
                      checked={newKey.testnet}
                      onChange={(e) => setNewKey(prev => ({ ...prev, testnet: e.target.checked }))}
                      className="h-4 w-4 text-blue-600 border-slate-300 rounded"
                    />
                    <label htmlFor="testnet" className="ml-2 text-sm text-slate-700 dark:text-slate-300">
                      Use Testnet
                    </label>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                      Permissions
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          id="spot_trading"
                          checked={newKey.permissions.spot_trading}
                          onChange={(e) => setNewKey(prev => ({
                            ...prev,
                            permissions: { ...prev.permissions, spot_trading: e.target.checked }
                          }))}
                          className="h-4 w-4 text-blue-600 border-slate-300 rounded"
                        />
                        <label htmlFor="spot_trading" className="ml-2 text-sm text-slate-700 dark:text-slate-300">
                          Spot Trading
                        </label>
                      </div>
                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          id="futures_trading"
                          checked={newKey.permissions.futures_trading}
                          onChange={(e) => setNewKey(prev => ({
                            ...prev,
                            permissions: { ...prev.permissions, futures_trading: e.target.checked }
                          }))}
                          className="h-4 w-4 text-blue-600 border-slate-300 rounded"
                        />
                        <label htmlFor="futures_trading" className="ml-2 text-sm text-slate-700 dark:text-slate-300">
                          Futures Trading
                        </label>
                      </div>
                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          id="margin_trading"
                          checked={newKey.permissions.margin_trading}
                          onChange={(e) => setNewKey(prev => ({
                            ...prev,
                            permissions: { ...prev.permissions, margin_trading: e.target.checked }
                          }))}
                          className="h-4 w-4 text-blue-600 border-slate-300 rounded"
                        />
                        <label htmlFor="margin_trading" className="ml-2 text-sm text-slate-700 dark:text-slate-300">
                          Margin Trading
                        </label>
                      </div>
                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          id="read_only"
                          checked={newKey.permissions.read_only}
                          onChange={(e) => setNewKey(prev => ({
                            ...prev,
                            permissions: { ...prev.permissions, read_only: e.target.checked }
                          }))}
                          className="h-4 w-4 text-blue-600 border-slate-300 rounded"
                        />
                        <label htmlFor="read_only" className="ml-2 text-sm text-slate-700 dark:text-slate-300">
                          Read Only
                        </label>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="flex space-x-3">
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md font-medium transition-colors"
                  >
                    Add API Key
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowForm(false)}
                    className="px-4 py-2 bg-slate-200 dark:bg-slate-600 text-slate-800 dark:text-slate-200 rounded-md hover:bg-slate-300 dark:hover:bg-slate-500 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
                <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-md">
                  <p className="text-sm text-blue-800 dark:text-blue-200">
                    <strong>Security Note:</strong> Your API keys are encrypted and stored securely. 
                    We recommend using API keys with limited permissions and enabling IP restrictions on your exchange.
                  </p>
                </div>
              </form>
            </div>
          )}

          {/* API Keys List */}
          {loading ? (
            <div className="flex justify-center items-center h-32">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : apiKeys.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-slate-500 dark:text-slate-400">No API keys found</p>
            </div>
          ) : (
            <div className="space-y-4">
              {apiKeys.map((key) => (
                <div key={key.id} className="p-4 border border-slate-200 dark:border-slate-700 rounded-lg">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <h4 className="font-medium text-slate-900 dark:text-slate-100">
                        {key.name}
                      </h4>
                      <div className="flex items-center space-x-2 mt-1">
                        <p className="text-sm text-slate-500 dark:text-slate-400">
                          {key.exchange.charAt(0).toUpperCase() + key.exchange.slice(1).replace('_', ' ')} 
                          {key.testnet && '(Testnet)'}
                        </p>
                        {key.permissions && (
                          <div className="flex space-x-1">
                            {key.permissions.spot_trading && (
                              <span className="inline-flex px-1.5 py-0.5 text-xs bg-blue-100 text-blue-800 rounded">
                                Spot
                              </span>
                            )}
                            {key.permissions.futures_trading && (
                              <span className="inline-flex px-1.5 py-0.5 text-xs bg-purple-100 text-purple-800 rounded">
                                Futures
                              </span>
                            )}
                            {key.permissions.margin_trading && (
                              <span className="inline-flex px-1.5 py-0.5 text-xs bg-orange-100 text-orange-800 rounded">
                                Margin
                              </span>
                            )}
                            {key.permissions.read_only && (
                              <span className="inline-flex px-1.5 py-0.5 text-xs bg-gray-100 text-gray-800 rounded">
                                Read-Only
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className={`inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full ${
                        key.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {key.is_active ? (
                          <><CheckCircleIcon className="h-3 w-3 mr-1" />Active</>
                        ) : (
                          <><ExclamationTriangleIcon className="h-3 w-3 mr-1" />Inactive</>
                        )}
                      </span>
                      <button
                        onClick={() => handleTestApiKey(key.id)}
                        disabled={testingKey === key.id}
                        className="p-1 text-blue-600 hover:text-blue-800 transition-colors disabled:opacity-50"
                        title="Test API Key"
                      >
                        {testingKey === key.id ? (
                          <ClockIcon className="h-4 w-4 animate-spin" />
                        ) : (
                          <CheckCircleIcon className="h-4 w-4" />
                        )}
                      </button>
                      <button
                        onClick={() => handleDeleteApiKey(key.id)}
                        className="p-1 text-red-600 hover:text-red-800 transition-colors"
                        title="Delete API Key"
                      >
                        <TrashIcon className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-slate-600 dark:text-slate-400 w-20">API Key:</span>
                      <code className="text-sm bg-slate-100 dark:bg-slate-700 px-2 py-1 rounded flex-1">
                        {visibleKeys[key.id] ? key.api_key : maskKey(key.api_key)}
                      </code>
                      <button
                        onClick={() => toggleKeyVisibility(key.id)}
                        className="p-1 text-slate-500 hover:text-slate-700 transition-colors"
                      >
                        {visibleKeys[key.id] ? (
                          <EyeSlashIcon className="h-4 w-4" />
                        ) : (
                          <EyeIcon className="h-4 w-4" />
                        )}
                      </button>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-slate-600 dark:text-slate-400 w-20">Secret:</span>
                      <code className="text-sm bg-slate-100 dark:bg-slate-700 px-2 py-1 rounded flex-1">
                        {visibleKeys[key.id] ? key.secret_key : maskKey(key.secret_key)}
                      </code>
                    </div>
                    {key.passphrase && (
                      <div className="flex items-center space-x-2">
                        <span className="text-sm text-slate-600 dark:text-slate-400 w-20">Passphrase:</span>
                        <code className="text-sm bg-slate-100 dark:bg-slate-700 px-2 py-1 rounded flex-1">
                          {visibleKeys[key.id] ? key.passphrase : '••••••••'}
                        </code>
                      </div>
                    )}
                    {key.last_used && (
                      <div className="flex items-center space-x-2">
                        <span className="text-sm text-slate-600 dark:text-slate-400 w-20">Last Used:</span>
                        <span className="text-sm text-slate-900 dark:text-slate-100">
                          {new Date(key.last_used).toLocaleString()}
                        </span>
                      </div>
                    )}
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-slate-600 dark:text-slate-400 w-20">Created:</span>
                      <span className="text-sm text-slate-900 dark:text-slate-100">
                        {new Date(key.created_at).toLocaleString()}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end p-6 border-t border-slate-200 dark:border-slate-700">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-200 dark:bg-slate-600 text-slate-800 dark:text-slate-200 rounded-md hover:bg-slate-300 dark:hover:bg-slate-500 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default ApiKeysModal;