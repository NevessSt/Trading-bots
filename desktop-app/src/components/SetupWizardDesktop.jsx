import React, { useState, useEffect } from 'react';
import './SetupWizard.css';

const SetupWizardDesktop = ({ onComplete, onSkip }) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [apiTestResult, setApiTestResult] = useState(null);
  const [formData, setFormData] = useState({
    // API Configuration
    exchange: 'binance',
    apiKey: '',
    apiSecret: '',
    testnet: true,
    
    // Trading Preferences
    defaultStrategy: 'dca',
    baseCurrency: 'USDT',
    maxActivePositions: 3,
    autoTrade: false,
    
    // Risk Management
    maxDailyLoss: 100,
    maxPositionSize: 50,
    stopLossPercentage: 5,
    takeProfitPercentage: 10,
    enableEmergencyStop: true
  });

  const steps = [
    { id: 1, title: 'Welcome', icon: '👋' },
    { id: 2, title: 'Exchange Setup', icon: '🔑' },
    { id: 3, title: 'Trading Preferences', icon: '⚙️' },
    { id: 4, title: 'Risk Management', icon: '🛡️' },
    { id: 5, title: 'Complete', icon: '✅' }
  ];

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (apiTestResult) {
      setApiTestResult(null); // Clear test result when API config changes
    }
  };

  const testApiConnection = async () => {
    if (!formData.apiKey || !formData.apiSecret) {
      setApiTestResult({ success: false, message: 'Please enter API key and secret' });
      return;
    }

    setIsLoading(true);
    setApiTestResult(null);

    try {
      const result = await window.electronAPI.testApiConnection({
        exchange: formData.exchange,
        apiKey: formData.apiKey,
        apiSecret: formData.apiSecret,
        testnet: formData.testnet
      });
      setApiTestResult(result);
    } catch (error) {
      setApiTestResult({ success: false, message: 'Connection test failed' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleNext = () => {
    if (currentStep < steps.length) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleComplete = async () => {
    setIsLoading(true);
    try {
      await window.electronAPI.saveSetupConfig({
        apiConfig: {
          exchange: formData.exchange,
          apiKey: formData.apiKey,
          apiSecret: formData.apiSecret,
          testnet: formData.testnet
        },
        tradingPrefs: {
          defaultStrategy: formData.defaultStrategy,
          baseCurrency: formData.baseCurrency,
          maxActivePositions: formData.maxActivePositions,
          autoTrade: formData.autoTrade
        },
        riskSettings: {
          maxDailyLoss: formData.maxDailyLoss,
          maxPositionSize: formData.maxPositionSize,
          stopLossPercentage: formData.stopLossPercentage,
          takeProfitPercentage: formData.takeProfitPercentage,
          enableEmergencyStop: formData.enableEmergencyStop
        }
      });
      onComplete();
    } catch (error) {
      console.error('Failed to save setup configuration:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSkip = async () => {
    try {
      await window.electronAPI.skipSetup();
      onSkip();
    } catch (error) {
      console.error('Failed to skip setup:', error);
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="step-content">
            <div className="welcome-content">
              <h2>Welcome to TradingBot Pro!</h2>
              <p>Let's get you set up with a quick configuration wizard. This will help you:</p>
              <ul>
                <li>🔑 Configure your exchange API credentials</li>
                <li>⚙️ Set your trading preferences</li>
                <li>🛡️ Configure risk management settings</li>
                <li>🚀 Start trading safely</li>
              </ul>
              <div className="setup-options">
                <p>This setup takes about 3-5 minutes and ensures you're ready to trade safely.</p>
              </div>
            </div>
          </div>
        );

      case 2:
        return (
          <div className="step-content">
            <h2>Exchange API Configuration</h2>
            <p>Connect your exchange account to enable trading</p>
            
            <div className="form-group">
              <label>Exchange</label>
              <select 
                value={formData.exchange} 
                onChange={(e) => handleInputChange('exchange', e.target.value)}
              >
                <option value="binance">Binance</option>
                <option value="coinbase">Coinbase Pro</option>
                <option value="kraken">Kraken</option>
                <option value="kucoin">KuCoin</option>
              </select>
            </div>

            <div className="form-group">
              <label>API Key</label>
              <input
                type="text"
                value={formData.apiKey}
                onChange={(e) => handleInputChange('apiKey', e.target.value)}
                placeholder="Enter your API key"
              />
            </div>

            <div className="form-group">
              <label>API Secret</label>
              <input
                type="password"
                value={formData.apiSecret}
                onChange={(e) => handleInputChange('apiSecret', e.target.value)}
                placeholder="Enter your API secret"
              />
            </div>

            <div className="form-group checkbox-group">
              <label>
                <input
                  type="checkbox"
                  checked={formData.testnet}
                  onChange={(e) => handleInputChange('testnet', e.target.checked)}
                />
                Use Testnet (Recommended for first-time users)
              </label>
            </div>

            <div className="api-test-section">
              <button 
                onClick={testApiConnection} 
                disabled={isLoading || !formData.apiKey || !formData.apiSecret}
                className="test-button"
              >
                {isLoading ? 'Testing...' : 'Test Connection'}
              </button>
              
              {apiTestResult && (
                <div className={`test-result ${apiTestResult.success ? 'success' : 'error'}`}>
                  {apiTestResult.success ? '✅' : '❌'} {apiTestResult.message}
                </div>
              )}
            </div>

            <div className="security-note">
              <p>🔒 Your API keys are stored securely and never shared</p>
            </div>
          </div>
        );

      case 3:
        return (
          <div className="step-content">
            <h2>Trading Preferences</h2>
            <p>Configure your default trading settings</p>

            <div className="form-group">
              <label>Default Strategy</label>
              <select 
                value={formData.defaultStrategy} 
                onChange={(e) => handleInputChange('defaultStrategy', e.target.value)}
              >
                <option value="dca">Dollar Cost Averaging (DCA)</option>
                <option value="grid">Grid Trading</option>
                <option value="scalping">Scalping</option>
                <option value="swing">Swing Trading</option>
              </select>
            </div>

            <div className="form-group">
              <label>Base Currency</label>
              <select 
                value={formData.baseCurrency} 
                onChange={(e) => handleInputChange('baseCurrency', e.target.value)}
              >
                <option value="USDT">USDT</option>
                <option value="BUSD">BUSD</option>
                <option value="USD">USD</option>
                <option value="EUR">EUR</option>
              </select>
            </div>

            <div className="form-group">
              <label>Max Active Positions</label>
              <input
                type="number"
                min="1"
                max="10"
                value={formData.maxActivePositions}
                onChange={(e) => handleInputChange('maxActivePositions', parseInt(e.target.value))}
              />
            </div>

            <div className="form-group checkbox-group">
              <label>
                <input
                  type="checkbox"
                  checked={formData.autoTrade}
                  onChange={(e) => handleInputChange('autoTrade', e.target.checked)}
                />
                Enable Automatic Trading (Can be changed later)
              </label>
            </div>
          </div>
        );

      case 4:
        return (
          <div className="step-content">
            <h2>Risk Management</h2>
            <p>Set up safety limits to protect your capital</p>

            <div className="form-group">
              <label>Max Daily Loss ($)</label>
              <input
                type="number"
                min="10"
                step="10"
                value={formData.maxDailyLoss}
                onChange={(e) => handleInputChange('maxDailyLoss', parseFloat(e.target.value))}
              />
            </div>

            <div className="form-group">
              <label>Max Position Size ($)</label>
              <input
                type="number"
                min="10"
                step="10"
                value={formData.maxPositionSize}
                onChange={(e) => handleInputChange('maxPositionSize', parseFloat(e.target.value))}
              />
            </div>

            <div className="form-group">
              <label>Stop Loss Percentage (%)</label>
              <input
                type="number"
                min="1"
                max="20"
                step="0.5"
                value={formData.stopLossPercentage}
                onChange={(e) => handleInputChange('stopLossPercentage', parseFloat(e.target.value))}
              />
            </div>

            <div className="form-group">
              <label>Take Profit Percentage (%)</label>
              <input
                type="number"
                min="1"
                max="50"
                step="0.5"
                value={formData.takeProfitPercentage}
                onChange={(e) => handleInputChange('takeProfitPercentage', parseFloat(e.target.value))}
              />
            </div>

            <div className="form-group checkbox-group">
              <label>
                <input
                  type="checkbox"
                  checked={formData.enableEmergencyStop}
                  onChange={(e) => handleInputChange('enableEmergencyStop', e.target.checked)}
                />
                Enable Emergency Stop (Recommended)
              </label>
            </div>

            <div className="risk-warning">
              <p>⚠️ These settings help protect your capital. You can adjust them later in settings.</p>
            </div>
          </div>
        );

      case 5:
        return (
          <div className="step-content">
            <div className="completion-content">
              <h2>🎉 Setup Complete!</h2>
              <p>Your TradingBot Pro is now configured and ready to use.</p>
              
              <div className="setup-summary">
                <h3>Configuration Summary:</h3>
                <ul>
                  <li>Exchange: {formData.exchange}</li>
                  <li>Strategy: {formData.defaultStrategy}</li>
                  <li>Base Currency: {formData.baseCurrency}</li>
                  <li>Max Daily Loss: ${formData.maxDailyLoss}</li>
                  <li>Auto Trading: {formData.autoTrade ? 'Enabled' : 'Disabled'}</li>
                </ul>
              </div>

              <div className="next-steps">
                <h3>Next Steps:</h3>
                <ul>
                  <li>📊 Review your dashboard</li>
                  <li>📈 Monitor market conditions</li>
                  <li>🎯 Start with small positions</li>
                  <li>📚 Check our documentation for advanced features</li>
                </ul>
              </div>

              <div className="safety-reminder">
                <p>🛡️ Remember: Start small, monitor closely, and never invest more than you can afford to lose.</p>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="setup-wizard-overlay">
      <div className="setup-wizard">
        <div className="wizard-header">
          <div className="progress-bar">
            {steps.map((step) => (
              <div 
                key={step.id} 
                className={`progress-step ${
                  step.id === currentStep ? 'active' : 
                  step.id < currentStep ? 'completed' : ''
                }`}
              >
                <div className="step-icon">{step.icon}</div>
                <div className="step-title">{step.title}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="wizard-content">
          {renderStepContent()}
        </div>

        <div className="wizard-footer">
          <div className="footer-left">
            {currentStep === 1 && (
              <button onClick={handleSkip} className="skip-button">
                Skip Setup
              </button>
            )}
          </div>
          
          <div className="footer-right">
            {currentStep > 1 && currentStep < steps.length && (
              <button onClick={handlePrevious} className="prev-button">
                Previous
              </button>
            )}
            
            {currentStep < steps.length - 1 && (
              <button 
                onClick={handleNext} 
                className="next-button"
                disabled={currentStep === 2 && (!apiTestResult || !apiTestResult.success)}
              >
                Next
              </button>
            )}
            
            {currentStep === steps.length - 1 && (
              <button 
                onClick={handleComplete} 
                className="complete-button"
                disabled={isLoading}
              >
                {isLoading ? 'Saving...' : 'Complete Setup'}
              </button>
            )}
            
            {currentStep === steps.length && (
              <button onClick={onComplete} className="finish-button">
                Start Trading
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SetupWizardDesktop;