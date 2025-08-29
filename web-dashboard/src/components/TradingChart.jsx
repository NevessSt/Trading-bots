import { useEffect, useRef, useState } from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'
import { Line } from 'react-chartjs-2'
import { TrendingUp, TrendingDown } from 'lucide-react'
import demoDataService from '../services/demoDataService'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

const TradingChart = ({ mode = 'demo' }) => {
  const [timeframe, setTimeframe] = useState('1H')
  const [symbol, setSymbol] = useState('BTC/USD')
  const [chartData, setChartData] = useState({
    labels: [],
    datasets: []
  })
  const [currentPrice, setCurrentPrice] = useState(43250.75)
  const [priceChange, setPriceChange] = useState(1.23)
  const [marketData, setMarketData] = useState([])

  // Generate sample data
  useEffect(() => {
    if (mode === 'demo') {
      loadDemoData()
      const interval = setInterval(loadDemoData, 5000) // Update every 5 seconds
      return () => clearInterval(interval)
    } else {
      generateData()
      const interval = setInterval(generateData, 5000)
      return () => clearInterval(interval)
    }
  }, [timeframe, symbol, mode])

  const loadDemoData = () => {
    const data = demoDataService.getMarketData()
    setMarketData(data)
    
    // Find current symbol data
    const symbolData = data.find(item => item.symbol === symbol.replace('/', ''))
    if (symbolData) {
      setCurrentPrice(symbolData.price)
      setPriceChange(symbolData.change24h)
    }
    
    // Generate chart data for the symbol
    const chartHistory = demoDataService.getChartData(symbol.replace('/', ''), timeframe)
    
    setChartData({
      labels: chartHistory.labels,
      datasets: [
        {
          label: symbol,
          data: chartHistory.prices,
          borderColor: symbolData?.change24h >= 0 ? '#10b981' : '#ef4444',
          backgroundColor: symbolData?.change24h >= 0 ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
          borderWidth: 2,
          fill: true,
          tension: 0.4,
          pointRadius: 0,
          pointHoverRadius: 6,
        }
      ]
    })
  }

  const generateData = () => {
    const now = new Date()
    const labels = []
    const prices = []
    let basePrice = 43000

    for (let i = 23; i >= 0; i--) {
      const time = new Date(now.getTime() - i * 60 * 60 * 1000)
      labels.push(time.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit' 
      }))
      
      basePrice += (Math.random() - 0.5) * 500
      prices.push(basePrice)
    }

    setCurrentPrice(prices[prices.length - 1])
    setPriceChange(((prices[prices.length - 1] - prices[0]) / prices[0]) * 100)

    setChartData({
      labels,
      datasets: [
        {
          label: symbol,
          data: prices,
          borderColor: priceChange >= 0 ? '#10b981' : '#ef4444',
          backgroundColor: priceChange >= 0 ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
          borderWidth: 2,
          fill: true,
          tension: 0.4,
          pointRadius: 0,
          pointHoverRadius: 6,
        }
      ]
    })
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#fff',
        bodyColor: '#fff',
        borderColor: '#374151',
        borderWidth: 1,
      }
    },
    scales: {
      x: {
        display: true,
        grid: {
          display: false
        },
        ticks: {
          color: '#6b7280',
          maxTicksLimit: 8
        }
      },
      y: {
        display: true,
        position: 'right',
        grid: {
          color: '#f3f4f6',
          drawBorder: false
        },
        ticks: {
          color: '#6b7280',
          callback: function(value) {
            return '$' + value.toLocaleString()
          }
        }
      }
    },
    interaction: {
      mode: 'nearest',
      axis: 'x',
      intersect: false
    },
    elements: {
      point: {
        hoverBackgroundColor: '#fff',
        hoverBorderWidth: 2
      }
    }
  }

  const timeframes = ['1M', '5M', '15M', '1H', '4H', '1D']
  const symbols = ['BTC/USD', 'ETH/USD', 'ADA/USD', 'DOT/USD', 'LINK/USD']

  return (
    <div className="card">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6">
        <div className="mb-4 sm:mb-0">
          <div className="flex items-center space-x-4">
            <select 
              value={symbol} 
              onChange={(e) => setSymbol(e.target.value)}
              className="text-lg font-semibold bg-transparent border-none focus:ring-0 p-0"
            >
              {symbols.map(s => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
            <div className={`flex items-center space-x-1 ${
              priceChange >= 0 ? 'text-success-600' : 'text-danger-600'
            }`}>
              {priceChange >= 0 ? (
                <TrendingUp className="h-4 w-4" />
              ) : (
                <TrendingDown className="h-4 w-4" />
              )}
              <span className="text-sm font-medium">
                {priceChange >= 0 ? '+' : ''}{priceChange.toFixed(2)}%
              </span>
            </div>
          </div>
          <div className="text-2xl font-bold text-gray-900 mt-1">
            ${currentPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
        </div>
        
        <div className="flex space-x-1">
          {timeframes.map(tf => (
            <button
              key={tf}
              onClick={() => setTimeframe(tf)}
              className={`px-3 py-1 text-sm font-medium rounded transition-colors ${
                timeframe === tf
                  ? 'bg-primary-100 text-primary-700'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              }`}
            >
              {tf}
            </button>
          ))}
        </div>
      </div>
      
      <div className="h-80">
        <Line data={chartData} options={options} />
      </div>
      
      <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
        <div>
          <span className="text-gray-600">24h High</span>
          <div className="font-semibold">${(currentPrice * 1.05).toLocaleString()}</div>
        </div>
        <div>
          <span className="text-gray-600">24h Low</span>
          <div className="font-semibold">${(currentPrice * 0.95).toLocaleString()}</div>
        </div>
        <div>
          <span className="text-gray-600">Volume</span>
          <div className="font-semibold">$2.4B</div>
        </div>
        <div>
          <span className="text-gray-600">Market Cap</span>
          <div className="font-semibold">$847B</div>
        </div>
      </div>
    </div>
  )
}

export default TradingChart