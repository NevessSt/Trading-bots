import React, { useState, useEffect } from 'react';
import { 
  CheckCircle, 
  AlertTriangle, 
  ArrowRight, 
  ArrowLeft, 
  Eye, 
  EyeOff,
  Shield,
  Settings,
  TrendingUp,
  Wallet,
  Info,
  ExternalLink,
  Copy,
  Check
} from 'lucide-react';

const SetupWizard = ({ onComplete, onSkip }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [formData, setFormData] = useState({
    // Exchange Configuration
    exchange: '',
    apiKey: '',
    apiSecret: '',
    testConnection: false,
    
    // Trading Preferences
    tradingPairs: ['BTC/USDT'],
    defaultStrategy: 'dca',
    timeframe: '1h',
    
    // Risk Management
    maxPortfolioRisk: 5,
    stopLossPercentage: 2,
    takeProfitPercentage: 5,
    maxPositionSize: 10,
    dailyLossLimit: 1000,
    
    // Notifications
    emailNotifications: true,
    tradeAlerts: true,
    riskAlerts: true
  });
  
  const [showApiSecret, setShowApiSecret] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [copiedField, setCopiedField] = useState(null);

  const steps = [
    {
      id: 'welcome',
      title: 'Welcome to Trading Bot Setup',
      icon: <Shield className="w-8 h-8" />,
      description: 'Let\'s get you started with safe and profitable trading'
    },
    {
      id: 'exchange',
      title: 'Exchange Configuration',
      icon: <Wallet className="w-8 h-8" />,
      description: 'Connect your exchange account securely'
    },
    {
      id: 'preferences',
      title: 'Trading Preferences',
      icon: <Settings className="w-8 h-8" />,
      description: 'Configure your trading strategy and preferences'
    },
    {
      id: 'risk',
      title: 'Risk Management',
      icon: <AlertTriangle className="w-8 h-8" />,
      description: 'Set up safety limits to protect your capital'
    },
    {
      id: 'complete',
      title: 'Setup Complete',
      icon: <CheckCircle className="w-8 h-8" />,
      description: 'You\'re ready to start trading!'
    }
  ];

  const exchanges = [
    { id: 'binance', name: 'Binance', supported: true },
    { id: 'coinbase', name: 'Coinbase Pro', supported: true },
    { id: 'kraken', name: 'Kraken', supported: true },
    { id: 'kucoin', name: 'KuCoin', supported: false },
  ];

  const strategies = [
    { id: 'dca', name: 'Dollar Cost Averaging', description: 'Buy fixed amounts regularly', risk: 'Low' },
    { id: 'grid', name: 'Grid Trading', description: 'Buy low, sell high in ranges', risk: 'Medium' },
    { id: 'scalping', name: 'Scalping', description: 'Quick small profits', risk: 'High' },
    { id: 'manual', name: 'Manual Trading', description: 'Full control over trades', risk: 'Variable' }
  ];

  const timeframes = [
    { id: '1m', name: '1 Minute', recommended: false },
    { id: '5m', name: '5 Minutes', recommended: false },
    { id: '15m', name: '15 Minutes', recommended: true },
    { id: '1h', name: '1 Hour', recommended: true },
    { id: '4h', name: '4 Hours', recommended: true },
    { id: '1d', name: '1 Day', recommended: true }
  ];

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleArrayChange = (field, value, checked) => {
    setFormData(prev => ({
      ...prev,
      [field]: checked 
        ? [...prev[field], value]
        : prev[field].filter(item => item !== value)
    }));
  };

  const testApiConnection = async () => {
    if (!formData.apiKey || !formData.apiSecret || !formData.exchange) {
      alert('Please fill in all API credentials first');
      return;
    }

    setIsLoading(true);
    setConnectionStatus(null);

    try {
      // Simulate API connection test
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Simulate success/failure
      const success = Math.random() > 0.3; // 70% success rate for demo
      
      if (success) {
        setConnectionStatus({ success: true, message: 'Connection successful!' });
        setFormData(prev => ({ ...prev, testConnection: true }));
      } else {
        setConnectionStatus({ 
          success: false, 
          message: 'Connection failed. Please check your API credentials.' 
        });
      }
    } catch (error) {
      setConnectionStatus({ 
        success: false, 
        message: 'Connection error. Please try again.' 
      });
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = (text, field) => {
    navigator.clipboard.writeText(text);
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 2000);
  };

  const canProceed = () => {
    switch (currentStep) {
      case 0: return true; // Welcome step
      case 1: return formData.exchange && formData.apiKey && formData.apiSecret; // Exchange step
      case 2: return formData.defaultStrategy && formData.timeframe; // Preferences step
      case 3: return true; // Risk management step
      case 4: return true; // Complete step
      default: return false;
    }
  };

  const nextStep = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const completeSetup = () => {
    // Save configuration
    localStorage.setItem('tradingBotConfig', JSON.stringify(formData));
    localStorage.setItem('setupCompleted', 'true');
    
    if (onComplete) {
      onComplete(formData);
    }
  };

  const skipSetup = () => {
    localStorage.setItem('setupSkipped', 'true');
    if (onSkip) {
      onSkip();
    }
  };

  const renderWelcomeStep = () => (
    <div className="text-center space-y-6">
      <div className="mx-auto w-24 h-24 bg-blue-100 rounded-full flex items-center justify-center">
        <Shield className="w-12 h-12 text-blue-600" />
      </div>
      
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          Welcome to Your Trading Bot Setup
        </h2>
        <p className="text-gray-600 text-lg mb-6">
          This wizard will guide you through setting up your trading bot safely and securely.
          The entire process takes about 5 minutes.
        </p>
      </div>

      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <AlertTriangle className="w-5 h-5 text-yellow-600 mt-0.5" />
          <div className="text-left">
            <h3 className="font-semibold text-yellow-800">Important Safety Reminder</h3>
            <p className="text-yellow-700 text-sm mt-1">
              Never invest more than you can afford to lose. Cryptocurrency trading involves substantial risk.
              Start with small amounts and test thoroughly before increasing your investment.
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
        <div className="bg-green-50 p-4 rounded-lg">
          <CheckCircle className="w-6 h-6 text-green-600 mx-auto mb-2" />
          <h4 className="font-semibold text-green-800">Secure</h4>
          <p className="text-green-700">API-only access, no withdrawals</p>
        </div>
        <div className="bg-blue-50 p-4 rounded-lg">
          <TrendingUp className="w-6 h-6 text-blue-600 mx-auto mb-2" />
          <h4 className="font-semibold text-blue-800">Profitable</h4>
          <p className="text-blue-700">Proven strategies with backtesting</p>
        </div>
        <div className="bg-purple-50 p-4 rounded-lg">
          <Settings className="w-6 h-6 text-purple-600 mx-auto mb-2" />
          <h4 className="font-semibold text-purple-800">Customizable</h4>
          <p className="text-purple-700">Tailored to your risk tolerance</p>
        </div>
      </div>
    </div>
  );

  const renderExchangeStep = () => (
    <div className="space-y-6">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Connect Your Exchange</h2>
        <p className="text-gray-600">
          Choose your exchange and enter your API credentials. We'll test the connection to ensure everything works.
        </p>
      </div>

      {/* Exchange Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">
          Select Exchange
        </label>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {exchanges.map(exchange => (
            <button
              key={exchange.id}
              onClick={() => exchange.supported && handleInputChange('exchange', exchange.id)}
              disabled={!exchange.supported}
              className={`p-4 border rounded-lg text-left transition-colors ${
                formData.exchange === exchange.id
                  ? 'border-blue-500 bg-blue-50'
                  : exchange.supported
                  ? 'border-gray-300 hover:border-gray-400'
                  : 'border-gray-200 bg-gray-50 cursor-not-allowed'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className={`font-medium ${
                  exchange.supported ? 'text-gray-900' : 'text-gray-400'
                }`}>
                  {exchange.name}
                </span>
                {!exchange.supported && (
                  <span className="text-xs text-gray-500 bg-gray-200 px-2 py-1 rounded">
                    Coming Soon
                  </span>
                )}
              </div>
            </button>
          ))}
        </div>
      </div>

      {formData.exchange && (
        <div className="space-y-4">
          {/* API Key */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              API Key
            </label>
            <div className="relative">
              <input
                type="text"
                value={formData.apiKey}
                onChange={(e) => handleInputChange('apiKey', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 pr-10"
                placeholder="Enter your API key"
              />
              <button
                onClick={() => copyToClipboard(formData.apiKey, 'apiKey')}
                className="absolute right-2 top-2 p-1 text-gray-400 hover:text-gray-600"
              >
                {copiedField === 'apiKey' ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {/* API Secret */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              API Secret
            </label>
            <div className="relative">
              <input
                type={showApiSecret ? 'text' : 'password'}
                value={formData.apiSecret}
                onChange={(e) => handleInputChange('apiSecret', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 pr-20"
                placeholder="Enter your API secret"
              />
              <div className="absolute right-2 top-2 flex space-x-1">
                <button
                  onClick={() => setShowApiSecret(!showApiSecret)}
                  className="p-1 text-gray-400 hover:text-gray-600"
                >
                  {showApiSecret ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
                <button
                  onClick={() => copyToClipboard(formData.apiSecret, 'apiSecret')}
                  className="p-1 text-gray-400 hover:text-gray-600"
                >
                  {copiedField === 'apiSecret' ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                </button>
              </div>
            </div>
          </div>

          {/* Test Connection */}
          <div className="space-y-3">
            <button
              onClick={testApiConnection}
              disabled={isLoading || !formData.apiKey || !formData.apiSecret}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
            >
              {isLoading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Testing Connection...</span>
                </>
              ) : (
                <span>Test API Connection</span>
              )}
            </button>

            {connectionStatus && (
              <div className={`p-3 rounded-md flex items-center space-x-2 ${
                connectionStatus.success 
                  ? 'bg-green-50 text-green-800 border border-green-200'
                  : 'bg-red-50 text-red-800 border border-red-200'
              }`}>
                {connectionStatus.success ? (
                  <CheckCircle className="w-5 h-5" />
                ) : (
                  <AlertTriangle className="w-5 h-5" />
                )}
                <span>{connectionStatus.message}</span>
              </div>
            )}
          </div>

          {/* API Setup Instructions */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start space-x-3">
              <Info className="w-5 h-5 text-blue-600 mt-0.5" />
              <div>
                <h4 className="font-semibold text-blue-800 mb-2">How to get API credentials:</h4>
                <ol className="text-blue-700 text-sm space-y-1 list-decimal list-inside">
                  <li>Log into your {formData.exchange} account</li>
                  <li>Go to API Management section</li>
                  <li>Create a new API key with "Spot Trading" permissions</li>
                  <li>Disable "Withdraw" permissions for security</li>
                  <li>Add your IP address to the whitelist</li>
                </ol>
                <a 
                  href={`https://${formData.exchange}.com/api-management`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center space-x-1 text-blue-600 hover:text-blue-800 mt-2"
                >
                  <span>Open API Management</span>
                  <ExternalLink className="w-4 h-4" />
                </a>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderPreferencesStep = () => (
    <div className="space-y-6">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Trading Preferences</h2>
        <p className="text-gray-600">
          Configure your default trading strategy and preferences. You can change these later.
        </p>
      </div>

      {/* Trading Strategy */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">
          Default Trading Strategy
        </label>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {strategies.map(strategy => (
            <button
              key={strategy.id}
              onClick={() => handleInputChange('defaultStrategy', strategy.id)}
              className={`p-4 border rounded-lg text-left transition-colors ${
                formData.defaultStrategy === strategy.id
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
            >
              <div className="flex items-start justify-between mb-2">
                <h4 className="font-semibold text-gray-900">{strategy.name}</h4>
                <span className={`text-xs px-2 py-1 rounded ${
                  strategy.risk === 'Low' ? 'bg-green-100 text-green-800' :
                  strategy.risk === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                  strategy.risk === 'High' ? 'bg-red-100 text-red-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {strategy.risk} Risk
                </span>
              </div>
              <p className="text-gray-600 text-sm">{strategy.description}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Timeframe */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">
          Default Timeframe
        </label>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {timeframes.map(timeframe => (
            <button
              key={timeframe.id}
              onClick={() => handleInputChange('timeframe', timeframe.id)}
              className={`p-3 border rounded-lg text-center transition-colors relative ${
                formData.timeframe === timeframe.id
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
            >
              <span className="font-medium">{timeframe.name}</span>
              {timeframe.recommended && (
                <span className="absolute -top-2 -right-2 bg-green-500 text-white text-xs px-2 py-1 rounded-full">
                  ✓
                </span>
              )}
            </button>
          ))}
        </div>
        <p className="text-sm text-gray-500 mt-2">
          ✓ indicates recommended timeframes for beginners
        </p>
      </div>

      {/* Trading Pairs */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">
          Trading Pairs (you can add more later)
        </label>
        <div className="space-y-2">
          {['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT'].map(pair => (
            <label key={pair} className="flex items-center space-x-3">
              <input
                type="checkbox"
                checked={formData.tradingPairs.includes(pair)}
                onChange={(e) => handleArrayChange('tradingPairs', pair, e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-gray-700">{pair}</span>
            </label>
          ))}
        </div>
      </div>
    </div>
  );

  const renderRiskStep = () => (
    <div className="space-y-6">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Risk Management</h2>
        <p className="text-gray-600">
          Set up safety limits to protect your capital. These are crucial for safe trading.
        </p>
      </div>

      <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
        <div className="flex items-start space-x-3">
          <AlertTriangle className="w-5 h-5 text-red-600 mt-0.5" />
          <div>
            <h4 className="font-semibold text-red-800">Risk Management is Critical</h4>
            <p className="text-red-700 text-sm mt-1">
              These settings help prevent large losses. Start conservative and adjust as you gain experience.
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Portfolio Risk */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Maximum Portfolio Risk: {formData.maxPortfolioRisk}%
          </label>
          <input
            type="range"
            min="1"
            max="20"
            value={formData.maxPortfolioRisk}
            onChange={(e) => handleInputChange('maxPortfolioRisk', parseInt(e.target.value))}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>Conservative (1%)</span>
            <span>Aggressive (20%)</span>
          </div>
        </div>

        {/* Stop Loss */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Default Stop Loss: {formData.stopLossPercentage}%
          </label>
          <input
            type="range"
            min="0.5"
            max="10"
            step="0.5"
            value={formData.stopLossPercentage}
            onChange={(e) => handleInputChange('stopLossPercentage', parseFloat(e.target.value))}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>Tight (0.5%)</span>
            <span>Loose (10%)</span>
          </div>
        </div>

        {/* Take Profit */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Default Take Profit: {formData.takeProfitPercentage}%
          </label>
          <input
            type="range"
            min="1"
            max="20"
            step="0.5"
            value={formData.takeProfitPercentage}
            onChange={(e) => handleInputChange('takeProfitPercentage', parseFloat(e.target.value))}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>Conservative (1%)</span>
            <span>Aggressive (20%)</span>
          </div>
        </div>

        {/* Position Size */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Max Position Size: {formData.maxPositionSize}%
          </label>
          <input
            type="range"
            min="1"
            max="50"
            value={formData.maxPositionSize}
            onChange={(e) => handleInputChange('maxPositionSize', parseInt(e.target.value))}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>Safe (1%)</span>
            <span>Risky (50%)</span>
          </div>
        </div>
      </div>

      {/* Daily Loss Limit */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Daily Loss Limit ($)
        </label>
        <input
          type="number"
          value={formData.dailyLossLimit}
          onChange={(e) => handleInputChange('dailyLossLimit', parseInt(e.target.value))}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Enter daily loss limit in USD"
        />
        <p className="text-sm text-gray-500 mt-1">
          Trading will stop if daily losses exceed this amount
        </p>
      </div>

      {/* Notifications */}
      <div>
        <h4 className="font-medium text-gray-700 mb-3">Notification Preferences</h4>
        <div className="space-y-2">
          <label className="flex items-center space-x-3">
            <input
              type="checkbox"
              checked={formData.tradeAlerts}
              onChange={(e) => handleInputChange('tradeAlerts', e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="text-gray-700">Trade execution alerts</span>
          </label>
          <label className="flex items-center space-x-3">
            <input
              type="checkbox"
              checked={formData.riskAlerts}
              onChange={(e) => handleInputChange('riskAlerts', e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="text-gray-700">Risk limit alerts</span>
          </label>
          <label className="flex items-center space-x-3">
            <input
              type="checkbox"
              checked={formData.emailNotifications}
              onChange={(e) => handleInputChange('emailNotifications', e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="text-gray-700">Email notifications</span>
          </label>
        </div>
      </div>
    </div>
  );

  const renderCompleteStep = () => (
    <div className="text-center space-y-6">
      <div className="mx-auto w-24 h-24 bg-green-100 rounded-full flex items-center justify-center">
        <CheckCircle className="w-12 h-12 text-green-600" />
      </div>
      
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          Setup Complete!
        </h2>
        <p className="text-gray-600 text-lg mb-6">
          Your trading bot is now configured and ready to use. Here's a summary of your settings:
        </p>
      </div>

      {/* Configuration Summary */}
      <div className="bg-gray-50 rounded-lg p-6 text-left space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h4 className="font-semibold text-gray-700 mb-2">Exchange & Strategy</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>Exchange: {formData.exchange?.toUpperCase()}</li>
              <li>Strategy: {strategies.find(s => s.id === formData.defaultStrategy)?.name}</li>
              <li>Timeframe: {timeframes.find(t => t.id === formData.timeframe)?.name}</li>
              <li>Trading Pairs: {formData.tradingPairs.join(', ')}</li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold text-gray-700 mb-2">Risk Management</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>Portfolio Risk: {formData.maxPortfolioRisk}%</li>
              <li>Stop Loss: {formData.stopLossPercentage}%</li>
              <li>Take Profit: {formData.takeProfitPercentage}%</li>
              <li>Daily Limit: ${formData.dailyLossLimit}</li>
            </ul>
          </div>
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <Info className="w-5 h-5 text-blue-600 mt-0.5" />
          <div className="text-left">
            <h4 className="font-semibold text-blue-800">Next Steps:</h4>
            <ol className="text-blue-700 text-sm mt-1 list-decimal list-inside space-y-1">
              <li>Start with paper trading to test your strategy</li>
              <li>Begin with small amounts when ready for live trading</li>
              <li>Monitor your trades regularly</li>
              <li>Adjust settings based on performance</li>
            </ol>
          </div>
        </div>
      </div>

      <div className="flex space-x-4 justify-center">
        <button
          onClick={completeSetup}
          className="bg-green-600 text-white px-6 py-3 rounded-md hover:bg-green-700 font-medium"
        >
          Start Trading Dashboard
        </button>
        <button
          onClick={() => setCurrentStep(0)}
          className="bg-gray-200 text-gray-700 px-6 py-3 rounded-md hover:bg-gray-300 font-medium"
        >
          Review Settings
        </button>
      </div>
    </div>
  );

  const renderCurrentStep = () => {
    switch (currentStep) {
      case 0: return renderWelcomeStep();
      case 1: return renderExchangeStep();
      case 2: return renderPreferencesStep();
      case 3: return renderRiskStep();
      case 4: return renderCompleteStep();
      default: return renderWelcomeStep();
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Trading Bot Setup</h1>
          <p className="text-gray-600">Get started with automated trading in just a few steps</p>
        </div>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            {steps.map((step, index) => (
              <div key={step.id} className="flex items-center">
                <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 ${
                  index <= currentStep 
                    ? 'bg-blue-600 border-blue-600 text-white'
                    : 'bg-white border-gray-300 text-gray-400'
                }`}>
                  {index < currentStep ? (
                    <CheckCircle className="w-6 h-6" />
                  ) : (
                    <span className="text-sm font-medium">{index + 1}</span>
                  )}
                </div>
                {index < steps.length - 1 && (
                  <div className={`w-full h-1 mx-4 ${
                    index < currentStep ? 'bg-blue-600' : 'bg-gray-300'
                  }`} />
                )}
              </div>
            ))}
          </div>
          <div className="flex justify-between text-sm text-gray-600">
            {steps.map((step, index) => (
              <div key={step.id} className="text-center" style={{ width: '20%' }}>
                <div className="font-medium">{step.title}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Main Content */}
        <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
          {renderCurrentStep()}
        </div>

        {/* Navigation */}
        {currentStep < steps.length - 1 && (
          <div className="flex justify-between items-center">
            <div>
              {currentStep > 0 && (
                <button
                  onClick={prevStep}
                  className="flex items-center space-x-2 text-gray-600 hover:text-gray-800"
                >
                  <ArrowLeft className="w-4 h-4" />
                  <span>Previous</span>
                </button>
              )}
            </div>
            
            <div className="flex space-x-4">
              <button
                onClick={skipSetup}
                className="text-gray-500 hover:text-gray-700 px-4 py-2"
              >
                Skip Setup
              </button>
              <button
                onClick={nextStep}
                disabled={!canProceed()}
                className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                <span>Continue</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SetupWizard;