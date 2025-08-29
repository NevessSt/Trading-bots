import { useState, useEffect } from 'react'
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  BarChart3, 
  Settings, 
  User, 
  Bell,
  Menu,
  X,
  Activity,
  Wallet,
  Target,
  Clock
} from 'lucide-react'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import TradingChart from './components/TradingChart'
import PortfolioOverview from './components/PortfolioOverview'
import TradingInterface from './components/TradingInterface'
import RecentTrades from './components/RecentTrades'
import MarketData from './components/MarketData'
import SetupWizardLauncher from './components/SetupWizardLauncher'
import DemoModeToggle from './components/DemoModeToggle'
import DemoBanner from './components/DemoBanner'
import demoDataService from './services/demoDataService'

// Create Material-UI theme
const muiTheme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    success: {
      main: '#2e7d32',
    },
    error: {
      main: '#d32f2f',
    },
    warning: {
      main: '#ed6c02',
    },
    info: {
      main: '#0288d1',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          borderRadius: 8,
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 6,
        },
      },
    },
  },
})

function App() {
  const [activeTab, setActiveTab] = useState('dashboard')
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [showSetupWizard, setShowSetupWizard] = useState(false)
  const [setupCompleted, setSetupCompleted] = useState(false)
  const [tradingMode, setTradingMode] = useState('demo')
  const [showDemoBanner, setShowDemoBanner] = useState(true)
  const [portfolioData, setPortfolioData] = useState(null)
  const [marketData, setMarketData] = useState([])
  const [recentTrades, setRecentTrades] = useState([])
  const [botMetrics, setBotMetrics] = useState(null)

  const navigation = [
    { id: 'dashboard', name: 'Dashboard', icon: BarChart3 },
    { id: 'trading', name: 'Trading', icon: TrendingUp },
    { id: 'portfolio', name: 'Portfolio', icon: Wallet },
    { id: 'history', name: 'History', icon: Clock },
    { id: 'settings', name: 'Settings', icon: Settings },
  ]

  // Initialize app on load
  useEffect(() => {
    const completed = localStorage.getItem('setupCompleted') === 'true'
    const skipped = localStorage.getItem('setupSkipped') === 'true'
    const savedMode = localStorage.getItem('tradingMode') || 'demo'
    const bannerDismissed = localStorage.getItem('demoBannerDismissed') === 'true'
    
    setSetupCompleted(completed)
    setTradingMode(savedMode)
    setShowDemoBanner(!bannerDismissed && savedMode === 'demo')
    
    // Show setup wizard if neither completed nor skipped
    if (!completed && !skipped) {
      setShowSetupWizard(true)
    }
    
    // Initialize data based on mode
    loadData(savedMode)
  }, [])

  // Load data based on current mode
  const loadData = (mode) => {
    if (mode === 'demo') {
      // Load demo data
      setPortfolioData(demoDataService.getPortfolioData())
      setMarketData(demoDataService.getMarketData())
      setRecentTrades(demoDataService.getRecentTrades())
      setBotMetrics(demoDataService.getBotMetrics())
    } else {
      // Load live data (would connect to real APIs)
      // For now, we'll use demo data as fallback
      setPortfolioData(demoDataService.getPortfolioData())
      setMarketData(demoDataService.getMarketData())
      setRecentTrades(demoDataService.getRecentTrades())
      setBotMetrics(demoDataService.getBotMetrics())
    }
  }

  // Real-time data updates
  useEffect(() => {
    const interval = setInterval(() => {
      if (tradingMode === 'demo') {
        setPortfolioData(demoDataService.getPortfolioData())
        setMarketData(demoDataService.getMarketData())
        setRecentTrades(demoDataService.getRecentTrades())
        setBotMetrics(demoDataService.getBotMetrics())
      }
    }, 5000)

    return () => clearInterval(interval)
  }, [tradingMode])

  const handleSetupComplete = (config) => {
    setSetupCompleted(true)
    setShowSetupWizard(false)
    // You can use the config data here to initialize the app with user settings
    console.log('Setup completed with config:', config)
  }

  const handleSetupSkip = () => {
    setShowSetupWizard(false)
  }

  const handleModeChange = (newMode) => {
    setTradingMode(newMode)
    loadData(newMode)
    
    // Show demo banner when switching to demo mode
    if (newMode === 'demo') {
      setShowDemoBanner(true)
      localStorage.removeItem('demoBannerDismissed')
    } else {
      setShowDemoBanner(false)
    }
  }

  const handleDemoBannerDismiss = () => {
    setShowDemoBanner(false)
  }

  const handleSwitchToLive = () => {
    handleModeChange('live')
  }

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return (
          <div className="space-y-6">
            {/* Demo Banner */}
            {tradingMode === 'demo' && showDemoBanner && (
              <DemoBanner 
                onDismiss={handleDemoBannerDismiss}
                onSwitchToLive={handleSwitchToLive}
              />
            )}
            
            {/* Portfolio Overview */}
            <PortfolioOverview data={portfolioData} />
            
            {/* Market Data and Trading Chart */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <TradingChart data={chartData} />
              </div>
              <div>
                <MarketData data={marketData} />
              </div>
            </div>
            
            {/* Recent Trades */}
            <RecentTrades data={recentTrades} />
          </div>
        )
      case 'trading':
        return (
          <div className="space-y-6">
            {/* Demo Banner */}
            {tradingMode === 'demo' && showDemoBanner && (
              <DemoBanner 
                onDismiss={handleDemoBannerDismiss}
                onSwitchToLive={handleSwitchToLive}
              />
            )}
            
            <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
              <div className="xl:col-span-2">
                <TradingChart mode={tradingMode} />
              </div>
              <div>
                <TradingInterface mode={tradingMode} marketData={marketData} />
              </div>
            </div>
          </div>
        )
      case 'portfolio':
        return (
          <div className="space-y-6">
            {/* Demo Banner */}
            {tradingMode === 'demo' && showDemoBanner && (
              <DemoBanner 
                onDismiss={handleDemoBannerDismiss}
                onSwitchToLive={handleSwitchToLive}
              />
            )}
            
            <PortfolioOverview data={portfolioData} detailed={true} />
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="card">
                <h3 className="text-lg font-semibold mb-4">Asset Allocation</h3>
                <div className="space-y-3">
                  {portfolioData.positions.map((position, index) => (
                    <div key={index} className="flex justify-between items-center">
                      <span className="font-medium">{position.symbol}</span>
                      <div className="text-right">
                        <div className="font-semibold">${position.value.toLocaleString()}</div>
                        <div className={`text-sm ${
                          position.change >= 0 ? 'text-success-600' : 'text-danger-600'
                        }`}>
                          {position.change >= 0 ? '+' : ''}{position.change.toFixed(2)}%
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="card">
                <h3 className="text-lg font-semibold mb-4">Performance Metrics</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Total Return</span>
                    <span className="font-semibold text-success-600">+$12,430</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Win Rate</span>
                    <span className="font-semibold">68.5%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Sharpe Ratio</span>
                    <span className="font-semibold">1.42</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Max Drawdown</span>
                    <span className="font-semibold text-danger-600">-8.3%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )
      case 'history':
        return (
          <div className="space-y-6">
            {/* Demo Banner */}
            {tradingMode === 'demo' && showDemoBanner && (
              <DemoBanner 
                onDismiss={handleDemoBannerDismiss}
                onSwitchToLive={handleSwitchToLive}
              />
            )}
            
            <RecentTrades data={recentTrades} detailed={true} />
          </div>
        )
      case 'settings':
        return (
          <div className="space-y-6">
            <div className="card">
              <h3 className="text-lg font-semibold mb-4">Trading Mode</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div>
                    <h4 className="font-medium">Current Mode</h4>
                    <p className="text-sm text-gray-600">
                      {tradingMode === 'demo' ? 'Demo mode with simulated data' : 'Live trading with real money'}
                    </p>
                  </div>
                  <DemoModeToggle 
                    currentMode={tradingMode}
                    onModeChange={handleModeChange}
                  />
                </div>
              </div>
            </div>
            
            <SetupWizardLauncher 
              onSetupComplete={handleSetupComplete}
            />
            <div className="card">
              <h3 className="text-lg font-semibold mb-4">Trading Settings</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Risk Level</label>
                  <select className="input-field">
                    <option>Conservative</option>
                    <option>Moderate</option>
                    <option>Aggressive</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Max Position Size (%)</label>
                  <input type="number" className="input-field" defaultValue="10" />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Stop Loss (%)</label>
                  <input type="number" className="input-field" defaultValue="5" />
                </div>
              </div>
            </div>
            <div className="card">
              <h3 className="text-lg font-semibold mb-4">API Configuration</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Exchange</label>
                  <select className="input-field">
                    <option>Binance</option>
                    <option>Coinbase Pro</option>
                    <option>Kraken</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">API Key</label>
                  <input type="password" className="input-field" placeholder="Enter API key" />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Secret Key</label>
                  <input type="password" className="input-field" placeholder="Enter secret key" />
                </div>
                <button className="btn-primary">Save Configuration</button>
              </div>
            </div>
          </div>
        )
      default:
        return null
    }
  }

  // If setup wizard should be shown, render it full screen
  if (showSetupWizard) {
    return (
      <SetupWizardLauncher 
        onSetupComplete={handleSetupComplete}
        onSkip={handleSetupSkip}
      />
    )
  }

  return (
    <ThemeProvider theme={muiTheme}>
      <CssBaseline />
      <div className="min-h-screen bg-gray-50">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0 ${
        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
      }`}>
        <div className="flex items-center justify-between h-16 px-6 border-b">
          <h1 className="text-xl font-bold text-gray-900">Trading Bot Pro</h1>
          <button 
            className="lg:hidden"
            onClick={() => setSidebarOpen(false)}
          >
            <X className="h-6 w-6" />
          </button>
        </div>
        <nav className="mt-6 px-3">
          {navigation.map((item) => {
            const Icon = item.icon
            return (
              <button
                key={item.id}
                onClick={() => {
                  setActiveTab(item.id)
                  setSidebarOpen(false)
                }}
                className={`w-full flex items-center px-3 py-2 mb-1 rounded-lg text-left transition-colors ${
                  activeTab === item.id
                    ? 'bg-primary-100 text-primary-700'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
              >
                <Icon className="h-5 w-5 mr-3" />
                {item.name}
              </button>
            )
          })}
        </nav>
      </div>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Top bar */}
        <div className="bg-white shadow-sm border-b px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <button
                className="lg:hidden mr-4"
                onClick={() => setSidebarOpen(true)}
              >
                <Menu className="h-6 w-6" />
              </button>
              <h2 className="text-2xl font-semibold text-gray-900 capitalize">
                {activeTab}
              </h2>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 text-sm">
                <Activity className="h-4 w-4 text-success-500" />
                <span className="text-gray-600">Bot Status:</span>
                <span className="font-medium text-success-600">Active</span>
              </div>
              <DemoModeToggle 
                currentMode={tradingMode}
                onModeChange={handleModeChange}
              />
              <button className="p-2 text-gray-400 hover:text-gray-600">
                <Bell className="h-5 w-5" />
              </button>
              <button className="p-2 text-gray-400 hover:text-gray-600">
                <User className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>

        {/* Page content */}
        <main className="p-6">
          {renderContent()}
        </main>
      </div>
      </div>
    </ThemeProvider>
  )
}

export default App
