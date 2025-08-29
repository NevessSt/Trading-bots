import { useState, useEffect } from 'react'
import { TrendingUp, TrendingDown, Activity, Eye } from 'lucide-react'

const MarketData = ({ data = null }) => {
  const defaultMarketData = [
    {
      symbol: 'BTC/USD',
      name: 'Bitcoin',
      price: 43250.75,
      change: 2.34,
      changePercent: 5.73,
      volume: '2.4B',
      marketCap: '847B'
    },
    {
      symbol: 'ETH/USD',
      name: 'Ethereum',
      price: 2087.50,
      change: -15.20,
      changePercent: -0.72,
      volume: '1.8B',
      marketCap: '251B'
    },
    {
      symbol: 'ADA/USD',
      name: 'Cardano',
      price: 1.266,
      change: 0.089,
      changePercent: 7.56,
      volume: '456M',
      marketCap: '42.1B'
    },
    {
      symbol: 'DOT/USD',
      name: 'Polkadot',
      price: 7.85,
      change: -0.23,
      changePercent: -2.85,
      volume: '234M',
      marketCap: '9.8B'
    },
    {
      symbol: 'LINK/USD',
      name: 'Chainlink',
      price: 14.23,
      change: 0.67,
      changePercent: 4.94,
      volume: '189M',
      marketCap: '8.4B'
    },
    {
      symbol: 'SOL/USD',
      name: 'Solana',
      price: 98.45,
      change: 3.21,
      changePercent: 3.37,
      volume: '567M',
      marketCap: '43.2B'
    }
  ]
  
  const [marketData, setMarketData] = useState(data || defaultMarketData)
  
  // Update market data when prop changes
  useEffect(() => {
    if (data) {
      setMarketData(data)
    }
  }, [data])

  const [watchlist, setWatchlist] = useState(['BTC/USD', 'ETH/USD', 'ADA/USD'])
  const [selectedTimeframe, setSelectedTimeframe] = useState('24h')

  // Simulate real-time price updates
  useEffect(() => {
    const interval = setInterval(() => {
      setMarketData(prev => prev.map(coin => ({
        ...coin,
        price: coin.price + (Math.random() - 0.5) * coin.price * 0.01,
        change: coin.change + (Math.random() - 0.5) * 2,
        changePercent: coin.changePercent + (Math.random() - 0.5) * 1
      })))
    }, 3000)

    return () => clearInterval(interval)
  }, [])

  const toggleWatchlist = (symbol) => {
    setWatchlist(prev => 
      prev.includes(symbol) 
        ? prev.filter(s => s !== symbol)
        : [...prev, symbol]
    )
  }

  const formatPrice = (price) => {
    if (price < 1) {
      return price.toFixed(4)
    } else if (price < 100) {
      return price.toFixed(2)
    } else {
      return price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    }
  }

  const marketSummary = {
    totalMarketCap: marketData.reduce((sum, coin) => {
      const cap = parseFloat(coin.marketCap.replace(/[^0-9.]/g, ''))
      const multiplier = coin.marketCap.includes('B') ? 1000000000 : 1000000
      return sum + (cap * multiplier)
    }, 0),
    avgChange: marketData.reduce((sum, coin) => sum + coin.changePercent, 0) / marketData.length,
    gainers: marketData.filter(coin => coin.changePercent > 0).length,
    losers: marketData.filter(coin => coin.changePercent < 0).length
  }

  return (
    <div className="space-y-6">
      {/* Market Summary */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Market Overview</h3>
          <Activity className="h-5 w-5 text-primary-600" />
        </div>
        
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="text-sm text-gray-600">Market Cap</div>
            <div className="text-lg font-bold">
              ${(marketSummary.totalMarketCap / 1000000000000).toFixed(2)}T
            </div>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="text-sm text-gray-600">Avg Change</div>
            <div className={`text-lg font-bold ${
              marketSummary.avgChange >= 0 ? 'text-success-600' : 'text-danger-600'
            }`}>
              {marketSummary.avgChange >= 0 ? '+' : ''}{marketSummary.avgChange.toFixed(2)}%
            </div>
          </div>
        </div>
        
        <div className="flex justify-between mt-4 text-sm">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-success-500 rounded-full"></div>
            <span className="text-gray-600">Gainers: {marketSummary.gainers}</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-danger-500 rounded-full"></div>
            <span className="text-gray-600">Losers: {marketSummary.losers}</span>
          </div>
        </div>
      </div>

      {/* Watchlist */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Watchlist</h3>
          <div className="flex space-x-1">
            {['1h', '24h', '7d'].map(tf => (
              <button
                key={tf}
                onClick={() => setSelectedTimeframe(tf)}
                className={`px-2 py-1 text-xs font-medium rounded transition-colors ${
                  selectedTimeframe === tf
                    ? 'bg-primary-100 text-primary-700'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
              >
                {tf}
              </button>
            ))}
          </div>
        </div>
        
        <div className="space-y-2">
          {marketData.filter(coin => watchlist.includes(coin.symbol)).map((coin) => (
            <div key={coin.symbol} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
                  <span className="text-xs font-bold text-primary-700">
                    {coin.symbol.split('/')[0].slice(0, 2)}
                  </span>
                </div>
                <div>
                  <div className="font-medium">{coin.symbol}</div>
                  <div className="text-sm text-gray-600">{coin.name}</div>
                </div>
              </div>
              <div className="text-right">
                <div className="font-semibold">${formatPrice(coin.price)}</div>
                <div className={`text-sm flex items-center ${
                  coin.changePercent >= 0 ? 'text-success-600' : 'text-danger-600'
                }`}>
                  {coin.changePercent >= 0 ? (
                    <TrendingUp className="h-3 w-3 mr-1" />
                  ) : (
                    <TrendingDown className="h-3 w-3 mr-1" />
                  )}
                  {coin.changePercent >= 0 ? '+' : ''}{coin.changePercent.toFixed(2)}%
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Top Movers */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Top Movers</h3>
        
        <div className="space-y-3">
          {marketData
            .sort((a, b) => Math.abs(b.changePercent) - Math.abs(a.changePercent))
            .slice(0, 4)
            .map((coin) => (
            <div key={coin.symbol} className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <button
                  onClick={() => toggleWatchlist(coin.symbol)}
                  className={`p-1 rounded transition-colors ${
                    watchlist.includes(coin.symbol)
                      ? 'text-primary-600 hover:text-primary-700'
                      : 'text-gray-400 hover:text-gray-600'
                  }`}
                >
                  <Eye className="h-4 w-4" />
                </button>
                <div>
                  <div className="font-medium text-sm">{coin.symbol}</div>
                  <div className="text-xs text-gray-600">{coin.volume} vol</div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm font-semibold">${formatPrice(coin.price)}</div>
                <div className={`text-xs ${
                  coin.changePercent >= 0 ? 'text-success-600' : 'text-danger-600'
                }`}>
                  {coin.changePercent >= 0 ? '+' : ''}{coin.changePercent.toFixed(2)}%
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Market Status */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Market Status</h3>
        
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-gray-600">Trading Status</span>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-success-500 rounded-full animate-pulse"></div>
              <span className="text-sm font-medium text-success-600">Active</span>
            </div>
          </div>
          
          <div className="flex items-center justify-between">
            <span className="text-gray-600">Next Update</span>
            <span className="text-sm font-medium">2 minutes</span>
          </div>
          
          <div className="flex items-center justify-between">
            <span className="text-gray-600">Data Source</span>
            <span className="text-sm font-medium">Live Feed</span>
          </div>
          
          <div className="flex items-center justify-between">
            <span className="text-gray-600">Last Sync</span>
            <span className="text-sm font-medium">
              {new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default MarketData