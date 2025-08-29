import React, { useState } from 'react'
import { Info, X, ExternalLink, Settings } from 'lucide-react'

const DemoBanner = ({ onDismiss, onSwitchToLive }) => {
  const [isVisible, setIsVisible] = useState(true)

  const handleDismiss = () => {
    setIsVisible(false)
    onDismiss?.()
    localStorage.setItem('demoBannerDismissed', 'true')
  }

  const handleSwitchToLive = () => {
    onSwitchToLive?.()
  }

  if (!isVisible) return null

  return (
    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4 mb-6">
      <div className="flex items-start justify-between">
        <div className="flex items-start space-x-3">
          <div className="flex-shrink-0">
            <Info className="h-5 w-5 text-blue-600 mt-0.5" />
          </div>
          <div className="flex-1">
            <h3 className="text-sm font-semibold text-blue-900 mb-1">
              🎯 Demo Mode Active - Explore Risk-Free!
            </h3>
            <p className="text-sm text-blue-800 mb-3">
              You're viewing <strong>simulated trading data</strong> with realistic market movements. 
              Perfect for testing strategies and learning the platform without any financial risk.
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div className="bg-white bg-opacity-60 rounded-lg p-3">
                <div className="text-xs font-medium text-blue-900 mb-1">📊 Real-Time Charts</div>
                <div className="text-xs text-blue-700">Live price movements with realistic volatility</div>
              </div>
              <div className="bg-white bg-opacity-60 rounded-lg p-3">
                <div className="text-xs font-medium text-blue-900 mb-1">💼 Portfolio Tracking</div>
                <div className="text-xs text-blue-700">Monitor positions and P&L in real-time</div>
              </div>
              <div className="bg-white bg-opacity-60 rounded-lg p-3">
                <div className="text-xs font-medium text-blue-900 mb-1">🤖 Bot Strategies</div>
                <div className="text-xs text-blue-700">Test automated trading algorithms safely</div>
              </div>
            </div>
            
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-2 sm:space-y-0">
              <div className="flex items-center space-x-4">
                <button
                  onClick={handleSwitchToLive}
                  className="inline-flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
                >
                  <ExternalLink className="h-4 w-4" />
                  <span>Switch to Live Trading</span>
                </button>
                <button className="inline-flex items-center space-x-2 bg-white bg-opacity-80 text-blue-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-opacity-100 transition-colors border border-blue-200">
                  <Settings className="h-4 w-4" />
                  <span>Configure API</span>
                </button>
              </div>
              
              <div className="text-xs text-blue-600">
                💡 <strong>Tip:</strong> All data updates in real-time just like live trading!
              </div>
            </div>
          </div>
        </div>
        
        <button
          onClick={handleDismiss}
          className="flex-shrink-0 p-1 text-blue-400 hover:text-blue-600 transition-colors"
          title="Dismiss banner"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  )
}

export default DemoBanner