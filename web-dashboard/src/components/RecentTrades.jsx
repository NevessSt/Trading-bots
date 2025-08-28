import { useState } from 'react'
import { TrendingUp, TrendingDown, Clock, Filter, Download } from 'lucide-react'

const RecentTrades = ({ detailed = false }) => {
  const [filter, setFilter] = useState('all')
  const [trades] = useState([
    {
      id: 1,
      symbol: 'BTC/USD',
      side: 'buy',
      amount: 0.5,
      price: 43200,
      total: 21600,
      fee: 21.60,
      time: '2024-08-28 10:30:15',
      status: 'completed',
      pnl: 125.50
    },
    {
      id: 2,
      symbol: 'ETH/USD',
      side: 'sell',
      amount: 2.0,
      price: 2100,
      total: 4200,
      fee: 4.20,
      time: '2024-08-28 10:25:30',
      status: 'completed',
      pnl: -45.20
    },
    {
      id: 3,
      symbol: 'ADA/USD',
      side: 'buy',
      amount: 1000,
      price: 1.25,
      total: 1250,
      fee: 1.25,
      time: '2024-08-28 10:20:45',
      status: 'completed',
      pnl: 67.80
    },
    {
      id: 4,
      symbol: 'DOT/USD',
      side: 'sell',
      amount: 50,
      price: 7.85,
      total: 392.50,
      fee: 0.39,
      time: '2024-08-28 10:15:20',
      status: 'completed',
      pnl: 23.10
    },
    {
      id: 5,
      symbol: 'LINK/USD',
      side: 'buy',
      amount: 25,
      price: 14.23,
      total: 355.75,
      fee: 0.36,
      time: '2024-08-28 10:10:10',
      status: 'completed',
      pnl: -12.30
    },
    {
      id: 6,
      symbol: 'BTC/USD',
      side: 'sell',
      amount: 0.25,
      price: 43100,
      total: 10775,
      fee: 10.78,
      time: '2024-08-28 10:05:55',
      status: 'completed',
      pnl: 89.45
    }
  ])

  const filteredTrades = trades.filter(trade => {
    if (filter === 'all') return true
    if (filter === 'buy') return trade.side === 'buy'
    if (filter === 'sell') return trade.side === 'sell'
    if (filter === 'profitable') return trade.pnl > 0
    if (filter === 'losses') return trade.pnl < 0
    return true
  })

  const formatTime = (timeString) => {
    const date = new Date(timeString)
    return {
      date: date.toLocaleDateString(),
      time: date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
    }
  }

  const totalPnL = trades.reduce((sum, trade) => sum + trade.pnl, 0)
  const winRate = (trades.filter(trade => trade.pnl > 0).length / trades.length) * 100
  const totalVolume = trades.reduce((sum, trade) => sum + trade.total, 0)

  if (detailed) {
    return (
      <div className="space-y-6">
        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total P&L</p>
                <p className={`text-2xl font-bold ${
                  totalPnL >= 0 ? 'text-success-600' : 'text-danger-600'
                }`}>
                  {totalPnL >= 0 ? '+' : ''}${totalPnL.toFixed(2)}
                </p>
              </div>
              <div className={`p-3 rounded-full ${
                totalPnL >= 0 ? 'bg-success-100' : 'bg-danger-100'
              }`}>
                {totalPnL >= 0 ? (
                  <TrendingUp className="h-6 w-6 text-success-600" />
                ) : (
                  <TrendingDown className="h-6 w-6 text-danger-600" />
                )}
              </div>
            </div>
          </div>
          
          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Win Rate</p>
                <p className="text-2xl font-bold text-gray-900">{winRate.toFixed(1)}%</p>
              </div>
              <div className="p-3 rounded-full bg-primary-100">
                <TrendingUp className="h-6 w-6 text-primary-600" />
              </div>
            </div>
          </div>
          
          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Volume</p>
                <p className="text-2xl font-bold text-gray-900">${totalVolume.toLocaleString()}</p>
              </div>
              <div className="p-3 rounded-full bg-gray-100">
                <Clock className="h-6 w-6 text-gray-600" />
              </div>
            </div>
          </div>
        </div>

        {/* Filters and Export */}
        <div className="card">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6">
            <h3 className="text-lg font-semibold mb-4 sm:mb-0">Trading History</h3>
            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-2">
                <Filter className="h-4 w-4 text-gray-600" />
                <select 
                  value={filter} 
                  onChange={(e) => setFilter(e.target.value)}
                  className="text-sm border border-gray-300 rounded px-2 py-1 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  <option value="all">All Trades</option>
                  <option value="buy">Buy Orders</option>
                  <option value="sell">Sell Orders</option>
                  <option value="profitable">Profitable</option>
                  <option value="losses">Losses</option>
                </select>
              </div>
              <button className="flex items-center space-x-2 px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded transition-colors">
                <Download className="h-4 w-4" />
                <span>Export</span>
              </button>
            </div>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Time</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Pair</th>
                  <th className="text-center py-3 px-4 font-medium text-gray-600">Side</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-600">Amount</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-600">Price</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-600">Total</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-600">Fee</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-600">P&L</th>
                </tr>
              </thead>
              <tbody>
                {filteredTrades.map((trade) => {
                  const { date, time } = formatTime(trade.time)
                  return (
                    <tr key={trade.id} className="border-b last:border-b-0 hover:bg-gray-50">
                      <td className="py-3 px-4">
                        <div className="text-sm">
                          <div className="font-medium">{time}</div>
                          <div className="text-gray-600">{date}</div>
                        </div>
                      </td>
                      <td className="py-3 px-4 font-medium">{trade.symbol}</td>
                      <td className="py-3 px-4 text-center">
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                          trade.side === 'buy' 
                            ? 'bg-success-100 text-success-700' 
                            : 'bg-danger-100 text-danger-700'
                        }`}>
                          {trade.side === 'buy' ? (
                            <TrendingUp className="h-3 w-3 mr-1" />
                          ) : (
                            <TrendingDown className="h-3 w-3 mr-1" />
                          )}
                          {trade.side.toUpperCase()}
                        </span>
                      </td>
                      <td className="text-right py-3 px-4">{trade.amount.toLocaleString()}</td>
                      <td className="text-right py-3 px-4">${trade.price.toLocaleString()}</td>
                      <td className="text-right py-3 px-4 font-medium">${trade.total.toLocaleString()}</td>
                      <td className="text-right py-3 px-4 text-gray-600">${trade.fee.toFixed(2)}</td>
                      <td className={`text-right py-3 px-4 font-medium ${
                        trade.pnl >= 0 ? 'text-success-600' : 'text-danger-600'
                      }`}>
                        {trade.pnl >= 0 ? '+' : ''}${trade.pnl.toFixed(2)}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Recent Trades</h3>
        <Clock className="h-5 w-5 text-gray-400" />
      </div>
      
      <div className="space-y-3">
        {trades.slice(0, 5).map((trade) => {
          const { time } = formatTime(trade.time)
          return (
            <div key={trade.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className={`p-2 rounded-full ${
                  trade.side === 'buy' ? 'bg-success-100' : 'bg-danger-100'
                }`}>
                  {trade.side === 'buy' ? (
                    <TrendingUp className="h-4 w-4 text-success-600" />
                  ) : (
                    <TrendingDown className="h-4 w-4 text-danger-600" />
                  )}
                </div>
                <div>
                  <div className="font-medium">{trade.symbol}</div>
                  <div className="text-sm text-gray-600">
                    {trade.side.toUpperCase()} {trade.amount} @ ${trade.price.toLocaleString()}
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div className={`font-semibold ${
                  trade.pnl >= 0 ? 'text-success-600' : 'text-danger-600'
                }`}>
                  {trade.pnl >= 0 ? '+' : ''}${trade.pnl.toFixed(2)}
                </div>
                <div className="text-sm text-gray-600">{time}</div>
              </div>
            </div>
          )
        })}
      </div>
      
      <div className="mt-4 pt-4 border-t">
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Total P&L Today:</span>
          <span className={`font-semibold ${
            totalPnL >= 0 ? 'text-success-600' : 'text-danger-600'
          }`}>
            {totalPnL >= 0 ? '+' : ''}${totalPnL.toFixed(2)}
          </span>
        </div>
      </div>
    </div>
  )
}

export default RecentTrades