import React, { useState, useEffect, useRef } from 'react';
import { 
  Box, 
  Grid, 
  Card, 
  CardContent, 
  Typography, 
  Button,
  Chip,
  IconButton,
  Tooltip,
  Switch,
  FormControlLabel,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Paper,
  Divider,
  Alert,
  CircularProgress
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Refresh,
  Settings,
  Fullscreen,
  FullscreenExit,
  Notifications,
  Speed,
  AccountBalance,
  ShowChart,
  Assessment
} from '@mui/icons-material';
import { Line, Doughnut, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
  ArcElement,
  BarElement,
  Filler
} from 'chart.js';
import { io } from 'socket.io-client';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import CandlestickChart from '../Charts/CandlestickChart';
import LiveTradesChart from '../Charts/LiveTradesChart';
import PnLChart from '../Charts/PnLChart';
import MarketOverview from '../Charts/MarketOverview';
import { toast } from 'react-hot-toast';
import axios from 'axios';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  ChartTooltip,
  Legend,
  ArcElement,
  BarElement,
  Filler
);

const ProDashboard = () => {
  const { user, token } = useAuth();
  const { isDark } = useTheme();
  const [dashboardData, setDashboardData] = useState(null);
  const [realTimeMetrics, setRealTimeMetrics] = useState(null);
  const [riskMetrics, setRiskMetrics] = useState(null);
  const [performanceData, setPerformanceData] = useState(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(5000);
  const [selectedTimeframe, setSelectedTimeframe] = useState('30d');
  const [loading, setLoading] = useState(true);
  const [connected, setConnected] = useState(false);
  const socketRef = useRef(null);
  const refreshIntervalRef = useRef(null);

  // Initialize WebSocket connection
  useEffect(() => {
    if (token && user) {
      const socket = io('http://localhost:5000', {
        auth: {
          user_id: user.id,
          token: token
        },
        transports: ['websocket', 'polling']
      });

      socketRef.current = socket;

      socket.on('connect', () => {
        console.log('Connected to WebSocket');
        setConnected(true);
        toast.success('Real-time connection established');
      });

      socket.on('disconnect', () => {
        console.log('Disconnected from WebSocket');
        setConnected(false);
        toast.error('Real-time connection lost');
      });

      socket.on('dashboard_update', (data) => {
        console.log('Dashboard update received:', data);
        setDashboardData(data);
      });

      socket.on('price_update', (data) => {
        console.log('Price update received:', data);
        // Handle price updates for charts
      });

      socket.on('bot_status_update', (data) => {
        console.log('Bot status update:', data);
        toast.info(`Bot ${data.bot_id} status: ${data.status}`);
      });

      socket.on('trade_notification', (data) => {
        console.log('Trade notification:', data);
        toast.success(`New trade executed: ${data.data.symbol}`);
      });

      socket.on('market_alert', (data) => {
        console.log('Market alert:', data);
        toast.warning(`Market Alert: ${data.data.message}`);
      });

      return () => {
        socket.disconnect();
      };
    }
  }, [token, user]);

  // Fetch initial data
  useEffect(() => {
    if (token) {
      fetchDashboardData();
      fetchRealTimeMetrics();
      fetchRiskMetrics();
      fetchPerformanceData();
    }
  }, [token, selectedTimeframe]);

  // Auto-refresh setup
  useEffect(() => {
    if (autoRefresh && token) {
      refreshIntervalRef.current = setInterval(() => {
        fetchRealTimeMetrics();
        fetchRiskMetrics();
      }, refreshInterval);

      return () => {
        if (refreshIntervalRef.current) {
          clearInterval(refreshIntervalRef.current);
        }
      };
    }
  }, [autoRefresh, refreshInterval, token]);

  const fetchDashboardData = async () => {
    try {
      const response = await axios.get('/api/pro-dashboard/overview', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setDashboardData(response.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      toast.error('Failed to fetch dashboard data');
    }
  };

  const fetchRealTimeMetrics = async () => {
    try {
      const response = await axios.get('/api/pro-dashboard/real-time-metrics', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setRealTimeMetrics(response.data);
    } catch (error) {
      console.error('Error fetching real-time metrics:', error);
    }
  };

  const fetchRiskMetrics = async () => {
    try {
      const response = await axios.get('/api/pro-dashboard/risk-metrics', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setRiskMetrics(response.data);
    } catch (error) {
      console.error('Error fetching risk metrics:', error);
    }
  };

  const fetchPerformanceData = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`/api/pro-dashboard/performance-analytics?timeframe=${selectedTimeframe}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPerformanceData(response.data);
    } catch (error) {
      console.error('Error fetching performance data:', error);
      toast.error('Failed to fetch performance data');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    fetchDashboardData();
    fetchRealTimeMetrics();
    fetchRiskMetrics();
    fetchPerformanceData();
    toast.success('Dashboard refreshed');
  };

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  // Chart configurations
  const portfolioChartData = {
    labels: performanceData?.daily_performance?.map(d => new Date(d.date).toLocaleDateString()) || [],
    datasets: [
      {
        label: 'Portfolio Value',
        data: performanceData?.daily_performance?.map(d => d.pnl) || [],
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
        tension: 0.4,
      },
    ],
  };

  const volumeChartData = {
    labels: performanceData?.daily_performance?.map(d => new Date(d.date).toLocaleDateString()) || [],
    datasets: [
      {
        label: 'Daily Volume',
        data: performanceData?.daily_performance?.map(d => d.volume) || [],
        backgroundColor: 'rgba(34, 197, 94, 0.8)',
        borderColor: '#22c55e',
        borderWidth: 1,
      },
    ],
  };

  const botPerformanceData = {
    labels: performanceData?.bot_performance?.map(bot => bot.name) || [],
    datasets: [
      {
        label: 'Bot PnL',
        data: performanceData?.bot_performance?.map(bot => bot.pnl) || [],
        backgroundColor: [
          '#3b82f6',
          '#22c55e',
          '#f59e0b',
          '#ef4444',
          '#8b5cf6',
        ],
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          color: isDark ? '#f1f5f9' : '#0f172a',
        },
      },
    },
    scales: {
      x: {
        ticks: {
          color: isDark ? '#94a3b8' : '#64748b',
        },
        grid: {
          color: isDark ? 'rgba(148, 163, 184, 0.1)' : 'rgba(148, 163, 184, 0.2)',
        },
      },
      y: {
        ticks: {
          color: isDark ? '#94a3b8' : '#64748b',
        },
        grid: {
          color: isDark ? 'rgba(148, 163, 184, 0.1)' : 'rgba(148, 163, 184, 0.2)',
        },
      },
    },
  };

  if (loading && !dashboardData) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3, minHeight: '100vh', bgcolor: isDark ? '#0f172a' : '#f8fafc' }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" fontWeight="bold" color={isDark ? '#f1f5f9' : '#0f172a'}>
          Pro Trading Dashboard
        </Typography>
        
        <Box display="flex" alignItems="center" gap={2}>
          {/* Connection Status */}
          <Chip 
            icon={connected ? <Speed /> : <Speed />}
            label={connected ? 'Live' : 'Offline'}
            color={connected ? 'success' : 'error'}
            variant="outlined"
          />
          
          {/* Auto Refresh Toggle */}
          <FormControlLabel
            control={
              <Switch
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                color="primary"
              />
            }
            label="Auto Refresh"
            sx={{ color: isDark ? '#f1f5f9' : '#0f172a' }}
          />
          
          {/* Timeframe Selector */}
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Timeframe</InputLabel>
            <Select
              value={selectedTimeframe}
              onChange={(e) => setSelectedTimeframe(e.target.value)}
              label="Timeframe"
            >
              <MenuItem value="7d">7 Days</MenuItem>
              <MenuItem value="30d">30 Days</MenuItem>
              <MenuItem value="90d">90 Days</MenuItem>
              <MenuItem value="1y">1 Year</MenuItem>
            </Select>
          </FormControl>
          
          {/* Action Buttons */}
          <Tooltip title="Refresh">
            <IconButton onClick={handleRefresh} color="primary">
              <Refresh />
            </IconButton>
          </Tooltip>
          
          <Tooltip title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}>
            <IconButton onClick={toggleFullscreen} color="primary">
              {isFullscreen ? <FullscreenExit /> : <Fullscreen />}
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Key Metrics Cards */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: isDark ? '#1e293b' : '#ffffff' }}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Total P&L
                  </Typography>
                  <Typography variant="h5" fontWeight="bold">
                    ${dashboardData?.portfolio?.total_pnl?.toFixed(2) || '0.00'}
                  </Typography>
                </Box>
                <AccountBalance color="primary" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: isDark ? '#1e293b' : '#ffffff' }}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Active Bots
                  </Typography>
                  <Typography variant="h5" fontWeight="bold">
                    {dashboardData?.portfolio?.active_bots || 0}
                  </Typography>
                </Box>
                <Speed color="success" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: isDark ? '#1e293b' : '#ffffff' }}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Win Rate
                  </Typography>
                  <Typography variant="h5" fontWeight="bold">
                    {dashboardData?.portfolio?.win_rate?.toFixed(1) || '0.0'}%
                  </Typography>
                </Box>
                <TrendingUp color="success" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: isDark ? '#1e293b' : '#ffffff' }}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Total Trades
                  </Typography>
                  <Typography variant="h5" fontWeight="bold">
                    {dashboardData?.portfolio?.total_trades || 0}
                  </Typography>
                </Box>
                <ShowChart color="info" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts Section */}
      <Grid container spacing={3} mb={3}>
        {/* Portfolio Performance Chart */}
        <Grid item xs={12} lg={8}>
          <Card sx={{ bgcolor: isDark ? '#1e293b' : '#ffffff', height: 400 }}>
            <CardContent sx={{ height: '100%' }}>
              <Typography variant="h6" gutterBottom>
                Portfolio Performance
              </Typography>
              <Box sx={{ height: 320 }}>
                <Line data={portfolioChartData} options={chartOptions} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Bot Performance Breakdown */}
        <Grid item xs={12} lg={4}>
          <Card sx={{ bgcolor: isDark ? '#1e293b' : '#ffffff', height: 400 }}>
            <CardContent sx={{ height: '100%' }}>
              <Typography variant="h6" gutterBottom>
                Bot Performance
              </Typography>
              <Box sx={{ height: 320 }}>
                <Doughnut data={botPerformanceData} options={chartOptions} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Advanced Charts */}
      <Grid container spacing={3} mb={3}>
        {/* Candlestick Chart */}
        <Grid item xs={12} lg={6}>
          <Card sx={{ bgcolor: isDark ? '#1e293b' : '#ffffff' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Market Analysis
              </Typography>
              <CandlestickChart 
                symbol="BTCUSDT" 
                height={300}
                showVolume={true}
                showIndicators={true}
              />
            </CardContent>
          </Card>
        </Grid>
        
        {/* Live Trades */}
        <Grid item xs={12} lg={6}>
          <Card sx={{ bgcolor: isDark ? '#1e293b' : '#ffffff' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Live Trades
              </Typography>
              <LiveTradesChart height={300} />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Volume and Risk Metrics */}
      <Grid container spacing={3} mb={3}>
        {/* Volume Chart */}
        <Grid item xs={12} lg={8}>
          <Card sx={{ bgcolor: isDark ? '#1e293b' : '#ffffff', height: 350 }}>
            <CardContent sx={{ height: '100%' }}>
              <Typography variant="h6" gutterBottom>
                Daily Volume
              </Typography>
              <Box sx={{ height: 270 }}>
                <Bar data={volumeChartData} options={chartOptions} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Risk Metrics */}
        <Grid item xs={12} lg={4}>
          <Card sx={{ bgcolor: isDark ? '#1e293b' : '#ffffff', height: 350 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Risk Metrics
              </Typography>
              <Box sx={{ mt: 2 }}>
                <Box display="flex" justifyContent="space-between" mb={2}>
                  <Typography>Sharpe Ratio:</Typography>
                  <Typography fontWeight="bold">
                    {riskMetrics?.sharpe_ratio?.toFixed(2) || '0.00'}
                  </Typography>
                </Box>
                <Box display="flex" justifyContent="space-between" mb={2}>
                  <Typography>Max Drawdown:</Typography>
                  <Typography fontWeight="bold" color="error">
                    {riskMetrics?.max_drawdown?.toFixed(2) || '0.00'}%
                  </Typography>
                </Box>
                <Box display="flex" justifyContent="space-between" mb={2}>
                  <Typography>VaR (95%):</Typography>
                  <Typography fontWeight="bold">
                    ${riskMetrics?.var_95?.toFixed(2) || '0.00'}
                  </Typography>
                </Box>
                <Divider sx={{ my: 2 }} />
                <Box display="flex" justifyContent="space-between" mb={1}>
                  <Typography>Winning Trades:</Typography>
                  <Typography color="success.main">
                    {riskMetrics?.winning_trades || 0}
                  </Typography>
                </Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography>Losing Trades:</Typography>
                  <Typography color="error.main">
                    {riskMetrics?.losing_trades || 0}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Market Overview */}
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Card sx={{ bgcolor: isDark ? '#1e293b' : '#ffffff' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Market Overview
              </Typography>
              <MarketOverview />
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ProDashboard;