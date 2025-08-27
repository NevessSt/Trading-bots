import React, { useEffect, useState, useCallback } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Chip,
  IconButton,
  Switch,
  FormControlLabel,
  Alert,
  Badge,
  Tooltip,
  LinearProgress,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Refresh,
  Settings,
  Notifications,
  NotificationsOff,
  WifiOff,
  Wifi,
  ShowChart,
  AccountBalance,
  Warning
} from '@mui/icons-material';
import { format } from 'date-fns';
import useTradingStore from '../../stores/useTradingStore';
import useAuthStore from '../../stores/useAuthStore';

const LivePriceTracker = ({ 
  symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT', 'XRPUSDT'],
  autoConnect = true,
  showPortfolio = true,
  showAlerts = true
}) => {
  const {
    realTimeData,
    portfolioData,
    liveAlerts,
    wsConnected,
    wsSubscriptions,
    initializeWebSocket,
    disconnectWebSocket,
    subscribeToSymbol,
    unsubscribeFromSymbol,
    requestPortfolioUpdate,
    getWebSocketStatus,
    clearLiveAlerts,
    error
  } = useTradingStore();

  const { token } = useAuthStore();
  
  const [isInitialized, setIsInitialized] = useState(false);
  const [notifications, setNotifications] = useState(true);
  const [selectedSymbols, setSelectedSymbols] = useState(new Set(symbols));
  const [connectionStats, setConnectionStats] = useState(null);

  // Initialize WebSocket connection
  useEffect(() => {
    if (autoConnect && !isInitialized && token) {
      initializeConnection();
    }
    
    return () => {
      if (isInitialized) {
        disconnectWebSocket();
      }
    };
  }, [autoConnect, token]);

  // Subscribe to selected symbols
  useEffect(() => {
    if (wsConnected && selectedSymbols.size > 0) {
      selectedSymbols.forEach(symbol => {
        if (!wsSubscriptions.has(symbol)) {
          subscribeToSymbol(symbol);
        }
      });
    }
  }, [wsConnected, selectedSymbols]);

  // Update connection stats periodically
  useEffect(() => {
    if (wsConnected) {
      const interval = setInterval(() => {
        const stats = getWebSocketStatus();
        setConnectionStats(stats);
      }, 5000);
      
      return () => clearInterval(interval);
    }
  }, [wsConnected]);

  const initializeConnection = async () => {
    try {
      const success = await initializeWebSocket(token);
      if (success) {
        setIsInitialized(true);
        // Request initial portfolio update
        setTimeout(() => {
          requestPortfolioUpdate();
        }, 1000);
      }
    } catch (error) {
      console.error('Failed to initialize WebSocket connection:', error);
    }
  };

  const handleToggleSymbol = useCallback((symbol) => {
    const newSelected = new Set(selectedSymbols);
    if (newSelected.has(symbol)) {
      newSelected.delete(symbol);
      unsubscribeFromSymbol(symbol);
    } else {
      newSelected.add(symbol);
      subscribeToSymbol(symbol);
    }
    setSelectedSymbols(newSelected);
  }, [selectedSymbols, subscribeToSymbol, unsubscribeFromSymbol]);

  const handleReconnect = useCallback(() => {
    disconnectWebSocket();
    setTimeout(() => {
      initializeConnection();
    }, 1000);
  }, []);

  const formatPrice = (price) => {
    if (!price) return 'N/A';
    return parseFloat(price).toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 8
    });
  };

  const formatPriceChange = (change, changePercent) => {
    if (!change && !changePercent) return { text: 'N/A', color: 'text.secondary' };
    
    const isPositive = parseFloat(change || changePercent) >= 0;
    return {
      text: `${isPositive ? '+' : ''}${change ? formatPrice(change) : ''}${changePercent ? ` (${parseFloat(changePercent).toFixed(2)}%)` : ''}`,
      color: isPositive ? 'success.main' : 'error.main'
    };
  };

  const getPriceData = (symbol) => {
    const data = realTimeData[symbol];
    if (!data) return null;
    
    return {
      symbol,
      price: data.price || data.c,
      change: data.priceChange || data.P,
      changePercent: data.priceChangePercent || data.p,
      volume: data.volume || data.v,
      high: data.high || data.h,
      low: data.low || data.l,
      timestamp: data.timestamp || Date.now()
    };
  };

  return (
    <Box sx={{ p: 2 }}>
      {/* Connection Status Header */}
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="h5" component="h2">
            Live Price Tracker
          </Typography>
          <Chip
            icon={wsConnected ? <Wifi /> : <WifiOff />}
            label={wsConnected ? 'Connected' : 'Disconnected'}
            color={wsConnected ? 'success' : 'error'}
            size="small"
          />
          {connectionStats && (
            <Tooltip title={`Subscriptions: ${connectionStats.subscriptions.length}`}>
              <Badge badgeContent={connectionStats.subscriptions.length} color="primary">
                <ShowChart />
              </Badge>
            </Tooltip>
          )}
        </Box>
        
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <FormControlLabel
            control={
              <Switch
                checked={notifications}
                onChange={(e) => setNotifications(e.target.checked)}
                size="small"
              />
            }
            label="Alerts"
          />
          <IconButton onClick={handleReconnect} disabled={wsConnected}>
            <Refresh />
          </IconButton>
        </Box>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => useTradingStore.getState().clearError()}>
          {error}
        </Alert>
      )}

      {/* Connection Progress */}
      {!wsConnected && isInitialized && (
        <Box sx={{ mb: 2 }}>
          <LinearProgress />
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Connecting to real-time data stream...
          </Typography>
        </Box>
      )}

      {/* Live Alerts */}
      {showAlerts && liveAlerts.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
              <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Warning color="warning" />
                Live Alerts ({liveAlerts.length})
              </Typography>
              <IconButton size="small" onClick={clearLiveAlerts}>
                <NotificationsOff />
              </IconButton>
            </Box>
            <List dense>
              {liveAlerts.slice(0, 5).map((alert, index) => (
                <ListItem key={index}>
                  <ListItemIcon>
                    <Notifications color={alert.type === 'warning' ? 'warning' : 'info'} />
                  </ListItemIcon>
                  <ListItemText
                    primary={alert.message}
                    secondary={format(new Date(alert.timestamp), 'HH:mm:ss')}
                  />
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
      )}

      {/* Portfolio Summary */}
      {showPortfolio && portfolioData && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <AccountBalance />
              Portfolio Summary
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={4}>
                <Typography variant="body2" color="text.secondary">Total P&L</Typography>
                <Typography 
                  variant="h6" 
                  color={portfolioData.total_pnl >= 0 ? 'success.main' : 'error.main'}
                >
                  ${formatPrice(portfolioData.total_pnl)}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Typography variant="body2" color="text.secondary">Active Bots</Typography>
                <Typography variant="h6">
                  {portfolioData.active_bots}/{portfolioData.total_bots}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Typography variant="body2" color="text.secondary">Last Update</Typography>
                <Typography variant="body2">
                  {format(new Date(portfolioData.timestamp), 'HH:mm:ss')}
                </Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Price Cards */}
      <Grid container spacing={2}>
        {symbols.map((symbol) => {
          const priceData = getPriceData(symbol);
          const isSubscribed = selectedSymbols.has(symbol);
          const priceChange = priceData ? formatPriceChange(priceData.change, priceData.changePercent) : null;
          
          return (
            <Grid item xs={12} sm={6} md={4} lg={3} key={symbol}>
              <Card 
                sx={{ 
                  cursor: 'pointer',
                  opacity: isSubscribed ? 1 : 0.6,
                  border: isSubscribed ? '2px solid' : '1px solid',
                  borderColor: isSubscribed ? 'primary.main' : 'divider',
                  transition: 'all 0.2s ease-in-out',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: 3
                  }
                }}
                onClick={() => handleToggleSymbol(symbol)}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="h6" component="div">
                      {symbol.replace('USDT', '/USDT')}
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      {priceChange && (
                        priceChange.color === 'success.main' ? 
                          <TrendingUp color="success" fontSize="small" /> : 
                          <TrendingDown color="error" fontSize="small" />
                      )}
                      <Chip
                        size="small"
                        label={isSubscribed ? 'Live' : 'Paused'}
                        color={isSubscribed ? 'success' : 'default'}
                        variant={isSubscribed ? 'filled' : 'outlined'}
                      />
                    </Box>
                  </Box>
                  
                  <Typography variant="h4" component="div" sx={{ mb: 1 }}>
                    ${priceData ? formatPrice(priceData.price) : 'N/A'}
                  </Typography>
                  
                  {priceChange && (
                    <Typography 
                      variant="body2" 
                      sx={{ color: priceChange.color, fontWeight: 'medium' }}
                    >
                      {priceChange.text}
                    </Typography>
                  )}
                  
                  {priceData && (
                    <>
                      <Divider sx={{ my: 1 }} />
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                        <Box>
                          <Typography variant="caption" color="text.secondary">High</Typography>
                          <Typography variant="body2">${formatPrice(priceData.high)}</Typography>
                        </Box>
                        <Box>
                          <Typography variant="caption" color="text.secondary">Low</Typography>
                          <Typography variant="body2">${formatPrice(priceData.low)}</Typography>
                        </Box>
                        <Box>
                          <Typography variant="caption" color="text.secondary">Volume</Typography>
                          <Typography variant="body2">
                            {priceData.volume ? parseFloat(priceData.volume).toLocaleString(undefined, { maximumFractionDigits: 0 }) : 'N/A'}
                          </Typography>
                        </Box>
                      </Box>
                      <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                        Updated: {format(new Date(priceData.timestamp), 'HH:mm:ss')}
                      </Typography>
                    </>
                  )}
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>

      {/* Connection Statistics */}
      {connectionStats && wsConnected && (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>Connection Statistics</Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={3}>
                <Typography variant="body2" color="text.secondary">Socket ID</Typography>
                <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                  {connectionStats.socketId?.substring(0, 8)}...
                </Typography>
              </Grid>
              <Grid item xs={12} sm={3}>
                <Typography variant="body2" color="text.secondary">Subscriptions</Typography>
                <Typography variant="body2">{connectionStats.subscriptions.length}</Typography>
              </Grid>
              <Grid item xs={12} sm={3}>
                <Typography variant="body2" color="text.secondary">Reconnect Attempts</Typography>
                <Typography variant="body2">{connectionStats.reconnectAttempts}</Typography>
              </Grid>
              <Grid item xs={12} sm={3}>
                <Typography variant="body2" color="text.secondary">Status</Typography>
                <Typography variant="body2" color={connectionStats.connected ? 'success.main' : 'error.main'}>
                  {connectionStats.connected ? 'Connected' : 'Disconnected'}
                </Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default LivePriceTracker;