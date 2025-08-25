import React, { useState, useEffect } from 'react';
import axios from 'axios';

const APIConnectionTest = () => {
  const [testResults, setTestResults] = useState({});
  const [loading, setLoading] = useState(false);
  const [supportedExchanges, setSupportedExchanges] = useState({});
  const [selectedExchange, setSelectedExchange] = useState('all');
  const [customCredentials, setCustomCredentials] = useState({
    binance: { api_key: '', secret_key: '', testnet: true },
    coinbase: { api_key: '', secret_key: '', passphrase: '', sandbox: true },
    kraken: { api_key: '', secret_key: '' }
  });
  const [useCustomCredentials, setUseCustomCredentials] = useState(false);

  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

  useEffect(() => {
    fetchSupportedExchanges();
  }, []);

  const fetchSupportedExchanges = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/connection/supported-exchanges`);
      if (response.data.success) {
        setSupportedExchanges(response.data.exchanges);
      }
    } catch (error) {
      console.error('Failed to fetch supported exchanges:', error);
    }
  };

  const testConnection = async (exchange) => {
    setLoading(true);
    try {
      const endpoint = exchange === 'all' ? '/test-all' : `/test-${exchange}`;
      const credentials = useCustomCredentials ? customCredentials[exchange] : {};
      
      const response = await axios.post(
        `${API_BASE_URL}/api/connection${endpoint}`,
        credentials,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
          }
        }
      );
      
      if (exchange === 'all') {
        setTestResults(response.data.results);
      } else {
        setTestResults(prev => ({ ...prev, [exchange]: response.data }));
      }
    } catch (error) {
      const errorData = error.response?.data || { success: false, error: 'Network error' };
      if (exchange === 'all') {
        setTestResults({ error: errorData });
      } else {
        setTestResults(prev => ({ ...prev, [exchange]: errorData }));
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCredentialChange = (exchange, field, value) => {
    setCustomCredentials(prev => ({
      ...prev,
      [exchange]: {
        ...prev[exchange],
        [field]: value
      }
    }));
  };

  const getStatusIcon = (result) => {
    if (!result) return '⏳';
    return result.success ? '✅' : '❌';
  };

  const getStatusColor = (result) => {
    if (!result) return 'text-gray-500';
    return result.success ? 'text-green-600' : 'text-red-600';
  };

  const renderExchangeResult = (exchange, result) => {
    if (!result) return null;

    return (
      <div className="bg-white rounded-lg shadow-md p-6 mb-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold capitalize flex items-center">
            <span className="mr-2">{getStatusIcon(result)}</span>
            {supportedExchanges[exchange]?.name || exchange}
          </h3>
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${
            result.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
          }`}>
            {result.success ? 'Connected' : 'Failed'}
          </span>
        </div>

        {result.success ? (
          <div className="space-y-3">
            {result.environment && (
              <div className="flex justify-between">
                <span className="font-medium">Environment:</span>
                <span className={`px-2 py-1 rounded text-sm ${
                  result.environment === 'testnet' || result.environment === 'sandbox'
                    ? 'bg-yellow-100 text-yellow-800'
                    : 'bg-blue-100 text-blue-800'
                }`}>
                  {result.environment}
                </span>
              </div>
            )}
            
            {result.account && (
              <div className="bg-gray-50 p-3 rounded">
                <h4 className="font-medium mb-2">Account Info:</h4>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>Type: {result.account.type}</div>
                  <div>Can Trade: {result.account.can_trade ? '✅' : '❌'}</div>
                  {result.account.can_withdraw !== undefined && (
                    <div>Can Withdraw: {result.account.can_withdraw ? '✅' : '❌'}</div>
                  )}
                  {result.account.can_deposit !== undefined && (
                    <div>Can Deposit: {result.account.can_deposit ? '✅' : '❌'}</div>
                  )}
                </div>
              </div>
            )}

            {result.balances && result.balances.length > 0 && (
              <div className="bg-gray-50 p-3 rounded">
                <h4 className="font-medium mb-2">Balances:</h4>
                <div className="space-y-1 text-sm max-h-32 overflow-y-auto">
                  {result.balances.map((balance, index) => (
                    <div key={index} className="flex justify-between">
                      <span>{balance.asset || balance.currency}:</span>
                      <span className="font-mono">
                        {balance.total ? balance.total.toFixed(8) : balance.balance?.toFixed(8) || '0'}
                      </span>
                    </div>
                  ))}
                  {result.total_assets > result.balances.length && (
                    <div className="text-gray-500 italic">
                      ... and {result.total_assets - result.balances.length} more assets
                    </div>
                  )}
                </div>
              </div>
            )}

            {result.market_data && (
              <div className="bg-gray-50 p-3 rounded">
                <h4 className="font-medium mb-2">Market Data Test:</h4>
                <div className="text-sm">
                  {result.market_data.symbol}: ${result.market_data.price.toLocaleString()}
                </div>
              </div>
            )}

            {result.trading_permissions && (
              <div className="bg-gray-50 p-3 rounded">
                <h4 className="font-medium mb-2">Trading Permissions:</h4>
                <div className="text-sm">
                  <div className="flex items-center">
                    <span className="mr-2">{result.trading_permissions.can_trade ? '✅' : '❌'}</span>
                    Can Place Orders
                  </div>
                  {result.trading_permissions.note && (
                    <div className="text-gray-600 mt-1">{result.trading_permissions.note}</div>
                  )}
                  {result.trading_permissions.error && (
                    <div className="text-red-600 mt-1">{result.trading_permissions.error}</div>
                  )}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-3">
            <div className="bg-red-50 p-3 rounded">
              <h4 className="font-medium text-red-800 mb-2">Error:</h4>
              <p className="text-red-700 text-sm">{result.error}</p>
              {result.details && (
                <p className="text-red-600 text-xs mt-1">{result.details}</p>
              )}
            </div>
            
            {result.suggestions && result.suggestions.length > 0 && (
              <div className="bg-yellow-50 p-3 rounded">
                <h4 className="font-medium text-yellow-800 mb-2">Suggestions:</h4>
                <ul className="text-yellow-700 text-sm space-y-1">
                  {result.suggestions.map((suggestion, index) => (
                    <li key={index} className="flex items-start">
                      <span className="mr-2">•</span>
                      {suggestion}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {result.timestamp && (
          <div className="text-xs text-gray-500 mt-3">
            Tested at: {new Date(result.timestamp).toLocaleString()}
          </div>
        )}
      </div>
    );
  };

  const renderCredentialForm = (exchange) => {
    const exchangeConfig = supportedExchanges[exchange];
    if (!exchangeConfig) return null;

    return (
      <div className="bg-gray-50 p-4 rounded-lg mb-4">
        <h4 className="font-medium mb-3">Custom Credentials for {exchangeConfig.name}</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {exchangeConfig.required_credentials.map(field => {
            const fieldName = field.toLowerCase().replace(/.*_/, '');
            return (
              <div key={field}>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {fieldName.charAt(0).toUpperCase() + fieldName.slice(1)}
                </label>
                <input
                  type={fieldName.includes('secret') || fieldName.includes('passphrase') ? 'password' : 'text'}
                  value={customCredentials[exchange][fieldName] || ''}
                  onChange={(e) => handleCredentialChange(exchange, fieldName, e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder={`Enter ${fieldName}`}
                />
              </div>
            );
          })}
          
          {exchangeConfig.optional_settings.map(setting => {
            const settingName = setting.toLowerCase().replace(/.*_/, '');
            if (settingName === 'testnet' || settingName === 'sandbox') {
              return (
                <div key={setting} className="flex items-center">
                  <input
                    type="checkbox"
                    id={`${exchange}-${settingName}`}
                    checked={customCredentials[exchange][settingName] || false}
                    onChange={(e) => handleCredentialChange(exchange, settingName, e.target.checked)}
                    className="mr-2"
                  />
                  <label htmlFor={`${exchange}-${settingName}`} className="text-sm">
                    Use {settingName}
                  </label>
                </div>
              );
            }
            return null;
          })}
        </div>
      </div>
    );
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">API Connection Test</h1>
        <p className="text-gray-600">
          Test your exchange API connections to ensure your trading bot can communicate properly.
        </p>
      </div>

      {/* Configuration Panel */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Test Configuration</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Exchange to Test
            </label>
            <select
              value={selectedExchange}
              onChange={(e) => setSelectedExchange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Configured Exchanges</option>
              {Object.entries(supportedExchanges).map(([key, exchange]) => (
                <option key={key} value={key}>
                  {exchange.name} {exchange.configured ? '(Configured)' : '(Not Configured)'}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="use-custom-credentials"
              checked={useCustomCredentials}
              onChange={(e) => setUseCustomCredentials(e.target.checked)}
              className="mr-2"
            />
            <label htmlFor="use-custom-credentials" className="text-sm">
              Use custom credentials (instead of .env file)
            </label>
          </div>
        </div>

        {/* Custom Credentials Forms */}
        {useCustomCredentials && selectedExchange !== 'all' && (
          <div className="mt-6">
            {renderCredentialForm(selectedExchange)}
          </div>
        )}

        {useCustomCredentials && selectedExchange === 'all' && (
          <div className="mt-6 space-y-4">
            {Object.keys(supportedExchanges).map(exchange => renderCredentialForm(exchange))}
          </div>
        )}

        {/* Test Button */}
        <div className="mt-6">
          <button
            onClick={() => testConnection(selectedExchange)}
            disabled={loading}
            className={`px-6 py-3 rounded-lg font-medium ${
              loading
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500'
            } text-white transition-colors`}
          >
            {loading ? (
              <span className="flex items-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Testing Connection...
              </span>
            ) : (
              `Test ${selectedExchange === 'all' ? 'All Exchanges' : supportedExchanges[selectedExchange]?.name || selectedExchange}`
            )}
          </button>
        </div>
      </div>

      {/* Results Panel */}
      {Object.keys(testResults).length > 0 && (
        <div>
          <h2 className="text-xl font-semibold mb-4">Test Results</h2>
          
          {testResults.error ? (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <h3 className="text-red-800 font-medium">Test Failed</h3>
              <p className="text-red-700 mt-1">{testResults.error.error || 'Unknown error occurred'}</p>
            </div>
          ) : (
            <div className="space-y-4">
              {Object.entries(testResults).map(([exchange, result]) => 
                renderExchangeResult(exchange, result)
              )}
            </div>
          )}
        </div>
      )}

      {/* Help Section */}
      <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-blue-800 font-medium mb-2">Need Help?</h3>
        <div className="text-blue-700 text-sm space-y-1">
          <p>• Make sure your API keys are properly configured in your .env file</p>
          <p>• Check that IP restrictions are set correctly in your exchange settings</p>
          <p>• Ensure your API keys have the necessary permissions enabled</p>
          <p>• For detailed setup instructions, see the API Integration Guide</p>
        </div>
      </div>
    </div>
  );
};

export default APIConnectionTest;