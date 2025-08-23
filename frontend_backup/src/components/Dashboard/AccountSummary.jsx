import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Grid,
  Paper,
  Divider,
  CircularProgress,
  Button
} from '@mui/material';
import { 
  AccountBalance as BalanceIcon,
  ShowChart as EquityIcon,
  Sync as SyncIcon,
  TrendingUp as ProfitIcon,
  TrendingDown as LossIcon
} from '@mui/icons-material';
import { tradingAPI } from '../../services/api';

const AccountSummary = () => {
  const [accountData, setAccountData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchAccountData = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await tradingAPI.getTradingStatus();
      setAccountData(response.data.account);
    } catch (err) {
      setError('Failed to load account data');
      console.error('Error fetching account data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAccountData();
  }, []);

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  const renderProfitLoss = (value) => {
    const isPositive = value >= 0;
    return (
      <Box sx={{ display: 'flex', alignItems: 'center' }}>
        {isPositive ? (
          <ProfitIcon fontSize="small" color="success" sx={{ mr: 0.5 }} />
        ) : (
          <LossIcon fontSize="small" color="error" sx={{ mr: 0.5 }} />
        )}
        <Typography 
          variant="h6" 
          color={isPositive ? 'success.main' : 'error.main'}
        >
          {isPositive ? '+' : ''}{formatCurrency(value)}
        </Typography>
      </Box>
    );
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress size={30} />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ textAlign: 'center', py: 3 }}>
        <Typography variant="body1" color="error" gutterBottom>
          {error}
        </Typography>
        <Button 
          variant="outlined" 
          startIcon={<SyncIcon />}
          onClick={fetchAccountData}
          sx={{ mt: 1 }}
        >
          Retry
        </Button>
      </Box>
    );
  }

  if (!accountData) {
    return (
      <Box sx={{ textAlign: 'center', py: 3 }}>
        <Typography variant="body1" color="text.secondary">
          No account data available
        </Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6" component="h2">
          Account Summary
        </Typography>
        <Button 
          startIcon={<SyncIcon />} 
          size="small" 
          onClick={fetchAccountData}
        >
          Refresh
        </Button>
      </Box>

      <Grid container spacing={2}>
        {/* Balance */}
        <Grid item xs={12} sm={6}>
          <Paper 
            variant="outlined" 
            sx={{ 
              p: 2, 
              display: 'flex', 
              flexDirection: 'column', 
              alignItems: 'center',
              height: '100%'
            }}
          >
            <BalanceIcon color="primary" sx={{ fontSize: 40, mb: 1 }} />
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Total Balance
            </Typography>
            <Typography variant="h5">
              {formatCurrency(accountData.total_balance)}
            </Typography>
          </Paper>
        </Grid>

        {/* Equity */}
        <Grid item xs={12} sm={6}>
          <Paper 
            variant="outlined" 
            sx={{ 
              p: 2, 
              display: 'flex', 
              flexDirection: 'column', 
              alignItems: 'center',
              height: '100%'
            }}
          >
            <EquityIcon color="primary" sx={{ fontSize: 40, mb: 1 }} />
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Available Equity
            </Typography>
            <Typography variant="h5">
              {formatCurrency(accountData.available_equity)}
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      <Box sx={{ mt: 3 }}>
        <Divider sx={{ mb: 2 }} />
        <Typography variant="subtitle1" gutterBottom>
          Trading Performance
        </Typography>
        
        <Grid container spacing={2}>
          {/* Daily P/L */}
          <Grid item xs={12} sm={6}>
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Today's P/L
              </Typography>
              {renderProfitLoss(accountData.daily_pnl)}
            </Box>
          </Grid>

          {/* Total P/L */}
          <Grid item xs={12} sm={6}>
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Total P/L
              </Typography>
              {renderProfitLoss(accountData.total_pnl)}
            </Box>
          </Grid>
        </Grid>
      </Box>

      <Box sx={{ mt: 3 }}>
        <Divider sx={{ mb: 2 }} />
        <Typography variant="subtitle1" gutterBottom>
          Assets
        </Typography>
        
        <Grid container spacing={2}>
          {accountData.assets && accountData.assets.map((asset) => (
            <Grid item xs={6} key={asset.symbol}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2">
                  {asset.symbol}
                </Typography>
                <Typography variant="body2">
                  {asset.amount.toFixed(6)}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                {formatCurrency(asset.value)}
              </Typography>
            </Grid>
          ))}
        </Grid>
      </Box>
    </Box>
  );
};

export default AccountSummary;