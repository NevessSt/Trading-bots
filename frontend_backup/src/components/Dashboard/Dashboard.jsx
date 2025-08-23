import React, { useEffect, useState } from 'react';
import { Box, Grid, Typography, Paper, Button, CircularProgress, Tabs, Tab } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import useTradingStore from '../../stores/useTradingStore';
import useAuthStore from '../../stores/useAuthStore';
import ActiveBotsList from './ActiveBotsList';
import RecentTradesList from './RecentTradesList';
import PerformanceChart from './PerformanceChart';
import AccountSummary from './AccountSummary';
import RealTimeTicker from './RealTimeTicker';
import AccountBalance from './AccountBalance';
import MarketDataChart from './MarketDataChart';
// Enhanced Chart Components
import CandlestickChart from '../Charts/CandlestickChart';
import PnLChart from '../Charts/PnLChart';
import LiveTradesChart from '../Charts/LiveTradesChart';
import MarketOverview from '../Charts/MarketOverview';

const Dashboard = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const { 
    activeBots, 
    trades, 
    performance, 
    isLoading, 
    error,
    fetchActiveBots, 
    fetchTrades, 
    fetchPerformance 
  } = useTradingStore();
  
  const [timeframe, setTimeframe] = useState('30d');
  const [activeTab, setActiveTab] = useState(0);
  const [marketData, setMarketData] = useState([]);
  const [candlestickData, setCandlestickData] = useState([]);
  const [interval, setInterval] = useState('1h');
  
  // Fetch market data for enhanced charts
  const fetchMarketData = async () => {
    try {
      // Fetch market overview data (top cryptocurrencies)
      const response = await fetch('https://api.binance.com/api/v3/ticker/24hr');
      const data = await response.json();
      // Filter to top 20 by volume
      const topMarkets = data
        .filter(item => item.symbol.endsWith('USDT'))
        .sort((a, b) => parseFloat(b.quoteVolume) - parseFloat(a.quoteVolume))
        .slice(0, 20);
      setMarketData(topMarkets);
    } catch (error) {
      console.error('Failed to fetch market data:', error);
    }
  };

  const fetchCandlestickData = async (symbol = 'BTCUSDT', interval = '1h') => {
    try {
      const response = await fetch(
        `https://api.binance.com/api/v3/klines?symbol=${symbol}&interval=${interval}&limit=100`
      );
      const data = await response.json();
      setCandlestickData(data);
    } catch (error) {
      console.error('Failed to fetch candlestick data:', error);
    }
  };

  useEffect(() => {
    // Fetch initial data
    fetchActiveBots();
    fetchTrades(1, 50); // Fetch more trades for live trades chart
    fetchPerformance(timeframe);
    fetchMarketData();
    fetchCandlestickData();
    
    // Set up polling for active bots (every 30 seconds)
    const botsInterval = setInterval(() => {
      fetchActiveBots();
    }, 30000);
    
    // Set up polling for recent trades (every minute)
    const tradesInterval = setInterval(() => {
      fetchTrades(1, 50);
    }, 60000);

    // Set up polling for market data (every 5 minutes)
    const marketInterval = setInterval(() => {
      fetchMarketData();
      fetchCandlestickData();
    }, 300000);
    
    return () => {
      clearInterval(botsInterval);
      clearInterval(tradesInterval);
      clearInterval(marketInterval);
    };
  }, [fetchActiveBots, fetchTrades, fetchPerformance, timeframe]);
  
  const handleTimeframeChange = (newTimeframe) => {
    setTimeframe(newTimeframe);
    fetchPerformance(newTimeframe);
  };
  
  const handleCreateBot = () => {
    navigate('/bots/new');
  };

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const handleIntervalChange = (newInterval) => {
    setInterval(newInterval);
    fetchCandlestickData('BTCUSDT', newInterval);
  };

  const handleRefreshMarketData = () => {
    fetchMarketData();
    fetchCandlestickData();
  };

  const handleRefreshTrades = () => {
    fetchTrades(1, 50);
  };
  
  if (!user) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
        <CircularProgress />
      </Box>
    );
  }
  
  return (
    <Box sx={{ flexGrow: 1, p: 3 }} className="animate-fade-in">
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }} className="animate-fade-in-down">
        <Typography variant="h4" component="h1" gutterBottom className="animate-slide-in-left">
          Pro Trading Dashboard
        </Typography>
        <Button 
          variant="contained" 
          color="primary" 
          onClick={handleCreateBot}
          className="animate-slide-in-right hover:scale-105 transition-transform duration-200"
        >
          Create New Bot
        </Button>
      </Box>
      
      {/* Real-time Market Data */}
      <div className="animate-stagger-1">
        <RealTimeTicker />
      </div>
      
      {/* Account Balance */}
      <div className="animate-stagger-2">
        <AccountBalance />
      </div>
      
      {/* Dashboard Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs 
          value={activeTab} 
          onChange={handleTabChange} 
          variant="scrollable"
          scrollButtons="auto"
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab label="Overview" />
          <Tab label="Advanced Charts" />
          <Tab label="Live Trades" />
          <Tab label="Market Analysis" />
        </Tabs>
      </Paper>

      {/* Tab Content */}
      {activeTab === 0 && (
        <Grid container spacing={3} className="animate-stagger-4">
          {/* Account Summary */}
          <Grid item xs={12} md={6} className="animate-fade-in-up hover-lift">
            <Paper sx={{ p: 2, height: '100%' }} className="transition-all duration-300 hover:shadow-lg">
              <AccountSummary />
            </Paper>
          </Grid>
          
          {/* Performance Chart */}
          <Grid item xs={12} md={6} className="animate-fade-in-up hover-lift" style={{ animationDelay: '0.1s' }}>
            <Paper sx={{ p: 2, height: '100%' }} className="transition-all duration-300 hover:shadow-lg">
              <PerformanceChart 
                performance={performance} 
                isLoading={isLoading} 
                timeframe={timeframe}
                onTimeframeChange={handleTimeframeChange}
              />
            </Paper>
          </Grid>
          
          {/* Enhanced P&L Chart */}
          <Grid item xs={12}>
            <PnLChart 
              data={trades || []} 
              timeframe={timeframe}
              onTimeframeChange={handleTimeframeChange}
              height={350}
            />
          </Grid>
          
          {/* Active Bots */}
          <Grid item xs={12} md={6} className="animate-fade-in-up hover-lift" style={{ animationDelay: '0.2s' }}>
            <Paper sx={{ p: 2, height: '100%' }} className="transition-all duration-300 hover:shadow-lg">
              <ActiveBotsList 
                bots={activeBots} 
                isLoading={isLoading} 
              />
            </Paper>
          </Grid>
          
          {/* Recent Trades */}
          <Grid item xs={12} md={6} className="animate-fade-in-up hover-lift" style={{ animationDelay: '0.3s' }}>
            <Paper sx={{ p: 2, height: '100%' }} className="transition-all duration-300 hover:shadow-lg">
              <RecentTradesList 
                trades={trades?.slice(0, 5) || []} 
                isLoading={isLoading} 
              />
            </Paper>
          </Grid>
        </Grid>
      )}

      {activeTab === 1 && (
        <Grid container spacing={3}>
          {/* Enhanced Candlestick Chart */}
          <Grid item xs={12}>
            <CandlestickChart 
              data={candlestickData}
              symbol="BTCUSDT"
              height={500}
              showVolume={true}
              showIndicators={true}
              onIntervalChange={handleIntervalChange}
              interval={interval}
            />
          </Grid>
          
          {/* Original Market Data Chart for comparison */}
          <Grid item xs={12}>
            <MarketDataChart symbol="BTCUSDT" />
          </Grid>
        </Grid>
      )}

      {activeTab === 2 && (
        <Grid container spacing={3}>
          {/* Live Trades Chart */}
          <Grid item xs={12}>
            <LiveTradesChart 
              trades={trades || []}
              onRefresh={handleRefreshTrades}
              autoRefresh={true}
              maxDisplayTrades={100}
            />
          </Grid>
        </Grid>
      )}

      {activeTab === 3 && (
        <Grid container spacing={3}>
          {/* Market Overview */}
          <Grid item xs={12}>
            <MarketOverview 
              marketData={marketData}
              onRefresh={handleRefreshMarketData}
              autoRefresh={true}
            />
          </Grid>
        </Grid>
      )}
      
      {error && (
        <Box sx={{ mt: 2, p: 2, bgcolor: 'error.light', borderRadius: 1 }} className="animate-fade-in-up animate-bounce-in">
          <Typography color="error" className="animate-fade-in">{error}</Typography>
        </Box>
      )}
    </Box>
  );
};

export default Dashboard;