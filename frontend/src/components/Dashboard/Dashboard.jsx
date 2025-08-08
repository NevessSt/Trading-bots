import React, { useEffect, useState } from 'react';
import { Box, Grid, Typography, Paper, Button, CircularProgress } from '@mui/material';
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
  
  useEffect(() => {
    // Fetch initial data
    fetchActiveBots();
    fetchTrades(1, 5); // Only fetch 5 most recent trades for dashboard
    fetchPerformance(timeframe);
    
    // Set up polling for active bots (every 30 seconds)
    const botsInterval = setInterval(() => {
      fetchActiveBots();
    }, 30000);
    
    // Set up polling for recent trades (every minute)
    const tradesInterval = setInterval(() => {
      fetchTrades(1, 5);
    }, 60000);
    
    return () => {
      clearInterval(botsInterval);
      clearInterval(tradesInterval);
    };
  }, [fetchActiveBots, fetchTrades, fetchPerformance, timeframe]);
  
  const handleTimeframeChange = (newTimeframe) => {
    setTimeframe(newTimeframe);
    fetchPerformance(newTimeframe);
  };
  
  const handleCreateBot = () => {
    navigate('/bots/new');
  };
  
  if (!user) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
        <CircularProgress />
      </Box>
    );
  }
  
  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Trading Dashboard
        </Typography>
        <Button 
          variant="contained" 
          color="primary" 
          onClick={handleCreateBot}
        >
          Create New Bot
        </Button>
      </Box>
      
      {/* Real-time Market Data */}
      <RealTimeTicker />
      
      {/* Account Balance */}
      <AccountBalance />
      
      {/* Market Data Chart */}
      <MarketDataChart symbol="BTCUSDT" />
      
      <Grid container spacing={3}>
        {/* Account Summary */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <AccountSummary />
          </Paper>
        </Grid>
        
        {/* Performance Chart */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <PerformanceChart 
              performance={performance} 
              isLoading={isLoading} 
              timeframe={timeframe}
              onTimeframeChange={handleTimeframeChange}
            />
          </Paper>
        </Grid>
        
        {/* Active Bots */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <ActiveBotsList 
              bots={activeBots} 
              isLoading={isLoading} 
            />
          </Paper>
        </Grid>
        
        {/* Recent Trades */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <RecentTradesList 
              trades={trades} 
              isLoading={isLoading} 
            />
          </Paper>
        </Grid>
      </Grid>
      
      {error && (
        <Box sx={{ mt: 2, p: 2, bgcolor: 'error.light', borderRadius: 1 }}>
          <Typography color="error">{error}</Typography>
        </Box>
      )}
    </Box>
  );
};

export default Dashboard;