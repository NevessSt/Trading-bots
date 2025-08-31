import { useState, useEffect } from 'react'
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Calendar, 
  Filter, 
  Download, 
  BarChart3, 
  PieChart, 
  Activity, 
  Target, 
  Percent, 
  Clock, 
  ArrowUpRight, 
  ArrowDownRight,
  RefreshCw
} from 'lucide-react'

const PnLTracker = ({ mode = 'demo' }) => {
  const [pnlData, setPnlData] = useState(null)
  const [trades, setTrades] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedTimeframe, setSelectedTimeframe] = useState('7d')
  const [selectedStrategy, setSelectedStrategy] = useState('all')
  const [selectedSymbol, setSelectedSymbol] = useState('all')
  const [strategies, setStrategies] = useState([])
  const [symbols, setSymbols] = useState([])
  const [showFilters, setShowFilters] = useState(false)

  // Mock data for demo mode
  const mockPnlData = {
    total_pnl: 2015.85,
    total_pnl_percent: 8.45,
    daily_pnl: 125.75,
    daily_pnl_percent: 0.52,
    weekly_pnl: 345.20,
    weekly_pnl_percent: 1.44,
    monthly_pnl: 1890.45,
    monthly_pnl_percent: 7.89,
    total_trades: 156,
    winning_trades: 98,
    losing_trades: 58,
    win_rate: 62.82,
    avg_win: 45.67,
    avg_loss: -28.34,
    largest_win: 234.56,
    largest_loss: -156.78,
    profit_factor: 1.61,
    sharpe_ratio: 1.34,
    max_drawdown: -345.67,
    max_drawdown_percent: -1.44,
    recovery_factor: 5.83,
    expectancy: 12.92
  }

  const mockTrades = [
    {
      trade_id: '1',
      symbol: 'BTC/USDT',
      strategy: 'scalping_strategy',
      side: 'buy',
      entry_price: 43250.50,
      exit_price: 43456.75,
      quantity: 0.0234,
      pnl: 4.83,
      pnl_percent: 0.48,
      entry_time: '2024-01-15T14:25:00Z',
      exit_time: '2024-01-15T14:47:00Z',
      duration: 22,
      fees: 0.12,
      status: 'closed'
    },
    {
      trade_id: '2',
      symbol: 'ETH/USDT',
      strategy: 'rsi_strategy',
      side: 'sell',
      entry_price: 2456.80,
      exit_price: 2398.45,
      quantity: 0.5678,
      pnl: -33.15,
      pnl_percent: -2.38,
      entry_time: '2024-01-15T13:15:00Z',
      exit_time: '2024-01-15T15:22:00Z',
      duration: 127,
      fees: 0.28,
      status: 'closed'
    },
    {
      trade_id: '3',
      symbol: 'ADA/USDT',
      strategy: 'ema_crossover',
      side: 'buy',
      entry_price: 0.4567,
      exit_price: 0.4789,
      quantity: 2500.00,
      pnl: 55.50,
      pnl_percent: 4.86,
      entry_time: '2024-01-15T11:30:00Z',
      exit_time: '2024-01-15T16:45:00Z',
      duration: 315,
      fees: 0.52,
      status: 'closed'
    },
    {
      trade_id: '4',
      symbol: 'BTC/USDT',
      strategy: 'scalping_strategy',
      side: 'buy',
      entry_price: 43180.25,
      exit_price: null,
      quantity: 0.0156,
      pnl: 12.45,
      pnl_percent: 1.84,
      entry_time: '2024-01-15T16:20:00Z',
      exit_time: null,
      duration: null,
      fees: 0.08,
      status: 'open'
    },
    {
      trade_id: '5',
      symbol: 'DOT/USDT',
      strategy: 'swing_trading',
      side: 'sell',
      entry_price: 7.234,
      exit_price: 6.987,
      quantity: 150.00,
      pnl: -37.05,
      pnl_percent: -3.41,
      entry_time: '2024-01-14T09:15:00Z',
      exit_time: '2024-01-15T14:30:00Z',
      duration: 1755,
      fees: 0.22,
      status: 'closed'
    }
  ]

  const mockStrategies = [
    { name: 'scalping_strategy', display_name: 'Scalping Strategy' },
    { name: 'rsi_strategy', display_name: 'RSI Strategy' },
    { name: 'ema_crossover', display_name: 'EMA Crossover' },
    { name: 'swing_trading', display_name: 'Swing Trading' }
  ]

  const mockSymbols = [
    { symbol: 'BTC/USDT' },
    { symbol: 'ETH/USDT' },
    { symbol: 'ADA/USDT' },
    { symbol: 'DOT/USDT' },
    { symbol: 'LINK/USDT' }
  ]

  useEffect(() => {
    loadPnLData()
    loadTrades()
    loadStrategies()
    loadSymbols()
  }, [mode, selectedTimeframe, selectedStrategy, selectedSymbol])

  const loadPnLData = async () => {
    setLoading(true)
    try {
      if (mode === 'demo') {
        setPnlData(mockPnlData)
      } else {
        const response = await fetch(`/api/bot/pnl?timeframe=${selectedTimeframe}&strategy=${selectedStrategy}&symbol=${selectedSymbol}`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        })
        const data = await response.json()
        if (data.success) {
          setPnlData(data.data)
        }
      }
    } catch (error) {
      console.error('Error loading P&L data:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadTrades = async () => {
    try {
      if (mode === 'demo') {
        setTrades(mockTrades)
      } else {
        const response = await fetch(`/api/bot/trades?timeframe=${selectedTimeframe}&strategy=${selectedStrategy}&symbol=${selectedSymbol}`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        })
        const data = await response.json()
        if (data.success) {
          setTrades(data.data.trades)
        }
      }
    } catch (error) {
      console.error('Error loading trades:', error)
    }
  }

  const loadStrategies = async () => {
    try {
      if (mode === 'demo') {
        setStrategies(mockStrategies)
      } else {
        const response = await fetch('/api/bot/strategies', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        })
        const data = await response.json()
        if (data.success) {
          setStrategies(data.data.strategies)
        }
      }
    } catch (error) {
      console.error('Error loading strategies:', error)
    }
  }

  const loadSymbols = async () => {
    try {
      if (mode === 'demo') {
        setSymbols(mockSymbols)
      } else {
        const response = await fetch('/api/bot/trading-pairs', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        })
        const data = await response.json()
        if (data.success) {
          setSymbols(data.data.pairs)
        }
      }
    } catch (error) {
      console.error('Error loading symbols:', error)
    }
  }

  const exportTrades = () => {
    const csvContent = [
      ['Trade ID', 'Symbol', 'Strategy', 'Side', 'Entry Price', 'Exit Price', 'Quantity', 'P&L', 'P&L %', 'Entry Time', 'Exit Time', 'Duration (min)', 'Fees', 'Status'],
      ...trades.map(trade => [
        trade.trade_id,
        trade.symbol,
        trade.strategy,
        trade.side,
        trade.entry_price,
        trade.exit_price || 'N/A',
        trade.quantity,
        trade.pnl,
        trade.pnl_percent,
        trade.entry_time,
        trade.exit_time || 'N/A',
        trade.duration || 'N/A',
        trade.fees,
        trade.status
      ])
    ].map(row => row.join(',')).join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `trades_${selectedTimeframe}_${Date.now()}.csv`
    a.click()
    window.URL.revokeObjectURL(url)
  }

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount)
  }

  const formatPercent = (percent) => {
    const sign = percent >= 0 ? '+' : ''
    return `${sign}${percent.toFixed(2)}%`
  }

  const formatDuration = (minutes) => {
    if (!minutes) return 'N/A'
    if (minutes < 60) return `${minutes}m`
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    return `${hours}h ${mins}m`
  }

  const MetricCard = ({ title, value, change, changePercent, icon: Icon, positive }) => {
    const isPositive = positive !== undefined ? positive : change >= 0
    
    return (
      <div className="bg-white rounded-lg border p-4">
        <div className="flex items-center justify-between mb-2">
          <div className={`p-2 rounded-full ${
            isPositive ? 'bg-green-100' : 'bg-red-100'
          }`}>
            <Icon className={`h-5 w-5 ${
              isPositive ? 'text-green-600' : 'text-red-600'
            }`} />
          </div>
          {change !== undefined && (
            <div className={`flex items-center space-x-1 text-sm ${
              isPositive ? 'text-green-600' : 'text-red-600'
            }`}>
              {isPositive ? (
                <ArrowUpRight className="h-3 w-3" />
              ) : (
                <ArrowDownRight className="h-3 w-3" />
              )}
              <span>{formatPercent(changePercent)}</span>
            </div>
          )}
        </div>
        <div>
          <p className="text-sm text-gray-600">{title}</p>
          <p className={`text-xl font-bold ${
            isPositive ? 'text-green-600' : 'text-red-600'
          }`}>
            {typeof value === 'number' && title.includes('$') ? formatCurrency(value) : value}
          </p>
        </div>
      </div>
    )
  }

  const TradeRow = ({ trade }) => {
    const isProfit = trade.pnl > 0
    const isOpen = trade.status === 'open'
    
    return (
      <tr className="hover:bg-gray-50">
        <td className="px-4 py-3 text-sm font-medium text-gray-900">
          {trade.trade_id}
        </td>
        <td className="px-4 py-3 text-sm text-gray-900">
          {trade.symbol}
        </td>
        <td className="px-4 py-3 text-sm text-gray-600">
          {strategies.find(s => s.name === trade.strategy)?.display_name || trade.strategy}
        </td>
        <td className="px-4 py-3">
          <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
            trade.side === 'buy' 
              ? 'bg-green-100 text-green-800' 
              : 'bg-red-100 text-red-800'
          }`}>
            {trade.side.toUpperCase()}
          </span>
        </td>
        <td className="px-4 py-3 text-sm text-gray-900">
          ${trade.entry_price.toFixed(4)}
        </td>
        <td className="px-4 py-3 text-sm text-gray-900">
          {trade.exit_price ? `$${trade.exit_price.toFixed(4)}` : 'N/A'}
        </td>
        <td className="px-4 py-3 text-sm text-gray-900">
          {trade.quantity}
        </td>
        <td className="px-4 py-3">
          <div className={`text-sm font-medium ${
            isProfit ? 'text-green-600' : 'text-red-600'
          }`}>
            {formatCurrency(trade.pnl)}
            <div className="text-xs">
              {formatPercent(trade.pnl_percent)}
            </div>
          </div>
        </td>
        <td className="px-4 py-3 text-sm text-gray-600">
          {formatDuration(trade.duration)}
        </td>
        <td className="px-4 py-3">
          <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
            isOpen 
              ? 'bg-blue-100 text-blue-800' 
              : 'bg-gray-100 text-gray-800'
          }`}>
            {trade.status.toUpperCase()}
          </span>
        </td>
        <td className="px-4 py-3 text-sm text-gray-600">
          {new Date(trade.entry_time).toLocaleString()}
        </td>
      </tr>
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (!pnlData) {
    return (
      <div className="text-center py-12">
        <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No P&L data available</h3>
        <p className="text-gray-600">Start trading to see your performance metrics</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">P&L Tracker</h2>
          <p className="text-gray-600">Monitor your trading performance</p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center space-x-2 px-3 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <Filter className="h-4 w-4" />
            <span>Filters</span>
          </button>
          <button
            onClick={exportTrades}
            className="flex items-center space-x-2 px-3 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <Download className="h-4 w-4" />
            <span>Export</span>
          </button>
          <button
            onClick={loadPnLData}
            className="flex items-center space-x-2 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <RefreshCw className="h-4 w-4" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="bg-white rounded-lg border p-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Timeframe
              </label>
              <select
                value={selectedTimeframe}
                onChange={(e) => setSelectedTimeframe(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="1d">Last 24 Hours</option>
                <option value="7d">Last 7 Days</option>
                <option value="30d">Last 30 Days</option>
                <option value="90d">Last 90 Days</option>
                <option value="all">All Time</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Strategy
              </label>
              <select
                value={selectedStrategy}
                onChange={(e) => setSelectedStrategy(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="all">All Strategies</option>
                {strategies.map(strategy => (
                  <option key={strategy.name} value={strategy.name}>
                    {strategy.display_name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Symbol
              </label>
              <select
                value={selectedSymbol}
                onChange={(e) => setSelectedSymbol(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="all">All Symbols</option>
                {symbols.map(symbol => (
                  <option key={symbol.symbol} value={symbol.symbol}>
                    {symbol.symbol}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total P&L"
          value={pnlData.total_pnl}
          changePercent={pnlData.total_pnl_percent}
          icon={DollarSign}
          positive={pnlData.total_pnl > 0}
        />
        <MetricCard
          title="Win Rate"
          value={`${pnlData.win_rate.toFixed(1)}%`}
          icon={Target}
          positive={pnlData.win_rate > 50}
        />
        <MetricCard
          title="Total Trades"
          value={pnlData.total_trades}
          icon={Activity}
          positive={true}
        />
        <MetricCard
          title="Profit Factor"
          value={pnlData.profit_factor.toFixed(2)}
          icon={BarChart3}
          positive={pnlData.profit_factor > 1}
        />
      </div>

      {/* Performance Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Period Performance</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Daily P&L</span>
              <span className={`font-medium ${
                pnlData.daily_pnl > 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {formatCurrency(pnlData.daily_pnl)} ({formatPercent(pnlData.daily_pnl_percent)})
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Weekly P&L</span>
              <span className={`font-medium ${
                pnlData.weekly_pnl > 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {formatCurrency(pnlData.weekly_pnl)} ({formatPercent(pnlData.weekly_pnl_percent)})
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Monthly P&L</span>
              <span className={`font-medium ${
                pnlData.monthly_pnl > 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {formatCurrency(pnlData.monthly_pnl)} ({formatPercent(pnlData.monthly_pnl_percent)})
              </span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Trade Statistics</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Winning Trades</span>
              <span className="font-medium text-green-600">{pnlData.winning_trades}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Losing Trades</span>
              <span className="font-medium text-red-600">{pnlData.losing_trades}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Average Win</span>
              <span className="font-medium text-green-600">{formatCurrency(pnlData.avg_win)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Average Loss</span>
              <span className="font-medium text-red-600">{formatCurrency(pnlData.avg_loss)}</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Risk Metrics</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Sharpe Ratio</span>
              <span className={`font-medium ${
                pnlData.sharpe_ratio > 1 ? 'text-green-600' : 'text-red-600'
              }`}>
                {pnlData.sharpe_ratio.toFixed(2)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Max Drawdown</span>
              <span className="font-medium text-red-600">
                {formatCurrency(pnlData.max_drawdown)} ({formatPercent(pnlData.max_drawdown_percent)})
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Recovery Factor</span>
              <span className={`font-medium ${
                pnlData.recovery_factor > 2 ? 'text-green-600' : 'text-red-600'
              }`}>
                {pnlData.recovery_factor.toFixed(2)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Expectancy</span>
              <span className={`font-medium ${
                pnlData.expectancy > 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {formatCurrency(pnlData.expectancy)}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Trades */}
      <div className="bg-white rounded-lg border">
        <div className="px-6 py-4 border-b">
          <h3 className="text-lg font-semibold text-gray-900">Recent Trades</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  ID
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Symbol
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Strategy
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Side
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Entry
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Exit
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Quantity
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  P&L
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Duration
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Entry Time
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {trades.length === 0 ? (
                <tr>
                  <td colSpan="11" className="px-4 py-8 text-center text-gray-500">
                    No trades found for the selected filters
                  </td>
                </tr>
              ) : (
                trades.slice(0, 10).map(trade => (
                  <TradeRow key={trade.trade_id} trade={trade} />
                ))
              )}
            </tbody>
          </table>
        </div>
        {trades.length > 10 && (
          <div className="px-6 py-4 border-t bg-gray-50">
            <p className="text-sm text-gray-600">
              Showing 10 of {trades.length} trades. Use filters or export to see all trades.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

export default PnLTracker