import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  LinearProgress,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Refresh,
  PieChart,
} from '@mui/icons-material';
import { PieChart as RechartsPieChart, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';

const Portfolio = () => {
  const [portfolioData, setPortfolioData] = useState({
    totalValue: 0,
    totalPnL: 0,
    totalPnLPercent: 0,
    holdings: [],
    allocation: [],
    performance: []
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPortfolioData();
    const interval = setInterval(fetchPortfolioData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchPortfolioData = async () => {
    try {
      setLoading(true);
      
      // Mock portfolio data
      const mockData = {
        totalValue: 125430.50,
        totalPnL: 15430.50,
        totalPnLPercent: 14.05,
        holdings: [
          {
            symbol: 'BTC',
            name: 'Bitcoin',
            amount: 2.5,
            value: 108125.00,
            price: 43250.00,
            change24h: 2.98,
            allocation: 86.2
          },
          {
            symbol: 'ETH',
            name: 'Ethereum',
            amount: 5.2,
            value: 13936.00,
            price: 2680.00,
            change24h: -1.25,
            allocation: 11.1
          },
          {
            symbol: 'USDT',
            name: 'Tether',
            amount: 3369.50,
            value: 3369.50,
            price: 1.00,
            change24h: 0.01,
            allocation: 2.7
          }
        ],
        allocation: [
          { name: 'BTC', value: 86.2, color: '#f7931a' },
          { name: 'ETH', value: 11.1, color: '#627eea' },
          { name: 'USDT', value: 2.7, color: '#26a17b' }
        ],
        performance: [
          { date: '2024-01-01', value: 110000 },
          { date: '2024-01-15', value: 115000 },
          { date: '2024-02-01', value: 118000 },
          { date: '2024-02-15', value: 122000 },
          { date: '2024-03-01', value: 125430 }
        ]
      };
      
      setPortfolioData(mockData);
    } catch (error) {
      console.error('Failed to fetch portfolio data:', error);
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

  return (
    <Box sx={{ flexGrow: 1 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" sx={{ fontWeight: 300 }}>
          Portfolio Overview
        </Typography>
        <Tooltip title="Refresh Portfolio">
          <IconButton onClick={fetchPortfolioData} disabled={loading}>
            <Refresh />
          </IconButton>
        </Tooltip>
      </Box>

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      <Grid container spacing={3}>
        {/* Portfolio Summary */}
        <Grid item xs={12} md={4}>
          <Card className="hover-card">
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <PieChart sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">Total Portfolio Value</Typography>
              </Box>
              <Typography variant="h3" className="number-large" sx={{ mb: 1 }}>
                {formatCurrency(portfolioData.totalValue)}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                {portfolioData.totalPnL >= 0 ? (
                  <TrendingUp sx={{ color: 'success.main', mr: 0.5 }} />
                ) : (
                  <TrendingDown sx={{ color: 'error.main', mr: 0.5 }} />
                )}
                <Typography 
                  variant="h6" 
                  sx={{ color: getPnLColor(portfolioData.totalPnL) }}
                >
                  {formatCurrency(portfolioData.totalPnL)} 
                  ({formatPercent(portfolioData.totalPnLPercent)})
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Total unrealized P&L
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Asset Allocation Chart */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Asset Allocation</Typography>
              <Box sx={{ height: 300, display: 'flex', alignItems: 'center' }}>
                <Box sx={{ flex: 1, height: '100%' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <RechartsPieChart>
                      <RechartsPieChart
                        data={portfolioData.allocation}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={120}
                        paddingAngle={5}
                        dataKey="value"
                      >
                        {portfolioData.allocation.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </RechartsPieChart>
                    </RechartsPieChart>
                  </ResponsiveContainer>
                </Box>
                <Box sx={{ ml: 3 }}>
                  {portfolioData.allocation.map((item, index) => (
                    <Box key={index} sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <Box 
                        sx={{ 
                          width: 16, 
                          height: 16, 
                          backgroundColor: item.color, 
                          borderRadius: '50%', 
                          mr: 1 
                        }} 
                      />
                      <Typography variant="body2">
                        {item.name}: {item.value}%
                      </Typography>
                    </Box>
                  ))}
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Holdings Table */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Holdings</Typography>
              <TableContainer component={Paper} className="data-table">
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Asset</TableCell>
                      <TableCell align="right">Amount</TableCell>
                      <TableCell align="right">Price</TableCell>
                      <TableCell align="right">Value</TableCell>
                      <TableCell align="right">24h Change</TableCell>
                      <TableCell align="right">Allocation</TableCell>
                      <TableCell align="right">Allocation %</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {portfolioData.holdings.map((holding) => (
                      <TableRow key={holding.symbol}>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <Box sx={{ ml: 1 }}>
                              <Typography variant="subtitle2">{holding.symbol}</Typography>
                              <Typography variant="body2" color="text.secondary">
                                {holding.name}
                              </Typography>
                            </Box>
                          </Box>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2">
                            {holding.amount.toLocaleString()}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          {formatCurrency(holding.price)}
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="subtitle2">
                            {formatCurrency(holding.value)}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
                            {holding.change24h >= 0 ? (
                              <TrendingUp sx={{ color: 'success.main', mr: 0.5, fontSize: 16 }} />
                            ) : (
                              <TrendingDown sx={{ color: 'error.main', mr: 0.5, fontSize: 16 }} />
                            )}
                            <Typography 
                              variant="body2" 
                              sx={{ color: getPnLColor(holding.change24h) }}
                            >
                              {formatPercent(holding.change24h)}
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell align="right">
                          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
                            <Box sx={{ width: 100, mr: 1 }}>
                              <LinearProgress 
                                variant="determinate" 
                                value={holding.allocation} 
                                sx={{ height: 6, borderRadius: 3 }}
                              />
                            </Box>
                          </Box>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2">
                            {holding.allocation.toFixed(1)}%
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

        {/* Portfolio Performance */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Portfolio Performance</Typography>
              <Box sx={{ height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={portfolioData.performance}>
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
                    <Bar
                      dataKey="value"
                      fill="#00d4ff"
                      radius={[4, 4, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Portfolio;