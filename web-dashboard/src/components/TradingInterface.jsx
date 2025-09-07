import { useState } from 'react'
import { ShoppingCart, TrendingUp, TrendingDown, AlertCircle, CheckCircle, Shield, Target, Percent, AlertTriangle } from 'lucide-react'

const TradingInterface = ({ mode = 'demo', marketData = [] }) => {
  const [orderType, setOrderType] = useState('market')
  const [side, setSide] = useState('buy')
  const [amount, setAmount] = useState('')
  const [price, setPrice] = useState('')
  const [symbol, setSymbol] = useState('BTC/USD')
  
  // Enhanced Risk Management States
  const [stopLoss, setStopLoss] = useState('')
  const [takeProfit, setTakeProfit] = useState('')
  const [positionSizePercent, setPositionSizePercent] = useState('2') // Default 2% risk
  const [riskRewardRatio, setRiskRewardRatio] = useState('2') // Default 1:2 risk/reward
  const [maxDailyLoss, setMaxDailyLoss] = useState('5') // Default 5% max daily loss
  const [enableRiskManagement, setEnableRiskManagement] = useState(true)
  
  const [balance] = useState({
    USD: mode === 'demo' ? 100000 : 10000,
    BTC: mode === 'demo' ? 2.5 : 0.5,
    ETH: mode === 'demo' ? 10.3 : 2.3
  })
  
  // Track daily P&L for risk management
  const [dailyPnL] = useState(-250) // Example daily loss
  const [orders, setOrders] = useState([
    { id: 1, symbol: 'BTC/USD', side: 'buy', amount: 0.5, price: 43200, status: 'filled', time: '10:30 AM' },
    { id: 2, symbol: 'ETH/USD', side: 'sell', amount: 2.0, price: 2100, status: 'pending', time: '10:25 AM' },
    { id: 3, symbol: 'ADA/USD', side: 'buy', amount: 1000, price: 1.25, status: 'cancelled', time: '10:20 AM' }
  ])

  const symbols = ['BTC/USD', 'ETH/USD', 'ADA/USD', 'DOT/USD', 'LINK/USD']
  const currentPrices = {
    'BTC/USD': 43250.75,
    'ETH/USD': 2087.50,
    'ADA/USD': 1.266,
    'DOT/USD': 7.85,
    'LINK/USD': 14.23
  }

  // Risk Management Calculations
  const calculatePositionSize = () => {
    if (!enableRiskManagement || !stopLoss || !amount) return parseFloat(amount) || 0
    
    const currentPrice = currentPrices[symbol]
    const stopLossPrice = parseFloat(stopLoss)
    const riskAmount = balance.USD * (parseFloat(positionSizePercent) / 100)
    const priceRisk = Math.abs(currentPrice - stopLossPrice)
    
    if (priceRisk === 0) return parseFloat(amount) || 0
    
    return riskAmount / priceRisk
  }

  const calculateRiskReward = () => {
    if (!stopLoss || !takeProfit) return null
    
    const currentPrice = currentPrices[symbol]
    const stopLossPrice = parseFloat(stopLoss)
    const takeProfitPrice = parseFloat(takeProfit)
    
    const risk = Math.abs(currentPrice - stopLossPrice)
    const reward = Math.abs(takeProfitPrice - currentPrice)
    
    return risk > 0 ? (reward / risk).toFixed(2) : null
  }

  const validateRiskManagement = () => {
    const errors = []
    
    // Check daily loss limit
    const dailyLossPercent = (Math.abs(dailyPnL) / balance.USD) * 100
    if (dailyLossPercent >= parseFloat(maxDailyLoss)) {
      errors.push(`Daily loss limit reached (${dailyLossPercent.toFixed(1)}% of ${maxDailyLoss}%)`)
    }
    
    // Check position size
    const orderValue = parseFloat(amount) * currentPrices[symbol]
    const positionPercent = (orderValue / balance.USD) * 100
    if (positionPercent > 10) {
      errors.push(`Position size too large (${positionPercent.toFixed(1)}% of portfolio)`)
    }
    
    // Check stop-loss placement
    if (enableRiskManagement && stopLoss) {
      const currentPrice = currentPrices[symbol]
      const stopLossPrice = parseFloat(stopLoss)
      const stopLossPercent = Math.abs((currentPrice - stopLossPrice) / currentPrice) * 100
      
      if (side === 'buy' && stopLossPrice >= currentPrice) {
        errors.push('Stop-loss must be below current price for buy orders')
      }
      if (side === 'sell' && stopLossPrice <= currentPrice) {
        errors.push('Stop-loss must be above current price for sell orders')
      }
      if (stopLossPercent > 10) {
        errors.push(`Stop-loss too far from current price (${stopLossPercent.toFixed(1)}%)`)
      }
    }
    
    // Check take-profit placement
    if (enableRiskManagement && takeProfit) {
      const currentPrice = currentPrices[symbol]
      const takeProfitPrice = parseFloat(takeProfit)
      
      if (side === 'buy' && takeProfitPrice <= currentPrice) {
        errors.push('Take-profit must be above current price for buy orders')
      }
      if (side === 'sell' && takeProfitPrice >= currentPrice) {
        errors.push('Take-profit must be below current price for sell orders')
      }
    }
    
    return errors
  }

  const handleSubmitOrder = (e) => {
    e.preventDefault()
    
    // Basic validation
    if (!amount || (orderType === 'limit' && !price)) {
      alert('Please fill in all required fields')
      return
    }

    // Risk management validation
    if (enableRiskManagement) {
      const riskErrors = validateRiskManagement()
      if (riskErrors.length > 0) {
        alert('Risk Management Errors:\n' + riskErrors.join('\n'))
        return
      }
      
      // Validate required risk management fields
      if (!stopLoss) {
        alert('Stop-loss is required when risk management is enabled')
        return
      }
    }

    const currentPrice = marketData.find(item => item.symbol === symbol.replace('/', ''))?.price || currentPrices[symbol]
    const finalAmount = enableRiskManagement ? calculatePositionSize() : parseFloat(amount)
    
    const newOrder = {
      id: orders.length + 1,
      symbol,
      side,
      amount: finalAmount,
      price: orderType === 'market' ? currentPrice : parseFloat(price),
      status: 'pending',
      time: new Date().toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit' 
      }),
      mode: mode,
      // Enhanced risk management data
      stopLoss: enableRiskManagement ? parseFloat(stopLoss) : null,
      takeProfit: enableRiskManagement ? parseFloat(takeProfit) : null,
      riskReward: calculateRiskReward(),
      positionSizePercent: parseFloat(positionSizePercent)
    }

    setOrders([newOrder, ...orders])
    
    // Reset form but keep risk management settings
    setAmount('')
    setPrice('')
    
    // Enhanced demo mode confirmation
    if (mode === 'demo') {
      const riskInfo = enableRiskManagement ? 
        `\nStop-Loss: $${stopLoss}\nTake-Profit: $${takeProfit || 'Not set'}\nRisk/Reward: ${calculateRiskReward() || 'N/A'}` : ''
      alert(`Demo Order Placed: ${side.toUpperCase()} ${finalAmount.toFixed(6)} ${symbol} ${orderType === 'market' ? 'at market price' : `at $${price}`}${riskInfo}`)
    }
    
    // Simulate order execution
    setTimeout(() => {
      setOrders(prev => prev.map(order => 
        order.id === newOrder.id 
          ? { ...order, status: 'filled' }
          : order
      ))
    }, mode === 'demo' ? 1000 : 2000)
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'filled': return 'text-success-600 bg-success-50'
      case 'pending': return 'text-yellow-600 bg-yellow-50'
      case 'cancelled': return 'text-danger-600 bg-danger-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'filled': return <CheckCircle className="h-3 w-3" />
      case 'pending': return <AlertCircle className="h-3 w-3" />
      case 'cancelled': return <AlertCircle className="h-3 w-3" />
      default: return null
    }
  }

  return (
    <div className="space-y-6">
      {/* Demo Mode Indicator */}
      {mode === 'demo' && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-blue-500 rounded-full animate-pulse"></div>
              <span className="text-blue-800 font-medium">Demo Trading Mode</span>
            </div>
            <span className="text-blue-600 text-sm">All trades are simulated with virtual funds</span>
          </div>
        </div>
      )}
      
      {/* Order Form */}
      <div className="card">
        <div className="flex items-center space-x-2 mb-4">
          <ShoppingCart className="h-5 w-5 text-primary-600" />
          <h3 className="text-lg font-semibold">Place Order</h3>
        </div>
        
        <form onSubmit={handleSubmitOrder} className="space-y-4">
          {/* Symbol Selection */}
          <div>
            <label className="block text-sm font-medium mb-2">Trading Pair</label>
            <select 
              value={symbol} 
              onChange={(e) => setSymbol(e.target.value)}
              className="input-field"
            >
              {symbols.map(s => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
            <div className="text-sm text-gray-600 mt-1">
              Current Price: ${currentPrices[symbol]?.toLocaleString()}
            </div>
          </div>

          {/* Order Type */}
          <div>
            <label className="block text-sm font-medium mb-2">Order Type</label>
            <div className="flex space-x-2">
              <button
                type="button"
                onClick={() => setOrderType('market')}
                className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors ${
                  orderType === 'market'
                    ? 'bg-primary-100 text-primary-700 border border-primary-200'
                    : 'bg-gray-100 text-gray-700 border border-gray-200 hover:bg-gray-200'
                }`}
              >
                Market
              </button>
              <button
                type="button"
                onClick={() => setOrderType('limit')}
                className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors ${
                  orderType === 'limit'
                    ? 'bg-primary-100 text-primary-700 border border-primary-200'
                    : 'bg-gray-100 text-gray-700 border border-gray-200 hover:bg-gray-200'
                }`}
              >
                Limit
              </button>
            </div>
          </div>

          {/* Buy/Sell Toggle */}
          <div>
            <label className="block text-sm font-medium mb-2">Side</label>
            <div className="flex space-x-2">
              <button
                type="button"
                onClick={() => setSide('buy')}
                className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors flex items-center justify-center space-x-2 ${
                  side === 'buy'
                    ? 'bg-success-100 text-success-700 border border-success-200'
                    : 'bg-gray-100 text-gray-700 border border-gray-200 hover:bg-gray-200'
                }`}
              >
                <TrendingUp className="h-4 w-4" />
                <span>Buy</span>
              </button>
              <button
                type="button"
                onClick={() => setSide('sell')}
                className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors flex items-center justify-center space-x-2 ${
                  side === 'sell'
                    ? 'bg-danger-100 text-danger-700 border border-danger-200'
                    : 'bg-gray-100 text-gray-700 border border-gray-200 hover:bg-gray-200'
                }`}
              >
                <TrendingDown className="h-4 w-4" />
                <span>Sell</span>
              </button>
            </div>
          </div>

          {/* Risk Management Toggle */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                <Shield className="h-5 w-5 text-blue-600" />
                <span className="font-medium text-blue-900">Risk Management</span>
              </div>
              <button
                type="button"
                onClick={() => setEnableRiskManagement(!enableRiskManagement)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  enableRiskManagement ? 'bg-blue-600' : 'bg-gray-200'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    enableRiskManagement ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
            
            {enableRiskManagement && (
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-blue-700 mb-1">Risk per Trade (%)</label>
                    <input
                      type="number"
                      step="0.1"
                      min="0.1"
                      max="10"
                      value={positionSizePercent}
                      onChange={(e) => setPositionSizePercent(e.target.value)}
                      className="w-full px-2 py-1 text-sm border border-blue-200 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-blue-700 mb-1">Max Daily Loss (%)</label>
                    <input
                      type="number"
                      step="0.1"
                      min="1"
                      max="20"
                      value={maxDailyLoss}
                      onChange={(e) => setMaxDailyLoss(e.target.value)}
                      className="w-full px-2 py-1 text-sm border border-blue-200 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                </div>
                
                <div className="text-xs text-blue-600">
                  Daily P&L: <span className={dailyPnL >= 0 ? 'text-green-600' : 'text-red-600'}>
                    ${dailyPnL.toLocaleString()} ({((dailyPnL / balance.USD) * 100).toFixed(1)}%)
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Amount */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Amount
              {enableRiskManagement && (
                <span className="text-xs text-gray-500 ml-2">
                  (Auto-calculated: {calculatePositionSize().toFixed(6)})
                </span>
              )}
            </label>
            <input
              type="number"
              step="0.00001"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder={enableRiskManagement ? "Will be auto-calculated" : "Enter amount"}
              className="input-field"
              required={!enableRiskManagement}
            />
          </div>

          {/* Price (for limit orders) */}
          {orderType === 'limit' && (
            <div>
              <label className="block text-sm font-medium mb-2">Price</label>
              <input
                type="number"
                step="0.01"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                placeholder="Enter price"
                className="input-field"
                required
              />
            </div>
          )}

          {/* Stop Loss & Take Profit */}
          {enableRiskManagement && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-center space-x-2 mb-3">
                <TrendingDown className="h-4 w-4 text-yellow-600" />
                <span className="font-medium text-yellow-900">Stop Loss & Take Profit</span>
              </div>
              
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-yellow-700 mb-1">Stop Loss (%)</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0.1"
                    max="50"
                    value={stopLoss}
                    onChange={(e) => setStopLoss(e.target.value)}
                    placeholder="e.g., 2.0"
                    className="w-full px-2 py-1 text-sm border border-yellow-200 rounded focus:ring-1 focus:ring-yellow-500 focus:border-yellow-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-yellow-700 mb-1">Take Profit (%)</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0.1"
                    max="100"
                    value={takeProfit}
                    onChange={(e) => setTakeProfit(e.target.value)}
                    placeholder="e.g., 4.0"
                    className="w-full px-2 py-1 text-sm border border-yellow-200 rounded focus:ring-1 focus:ring-yellow-500 focus:border-yellow-500"
                  />
                </div>
              </div>
              
              <div className="mt-2 text-xs text-yellow-600">
                Risk/Reward Ratio: {calculateRiskReward()}
                {parseFloat(calculateRiskReward()) < 1.5 && (
                  <span className="text-red-500 ml-2">⚠️ Consider higher reward ratio</span>
                )}
              </div>
            </div>
          )}

          {/* Order Summary */}
          {amount && (
            <div className="bg-gray-50 p-3 rounded-lg">
              <div className="text-sm space-y-1">
                <div className="flex justify-between">
                  <span className="text-gray-600">Order Value:</span>
                  <span className="font-medium">
                    ${(
                      parseFloat(amount) * 
                      (orderType === 'market' ? currentPrices[symbol] : parseFloat(price) || 0)
                    ).toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Estimated Fee:</span>
                  <span className="font-medium">$2.50</span>
                </div>
              </div>
              
              {/* Risk Validation Warnings */}
              {enableRiskManagement && (
                <div className="mt-3 space-y-1">
                  {validateRiskManagement().map((warning, index) => (
                    <div key={index} className="flex items-center space-x-2 text-xs text-red-600 bg-red-50 border border-red-200 rounded p-2">
                      <AlertCircle className="h-3 w-3 flex-shrink-0" />
                      <span>{warning}</span>
                    </div>
                  ))}
                  {validateRiskManagement().length === 0 && (
                    <div className="flex items-center space-x-2 text-xs text-green-600 bg-green-50 border border-green-200 rounded p-2">
                      <CheckCircle className="h-3 w-3 flex-shrink-0" />
                      <span>Risk parameters validated ✓</span>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          <button
            type="submit"
            disabled={enableRiskManagement && validateRiskManagement().length > 0}
            className={`w-full py-3 px-4 rounded-lg font-medium transition-colors ${
              enableRiskManagement && validateRiskManagement().length > 0
                ? 'bg-gray-400 cursor-not-allowed text-white'
                : side === 'buy'
                ? 'bg-success-600 hover:bg-success-700 text-white'
                : 'bg-danger-600 hover:bg-danger-700 text-white'
            }`}
          >
            {enableRiskManagement && validateRiskManagement().length > 0
              ? 'Fix Risk Issues to Continue'
              : side === 'buy' ? 'Place Buy Order' : 'Place Sell Order'
            }
          </button>
        </form>
      </div>

      {/* Recent Orders */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Recent Orders</h3>
        <div className="space-y-3">
          {orders.slice(0, 5).map((order) => (
            <div key={order.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className={`p-2 rounded-full ${
                  order.side === 'buy' ? 'bg-success-100' : 'bg-danger-100'
                }`}>
                  {order.side === 'buy' ? (
                    <TrendingUp className={`h-4 w-4 text-success-600`} />
                  ) : (
                    <TrendingDown className={`h-4 w-4 text-danger-600`} />
                  )}
                </div>
                <div>
                  <div className="font-medium">{order.symbol}</div>
                  <div className="text-sm text-gray-600">
                    {order.side.toUpperCase()} {order.amount} @ ${order.price.toLocaleString()}
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div className={`inline-flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(order.status)}`}>
                  {getStatusIcon(order.status)}
                  <span className="capitalize">{order.status}</span>
                </div>
                <div className="text-sm text-gray-600 mt-1">{order.time}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default TradingInterface