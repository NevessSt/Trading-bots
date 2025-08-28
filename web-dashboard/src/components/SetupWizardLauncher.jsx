import React, { useState, useEffect } from 'react';
import { Settings, Zap, Shield, TrendingUp } from 'lucide-react';
import SetupWizard from './SetupWizard';

const SetupWizardLauncher = ({ onSetupComplete }) => {
  const [showWizard, setShowWizard] = useState(false);
  const [setupCompleted, setSetupCompleted] = useState(false);
  const [setupSkipped, setSetupSkipped] = useState(false);

  useEffect(() => {
    // Check if setup has been completed or skipped
    const completed = localStorage.getItem('setupCompleted') === 'true';
    const skipped = localStorage.getItem('setupSkipped') === 'true';
    
    setSetupCompleted(completed);
    setSetupSkipped(skipped);
    
    // Auto-show wizard if neither completed nor skipped
    if (!completed && !skipped) {
      setShowWizard(true);
    }
  }, []);

  const handleSetupComplete = (config) => {
    setSetupCompleted(true);
    setShowWizard(false);
    
    if (onSetupComplete) {
      onSetupComplete(config);
    }
  };

  const handleSetupSkip = () => {
    setSetupSkipped(true);
    setShowWizard(false);
  };

  const launchWizard = () => {
    setShowWizard(true);
  };

  const resetSetup = () => {
    localStorage.removeItem('setupCompleted');
    localStorage.removeItem('setupSkipped');
    localStorage.removeItem('tradingBotConfig');
    setSetupCompleted(false);
    setSetupSkipped(false);
    setShowWizard(true);
  };

  // If wizard is showing, render it full screen
  if (showWizard) {
    return (
      <SetupWizard 
        onComplete={handleSetupComplete}
        onSkip={handleSetupSkip}
      />
    );
  }

  // If setup is completed or skipped, show launcher options
  return (
    <div className="setup-wizard-launcher">
      {/* Setup Status Banner */}
      {!setupCompleted && setupSkipped && (
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Settings className="w-5 h-5 text-yellow-600" />
              <div>
                <h3 className="text-sm font-medium text-yellow-800">
                  Setup Not Completed
                </h3>
                <p className="text-sm text-yellow-700">
                  Complete the setup wizard to configure your trading bot safely.
                </p>
              </div>
            </div>
            <button
              onClick={launchWizard}
              className="bg-yellow-600 text-white px-4 py-2 rounded-md hover:bg-yellow-700 text-sm font-medium"
            >
              Complete Setup
            </button>
          </div>
        </div>
      )}

      {/* Setup Completed Banner */}
      {setupCompleted && (
        <div className="bg-green-50 border-l-4 border-green-400 p-4 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Shield className="w-5 h-5 text-green-600" />
              <div>
                <h3 className="text-sm font-medium text-green-800">
                  Setup Completed
                </h3>
                <p className="text-sm text-green-700">
                  Your trading bot is configured and ready to use.
                </p>
              </div>
            </div>
            <div className="flex space-x-2">
              <button
                onClick={launchWizard}
                className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 text-sm font-medium"
              >
                Review Settings
              </button>
              <button
                onClick={resetSetup}
                className="bg-gray-200 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-300 text-sm font-medium"
              >
                Reset Setup
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Quick Setup Card (for new users) */}
      {!setupCompleted && !setupSkipped && (
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <div className="text-center">
            <div className="mx-auto w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
              <Zap className="w-8 h-8 text-blue-600" />
            </div>
            <h2 className="text-xl font-bold text-gray-900 mb-2">
              Welcome to Trading Bot Pro
            </h2>
            <p className="text-gray-600 mb-6">
              Get started with automated trading in just 5 minutes. Our setup wizard will guide you through the process safely.
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="text-center">
                <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-2">
                  <Shield className="w-6 h-6 text-green-600" />
                </div>
                <h3 className="font-semibold text-gray-900">Secure</h3>
                <p className="text-sm text-gray-600">API-only access, no withdrawals</p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-2">
                  <TrendingUp className="w-6 h-6 text-blue-600" />
                </div>
                <h3 className="font-semibold text-gray-900">Profitable</h3>
                <p className="text-sm text-gray-600">Proven strategies with backtesting</p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-2">
                  <Settings className="w-6 h-6 text-purple-600" />
                </div>
                <h3 className="font-semibold text-gray-900">Customizable</h3>
                <p className="text-sm text-gray-600">Tailored to your risk tolerance</p>
              </div>
            </div>
            
            <div className="flex justify-center space-x-4">
              <button
                onClick={launchWizard}
                className="bg-blue-600 text-white px-6 py-3 rounded-md hover:bg-blue-700 font-medium flex items-center space-x-2"
              >
                <Zap className="w-4 h-4" />
                <span>Start Setup Wizard</span>
              </button>
              <button
                onClick={handleSetupSkip}
                className="bg-gray-200 text-gray-700 px-6 py-3 rounded-md hover:bg-gray-300 font-medium"
              >
                Skip for Now
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SetupWizardLauncher;