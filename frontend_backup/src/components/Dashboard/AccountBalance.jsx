import React, { useEffect, useState } from 'react';
import { 
  Box, 
  Typography, 
  Card, 
  CardContent, 
  Grid, 
  Chip,
  IconButton,
  Tooltip,
  CircularProgress
} from '@mui/material';
import { 
  Refresh, 
  AccountBalanceWallet, 
  TrendingUp,
  Visibility,
  VisibilityOff
} from '@mui/icons-material';
import useTradingStore from '../../stores/useTradingStore';

const AccountBalance = () => {
  const { 
    accountBalance, 
    fetchAccountBalance, 
    isLoading 
  } = useTradingStore();
  
  const [showBalances, setShowBalances] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(null);
  
  useEffect(() => {
    // Fetch initial balance
    fetchAccountBalance().then(() => {
      setLastUpdated(new Date());
    });
    
    // Set up periodic refresh every 30 seconds
    const interval = setInterval(() => {
      fetchAccountBalance().then(() => {
        setLastUpdated(new Date());
      });
    }, 30000);
    
    return () => clearInterval(interval);
  }, [fetchAccountBalance]);
  
  const handleRefresh = () => {
    fetchAccountBalance().then(() => {
      setLastUpdated(new Date());
    });
  };
  
  const formatBalance = (balance) => {
    if (!showBalances) return '••••••';
    return parseFloat(balance).toFixed(6);
  };
  
  const formatUSDValue = (balance, price = 1) => {
    if (!showBalances) return '••••••';
    const usdValue = parseFloat(balance) * price;
    return usdValue.toLocaleString('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  };
  
  if (isLoading && !accountBalance) {
    return (
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', py: 4 }}>
            <CircularProgress size={40} />
            <Typography sx={{ ml: 2 }}>Loading account balance...</Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }
  
  if (!accountBalance) {
    return (
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography color="error">Failed to load account balance</Typography>
        </CardContent>
      </Card>
    );
  }
  
  const totalUSDValue = accountBalance.balances?.reduce((total, balance) => {
    return total + (parseFloat(balance.free) + parseFloat(balance.locked)) * (balance.usdPrice || 0);
  }, 0) || 0;
  
  const significantBalances = accountBalance.balances?.filter(balance => 
    parseFloat(balance.free) > 0.001 || parseFloat(balance.locked) > 0.001
  ) || [];
  
  return (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <AccountBalanceWallet sx={{ mr: 1, color: 'primary.main' }} />
            <Typography variant="h6">Account Balance</Typography>
          </Box>
          
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Tooltip title={showBalances ? 'Hide balances' : 'Show balances'}>
              <IconButton 
                onClick={() => setShowBalances(!showBalances)}
                size="small"
              >
                {showBalances ? <VisibilityOff /> : <Visibility />}
              </IconButton>
            </Tooltip>
            
            <Tooltip title="Refresh balance">
              <IconButton 
                onClick={handleRefresh} 
                disabled={isLoading}
                size="small"
              >
                <Refresh sx={{ 
                  animation: isLoading ? 'spin 1s linear infinite' : 'none',
                  '@keyframes spin': {
                    '0%': { transform: 'rotate(0deg)' },
                    '100%': { transform: 'rotate(360deg)' }
                  }
                }} />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
        
        {/* Total Portfolio Value */}
        <Box sx={{ mb: 3, p: 2, bgcolor: 'primary.main', borderRadius: 2, color: 'white' }}>
          <Typography variant="body2" sx={{ opacity: 0.9 }}>
            Total Portfolio Value
          </Typography>
          <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
            {formatUSDValue(totalUSDValue)}
          </Typography>
        </Box>
        
        {/* Individual Balances */}
        <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 'bold' }}>
          Asset Breakdown
        </Typography>
        
        <Grid container spacing={2}>
          {significantBalances.length > 0 ? (
            significantBalances.map((balance, index) => {
              const totalBalance = parseFloat(balance.free) + parseFloat(balance.locked);
              const usdValue = totalBalance * (balance.usdPrice || 0);
              
              return (
                <Grid item xs={12} sm={6} md={4} key={balance.asset || index}>
                  <Card variant="outlined" sx={{ height: '100%' }}>
                    <CardContent sx={{ p: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                        <Typography variant="h6" component="div">
                          {balance.asset}
                        </Typography>
                        {balance.usdPrice && (
                          <Chip 
                            icon={<TrendingUp />} 
                            label={`$${balance.usdPrice.toFixed(4)}`}
                            size="small"
                            color="primary"
                          />
                        )}
                      </Box>
                      
                      <Typography variant="h5" sx={{ fontWeight: 'bold', mb: 1 }}>
                        {formatBalance(totalBalance)}
                      </Typography>
                      
                      {usdValue > 0 && (
                        <Typography variant="body1" color="primary" sx={{ fontWeight: 'bold' }}>
                          {formatUSDValue(usdValue)}
                        </Typography>
                      )}
                      
                      <Box sx={{ mt: 1 }}>
                        <Typography variant="body2" color="text.secondary">
                          Available: {formatBalance(balance.free)}
                        </Typography>
                        {parseFloat(balance.locked) > 0 && (
                          <Typography variant="body2" color="warning.main">
                            Locked: {formatBalance(balance.locked)}
                          </Typography>
                        )}
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              );
            })
          ) : (
            <Grid item xs={12}>
              <Typography color="text.secondary" sx={{ textAlign: 'center', py: 2 }}>
                No significant balances found
              </Typography>
            </Grid>
          )}
        </Grid>
        
        {lastUpdated && (
          <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block', textAlign: 'center' }}>
            Last updated: {lastUpdated.toLocaleTimeString()}
          </Typography>
        )}
      </CardContent>
    </Card>
  );
};

export default AccountBalance;