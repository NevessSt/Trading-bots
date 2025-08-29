import React, { useState, useEffect } from 'react';
import { AlertTriangle, Info } from 'lucide-react';
import demoDataService from '../services/demoDataService';

const DemoModeToggle = ({ onModeChange }) => {
  const [isDemoMode, setIsDemoMode] = useState(false);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [pendingMode, setPendingMode] = useState(false);

  useEffect(() => {
    // Initialize demo mode state
    const demoMode = demoDataService.isDemoMode();
    setIsDemoMode(demoMode);
  }, []);

  const handleToggleChange = (event) => {
    const newMode = event.target.checked;
    setPendingMode(newMode);
    setShowConfirmDialog(true);
  };

  const handleConfirmModeChange = () => {
    setIsDemoMode(pendingMode);
    demoDataService.setDemoMode(pendingMode);
    
    if (onModeChange) {
      onModeChange(pendingMode);
    }
    
    setShowConfirmDialog(false);
    
    // Reload the page to refresh all data
    window.location.reload();
  };

  const handleCancelModeChange = () => {
    setShowConfirmDialog(false);
    setPendingMode(isDemoMode);
  };

  const resetDemoData = () => {
    if (isDemoMode) {
      demoDataService.resetDemoData();
      window.location.reload();
    }
  };

  return (
    <>
      <div className="flex items-center space-x-4">
        {/* Demo Mode Indicator */}
        {isDemoMode && (
          <span className="px-2 py-1 text-xs font-bold text-orange-800 bg-orange-200 rounded-full animate-pulse">
            DEMO MODE
          </span>
        )}
        
        {/* Mode Toggle Switch */}
        <div className="flex items-center space-x-3">
          <span className="text-sm font-medium text-gray-700">
            {isDemoMode ? 'Demo Mode' : 'Live Mode'}
          </span>
          <button
            onClick={handleToggleChange}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              isDemoMode ? 'bg-orange-500' : 'bg-gray-200'
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                isDemoMode ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>
        
        {/* Reset Demo Data Button */}
        {isDemoMode && (
          <button
            onClick={resetDemoData}
            className="px-3 py-1 text-sm text-orange-700 border border-orange-300 rounded hover:bg-orange-50 transition-colors"
          >
            Reset Demo Data
          </button>
        )}
      </div>

      {/* Confirmation Dialog */}
      {showConfirmDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center space-x-2 mb-4">
              {pendingMode ? (
                <>
                  <AlertTriangle className="h-6 w-6 text-orange-500" />
                  <h3 className="text-lg font-semibold">Switch to Demo Mode?</h3>
                </>
              ) : (
                <>
                  <Info className="h-6 w-6 text-blue-500" />
                  <h3 className="text-lg font-semibold">Switch to Live Mode?</h3>
                </>
              )}
            </div>
            
            <div className="space-y-4 mb-6">
              {pendingMode ? (
                <div>
                  <p className="text-gray-700 mb-3">
                    You are about to switch to <strong>Demo Mode</strong>. In demo mode:
                  </p>
                  <ul className="space-y-2 text-sm text-gray-600 ml-4">
                    <li>• All trading data will be simulated with fake data</li>
                    <li>• You'll start with a virtual $100,000 portfolio</li>
                    <li>• No real trades will be executed</li>
                    <li>• Perfect for testing strategies without financial risk</li>
                  </ul>
                  <div className="mt-4 p-3 bg-orange-50 border border-orange-200 rounded-lg">
                    <p className="text-sm text-orange-800">
                      <strong>Note:</strong> This is ideal for buyers who want to test the platform before connecting their real trading accounts.
                    </p>
                  </div>
                </div>
              ) : (
                <div>
                  <p className="text-gray-700 mb-3">
                    You are about to switch to <strong>Live Mode</strong>. In live mode:
                  </p>
                  <ul className="space-y-2 text-sm text-gray-600 ml-4">
                    <li>• Real trading data from your connected exchange accounts</li>
                    <li>• Actual trades can be executed with real money</li>
                    <li>• Requires valid API keys and exchange connections</li>
                    <li>• All profits and losses will be real</li>
                  </ul>
                  <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                    <p className="text-sm text-red-800">
                      <strong>Warning:</strong> Make sure you have properly configured your API keys and risk management settings before switching to live mode.
                    </p>
                  </div>
                </div>
              )}
            </div>
            
            <div className="flex space-x-3">
              <button
                onClick={handleCancelModeChange}
                className="flex-1 px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmModeChange}
                className={`flex-1 px-4 py-2 text-white rounded-lg transition-colors ${
                  pendingMode ? 'bg-orange-600 hover:bg-orange-700' : 'bg-blue-600 hover:bg-blue-700'
                }`}
              >
                {pendingMode ? 'Switch to Demo' : 'Switch to Live'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default DemoModeToggle