import React, { useState, useEffect, useMemo } from 'react';
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
  ScatterChart,
  Scatter,
  ComposedChart,
  ReferenceLine
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Badge } from './ui/badge';
import {
  TrendingUp,
  TrendingDown,
  BarChart3,
  Activity,
  Target,
  AlertCircle,
  Download,
  Settings,
  Maximize2
} from 'lucide-react';

const PerformanceCharts = ({ data, timeframe = '1d', isRealTime = false }) => {
  const [selectedMetric, setSelectedMetric] = useState('portfolio_value');
  const [showBenchmark, setShowBenchmark] = useState(true);
  const [chartType, setChartType] = useState('line');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [performanceData, setPerformanceData] = useState([]);
  const [analytics, setAnalytics] = useState({});

  // Chart colors
  const COLORS = {
    primary: '#3b82f6',
    success: '#10b981',
    danger: '#ef4444',
    warning: '#f59e0b',
    info: '#06b6d4',
    purple: '#8b5cf6',
    benchmark: '#6b7280'
  };

  useEffect(() => {
    if (data && data.length > 0) {
      setPerformanceData(data);
      calculateAnalytics(data);
    }
  }, [data]);

  const calculateAnalytics = (data) => {
    if (!data || data.length === 0) return;

    const returns = data.map((d, i) => {
      if (i === 0) return 0;
      return (d.portfolio_value - data[i - 1].portfolio_value) / data[i - 1].portfolio_value;
    }).filter(r => r !== 0);

    const totalReturn = data.length > 0 ? 
      (data[data.length - 1].portfolio_value - data[0].portfolio_value) / data[0].portfolio_value : 0;

    const avgReturn = returns.reduce((sum, r) => sum + r, 0) / returns.length;
    const volatility = Math.sqrt(
      returns.reduce((sum, r) => sum + Math.pow(r - avgReturn, 2), 0) / returns.length
    );

    const sharpeRatio = volatility !== 0 ? avgReturn / volatility : 0;

    // Calculate maximum drawdown
    let maxDrawdown = 0;
    let peak = data[0]?.portfolio_value || 0;
    
    data.forEach(point => {
      if (point.portfolio_value > peak) {
        peak = point.portfolio_value;
      }
      const drawdown = (peak - point.portfolio_value) / peak;
      if (drawdown > maxDrawdown) {
        maxDrawdown = drawdown;
      }
    });

    // Win rate calculation
    const profitableTrades = returns.filter(r => r > 0).length;
    const winRate = returns.length > 0 ? profitableTrades / returns.length : 0;

    setAnalytics({
      totalReturn,
      avgReturn,
      volatility,
      sharpeRatio,
      maxDrawdown,
      winRate,
      totalTrades: returns.length,
      profitableTrades
    });
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

  const formatDate = (timestamp) => {
    return new Date(timestamp).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: timeframe.includes('h') || timeframe.includes('m') ? '2-digit' : undefined,
      minute: timeframe.includes('m') ? '2-digit' : undefined
    });
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-medium text-gray-900">{formatDate(label)}</p>
          {payload.map((entry, index) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {entry.name.includes('value') || entry.name.includes('pnl') ? 
                formatCurrency(entry.value) : formatPercentage(entry.value)}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  const MetricCard = ({ title, value, change, icon: Icon, color = 'text-gray-900' }) => (
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

  const renderChart = () => {
    const chartProps = {
      data: performanceData,
      margin: { top: 5, right: 30, left: 20, bottom: 5 }
    };

    switch (chartType) {
      case 'area':
        return (
          <AreaChart {...chartProps}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis 
              dataKey="timestamp" 
              tickFormatter={formatDate}
              stroke="#6b7280"
            />
            <YAxis 
              tickFormatter={formatCurrency}
              stroke="#6b7280"
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Area
              type="monotone"
              dataKey={selectedMetric}
              stroke={COLORS.primary}
              fill={COLORS.primary}
              fillOpacity={0.3}
              strokeWidth={2}
              name="Portfolio Value"
            />
            {showBenchmark && (
              <Area
                type="monotone"
                dataKey="benchmark_value"
                stroke={COLORS.benchmark}
                fill={COLORS.benchmark}
                fillOpacity={0.1}
                strokeWidth={1}
                strokeDasharray="5 5"
                name="Benchmark"
              />
            )}
          </AreaChart>
        );

      case 'bar':
        return (
          <BarChart {...chartProps}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis 
              dataKey="timestamp" 
              tickFormatter={formatDate}
              stroke="#6b7280"
            />
            <YAxis 
              tickFormatter={formatCurrency}
              stroke="#6b7280"
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Bar
              dataKey="daily_pnl"
              fill={(entry) => entry?.daily_pnl >= 0 ? COLORS.success : COLORS.danger}
              name="Daily P&L"
            />
          </BarChart>
        );

      case 'composed':
        return (
          <ComposedChart {...chartProps}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis 
              dataKey="timestamp" 
              tickFormatter={formatDate}
              stroke="#6b7280"
            />
            <YAxis 
              yAxisId="left"
              tickFormatter={formatCurrency}
              stroke="#6b7280"
            />
            <YAxis 
              yAxisId="right"
              orientation="right"
              tickFormatter={formatPercentage}
              stroke="#6b7280"
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Area
              yAxisId="left"
              type="monotone"
              dataKey="portfolio_value"
              fill={COLORS.primary}
              fillOpacity={0.3}
              stroke={COLORS.primary}
              strokeWidth={2}
              name="Portfolio Value"
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="daily_return"
              stroke={COLORS.warning}
              strokeWidth={2}
              dot={false}
              name="Daily Return %"
            />
            <Bar
              yAxisId="left"
              dataKey="volume"
              fill={COLORS.info}
              fillOpacity={0.6}
              name="Volume"
            />
          </ComposedChart>
        );

      default: // line chart
        return (
          <LineChart {...chartProps}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis 
              dataKey="timestamp" 
              tickFormatter={formatDate}
              stroke="#6b7280"
            />
            <YAxis 
              tickFormatter={formatCurrency}
              stroke="#6b7280"
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Line
              type="monotone"
              dataKey={selectedMetric}
              stroke={COLORS.primary}
              strokeWidth={2}
              dot={false}
              name="Portfolio Value"
            />
            {showBenchmark && (
              <Line
                type="monotone"
                dataKey="benchmark_value"
                stroke={COLORS.benchmark}
                strokeWidth={1}
                strokeDasharray="5 5"
                dot={false}
                name="Benchmark"
              />
            )}
            <ReferenceLine 
              y={performanceData[0]?.portfolio_value || 0} 
              stroke={COLORS.benchmark} 
              strokeDasharray="2 2" 
              label="Initial Value"
            />
          </LineChart>
        );
    }
  };

  const downloadChart = () => {
    // Implementation for chart download
    console.log('Downloading chart...');
  };

  return (
    <div className={`space-y-6 ${isFullscreen ? 'fixed inset-0 z-50 bg-white p-6 overflow-auto' : ''}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <h3 className="text-xl font-bold text-gray-900">Performance Analytics</h3>
          {isRealTime && (
            <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
              <div className="h-2 w-2 bg-green-500 rounded-full mr-2 animate-pulse" />
              Live
            </Badge>
          )}
        </div>
        
        <div className="flex items-center space-x-2">
          <select
            value={selectedMetric}
            onChange={(e) => setSelectedMetric(e.target.value)}
            className="px-3 py-1 border border-gray-300 rounded text-sm"
          >
            <option value="portfolio_value">Portfolio Value</option>
            <option value="unrealized_pnl">Unrealized P&L</option>
            <option value="realized_pnl">Realized P&L</option>
            <option value="daily_return">Daily Return</option>
          </select>
          
          <select
            value={chartType}
            onChange={(e) => setChartType(e.target.value)}
            className="px-3 py-1 border border-gray-300 rounded text-sm"
          >
            <option value="line">Line Chart</option>
            <option value="area">Area Chart</option>
            <option value="bar">Bar Chart</option>
            <option value="composed">Combined</option>
          </select>
          
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowBenchmark(!showBenchmark)}
          >
            {showBenchmark ? 'Hide' : 'Show'} Benchmark
          </Button>
          
          <Button variant="outline" size="sm" onClick={downloadChart}>
            <Download className="h-4 w-4" />
          </Button>
          
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => setIsFullscreen(!isFullscreen)}
          >
            <Maximize2 className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Analytics Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <MetricCard
          title="Total Return"
          value={formatPercentage(analytics.totalReturn || 0)}
          change={analytics.totalReturn}
          icon={TrendingUp}
          color={analytics.totalReturn >= 0 ? 'text-green-600' : 'text-red-600'}
        />
        <MetricCard
          title="Sharpe Ratio"
          value={(analytics.sharpeRatio || 0).toFixed(2)}
          icon={Target}
          color="text-blue-600"
        />
        <MetricCard
          title="Max Drawdown"
          value={formatPercentage(analytics.maxDrawdown || 0)}
          icon={TrendingDown}
          color="text-red-600"
        />
        <MetricCard
          title="Win Rate"
          value={formatPercentage(analytics.winRate || 0)}
          icon={Activity}
          color="text-green-600"
        />
        <MetricCard
          title="Volatility"
          value={formatPercentage(analytics.volatility || 0)}
          icon={BarChart3}
          color="text-yellow-600"
        />
        <MetricCard
          title="Total Trades"
          value={(analytics.totalTrades || 0).toLocaleString()}
          icon={AlertCircle}
        />
      </div>

      {/* Main Chart */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Performance Chart</span>
            <div className="flex items-center space-x-2">
              <Button variant="ghost" size="sm">
                <Settings className="h-4 w-4" />
              </Button>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={isFullscreen ? 600 : 400}>
            {renderChart()}
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Additional Analytics */}
      <Tabs defaultValue="returns" className="space-y-4">
        <TabsList>
          <TabsTrigger value="returns">Returns Analysis</TabsTrigger>
          <TabsTrigger value="drawdown">Drawdown</TabsTrigger>
          <TabsTrigger value="correlation">Correlation</TabsTrigger>
          <TabsTrigger value="risk">Risk Metrics</TabsTrigger>
        </TabsList>

        <TabsContent value="returns">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Return Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={performanceData.slice(-30)}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" tickFormatter={formatDate} />
                    <YAxis tickFormatter={formatPercentage} />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar
                      dataKey="daily_return"
                      fill={(entry) => entry?.daily_return >= 0 ? COLORS.success : COLORS.danger}
                      name="Daily Return"
                    />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Cumulative Returns</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={performanceData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" tickFormatter={formatDate} />
                    <YAxis tickFormatter={formatPercentage} />
                    <Tooltip content={<CustomTooltip />} />
                    <Line
                      type="monotone"
                      dataKey="cumulative_return"
                      stroke={COLORS.primary}
                      strokeWidth={2}
                      dot={false}
                      name="Cumulative Return"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="drawdown">
          <Card>
            <CardHeader>
              <CardTitle>Drawdown Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <AreaChart data={performanceData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" tickFormatter={formatDate} />
                  <YAxis tickFormatter={formatPercentage} />
                  <Tooltip content={<CustomTooltip />} />
                  <Area
                    type="monotone"
                    dataKey="drawdown"
                    stroke={COLORS.danger}
                    fill={COLORS.danger}
                    fillOpacity={0.3}
                    name="Drawdown"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="correlation">
          <Card>
            <CardHeader>
              <CardTitle>Market Correlation</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <ScatterChart data={performanceData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="market_return" 
                    tickFormatter={formatPercentage}
                    name="Market Return"
                  />
                  <YAxis 
                    dataKey="portfolio_return" 
                    tickFormatter={formatPercentage}
                    name="Portfolio Return"
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Scatter 
                    dataKey="portfolio_return" 
                    fill={COLORS.primary}
                    name="Portfolio vs Market"
                  />
                </ScatterChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="risk">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Risk Metrics Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center py-2 border-b">
                    <span className="font-medium">Value at Risk (95%)</span>
                    <span className="text-red-600 font-bold">-2.3%</span>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b">
                    <span className="font-medium">Expected Shortfall</span>
                    <span className="text-red-600 font-bold">-3.8%</span>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b">
                    <span className="font-medium">Beta</span>
                    <span className="font-bold">0.85</span>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b">
                    <span className="font-medium">Alpha</span>
                    <span className="text-green-600 font-bold">2.1%</span>
                  </div>
                  <div className="flex justify-between items-center py-2">
                    <span className="font-medium">Information Ratio</span>
                    <span className="font-bold">1.24</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Rolling Volatility</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={performanceData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" tickFormatter={formatDate} />
                    <YAxis tickFormatter={formatPercentage} />
                    <Tooltip content={<CustomTooltip />} />
                    <Line
                      type="monotone"
                      dataKey="rolling_volatility"
                      stroke={COLORS.warning}
                      strokeWidth={2}
                      dot={false}
                      name="30-Day Rolling Volatility"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default PerformanceCharts;