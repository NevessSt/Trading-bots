import { useState, useEffect } from 'react'
import { 
  Play, 
  Pause, 
  Settings, 
  Plus, 
  Edit, 
  Trash2, 
  Activity,
  TrendingUp,
  TrendingDown,
  AlertCircle,
  CheckCircle,
  Clock,
  DollarSign
} from 'lucide-react'

const BotControl = ({ mode = 'demo' }) => {
  const [bots, setBots] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedBot, setSelectedBot] = useState(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [strategies, setStrategies] = useState([])
  const [tradingPairs, setTradingPairs] = useState([])

  // Mock data for demo mode
  const mockBots = [
    {
      bot_id: '1',
      name: 'BTC Scalper',
      strategy: 'scalping_strategy',
      symbol: 'BTC/USDT',
      is_active: true,
      created_at: '2024-01-15T10:30:00Z',
      last_trade: '2024-01-15T14:25:00Z',
      total_trades: 45,
      profit_loss: 1250.75,
      win_rate: 68.5
    },
    {
      bot_id: '2',
      name: 'ETH Swing Trader',
      strategy: 'swing_trading',
      symbol: 'ETH/USDT',
      is_active: false,
      created_at: '2024-01-14T09:15:00Z',
      last_trade: '2024-01-14T16:45:00Z',
      total_trades: 23,
      profit_loss: -125.30,
      win_rate: 45.2
    },
    {
      bot_id: '3',
      name: 'ADA RSI Bot',
      strategy: 'rsi_strategy',
      symbol: 'ADA/USDT',
      is_active: true,
      created_at: '2024-01-13T11:20:00Z',
      last_trade: '2024-01-15T13:10:00Z',
      total_trades: 67,
      profit_loss: 890.45,
      win_rate: 72.1
    }
  ]

  const mockStrategies = [
    {
      name: 'rsi_strategy',
      display_name: 'RSI Strategy',
      description: 'Uses RSI indicator for overbought/oversold signals'
    },
    {
      name: 'ema_crossover',
      display_name: 'EMA Crossover',
      description: 'Uses exponential moving average crossovers'
    },
    {
      name: 'scalping_strategy',
      display_name: 'Scalping Strategy',
      description: 'High-frequency trading for small profits'
    },
    {
      name: 'swing_trading',
      display_name: 'Swing Trading',
      description: 'Medium-term trading strategy'
    }
  ]

  const mockTradingPairs = [
    { symbol: 'BTC/USDT', base: 'BTC', quote: 'USDT' },
    { symbol: 'ETH/USDT', base: 'ETH', quote: 'USDT' },
    { symbol: 'ADA/USDT', base: 'ADA', quote: 'USDT' },
    { symbol: 'DOT/USDT', base: 'DOT', quote: 'USDT' },
    { symbol: 'LINK/USDT', base: 'LINK', quote: 'USDT' }
  ]

  useEffect(() => {
    loadBots()
    loadStrategies()
    loadTradingPairs()
  }, [mode])

  const loadBots = async () => {
    setLoading(true)
    try {
      if (mode === 'demo') {
        // Use mock data for demo mode
        setBots(mockBots)
      } else {
        // In live mode, fetch from API
        const response = await fetch('/api/bot/status', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        })
        const data = await response.json()
        if (data.success) {
          setBots(data.data.bots)
        }
      }
    } catch (error) {
      console.error('Error loading bots:', error)
    } finally {
      setLoading(false)
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

  const loadTradingPairs = async () => {
    try {
      if (mode === 'demo') {
        setTradingPairs(mockTradingPairs)
      } else {
        const response = await fetch('/api/bot/trading-pairs', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        })
        const data = await response.json()
        if (data.success) {
          setTradingPairs(data.data.pairs)
        }
      }
    } catch (error) {
      console.error('Error loading trading pairs:', error)
    }
  }

  const handleStartBot = async (botId) => {
    try {
      if (mode === 'demo') {
        // Update mock data
        setBots(bots.map(bot => 
          bot.bot_id === botId ? { ...bot, is_active: true } : bot
        ))
        return
      }

      const response = await fetch('/api/bot/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ bot_id: botId })
      })
      
      const data = await response.json()
      if (data.success) {
        loadBots() // Reload bots to get updated status
      } else {
        alert(data.error || 'Failed to start bot')
      }
    } catch (error) {
      console.error('Error starting bot:', error)
      alert('Failed to start bot')
    }
  }

  const handleStopBot = async (botId) => {
    try {
      if (mode === 'demo') {
        // Update mock data
        setBots(bots.map(bot => 
          bot.bot_id === botId ? { ...bot, is_active: false } : bot
        ))
        return
      }

      const response = await fetch('/api/bot/stop', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ bot_id: botId })
      })
      
      const data = await response.json()
      if (data.success) {
        loadBots() // Reload bots to get updated status
      } else {
        alert(data.error || 'Failed to stop bot')
      }
    } catch (error) {
      console.error('Error stopping bot:', error)
      alert('Failed to stop bot')
    }
  }

  const handleDeleteBot = async (botId) => {
    if (!confirm('Are you sure you want to delete this bot?')) {
      return
    }

    try {
      if (mode === 'demo') {
        // Update mock data
        setBots(bots.filter(bot => bot.bot_id !== botId))
        return
      }

      const response = await fetch(`/api/bot/delete/${botId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      })
      
      const data = await response.json()
      if (data.success) {
        loadBots() // Reload bots
      } else {
        alert(data.error || 'Failed to delete bot')
      }
    } catch (error) {
      console.error('Error deleting bot:', error)
      alert('Failed to delete bot')
    }
  }

  const BotCard = ({ bot }) => {
    const isActive = bot.is_active
    const isProfitable = bot.profit_loss > 0

    return (
      <div className="bg-white rounded-lg border p-6 hover:shadow-md transition-shadow">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className={`p-2 rounded-full ${
              isActive ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-600'
            }`}>
              <Activity className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">{bot.name}</h3>
              <p className="text-sm text-gray-500">{bot.symbol}</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {isActive ? (
              <button
                onClick={() => handleStopBot(bot.bot_id)}
                className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                title="Stop Bot"
              >
                <Pause className="h-4 w-4" />
              </button>
            ) : (
              <button
                onClick={() => handleStartBot(bot.bot_id)}
                className="p-2 text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                title="Start Bot"
              >
                <Play className="h-4 w-4" />
              </button>
            )}
            <button
              onClick={() => {
                setSelectedBot(bot)
                setShowEditModal(true)
              }}
              className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
              title="Edit Bot"
            >
              <Edit className="h-4 w-4" />
            </button>
            <button
              onClick={() => handleDeleteBot(bot.bot_id)}
              className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
              title="Delete Bot"
              disabled={isActive}
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <p className="text-sm text-gray-500">Strategy</p>
            <p className="font-medium">
              {strategies.find(s => s.name === bot.strategy)?.display_name || bot.strategy}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Status</p>
            <div className="flex items-center space-x-1">
              {isActive ? (
                <>
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  <span className="text-green-600 font-medium">Running</span>
                </>
              ) : (
                <>
                  <AlertCircle className="h-4 w-4 text-gray-500" />
                  <span className="text-gray-600 font-medium">Stopped</span>
                </>
              )}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4 pt-4 border-t">
          <div className="text-center">
            <p className="text-sm text-gray-500">P&L</p>
            <div className="flex items-center justify-center space-x-1">
              {isProfitable ? (
                <TrendingUp className="h-4 w-4 text-green-500" />
              ) : (
                <TrendingDown className="h-4 w-4 text-red-500" />
              )}
              <span className={`font-semibold ${
                isProfitable ? 'text-green-600' : 'text-red-600'
              }`}>
                ${Math.abs(bot.profit_loss).toFixed(2)}
              </span>
            </div>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-500">Trades</p>
            <p className="font-semibold text-gray-900">{bot.total_trades}</p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-500">Win Rate</p>
            <p className="font-semibold text-gray-900">{bot.win_rate.toFixed(1)}%</p>
          </div>
        </div>

        {bot.last_trade && (
          <div className="mt-4 pt-4 border-t">
            <div className="flex items-center space-x-2 text-sm text-gray-500">
              <Clock className="h-4 w-4" />
              <span>Last trade: {new Date(bot.last_trade).toLocaleString()}</span>
            </div>
          </div>
        )}
      </div>
    )
  }

  const CreateBotModal = () => {
    const [formData, setFormData] = useState({
      name: '',
      strategy: '',
      symbol: '',
      timeframe: '1h'
    })

    const handleSubmit = async (e) => {
      e.preventDefault()
      
      try {
        if (mode === 'demo') {
          // Add to mock data
          const newBot = {
            bot_id: String(Date.now()),
            name: formData.name,
            strategy: formData.strategy,
            symbol: formData.symbol,
            is_active: false,
            created_at: new Date().toISOString(),
            last_trade: null,
            total_trades: 0,
            profit_loss: 0,
            win_rate: 0
          }
          setBots([...bots, newBot])
          setShowCreateModal(false)
          setFormData({ name: '', strategy: '', symbol: '', timeframe: '1h' })
          return
        }

        const response = await fetch('/api/bot/create', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify(formData)
        })
        
        const data = await response.json()
        if (data.success) {
          setShowCreateModal(false)
          setFormData({ name: '', strategy: '', symbol: '', timeframe: '1h' })
          loadBots()
        } else {
          alert(data.error || 'Failed to create bot')
        }
      } catch (error) {
        console.error('Error creating bot:', error)
        alert('Failed to create bot')
      }
    }

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 w-full max-w-md">
          <h2 className="text-xl font-semibold mb-4">Create New Bot</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Bot Name
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Strategy
              </label>
              <select
                value={formData.strategy}
                onChange={(e) => setFormData({ ...formData, strategy: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              >
                <option value="">Select Strategy</option>
                {strategies.map(strategy => (
                  <option key={strategy.name} value={strategy.name}>
                    {strategy.display_name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Trading Pair
              </label>
              <select
                value={formData.symbol}
                onChange={(e) => setFormData({ ...formData, symbol: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              >
                <option value="">Select Trading Pair</option>
                {tradingPairs.map(pair => (
                  <option key={pair.symbol} value={pair.symbol}>
                    {pair.symbol}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Timeframe
              </label>
              <select
                value={formData.timeframe}
                onChange={(e) => setFormData({ ...formData, timeframe: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="1m">1 Minute</option>
                <option value="5m">5 Minutes</option>
                <option value="15m">15 Minutes</option>
                <option value="1h">1 Hour</option>
                <option value="4h">4 Hours</option>
                <option value="1d">1 Day</option>
              </select>
            </div>
            <div className="flex space-x-3 pt-4">
              <button
                type="button"
                onClick={() => {
                  setShowCreateModal(false)
                  setFormData({ name: '', strategy: '', symbol: '', timeframe: '1h' })
                }}
                className="flex-1 px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Create Bot
              </button>
            </div>
          </form>
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Bot Control</h2>
          <p className="text-gray-600">Manage your trading bots</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus className="h-4 w-4" />
          <span>Create Bot</span>
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-green-100 rounded-full">
              <Activity className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Active Bots</p>
              <p className="text-2xl font-bold text-gray-900">
                {bots.filter(bot => bot.is_active).length}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-full">
              <Settings className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Total Bots</p>
              <p className="text-2xl font-bold text-gray-900">{bots.length}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-yellow-100 rounded-full">
              <DollarSign className="h-5 w-5 text-yellow-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Total P&L</p>
              <p className="text-2xl font-bold text-gray-900">
                ${bots.reduce((sum, bot) => sum + bot.profit_loss, 0).toFixed(2)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Bots Grid */}
      {bots.length === 0 ? (
        <div className="text-center py-12">
          <Activity className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No bots created yet</h3>
          <p className="text-gray-600 mb-4">Create your first trading bot to get started</p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="h-4 w-4" />
            <span>Create Bot</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {bots.map(bot => (
            <BotCard key={bot.bot_id} bot={bot} />
          ))}
        </div>
      )}

      {/* Create Bot Modal */}
      {showCreateModal && <CreateBotModal />}
    </div>
  )
}

export default BotControl