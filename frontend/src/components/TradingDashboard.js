import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import LiveTradeVisualization from './LiveTradeVisualization';
import PerformanceCharts from './PerformanceCharts';
import {
  Activity,
  TrendingUp,
  TrendingDown,
  DollarSign,
  BarChart3,
  Settings,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  XCircle,
  Clock,
  Target,
  Zap
} from 'lucide-react';

const TradingDashboard = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [portfolioData, setPortfolioData] = useState({
    totalValue: 50000,
    dailyPnL: 1250.50,
    dailyPnLPercent: 2.56,
    totalPnL: 8750.25,
    totalPnLPercent: 21.25,
    availableBalance: 12500.75,
    marginUsed: 37499.25,
    marginLevel: 133.33
  });
  
  const [systemStatus, setSystemStatus] = useState({
    tradingEngine: 'active',
    dataFeed: 'active',
    riskManager: 'active',
    orderManager: 'active',
    notifications: 'active'
  });
  
  const [activePositions, setActivePositions] = useState([
    {
      id: 1,
      symbol: 'BTC/USDT',
      side: 'long',
      size: 0.5,
      entryPrice: 45250.00,
      currentPrice: 46100.00,
      pnl: 425.00,
      pnlPercent: 1.88,
      timestamp: Date.now() - 3600000
    },
    {
      id: 2,
      symbol: 'ETH/USDT',
      side: 'short',
      size: 2.0,
      entryPrice: 3150.00,
      currentPrice: 3095.00,
      pnl: 110.00,
      pnlPercent: 1.75,
      timestamp: Date.now() - 1800000
    },
    {
      id: 3,
      symbol: 'ADA/USDT',
      side: 'long',
      size: 1000,
      entryPrice: 0.485,
      currentPrice: 0.492,
      pnl: 7.00,
      pnlPercent: 1.44,
      timestamp: Date.now() - 900000
    }
  ]);
  
  const [recentTrades, setRecentTrades] = useState([
    {
      id: 1,
      symbol: 'BTC/USDT',
      side: 'buy',
      amount: 0.25,
      price: 45800.00,
      total: 11450.00,
      timestamp: Date.now() - 300000,
      status: 'filled'
    },
    {
      id: 2,
      symbol: 'ETH/USDT',
      side: 'sell',
      amount: 1.5,
      price: 3120.00,
      total: 4680.00,
      timestamp: Date.now() - 600000,
      status: 'filled'
    },
    {
      id: 3,
      symbol: 'SOL/USDT',
      side: 'buy',
      amount: 10,
      price: 98.50,
      total: 985.00,
      timestamp: Date.now() - 900000,
      status: 'partial'
    }
  ]);
  
  const [performanceData, setPerformanceData] = useState([]);
  
  useEffect(() => {
    // Simulate WebSocket connection
    const connectWebSocket = () => {
      setIsConnected(true);
      
      // Simulate real-time data updates
      const interval = setInterval(() => {
        // Update portfolio data
        setPortfolioData(prev => ({
          ...prev,
          totalValue: prev.totalValue + (Math.random() - 0.5) * 100,
          dailyPnL: prev.dailyPnL + (Math.random() - 0.5) * 50
        }));
        
        // Update performance data
        const newDataPoint = {
          timestamp: Date.now(),
          portfolio_value: portfolioData.totalValue,
          daily_pnl: (Math.random() - 0.5) * 200,
          daily_return: (Math.random() - 0.5) * 0.05,
          cumulative_return: Math.random() * 0.3,
          drawdown: -Math.random() * 0.1,
          volume: Math.random() * 10000,
          benchmark_value: portfolioData.totalValue * 0.95,
          unrealized_pnl: (Math.random() - 0.5) * 500,
          realized_pnl: (Math.random() - 0.5) * 300,
          rolling_volatility: Math.random() * 0.02,
          market_return: (Math.random() - 0.5) * 0.03,
          portfolio_return: (Math.random() - 0.5) * 0.04
        };
        
        setPerformanceData(prev => [...prev.slice(-99), newDataPoint]);
      }, 5000);
      
      return () => clearInterval(interval);
    };
    
    const cleanup = connectWebSocket();
    return cleanup;
  }, []);
  
  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(value);
  };
  
  const formatPercentage = (value) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };
  
  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };
  
  const getStatusIcon = (status) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'warning':
        return <AlertCircle className="h-4 w-4 text-yellow-500" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };
  
  const StatusCard = ({ title, value, change, icon: Icon, color = 'text-gray-900' }) => (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600">{title}</p>
            <p className={`text-xl font-bold ${color}`}>{value}</p>
            {change !== undefined && (
              <div className="flex items-center mt-1">
                {change >= 0 ? (
                  <TrendingUp className="h-3 w-3 text-green-500 mr-1" />
                ) : (
                  <TrendingDown className="h-3 w-3 text-red-500 mr-1" />
                )}
                <span className={`text-xs ${change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatPercentage(Math.abs(change))}
                </span>
              </div>
            )}
          </div>
          <Icon className="h-6 w-6 text-gray-400" />
        </div>
      </CardContent>
    </Card>
  );
  
  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-4">
          <h1 className="text-3xl font-bold text-gray-900">Trading Dashboard</h1>
          <Badge variant={isConnected ? 'default' : 'destructive'} className="flex items-center">
            <div className={`h-2 w-2 rounded-full mr-2 ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
            {isConnected ? 'Connected' : 'Disconnected'}
          </Badge>
        </div>
        
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button variant="outline" size="sm">
            <Settings className="h-4 w-4 mr-2" />
            Settings
          </Button>
        </div>
      </div>
      
      {/* Portfolio Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        <StatusCard
          title="Portfolio Value"
          value={formatCurrency(portfolioData.totalValue)}
          change={portfolioData.dailyPnLPercent}
          icon={DollarSign}
          color="text-blue-600"
        />
        <StatusCard
          title="Daily P&L"
          value={formatCurrency(portfolioData.dailyPnL)}
          change={portfolioData.dailyPnLPercent}
          icon={TrendingUp}
          color={portfolioData.dailyPnL >= 0 ? 'text-green-600' : 'text-red-600'}
        />
        <StatusCard
          title="Total P&L"
          value={formatCurrency(portfolioData.totalPnL)}
          change={portfolioData.totalPnLPercent}
          icon={BarChart3}
          color={portfolioData.totalPnL >= 0 ? 'text-green-600' : 'text-red-600'}
        />
        <StatusCard
          title="Available Balance"
          value={formatCurrency(portfolioData.availableBalance)}
          icon={Target}
          color="text-purple-600"
        />
      </div>
      
      {/* System Status */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center">
            <Activity className="h-5 w-5 mr-2" />
            System Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {Object.entries(systemStatus).map(([key, status]) => (
              <div key={key} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="text-sm font-medium text-gray-900 capitalize">
                    {key.replace(/([A-Z])/g, ' $1').trim()}
                  </p>
                  <p className={`text-xs ${status === 'active' ? 'text-green-600' : status === 'warning' ? 'text-yellow-600' : 'text-red-600'}`}>
                    {status.toUpperCase()}
                  </p>
                </div>
                {getStatusIcon(status)}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
      
      {/* Main Content Tabs */}
      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="positions">Positions</TabsTrigger>
          <TabsTrigger value="trades">Recent Trades</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>
        
        <TabsContent value="overview">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <LiveTradeVisualization />
            <Card>
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  <Button className="h-12">
                    <Zap className="h-4 w-4 mr-2" />
                    Start Bot
                  </Button>
                  <Button variant="outline" className="h-12">
                    <Settings className="h-4 w-4 mr-2" />
                    Configure
                  </Button>
                  <Button variant="outline" className="h-12">
                    <BarChart3 className="h-4 w-4 mr-2" />
                    Backtest
                  </Button>
                  <Button variant="outline" className="h-12">
                    <Activity className="h-4 w-4 mr-2" />
                    Monitor
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
        
        <TabsContent value="positions">
          <Card>
            <CardHeader>
              <CardTitle>Active Positions ({activePositions.length})</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-2">Symbol</th>
                      <th className="text-left p-2">Side</th>
                      <th className="text-right p-2">Size</th>
                      <th className="text-right p-2">Entry Price</th>
                      <th className="text-right p-2">Current Price</th>
                      <th className="text-right p-2">P&L</th>
                      <th className="text-right p-2">P&L %</th>
                      <th className="text-left p-2">Time</th>
                    </tr>
                  </thead>
                  <tbody>
                    {activePositions.map((position) => (
                      <tr key={position.id} className="border-b hover:bg-gray-50">
                        <td className="p-2 font-medium">{position.symbol}</td>
                        <td className="p-2">
                          <Badge variant={position.side === 'long' ? 'default' : 'destructive'}>
                            {position.side.toUpperCase()}
                          </Badge>
                        </td>
                        <td className="p-2 text-right">{position.size}</td>
                        <td className="p-2 text-right">{formatCurrency(position.entryPrice)}</td>
                        <td className="p-2 text-right">{formatCurrency(position.currentPrice)}</td>
                        <td className={`p-2 text-right font-medium ${position.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {formatCurrency(position.pnl)}
                        </td>
                        <td className={`p-2 text-right font-medium ${position.pnlPercent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {formatPercentage(position.pnlPercent)}
                        </td>
                        <td className="p-2 text-sm text-gray-500">{formatTime(position.timestamp)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="trades">
          <Card>
            <CardHeader>
              <CardTitle>Recent Trades</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-2">Symbol</th>
                      <th className="text-left p-2">Side</th>
                      <th className="text-right p-2">Amount</th>
                      <th className="text-right p-2">Price</th>
                      <th className="text-right p-2">Total</th>
                      <th className="text-left p-2">Status</th>
                      <th className="text-left p-2">Time</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recentTrades.map((trade) => (
                      <tr key={trade.id} className="border-b hover:bg-gray-50">
                        <td className="p-2 font-medium">{trade.symbol}</td>
                        <td className="p-2">
                          <Badge variant={trade.side === 'buy' ? 'default' : 'destructive'}>
                            {trade.side.toUpperCase()}
                          </Badge>
                        </td>
                        <td className="p-2 text-right">{trade.amount}</td>
                        <td className="p-2 text-right">{formatCurrency(trade.price)}</td>
                        <td className="p-2 text-right font-medium">{formatCurrency(trade.total)}</td>
                        <td className="p-2">
                          <Badge 
                            variant={trade.status === 'filled' ? 'default' : trade.status === 'partial' ? 'secondary' : 'destructive'}
                          >
                            {trade.status.toUpperCase()}
                          </Badge>
                        </td>
                        <td className="p-2 text-sm text-gray-500">{formatTime(trade.timestamp)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="analytics">
          <PerformanceCharts 
            data={performanceData} 
            timeframe="1h" 
            isRealTime={isConnected}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default TradingDashboard;