import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  LinearProgress,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  AccountBalance,
  ShowChart,
  Speed,
  Refresh,
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer, AreaChart, Area } from 'recharts';

const Dashboard = () => {
  const [dashboardData, setDashboardData] = useState({
    portfolio: {
      totalValue: 0,
      dailyPnL: 0,
      dailyPnLPercent: 0,
      availableBalance: 0,
      positions: 0
    },
    performance: {
      totalTrades: 0,
      winRate: 0,
      profitFactor: 0,
      sharpeRatio: 0
    },
    activeStrategies: [],
    recentTrades: [],
    priceData: []
  });
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Mock data - replace with actual API calls
      const mockData = {
        portfolio: {
          totalValue: 125430.50,
          dailyPnL: 2340.75,
          dailyPnLPercent: 1.89,
          availableBalance: 15230.25,
          positions: 8
        },
        performance: {
          totalTrades: 1247,
          winRate: 68.5,
          profitFactor: 1.85,
          sharpeRatio: 2.34
        },
        activeStrategies: [
          { name: 'Grid Trading', status: 'active', pnl: 1250.30, trades: 45 },
          { name: 'DCA Bot', status: 'active', pnl: 890.45, trades: 23 },
          { name: 'Arbitrage', status: 'paused', pnl: 200.00, trades: 12 }
        ],
        recentTrades: [
          { id: 1, pair: 'BTC/USDT', side: 'BUY', amount: 0.025, price: 43250.00, time: '14:32:15', pnl: 125.50 },
          { id: 2, pair: 'ETH/USDT', side: 'SELL', amount: 1.5, price: 2680.50, time: '14:28:42', pnl: -45.20 },
          { id: 3, pair: 'BTC/USDT', side: 'SELL', amount: 0.015, price: 43180.00, time: '14:25:33', pnl: 89.30 },
          { id: 4, pair: 'ADA/USDT', side: 'BUY', amount: 1000, price: 0.485, time: '14:22:18', pnl: 23.45 },
          { id: 5, pair: 'SOL/USDT', side: 'BUY', amount: 5, price: 98.75, time: '14:18:55', pnl: 67.80 }
        ],
        priceData: generateMockPriceData()
      };
      
      setDashboardData(mockData);
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateMockPriceData = () => {
    const data = [];
    const now = new Date();
    for (let i = 23; i >= 0; i--) {
      const time = new Date(now.getTime() - i * 60 * 60 * 1000);
      data.push({
        time: time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
        value: 125000 + Math.random() * 5000 - 2500,
        pnl: Math.random() * 1000 - 500
      });
    }
    return data;
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

  return (
    <Box sx={{ flexGrow: 1 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" sx={{ fontWeight: 300 }}>
          Trading Dashboard
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="body2" color="text.secondary">
            Last updated: {lastUpdate.toLocaleTimeString()}
          </Typography>
          <Tooltip title="Refresh Data">
            <IconButton onClick={fetchDashboardData} disabled={loading}>
              <Refresh />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      <Grid container spacing={3}>
        {/* Portfolio Overview */}
        <Grid item xs={12} md={3}>
          <Card className="hover-card">
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <AccountBalance sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">Portfolio Value</Typography>
              </Box>
              <Typography variant="h4" className="number-large">
                {formatCurrency(dashboardData.portfolio.totalValue)}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                {dashboardData.portfolio.dailyPnL >= 0 ? (
                  <TrendingUp sx={{ color: 'success.main', mr: 0.5 }} />
                ) : (
                  <TrendingDown sx={{ color: 'error.main', mr: 0.5 }} />
                )}
                <Typography 
                  variant="body2" 
                  sx={{ color: getPnLColor(dashboardData.portfolio.dailyPnL) }}
                >
                  {formatCurrency(dashboardData.portfolio.dailyPnL)} 
                  ({formatPercent(dashboardData.portfolio.dailyPnLPercent)})
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Available Balance */}
        <Grid item xs={12} md={3}>
          <Card className="hover-card">
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <ShowChart sx={{ mr: 1, color: 'secondary.main' }} />
                <Typography variant="h6">Available Balance</Typography>
              </Box>
              <Typography variant="h4" className="number-large">
                {formatCurrency(dashboardData.portfolio.availableBalance)}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                {dashboardData.portfolio.positions} active positions
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Win Rate */}
        <Grid item xs={12} md={3}>
          <Card className="hover-card">
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Speed sx={{ mr: 1, color: 'success.main' }} />
                <Typography variant="h6">Win Rate</Typography>
              </Box>
              <Typography variant="h4" className="number-large">
                {dashboardData.performance.winRate}%
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                {dashboardData.performance.totalTrades} total trades
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Profit Factor */}
        <Grid item xs={12} md={3}>
          <Card className="hover-card">
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <TrendingUp sx={{ mr: 1, color: 'info.main' }} />
                <Typography variant="h6">Profit Factor</Typography>
              </Box>
              <Typography variant="h4" className="number-large">
                {dashboardData.performance.profitFactor}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Sharpe: {dashboardData.performance.sharpeRatio}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Portfolio Performance Chart */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Portfolio Performance (24h)</Typography>
              <Box sx={{ height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={dashboardData.priceData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                    <XAxis 
                      dataKey="time" 
                      stroke="#b0bec5"
                      fontSize={12}
                    />
                    <YAxis 
                      stroke="#b0bec5"
                      fontSize={12}
                      tickFormatter={(value) => `$${(value/1000).toFixed(0)}k`}
                    />
                    <Area
                      type="monotone"
                      dataKey="value"
                      stroke="#00d4ff"
                      fill="url(#colorGradient)"
                      strokeWidth={2}
                    />
                    <defs>
                      <linearGradient id="colorGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#00d4ff" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#00d4ff" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                  </AreaChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Active Strategies */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Active Strategies</Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {dashboardData.activeStrategies.map((strategy, index) => (
                  <Box key={index} sx={{ 
                    p: 2, 
                    border: '1px solid rgba(255,255,255,0.1)', 
                    borderRadius: 2,
                    background: 'rgba(26, 31, 58, 0.3)'
                  }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                      <Typography variant="subtitle2">{strategy.name}</Typography>
                      <Chip 
                        label={strategy.status} 
                        size="small"
                        color={strategy.status === 'active' ? 'success' : 'warning'}
                      />
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2" color="text.secondary">
                        {strategy.trades} trades
                      </Typography>
                      <Typography 
                        variant="body2" 
                        sx={{ color: getPnLColor(strategy.pnl) }}
                      >
                        {formatCurrency(strategy.pnl)}
                      </Typography>
                    </Box>
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Trades */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Recent Trades</Typography>
              <TableContainer component={Paper} className="data-table">
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Time</TableCell>
                      <TableCell>Pair</TableCell>
                      <TableCell>Side</TableCell>
                      <TableCell align="right">Amount</TableCell>
                      <TableCell align="right">Price</TableCell>
                      <TableCell align="right">P&L</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {dashboardData.recentTrades.map((trade) => (
                      <TableRow key={trade.id}>
                        <TableCell>{trade.time}</TableCell>
                        <TableCell>
                          <span className="trading-pair">
                            <span className="base">{trade.pair.split('/')[0]}</span>
                            <span className="quote">/{trade.pair.split('/')[1]}</span>
                          </span>
                        </TableCell>
                        <TableCell>
                          <Chip 
                            label={trade.side} 
                            size="small"
                            color={trade.side === 'BUY' ? 'success' : 'error'}
                          />
                        </TableCell>
                        <TableCell align="right">{trade.amount}</TableCell>
                        <TableCell align="right">{formatCurrency(trade.price)}</TableCell>
                        <TableCell align="right">
                          <Typography sx={{ color: getPnLColor(trade.pnl) }}>
                            {formatCurrency(trade.pnl)}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;