import { useState } from 'react'
import { ShoppingCart, TrendingUp, TrendingDown, AlertCircle, CheckCircle } from 'lucide-react'

const TradingInterface = ({ mode = 'demo', marketData = [] }) => {
  const [orderType, setOrderType] = useState('market')
  const [side, setSide] = useState('buy')
  const [amount, setAmount] = useState('')
  const [price, setPrice] = useState('')
  const [symbol, setSymbol] = useState('BTC/USD')
  const [balance] = useState({
    USD: mode === 'demo' ? 100000 : 10000,
    BTC: mode === 'demo' ? 2.5 : 0.5,
    ETH: mode === 'demo' ? 10.3 : 2.3
  })
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

  const handleSubmitOrder = (e) => {
    e.preventDefault()
    if (!amount || (orderType === 'limit' && !price)) {
      alert('Please fill in all required fields')
      return
    }

    const currentPrice = marketData.find(item => item.symbol === symbol.replace('/', ''))?.price || currentPrices[symbol]
    
    const newOrder = {
      id: orders.length + 1,
      symbol,
      side,
      amount: parseFloat(amount),
      price: orderType === 'market' ? currentPrice : parseFloat(price),
      status: 'pending',
      time: new Date().toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit' 
      }),
      mode: mode
    }

    setOrders([newOrder, ...orders])
    setAmount('')
    setPrice('')
    
    // Show demo mode confirmation
    if (mode === 'demo') {
      alert(`Demo Order Placed: ${side.toUpperCase()} ${amount} ${symbol} ${orderType === 'market' ? 'at market price' : `at $${price}`}`)
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

          {/* Amount */}
          <div>
            <label className="block text-sm font-medium mb-2">Amount</label>
            <input
              type="number"
              step="0.00001"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="Enter amount"
              className="input-field"
              required
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
            </div>
          )}

          <button
            type="submit"
            className={`w-full py-3 px-4 rounded-lg font-medium transition-colors ${
              side === 'buy'
                ? 'bg-success-600 hover:bg-success-700 text-white'
                : 'bg-danger-600 hover:bg-danger-700 text-white'
            }`}
          >
            {side === 'buy' ? 'Place Buy Order' : 'Place Sell Order'}
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