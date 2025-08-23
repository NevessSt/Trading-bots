import React, { useState, useEffect } from 'react';
import { Dialog } from '@headlessui/react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { useLicense } from '../contexts/LicenseContext';
import axios from 'axios';
import toast from 'react-hot-toast';

const CreateBotModal = ({ isOpen, onClose, onSuccess }) => {
  const { requiresLicense, hasFeature } = useLicense();
  const [formData, setFormData] = useState({
    name: '',
    strategy: 'sma_crossover',
    exchange: 'binance',
    symbol: 'BTCUSDT',
    balance: 1000,
    api_key_id: '',
    parameters: {
      short_window: 10,
      long_window: 30,
      stop_loss: 0.02,
      take_profit: 0.04
    }
  });
  const [apiKeys, setApiKeys] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingKeys, setLoadingKeys] = useState(true);

  const strategies = [
    { value: 'sma_crossover', label: 'SMA Crossover', description: 'Simple Moving Average crossover strategy' },
    { value: 'rsi_oversold', label: 'RSI Oversold', description: 'Buy when RSI indicates oversold conditions' },
    { value: 'bollinger_bands', label: 'Bollinger Bands', description: 'Trade based on Bollinger Band signals' },
    { value: 'macd_signal', label: 'MACD Signal', description: 'MACD line and signal line crossover' },
    { value: 'mean_reversion', label: 'Mean Reversion', description: 'Price reversion to mean strategy' }
  ];

  const exchanges = [
    { value: 'binance', label: 'Binance' },
    { value: 'bybit', label: 'Bybit' },
    { value: 'coinbase', label: 'Coinbase Pro' },
    { value: 'kraken', label: 'Kraken' }
  ];

  const popularSymbols = [
    'BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOTUSDT', 'LINKUSDT',
    'BNBUSDT', 'SOLUSDT', 'MATICUSDT', 'AVAXUSDT', 'ATOMUSDT'
  ];

  useEffect(() => {
    if (isOpen) {
      fetchApiKeys();
    }
  }, [isOpen]);

  const fetchApiKeys = async () => {
    try {
      const response = await axios.get('/api/api-keys');
      setApiKeys(response.data.api_keys || []);
    } catch (error) {
      console.error('Failed to fetch API keys:', error);
      toast.error('Failed to load API keys');
    } finally {
      setLoadingKeys(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    if (name.startsWith('parameters.')) {
      const paramName = name.split('.')[1];
      setFormData(prev => ({
        ...prev,
        parameters: {
          ...prev.parameters,
          [paramName]: parseFloat(value) || value
        }
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: name === 'balance' ? parseFloat(value) || 0 : value
      }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Check license before creating bot
    if (!requiresLicense('bot_creation')) {
      return;
    }
    
    if (!formData.api_key_id) {
      toast.error('Please select an API key');
      return;
    }

    setLoading(true);
    try {
      await axios.post('/api/bots', formData);
      toast.success('Bot created successfully!');
      onSuccess();
    } catch (error) {
      const message = error.response?.data?.error || 'Failed to create bot';
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  const getStrategyParameters = () => {
    switch (formData.strategy) {
      case 'sma_crossover':
        return (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Short Window
              </label>
              <input
                type="number"
                name="parameters.short_window"
                value={formData.parameters.short_window}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                min="1"
                max="50"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Long Window
              </label>
              <input
                type="number"
                name="parameters.long_window"
                value={formData.parameters.long_window}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                min="2"
                max="200"
              />
            </div>
          </>
        );
      case 'rsi_oversold':
        return (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                RSI Period
              </label>
              <input
                type="number"
                name="parameters.rsi_period"
                value={formData.parameters.rsi_period || 14}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                min="2"
                max="50"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Oversold Threshold
              </label>
              <input
                type="number"
                name="parameters.oversold_threshold"
                value={formData.parameters.oversold_threshold || 30}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                min="10"
                max="40"
              />
            </div>
          </>
        );
      case 'bollinger_bands':
        return (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Period
              </label>
              <input
                type="number"
                name="parameters.period"
                value={formData.parameters.period || 20}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                min="5"
                max="50"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Standard Deviations
              </label>
              <input
                type="number"
                step="0.1"
                name="parameters.std_dev"
                value={formData.parameters.std_dev || 2}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                min="1"
                max="3"
              />
            </div>
          </>
        );
      default:
        return null;
    }
  };

  return (
    <Dialog open={isOpen} onClose={onClose} className="relative z-50">
      <div className="fixed inset-0 bg-black/30" aria-hidden="true" />
      
      <div className="fixed inset-0 flex items-center justify-center p-4">
        <Dialog.Panel className="mx-auto max-w-2xl w-full bg-white rounded-lg shadow-xl max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <Dialog.Title className="text-lg font-semibold text-gray-900">
              Create New Trading Bot
            </Dialog.Title>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="p-6 space-y-6">
            {/* Basic Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Bot Name *
                </label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="My Trading Bot"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Initial Balance (USD) *
                </label>
                <input
                  type="number"
                  name="balance"
                  value={formData.balance}
                  onChange={handleInputChange}
                  required
                  min="100"
                  step="0.01"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="1000"
                />
              </div>
            </div>

            {/* Strategy Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Trading Strategy *
              </label>
              <select
                name="strategy"
                value={formData.strategy}
                onChange={handleInputChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {strategies.map(strategy => (
                  <option key={strategy.value} value={strategy.value}>
                    {strategy.label}
                  </option>
                ))}
              </select>
              <p className="text-sm text-gray-600 mt-1">
                {strategies.find(s => s.value === formData.strategy)?.description}
              </p>
            </div>

            {/* Exchange and Symbol */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Exchange *
                </label>
                <select
                  name="exchange"
                  value={formData.exchange}
                  onChange={handleInputChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {exchanges.map(exchange => (
                    <option key={exchange.value} value={exchange.value}>
                      {exchange.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Trading Pair *
                </label>
                <input
                  type="text"
                  name="symbol"
                  value={formData.symbol}
                  onChange={handleInputChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="BTCUSDT"
                  list="popular-symbols"
                />
                <datalist id="popular-symbols">
                  {popularSymbols.map(symbol => (
                    <option key={symbol} value={symbol} />
                  ))}
                </datalist>
              </div>
            </div>

            {/* API Key Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                API Key *
              </label>
              {loadingKeys ? (
                <div className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50">
                  Loading API keys...
                </div>
              ) : apiKeys.length === 0 ? (
                <div className="w-full px-3 py-2 border border-gray-300 rounded-md bg-yellow-50 text-yellow-700">
                  No API keys found. Please add an API key first.
                </div>
              ) : (
                <select
                  name="api_key_id"
                  value={formData.api_key_id}
                  onChange={handleInputChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select an API key</option>
                  {apiKeys.map(key => (
                    <option key={key._id} value={key._id}>
                      {key.name} ({key.exchange})
                    </option>
                  ))}
                </select>
              )}
            </div>

            {/* Strategy Parameters */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Strategy Parameters
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {getStrategyParameters()}
                
                {/* Common Risk Management */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Stop Loss (%)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    name="parameters.stop_loss"
                    value={formData.parameters.stop_loss}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    min="0.01"
                    max="0.1"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Take Profit (%)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    name="parameters.take_profit"
                    value={formData.parameters.take_profit}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    min="0.01"
                    max="0.2"
                  />
                </div>
              </div>
            </div>

            {/* Submit Buttons */}
            <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading || apiKeys.length === 0}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Creating...' : 'Create Bot'}
              </button>
            </div>
          </form>
        </Dialog.Panel>
      </div>
    </Dialog>
  );
};

export default CreateBotModal;