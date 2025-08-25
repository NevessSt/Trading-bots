import React, { useState, useEffect } from 'react';
import { XMarkIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

const RiskDisclaimer = ({ isOpen, onAccept, onDecline }) => {
  const [hasScrolled, setHasScrolled] = useState(false);
  const [acceptChecked, setAcceptChecked] = useState(false);
  const [understandChecked, setUnderstandChecked] = useState(false);

  const handleScroll = (e) => {
    const { scrollTop, scrollHeight, clientHeight } = e.target;
    if (scrollTop + clientHeight >= scrollHeight - 10) {
      setHasScrolled(true);
    }
  };

  const canProceed = hasScrolled && acceptChecked && understandChecked;

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-200 dark:border-slate-700">
          <div className="flex items-center space-x-3">
            <ExclamationTriangleIcon className="h-8 w-8 text-red-500" />
            <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
              ⚠️ IMPORTANT RISK DISCLAIMER
            </h2>
          </div>
          <button
            onClick={onDecline}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        {/* Content */}
        <div 
          className="flex-1 overflow-y-auto p-6 space-y-6"
          onScroll={handleScroll}
        >
          {/* Main Warning */}
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-red-800 dark:text-red-200 mb-2">
              🚨 CRYPTOCURRENCY TRADING INVOLVES SUBSTANTIAL RISK
            </h3>
            <p className="text-red-700 dark:text-red-300">
              This software is for <strong>educational and research purposes only</strong>. 
              Cryptocurrency trading involves substantial risk of loss and is not suitable for all investors.
            </p>
          </div>

          {/* Key Risks */}
          <div className="space-y-4">
            <h3 className="text-xl font-semibold text-slate-900 dark:text-slate-100">
              Key Risks You Must Understand:
            </h3>
            
            <div className="grid md:grid-cols-2 gap-4">
              <div className="bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg p-4">
                <h4 className="font-semibold text-orange-800 dark:text-orange-200 mb-2">
                  💸 Financial Loss Risk
                </h4>
                <ul className="text-sm text-orange-700 dark:text-orange-300 space-y-1">
                  <li>• You can lose your entire investment</li>
                  <li>• Past performance doesn't guarantee future results</li>
                  <li>• Automated trading can amplify losses</li>
                  <li>• Market volatility can cause rapid losses</li>
                </ul>
              </div>

              <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
                <h4 className="font-semibold text-yellow-800 dark:text-yellow-200 mb-2">
                  ⚡ Technical Risks
                </h4>
                <ul className="text-sm text-yellow-700 dark:text-yellow-300 space-y-1">
                  <li>• Software bugs or glitches</li>
                  <li>• Internet connectivity issues</li>
                  <li>• Exchange API failures</li>
                  <li>• System downtime during critical moments</li>
                </ul>
              </div>

              <div className="bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg p-4">
                <h4 className="font-semibold text-purple-800 dark:text-purple-200 mb-2">
                  📊 Market Risks
                </h4>
                <ul className="text-sm text-purple-700 dark:text-purple-300 space-y-1">
                  <li>• Extreme price volatility</li>
                  <li>• Low liquidity in some markets</li>
                  <li>• Regulatory changes</li>
                  <li>• Market manipulation</li>
                </ul>
              </div>

              <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                <h4 className="font-semibold text-blue-800 dark:text-blue-200 mb-2">
                  🔒 Security Risks
                </h4>
                <ul className="text-sm text-blue-700 dark:text-blue-300 space-y-1">
                  <li>• API key compromise</li>
                  <li>• Unauthorized access</li>
                  <li>• Exchange security breaches</li>
                  <li>• Phishing and social engineering</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Important Disclaimers */}
          <div className="bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-3">
              📋 Important Disclaimers:
            </h3>
            <div className="space-y-2 text-sm text-slate-700 dark:text-slate-300">
              <p><strong>No Financial Advice:</strong> This software does not provide financial, investment, or trading advice.</p>
              <p><strong>No Guarantees:</strong> We make no guarantees about profitability or performance.</p>
              <p><strong>Your Responsibility:</strong> You are solely responsible for your trading decisions and outcomes.</p>
              <p><strong>Regulatory Compliance:</strong> Ensure compliance with your local laws and regulations.</p>
              <p><strong>Tax Implications:</strong> Trading may have tax consequences in your jurisdiction.</p>
            </div>
          </div>

          {/* Best Practices */}
          <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-green-800 dark:text-green-200 mb-3">
              ✅ Recommended Best Practices:
            </h3>
            <div className="grid md:grid-cols-2 gap-3 text-sm text-green-700 dark:text-green-300">
              <div>
                <p><strong>Start Small:</strong> Begin with small amounts you can afford to lose</p>
                <p><strong>Paper Trading:</strong> Test strategies with virtual money first</p>
                <p><strong>Risk Management:</strong> Set strict stop-losses and position limits</p>
              </div>
              <div>
                <p><strong>Education:</strong> Learn about trading and risk management</p>
                <p><strong>Diversification:</strong> Don't put all funds in one strategy</p>
                <p><strong>Professional Advice:</strong> Consider consulting a financial advisor</p>
              </div>
            </div>
          </div>

          {/* Legal Notice */}
          <div className="bg-slate-100 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-2">
              ⚖️ Legal Notice:
            </h3>
            <p className="text-sm text-slate-700 dark:text-slate-300">
              By using this software, you acknowledge that the authors, contributors, and service providers 
              are not liable for any financial losses, damages, or consequences resulting from your use of this software. 
              You use this software entirely at your own risk and discretion.
            </p>
          </div>

          {/* Scroll Indicator */}
          {!hasScrolled && (
            <div className="text-center text-sm text-slate-500 dark:text-slate-400 animate-pulse">
              ↓ Please scroll down to read the complete disclaimer ↓
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-slate-200 dark:border-slate-700 p-6 space-y-4">
          {/* Checkboxes */}
          <div className="space-y-3">
            <label className="flex items-start space-x-3 cursor-pointer">
              <input
                type="checkbox"
                checked={acceptChecked}
                onChange={(e) => setAcceptChecked(e.target.checked)}
                className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-slate-300 rounded"
                disabled={!hasScrolled}
              />
              <span className={`text-sm ${!hasScrolled ? 'text-slate-400' : 'text-slate-700 dark:text-slate-300'}`}>
                I have read and understand all the risks associated with cryptocurrency trading and automated trading systems.
              </span>
            </label>

            <label className="flex items-start space-x-3 cursor-pointer">
              <input
                type="checkbox"
                checked={understandChecked}
                onChange={(e) => setUnderstandChecked(e.target.checked)}
                className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-slate-300 rounded"
                disabled={!hasScrolled}
              />
              <span className={`text-sm ${!hasScrolled ? 'text-slate-400' : 'text-slate-700 dark:text-slate-300'}`}>
                I understand that this software is for educational purposes only and I am solely responsible for my trading decisions and any resulting losses.
              </span>
            </label>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end space-x-3">
            <button
              onClick={onDecline}
              className="px-6 py-2 border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
            >
              I Do Not Accept
            </button>
            <button
              onClick={onAccept}
              disabled={!canProceed}
              className={`px-6 py-2 rounded-lg font-medium transition-colors ${
                canProceed
                  ? 'bg-blue-600 hover:bg-blue-700 text-white'
                  : 'bg-slate-300 dark:bg-slate-600 text-slate-500 dark:text-slate-400 cursor-not-allowed'
              }`}
            >
              I Accept the Risks and Continue
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RiskDisclaimer;