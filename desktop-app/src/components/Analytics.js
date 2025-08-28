import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Assessment,
  Timeline,
  ShowChart,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Cell,
} from 'recharts';

const Analytics = () => {
  const [timeframe, setTimeframe] = useState('7d');
  const [analyticsData, setAnalyticsData] = useState({
    performance: [],
    metrics: {},
    strategies: [],
    pairs: [],
    monthlyReturns: []
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalyticsData();
  }, [timeframe]);

  const fetchAnalyticsData = async () => {
    try {
      setLoading(true);
      
      // Mock analytics data
      const mockData = {
        performance: [
          { date: '2024-01-01', pnl: 0, cumulative: 100000 },
          { date: '2024-01-02', pnl: 1250, cumulative: 101250 },
          { date: '2024-01-03', pnl: -800, cumulative: 100450 },
          { date: '2024-01-04', pnl: 2100, cumulative: 102550 },
          { date: '2024-01-05', pnl: 1800, cumulative: 104350 },
          { date: '2024-01-06', pnl: -500, cumulative: 103850 },
          { date: '2024-01-07', pnl: 3200, cumulative: 107050 },
        ],
        metrics: {
          totalTrades: 247,
          winRate: 68.4,
          profitFactor: 2.34,
          sharpeRatio: 1.87,
          maxDrawdown: -8.2,
          avgWin: 1250.50,
          avgLoss: -680.25,
          largestWin: 4850.00,
          largestLoss: -2100.00,
          avgHoldTime: '4h 23m',
          totalPnL: 15430.50,
          totalPnLPercent: 15.43
        },
        strategies: [
          {
            name: 'Momentum Scalping',
            trades: 89,
            winRate: 72.1,
            pnl: 8950.25,
            pnlPercent: 8.95,
            status: 'active'
          },
          {
            name: 'Mean Reversion',
            trades: 67,
            winRate: 64.2,
            pnl: 4280.75,
            pnlPercent: 4.28,
            status: 'active'
          },
          {
            name: 'Breakout Trading',
            trades: 91,
            winRate: 69.2,
            pnl: 2199.50,
            pnlPercent: 2.20,
            status: 'paused'
          }
        ],
        pairs: [
          { pair: 'BTC/USDT', trades: 45, winRate: 71.1, pnl: 6850.25, volume: 125000 },
          { pair: 'ETH/USDT', trades: 38, winRate: 65.8, pnl: 4280.50, volume: 89000 },
          { pair: 'ADA/USDT', trades: 52, winRate: 69.2, pnl: 2890.75, volume: 67000 },
          { pair: 'SOL/USDT', trades: 31, winRate: 67.7, pnl: 1409.00, volume: 45000 }
        ],
        monthlyReturns: [
          { month: 'Jan', returns: 8.5, color: '#4caf50' },
          { month: 'Feb', returns: 12.3, color: '#4caf50' },
          { month: 'Mar', returns: -3.2, color: '#f44336' },
          { month: 'Apr', returns: 15.7, color: '#4caf50' },
          { month: 'May', returns: 9.1, color: '#4caf50' }
        ]
      };
      
      setAnalyticsData(mockData);
    } catch (error) {
      console.error('Failed to fetch analytics data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(amount);
  };

  const formatPercent = (percent) => {
    return `${percent >= 0 ? '+' : ''}${percent.toFixed(2)}%`;
  };

  const getPnLColor = (value) => {
    if (value > 0) return 'success.main';
    if (value < 0) return 'error.main';
    return 'text.primary';
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'success';
      case 'paused': return 'warning';
      case 'stopped': return 'error';
      default: return 'default';
    }
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" sx={{ fontWeight: 300 }}>
          Trading Analytics
        </Typography>
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>Timeframe</InputLabel>
          <Select
            value={timeframe}
            label="Timeframe"
            onChange={(e) => setTimeframe(e.target.value)}
          >
            <MenuItem value="1d">1 Day</MenuItem>
            <MenuItem value="7d">7 Days</MenuItem>
            <MenuItem value="30d">30 Days</MenuItem>
            <MenuItem value="90d">90 Days</MenuItem>
            <MenuItem value="1y">1 Year</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      <Grid container spacing={3}>
        {/* Key Metrics */}
        <Grid item xs={12} md={3}>
          <Card className="hover-card">
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Assessment sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">Total P&L</Typography>
              </Box>
              <Typography variant="h3" className="number-large" sx={{ mb: 1 }}>
                {formatCurrency(analyticsData.metrics.totalPnL || 0)}
              </Typography>
              <Typography 
                variant="h6" 
                sx={{ color: getPnLColor(analyticsData.metrics.totalPnLPercent || 0) }}
              >
                {formatPercent(analyticsData.metrics.totalPnLPercent || 0)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card className="hover-card">
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Timeline sx={{ mr: 1, color: 'success.main' }} />
                <Typography variant="h6">Win Rate</Typography>
              </Box>
              <Typography variant="h3" className="number-large" sx={{ mb: 1 }}>
                {(analyticsData.metrics.winRate || 0).toFixed(1)}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {analyticsData.metrics.totalTrades || 0} total trades
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card className="hover-card">
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <ShowChart sx={{ mr: 1, color: 'info.main' }} />
                <Typography variant="h6">Profit Factor</Typography>
              </Box>
              <Typography variant="h3" className="number-large" sx={{ mb: 1 }}>
                {(analyticsData.metrics.profitFactor || 0).toFixed(2)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Sharpe: {(analyticsData.metrics.sharpeRatio || 0).toFixed(2)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card className="hover-card">
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <TrendingDown sx={{ mr: 1, color: 'error.main' }} />
                <Typography variant="h6">Max Drawdown</Typography>
              </Box>
              <Typography variant="h3" className="number-large" sx={{ mb: 1, color: 'error.main' }}>
                {(analyticsData.metrics.maxDrawdown || 0).toFixed(1)}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Risk metric
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Performance Chart */}
        <Grid item xs={12} lg={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Cumulative P&L</Typography>
              <Box sx={{ height: 400 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={analyticsData.performance}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                    <XAxis 
                      dataKey="date" 
                      stroke="#b0bec5"
                      fontSize={12}
                    />
                    <YAxis 
                      stroke="#b0bec5"
                      fontSize={12}
                      tickFormatter={(value) => `$${(value/1000).toFixed(0)}k`}
                    />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: '#1e1e1e', 
                        border: '1px solid #333',
                        borderRadius: '8px'
                      }}
                      formatter={(value, name) => [
                        name === 'cumulative' ? formatCurrency(value) : formatCurrency(value),
                        name === 'cumulative' ? 'Portfolio Value' : 'Daily P&L'
                      ]}
                    />
                    <Line
                      type="monotone"
                      dataKey="cumulative"
                      stroke="#00d4ff"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Monthly Returns */}
        <Grid item xs={12} lg={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Monthly Returns</Typography>
              <Box sx={{ height: 400 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={analyticsData.monthlyReturns}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                    <XAxis 
                      dataKey="month" 
                      stroke="#b0bec5"
                      fontSize={12}
                    />
                    <YAxis 
                      stroke="#b0bec5"
                      fontSize={12}
                      tickFormatter={(value) => `${value}%`}
                    />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: '#1e1e1e', 
                        border: '1px solid #333',
                        borderRadius: '8px'
                      }}
                      formatter={(value) => [`${value}%`, 'Returns']}
                    />
                    <Bar
                      dataKey="returns"
                      fill={(entry) => entry.color}
                      radius={[4, 4, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Strategy Performance */}
        <Grid item xs={12} lg={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Strategy Performance</Typography>
              <TableContainer component={Paper} className="data-table">
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Strategy</TableCell>
                      <TableCell align="right">Trades</TableCell>
                      <TableCell align="right">Win Rate</TableCell>
                      <TableCell align="right">P&L</TableCell>
                      <TableCell align="center">Status</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {analyticsData.strategies.map((strategy, index) => (
                      <TableRow key={index}>
                        <TableCell>
                          <Typography variant="subtitle2">{strategy.name}</Typography>
                        </TableCell>
                        <TableCell align="right">{strategy.trades}</TableCell>
                        <TableCell align="right">{strategy.winRate.toFixed(1)}%</TableCell>
                        <TableCell align="right">
                          <Typography sx={{ color: getPnLColor(strategy.pnl) }}>
                            {formatCurrency(strategy.pnl)}
                          </Typography>
                        </TableCell>
                        <TableCell align="center">
                          <Chip 
                            label={strategy.status} 
                            color={getStatusColor(strategy.status)}
                            size="small"
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Trading Pairs Performance */}
        <Grid item xs={12} lg={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Top Trading Pairs</Typography>
              <TableContainer component={Paper} className="data-table">
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Pair</TableCell>
                      <TableCell align="right">Trades</TableCell>
                      <TableCell align="right">Win Rate</TableCell>
                      <TableCell align="right">P&L</TableCell>
                      <TableCell align="right">Volume</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {analyticsData.pairs.map((pair, index) => (
                      <TableRow key={index}>
                        <TableCell>
                          <Typography variant="subtitle2" className="trading-pair">
                            {pair.pair}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">{pair.trades}</TableCell>
                        <TableCell align="right">{pair.winRate.toFixed(1)}%</TableCell>
                        <TableCell align="right">
                          <Typography sx={{ color: getPnLColor(pair.pnl) }}>
                            {formatCurrency(pair.pnl)}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          {formatCurrency(pair.volume)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Additional Metrics */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Detailed Metrics</Typography>
              <Grid container spacing={2}>
                <Grid item xs={6} md={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h5" className="number-large">
                      {formatCurrency(analyticsData.metrics.avgWin || 0)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Average Win
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h5" className="number-large" sx={{ color: 'error.main' }}>
                      {formatCurrency(analyticsData.metrics.avgLoss || 0)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Average Loss
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h5" className="number-large">
                      {formatCurrency(analyticsData.metrics.largestWin || 0)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Largest Win
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h5" className="number-large">
                      {analyticsData.metrics.avgHoldTime || 'N/A'}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Avg Hold Time
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Analytics;