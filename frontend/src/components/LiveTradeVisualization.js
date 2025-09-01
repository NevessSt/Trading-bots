import React, { useState, useEffect, useRef } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import {
  TrendingUp,
  TrendingDown,
  Activity,
  DollarSign,
  BarChart3,
  PieChart as PieChartIcon,
  RefreshCw,
  Play,
  Pause,
  AlertTriangle,
  CheckCircle
} from 'lucide-react';

const LiveTradeVisualization = () => {
  const [trades, setTrades] = useState([]);
  const [performanceData, setPerformanceData] = useState([]);
  const [portfolioData, setPortfolioData] = useState([]);
  const [isLive, setIsLive] = useState(true);
  const [selectedTimeframe, setSelectedTimeframe] = useState('1h');
  const [stats, setStats] = useState({
    totalPnL: 0,
    winRate: 0,
    totalTrades: 0,
    activePositions: 0,
    dailyReturn: 0,
    sharpeRatio: 0
  });
  const wsRef = useRef(null);
  const intervalRef = useRef(null);

  // Colors for charts
  const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#8dd1e1', '#d084d0'];
  const PROFIT_COLOR = '#10b981';
  const LOSS_COLOR = '#ef4444';

  useEffect(() => {
    // Initialize WebSocket connection for real-time data
    if (isLive) {
      connectWebSocket();
    } else {
      disconnectWebSocket();
    }

    // Fetch initial data
    fetchTradeData();
    fetchPerformanceData();
    fetchPortfolioData();

    // Set up polling for updates
    intervalRef.current = setInterval(() => {
      if (!isLive) {
        fetchTradeData();
        fetchPerformanceData();
        fetchPortfolioData();
      }
    }, 5000);

    return () => {
      disconnectWebSocket();
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isLive, selectedTimeframe]);

  const connectWebSocket = () => {
    try {
      wsRef.current = new WebSocket('ws://localhost:5000/ws/trades');
      
      wsRef.current.onopen = () => {
        console.log('WebSocket connected for live trade data');
      };

      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleRealtimeUpdate(data);
      };

      wsRef.current.onclose = () => {
        console.log('WebSocket disconnected');
        // Attempt to reconnect after 3 seconds
        setTimeout(() => {
          if (isLive) {
            connectWebSocket();
          }
        }, 3000);
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
    }
  };

  const disconnectWebSocket = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  };

  const handleRealtimeUpdate = (data) => {
    switch (data.type) {
      case 'new_trade':
        setTrades(prev => [data.trade, ...prev.slice(0, 99)]); // Keep last 100 trades
        updateStats(data.trade);
        break;
      case 'performance_update':
        setPerformanceData(prev => [...prev, data.performance].slice(-100));
        break;
      case 'portfolio_update':
        setPortfolioData(data.portfolio);
        break;
      default:
        break;
    }
  };

  const fetchTradeData = async () => {
    try {
      const response = await fetch(`/api/trades?timeframe=${selectedTimeframe}&limit=100`);
      const data = await response.json();
      setTrades(data.trades || []);
      setStats(data.stats || stats);
    } catch (error) {
      console.error('Failed to fetch trade data:', error);
    }
  };

  const fetchPerformanceData = async () => {
    try {
      const response = await fetch(`/api/performance?timeframe=${selectedTimeframe}`);
      const data = await response.json();
      setPerformanceData(data.performance || []);
    } catch (error) {
      console.error('Failed to fetch performance data:', error);
    }
  };

  const fetchPortfolioData = async () => {
    try {
      const response = await fetch('/api/portfolio');
      const data = await response.json();
      setPortfolioData(data.portfolio || []);
    } catch (error) {
      console.error('Failed to fetch portfolio data:', error);
    }
  };

  const updateStats = (newTrade) => {
    setStats(prev => ({
      ...prev,
      totalTrades: prev.totalTrades + 1,
      totalPnL: prev.totalPnL + (newTrade.pnl || 0)
    }));
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(value);
  };

  const formatPercentage = (value) => {
    return `${(value * 100).toFixed(2)}%`;
  };

  const getTradeStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'active':
        return 'bg-blue-100 text-blue-800';
      case 'cancelled':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const StatCard = ({ title, value, icon: Icon, trend, color = 'text-gray-900' }) => (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600">{title}</p>
            <p className={`text-2xl font-bold ${color}`}>{value}</p>
            {trend && (
              <div className="flex items-center mt-1">
                {trend > 0 ? (
                  <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
                ) : (
                  <TrendingDown className="h-4 w-4 text-red-500 mr-1" />
                )}
                <span className={`text-sm ${trend > 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatPercentage(Math.abs(trend))}
                </span>
              </div>
            )}
          </div>
          <Icon className="h-8 w-8 text-gray-400" />
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="space-y-6">
      {/* Header Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <h2 className="text-2xl font-bold text-gray-900">Live Trading Dashboard</h2>
          <div className="flex items-center space-x-2">
            <div className={`h-3 w-3 rounded-full ${isLive ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`} />
            <span className="text-sm text-gray-600">
              {isLive ? 'Live' : 'Paused'}
            </span>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <select
            value={selectedTimeframe}
            onChange={(e) => setSelectedTimeframe(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm"
          >
            <option value="5m">5 Minutes</option>
            <option value="15m">15 Minutes</option>
            <option value="1h">1 Hour</option>
            <option value="4h">4 Hours</option>
            <option value="1d">1 Day</option>
          </select>
          
          <Button
            variant={isLive ? "destructive" : "default"}
            size="sm"
            onClick={() => setIsLive(!isLive)}
          >
            {isLive ? <Pause className="h-4 w-4 mr-2" /> : <Play className="h-4 w-4 mr-2" />}
            {isLive ? 'Pause' : 'Resume'}
          </Button>
          
          <Button variant="outline" size="sm" onClick={fetchTradeData}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total P&L"
          value={formatCurrency(stats.totalPnL)}
          icon={DollarSign}
          trend={stats.dailyReturn}
          color={stats.totalPnL >= 0 ? 'text-green-600' : 'text-red-600'}
        />
        <StatCard
          title="Win Rate"
          value={formatPercentage(stats.winRate)}
          icon={Activity}
          color="text-blue-600"
        />
        <StatCard
          title="Total Trades"
          value={stats.totalTrades.toLocaleString()}
          icon={BarChart3}
        />
        <StatCard
          title="Active Positions"
          value={stats.activePositions}
          icon={PieChartIcon}
          color="text-purple-600"
        />
      </div>

      {/* Charts Section */}
      <Tabs defaultValue="performance" className="space-y-4">
        <TabsList>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="trades">Trade History</TabsTrigger>
          <TabsTrigger value="portfolio">Portfolio</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="performance" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Portfolio Performance</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <AreaChart data={performanceData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" />
                  <YAxis />
                  <Tooltip formatter={(value) => formatCurrency(value)} />
                  <Legend />
                  <Area
                    type="monotone"
                    dataKey="portfolio_value"
                    stroke={PROFIT_COLOR}
                    fill={PROFIT_COLOR}
                    fillOpacity={0.3}
                    name="Portfolio Value"
                  />
                  <Area
                    type="monotone"
                    dataKey="unrealized_pnl"
                    stroke={COLORS[1]}
                    fill={COLORS[1]}
                    fillOpacity={0.3}
                    name="Unrealized P&L"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="trades" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Recent Trades</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {trades.slice(0, 10).map((trade, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <div className={`h-3 w-3 rounded-full ${
                          trade.side === 'buy' ? 'bg-green-500' : 'bg-red-500'
                        }`} />
                        <div>
                          <p className="font-medium">{trade.symbol}</p>
                          <p className="text-sm text-gray-600">
                            {trade.side.toUpperCase()} {trade.quantity}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-medium">{formatCurrency(trade.price)}</p>
                        <Badge className={getTradeStatusColor(trade.status)}>
                          {trade.status}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>P&L Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={performanceData.slice(-20)}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" />
                    <YAxis />
                    <Tooltip formatter={(value) => formatCurrency(value)} />
                    <Bar
                      dataKey="daily_pnl"
                      fill={(entry) => entry.daily_pnl >= 0 ? PROFIT_COLOR : LOSS_COLOR}
                      name="Daily P&L"
                    />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="portfolio" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Asset Allocation</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={portfolioData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {portfolioData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value) => formatCurrency(value)} />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Position Details</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 max-h-80 overflow-y-auto">
                  {portfolioData.map((position, index) => (
                    <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                      <div>
                        <p className="font-medium">{position.symbol}</p>
                        <p className="text-sm text-gray-600">
                          {position.quantity} @ {formatCurrency(position.avg_price)}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="font-medium">{formatCurrency(position.market_value)}</p>
                        <p className={`text-sm ${
                          position.unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {formatCurrency(position.unrealized_pnl)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Risk Metrics</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium">Sharpe Ratio</span>
                    <span className="text-lg font-bold">{stats.sharpeRatio?.toFixed(2) || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium">Max Drawdown</span>
                    <span className="text-lg font-bold text-red-600">-5.2%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium">Volatility</span>
                    <span className="text-lg font-bold">12.4%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium">Beta</span>
                    <span className="text-lg font-bold">0.85</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>System Status</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Trading Engine</span>
                    <div className="flex items-center">
                      <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                      <span className="text-sm text-green-600">Active</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Market Data</span>
                    <div className="flex items-center">
                      <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                      <span className="text-sm text-green-600">Connected</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Risk Monitor</span>
                    <div className="flex items-center">
                      <AlertTriangle className="h-4 w-4 text-yellow-500 mr-2" />
                      <span className="text-sm text-yellow-600">Warning</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Database</span>
                    <div className="flex items-center">
                      <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                      <span className="text-sm text-green-600">Healthy</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default LiveTradeVisualization;