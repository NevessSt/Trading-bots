import React, { useEffect, useState } from 'react';
import { Box, Typography, Grid, Card, CardContent, Chip } from '@mui/material';
import { TrendingUp, TrendingDown } from '@mui/icons-material';
import useTradingStore from '../../stores/useTradingStore';

const RealTimeTicker = ({ symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT'] }) => {
  const { 
    realTimeData, 
    fetchAllRealTimeData, 
    startWebSocketStream 
  } = useTradingStore();
  
  const [isPolling, setIsPolling] = useState(false);
  
  useEffect(() => {
    // Start WebSocket streams for all symbols
    const initializeStreams = async () => {
      for (const symbol of symbols) {
        await startWebSocketStream(symbol);
      }
    };
    
    initializeStreams();
    
    // Fallback polling for real-time data
    const startPolling = () => {
      setIsPolling(true);
      const interval = setInterval(() => {
        fetchAllRealTimeData();
      }, 5000); // Poll every 5 seconds
      
      return interval;
    };
    
    const pollInterval = startPolling();
    
    return () => {
      clearInterval(pollInterval);
      setIsPolling(false);
    };
  }, [symbols, startWebSocketStream, fetchAllRealTimeData]);
  
  const formatPrice = (price) => {
    if (price >= 1) {
      return price.toFixed(2);
    } else {
      return price.toFixed(6);
    }
  };
  
  const formatChange = (change) => {
    return change >= 0 ? `+${change.toFixed(2)}%` : `${change.toFixed(2)}%`;
  };
  
  return (
    <Box sx={{ mb: 3 }}>
      <Typography variant="h6" gutterBottom>
        Live Market Prices
      </Typography>
      
      <Grid container spacing={2}>
        {symbols.map((symbol) => {
          const data = realTimeData[symbol];
          
          if (!data) {
            return (
              <Grid item xs={12} sm={6} md={3} key={symbol}>
                <Card sx={{ height: '100%' }}>
                  <CardContent>
                    <Typography variant="h6" component="div">
                      {symbol}
                    </Typography>
                    <Typography color="text.secondary">
                      Loading...
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            );
          }
          
          const isPositive = data.change >= 0;
          
          return (
            <Grid item xs={12} sm={6} md={3} key={symbol}>
              <Card 
                sx={{ 
                  height: '100%',
                  border: `2px solid ${isPositive ? '#4caf50' : '#f44336'}`,
                  transition: 'all 0.3s ease'
                }}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                    <Typography variant="h6" component="div">
                      {symbol.replace('USDT', '/USDT')}
                    </Typography>
                    <Chip
                      icon={isPositive ? <TrendingUp /> : <TrendingDown />}
                      label={formatChange(data.change)}
                      color={isPositive ? 'success' : 'error'}
                      size="small"
                    />
                  </Box>
                  
                  <Typography 
                    variant="h5" 
                    component="div" 
                    sx={{ 
                      color: isPositive ? '#4caf50' : '#f44336',
                      fontWeight: 'bold',
                      mb: 1
                    }}
                  >
                    ${formatPrice(data.price)}
                  </Typography>
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      24h High: ${formatPrice(data.high)}
                    </Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2" color="text.secondary">
                      24h Low: ${formatPrice(data.low)}
                    </Typography>
                  </Box>
                  
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                    Volume: {data.volume ? data.volume.toLocaleString() : 'N/A'}
                  </Typography>
                  
                  <Typography variant="caption" color="text.secondary">
                    Last updated: {new Date(data.timestamp).toLocaleTimeString()}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>
      
      {isPolling && (
        <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Typography variant="caption" color="text.secondary">
            🔴 Live data updating every 5 seconds
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default RealTimeTicker;