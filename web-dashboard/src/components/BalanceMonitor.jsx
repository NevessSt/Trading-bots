import { useState, useEffect } from 'react'
import { 
  Wallet, 
  TrendingUp, 
  TrendingDown, 
  RefreshCw, 
  Eye, 
  EyeOff,
  DollarSign,
  Bitcoin,
  Activity,
  PieChart,
  BarChart3,
  ArrowUpRight,
  ArrowDownRight
} from 'lucide-react'

const BalanceMonitor = ({ mode = 'demo' }) => {
  const [balances, setBalances] = useState([])
  const [totalBalance, setTotalBalance] = useState(0)
  const [dailyChange, setDailyChange] = useState(0)
  const [dailyChangePercent, setDailyChangePercent] = useState(0)
  const [loading, setLoading] = useState(true)
  const [hideBalances, setHideBalances] = useState(false)
  const [selectedTimeframe, setSelectedTimeframe] = useState('24h')
  const [portfolioHistory, setPortfolioHistory] = useState([])

  // Mock data for demo mode
  const mockBalances = [
    {
      asset: 'USDT',
      free: 5420.75,
      locked: 1200.00,
      total: 6620.75,
      usd_value: 6620.75,
      percentage: 45.2,
      change_24h: 2.5,
      change_24h_percent: 0.04
    },
    {
      asset: 'BTC',
      free: 0.15234,
      locked: 0.02500,
      total: 0.17734,
      usd_value: 7650.32,
      percentage: 52.1,
      change_24h: 125.75,
      change_24h_percent: 1.67
    },
    {
      asset: 'ETH',
      free: 1.2456,
      locked: 0.0000,
      total: 1.2456,
      usd_value: 2890.45,
      percentage: 19.7,
      change_24h: -45.20,
      change_24h_percent: -1.54
    },
    {
      asset: 'ADA',
      free: 2500.00,
      locked: 0.00,
      total: 2500.00,
      usd_value: 1125.00,
      percentage: 7.7,
      change_24h: 15.75,
      change_24h_percent: 1.42
    },
    {
      asset: 'DOT',
      free: 45.67,
      locked: 0.00,
      total: 45.67,
      usd_value: 320.69,
      percentage: 2.2,
      change_24h: -8.45,
      change_24h_percent: -2.57
    }
  ]

  const mockPortfolioHistory = [
    { timestamp: '2024-01-15T00:00:00Z', value: 14500.00 },
    { timestamp: '2024-01-15T04:00:00Z', value: 14650.25 },
    { timestamp: '2024-01-15T08:00:00Z', value: 14420.75 },
    { timestamp: '2024-01-15T12:00:00Z', value: 14780.50 },
    { timestamp: '2024-01-15T16:00:00Z', value: 14890.25 },
    { timestamp: '2024-01-15T20:00:00Z', value: 14756.85 },
    { timestamp: '2024-01-16T00:00:00Z', value: 14606.41 }
  ]

  useEffect(() => {
    loadBalances()
    loadPortfolioHistory()
    
    // Set up real-time updates
    const interval = setInterval(() => {
      if (mode !== 'demo') {
        loadBalances()
      }
    }, 30000) // Update every 30 seconds

    return () => clearInterval(interval)
  }, [mode, selectedTimeframe])

  const loadBalances = async () => {
    setLoading(true)
    try {
      if (mode === 'demo') {
        // Use mock data for demo mode
        setBalances(mockBalances)
        const total = mockBalances.reduce((sum, balance) => sum + balance.usd_value, 0)
        setTotalBalance(total)
        setDailyChange(89.35)
        setDailyChangePercent(0.61)
      } else {
        // In live mode, fetch from API
        const response = await fetch('/api/bot/balance', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        })
        const data = await response.json()
        if (data.success) {
          setBalances(data.data.balances)
          setTotalBalance(data.data.total_usd_value)
          setDailyChange(data.data.daily_change)
          setDailyChangePercent(data.data.daily_change_percent)
        }
      }
    } catch (error) {
      console.error('Error loading balances:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadPortfolioHistory = async () => {
    try {
      if (mode === 'demo') {
        setPortfolioHistory(mockPortfolioHistory)
      } else {
        const response = await fetch(`/api/bot/portfolio-history?timeframe=${selectedTimeframe}`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        })
        const data = await response.json()
        if (data.success) {
          setPortfolioHistory(data.data.history)
        }
      }
    } catch (error) {
      console.error('Error loading portfolio history:', error)
    }
  }

  const formatCurrency = (amount, currency = 'USD') => {
    if (hideBalances) return '****'
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount)
  }

  const formatCrypto = (amount, decimals = 8) => {
    if (hideBalances) return '****'
    return amount.toFixed(decimals).replace(/\.?0+$/, '')
  }

  const formatPercent = (percent) => {
    const sign = percent >= 0 ? '+' : ''
    return `${sign}${percent.toFixed(2)}%`
  }

  const BalanceCard = ({ balance }) => {
    const isPositive = balance.change_24h >= 0
    
    return (
      <div className="bg-white rounded-lg border p-4 hover:shadow-md transition-shadow">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-gray-100 rounded-full">
              {balance.asset === 'BTC' ? (
                <Bitcoin className="h-5 w-5 text-orange-500" />
              ) : (
                <DollarSign className="h-5 w-5 text-gray-600" />
              )}
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">{balance.asset}</h3>
              <p className="text-sm text-gray-500">
                {balance.percentage.toFixed(1)}% of portfolio
              </p>
            </div>
          </div>
          <div className="text-right">
            <p className="font-semibold text-gray-900">
              {formatCurrency(balance.usd_value)}
            </p>
            <div className={`flex items-center space-x-1 text-sm ${
              isPositive ? 'text-green-600' : 'text-red-600'
            }`}>
              {isPositive ? (
                <ArrowUpRight className="h-3 w-3" />
              ) : (
                <ArrowDownRight className="h-3 w-3" />
              )}
              <span>{formatPercent(balance.change_24h_percent)}</span>
            </div>
          </div>
        </div>
        
        <div className="grid grid-cols-3 gap-3 text-sm">
          <div>
            <p className="text-gray-500">Free</p>
            <p className="font-medium">
              {formatCrypto(balance.free, balance.asset === 'USDT' ? 2 : 6)}
            </p>
          </div>
          <div>
            <p className="text-gray-500">Locked</p>
            <p className="font-medium">
              {formatCrypto(balance.locked, balance.asset === 'USDT' ? 2 : 6)}
            </p>
          </div>
          <div>
            <p className="text-gray-500">Total</p>
            <p className="font-medium">
              {formatCrypto(balance.total, balance.asset === 'USDT' ? 2 : 6)}
            </p>
          </div>
        </div>
        
        {/* Portfolio percentage bar */}
        <div className="mt-3">
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${balance.percentage}%` }}
            ></div>
          </div>
        </div>
      </div>
    )
  }

  const PortfolioChart = () => {
    if (portfolioHistory.length === 0) return null

    const minValue = Math.min(...portfolioHistory.map(p => p.value))
    const maxValue = Math.max(...portfolioHistory.map(p => p.value))
    const range = maxValue - minValue

    return (
      <div className="bg-white rounded-lg border p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Portfolio Value</h3>
          <div className="flex space-x-2">
            {['1h', '24h', '7d', '30d'].map(timeframe => (
              <button
                key={timeframe}
                onClick={() => setSelectedTimeframe(timeframe)}
                className={`px-3 py-1 text-sm rounded-lg transition-colors ${
                  selectedTimeframe === timeframe
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {timeframe}
              </button>
            ))}
          </div>
        </div>
        
        <div className="h-48 relative">
          <svg className="w-full h-full" viewBox="0 0 400 200">
            <defs>
              <linearGradient id="portfolioGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor="#3B82F6" stopOpacity="0.3" />
                <stop offset="100%" stopColor="#3B82F6" stopOpacity="0.05" />
              </linearGradient>
            </defs>
            
            {/* Chart area */}
            <path
              d={portfolioHistory.map((point, index) => {
                const x = (index / (portfolioHistory.length - 1)) * 380 + 10
                const y = 180 - ((point.value - minValue) / range) * 160
                return `${index === 0 ? 'M' : 'L'} ${x} ${y}`
              }).join(' ')}
              fill="none"
              stroke="#3B82F6"
              strokeWidth="2"
            />
            
            {/* Fill area */}
            <path
              d={[
                portfolioHistory.map((point, index) => {
                  const x = (index / (portfolioHistory.length - 1)) * 380 + 10
                  const y = 180 - ((point.value - minValue) / range) * 160
                  return `${index === 0 ? 'M' : 'L'} ${x} ${y}`
                }).join(' '),
                'L 390 180 L 10 180 Z'
              ].join(' ')}
              fill="url(#portfolioGradient)"
            />
            
            {/* Data points */}
            {portfolioHistory.map((point, index) => {
              const x = (index / (portfolioHistory.length - 1)) * 380 + 10
              const y = 180 - ((point.value - minValue) / range) * 160
              return (
                <circle
                  key={index}
                  cx={x}
                  cy={y}
                  r="3"
                  fill="#3B82F6"
                  className="hover:r-4 transition-all cursor-pointer"
                >
                  <title>{formatCurrency(point.value)} at {new Date(point.timestamp).toLocaleString()}</title>
                </circle>
              )
            })}
          </svg>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  const isPositiveChange = dailyChange >= 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Balance Monitor</h2>
          <p className="text-gray-600">Track your portfolio and balances</p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setHideBalances(!hideBalances)}
            className="flex items-center space-x-2 px-3 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          >
            {hideBalances ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            <span>{hideBalances ? 'Show' : 'Hide'}</span>
          </button>
          <button
            onClick={loadBalances}
            className="flex items-center space-x-2 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <RefreshCw className="h-4 w-4" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Portfolio Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg border p-6">
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-blue-100 rounded-full">
              <Wallet className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Total Portfolio Value</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(totalBalance)}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg border p-6">
          <div className="flex items-center space-x-3">
            <div className={`p-3 rounded-full ${
              isPositiveChange ? 'bg-green-100' : 'bg-red-100'
            }`}>
              {isPositiveChange ? (
                <TrendingUp className={`h-6 w-6 ${
                  isPositiveChange ? 'text-green-600' : 'text-red-600'
                }`} />
              ) : (
                <TrendingDown className={`h-6 w-6 ${
                  isPositiveChange ? 'text-green-600' : 'text-red-600'
                }`} />
              )}
            </div>
            <div>
              <p className="text-sm text-gray-600">24h Change</p>
              <p className={`text-2xl font-bold ${
                isPositiveChange ? 'text-green-600' : 'text-red-600'
              }`}>
                {hideBalances ? '****' : formatPercent(dailyChangePercent)}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg border p-6">
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-purple-100 rounded-full">
              <PieChart className="h-6 w-6 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Assets</p>
              <p className="text-2xl font-bold text-gray-900">
                {balances.filter(b => b.total > 0).length}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Portfolio Chart */}
      <PortfolioChart />

      {/* Asset Balances */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Asset Balances</h3>
        {balances.length === 0 ? (
          <div className="text-center py-12">
            <Wallet className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No balances found</h3>
            <p className="text-gray-600">Your account balances will appear here</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {balances
              .filter(balance => balance.total > 0)
              .sort((a, b) => b.usd_value - a.usd_value)
              .map(balance => (
                <BalanceCard key={balance.asset} balance={balance} />
              ))
            }
          </div>
        )}
      </div>

      {/* Quick Stats */}
      <div className="bg-white rounded-lg border p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Stats</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <p className="text-sm text-gray-600">Free Balance</p>
            <p className="text-lg font-semibold text-gray-900">
              {formatCurrency(balances.reduce((sum, b) => sum + (b.free * b.usd_value / b.total), 0))}
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-600">Locked Balance</p>
            <p className="text-lg font-semibold text-gray-900">
              {formatCurrency(balances.reduce((sum, b) => sum + (b.locked * b.usd_value / b.total), 0))}
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-600">Best Performer</p>
            <p className="text-lg font-semibold text-green-600">
              {balances.length > 0 ? 
                balances.reduce((best, current) => 
                  current.change_24h_percent > best.change_24h_percent ? current : best
                ).asset : 'N/A'
              }
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-600">Worst Performer</p>
            <p className="text-lg font-semibold text-red-600">
              {balances.length > 0 ? 
                balances.reduce((worst, current) => 
                  current.change_24h_percent < worst.change_24h_percent ? current : worst
                ).asset : 'N/A'
              }
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default BalanceMonitor