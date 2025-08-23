import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Chip,
  IconButton,
  Tooltip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Avatar,
  LinearProgress
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Refresh,
  ShowChart,
  Timeline,
  Assessment,
  Speed
} from '@mui/icons-material';

const MarketOverview = ({ 
  marketData = [],
  indices = [],
  onRefresh,
  autoRefresh = true
}) => {
  const [topGainers, setTopGainers] = useState([]);
  const [topLosers, setTopLosers] = useState([]);
  const [marketStats, setMarketStats] = useState({
    totalMarketCap: 0,
    totalVolume: 0,
    btcDominance: 0,
    fearGreedIndex: 50
  });

  useEffect(() => {
    if (marketData.length === 0) return;

    // Sort by 24h change percentage
    const sortedData = [...marketData].sort((a, b) => 
      parseFloat(b.priceChangePercent || 0) - parseFloat(a.priceChangePercent || 0)
    );

    setTopGainers(sortedData.slice(0, 5));
    setTopLosers(sortedData.slice(-5).reverse());

    // Calculate market stats (mock data for demonstration)
    const totalVolume = marketData.reduce((sum, item) => 
      sum + parseFloat(item.volume || 0), 0
    );

    setMarketStats({
      totalMarketCap: 2.1e12, // $2.1T
      totalVolume,
      btcDominance: 52.3,
      fearGreedIndex: Math.floor(Math.random() * 100)
    });
  }, [marketData]);

  const formatCurrency = (value, decimals = 2) => {
    if (value >= 1e12) {
      return `$${(value / 1e12).toFixed(1)}T`;
    } else if (value >= 1e9) {
      return `$${(value / 1e9).toFixed(1)}B`;
    } else if (value >= 1e6) {
      return `$${(value / 1e6).toFixed(1)}M`;
    } else if (value >= 1e3) {
      return `$${(value / 1e3).toFixed(1)}K`;
    }
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }).format(value);
  };

  const formatPercentage = (value) => {
    const num = parseFloat(value || 0);
    return `${num >= 0 ? '+' : ''}${num.toFixed(2)}%`;
  };

  const getPercentageColor = (value) => {
    const num = parseFloat(value || 0);
    return num >= 0 ? 'success.main' : 'error.main';
  };

  const getFearGreedColor = (value) => {
    if (value <= 25) return 'error.main';
    if (value <= 45) return 'warning.main';
    if (value <= 55) return 'info.main';
    if (value <= 75) return 'success.light';
    return 'success.main';
  };

  const getFearGreedLabel = (value) => {
    if (value <= 25) return 'Extreme Fear';
    if (value <= 45) return 'Fear';
    if (value <= 55) return 'Neutral';
    if (value <= 75) return 'Greed';
    return 'Extreme Greed';
  };

  const MarketStatCard = ({ title, value, subtitle, icon, color = 'primary' }) => (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          {icon}
          <Typography variant="h6" sx={{ ml: 1, fontWeight: 'medium' }}>
            {title}
          </Typography>
        </Box>
        <Typography variant="h4" sx={{ fontWeight: 'bold', color: `${color}.main` }}>
          {value}
        </Typography>
        {subtitle && (
          <Typography variant="body2" color="text.secondary">
            {subtitle}
          </Typography>
        )}
      </CardContent>
    </Card>
  );

  const CryptoRow = ({ crypto, showRank = false }) => (
    <TableRow sx={{ '&:hover': { bgcolor: 'action.hover' } }}>
      <TableCell>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Avatar sx={{ width: 32, height: 32, fontSize: 12 }}>
            {crypto.symbol?.substring(0, 2) || 'BT'}
          </Avatar>
          <Box>
            <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
              {crypto.symbol?.replace('USDT', '') || 'BTC'}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {crypto.baseAsset || crypto.symbol?.replace('USDT', '')}
            </Typography>
          </Box>
        </Box>
      </TableCell>
      <TableCell align="right">
        <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
          {formatCurrency(crypto.price || crypto.lastPrice)}
        </Typography>
      </TableCell>
      <TableCell align="right">
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 0.5 }}>
          {parseFloat(crypto.priceChangePercent || 0) >= 0 ? (
            <TrendingUp sx={{ fontSize: 16, color: 'success.main' }} />
          ) : (
            <TrendingDown sx={{ fontSize: 16, color: 'error.main' }} />
          )}
          <Typography 
            variant="body2" 
            sx={{ 
              fontWeight: 'medium',
              color: getPercentageColor(crypto.priceChangePercent)
            }}
          >
            {formatPercentage(crypto.priceChangePercent)}
          </Typography>
        </Box>
      </TableCell>
      <TableCell align="right">
        <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
          {formatCurrency(crypto.volume || crypto.quoteVolume)}
        </Typography>
      </TableCell>
    </TableRow>
  );

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        mb: 3 
      }}>
        <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
          Market Overview
        </Typography>
        
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {autoRefresh && (
            <Chip 
              label="Live" 
              color="success" 
              size="small" 
              variant="outlined"
            />
          )}
          <Tooltip title="Refresh Data">
            <IconButton onClick={onRefresh}>
              <Refresh />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Market Stats */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <MarketStatCard
            title="Market Cap"
            value={formatCurrency(marketStats.totalMarketCap)}
            subtitle="Total cryptocurrency market cap"
            icon={<Assessment color="primary" />}
            color="primary"
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <MarketStatCard
            title="24h Volume"
            value={formatCurrency(marketStats.totalVolume)}
            subtitle="Total trading volume"
            icon={<ShowChart color="info" />}
            color="info"
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <MarketStatCard
            title="BTC Dominance"
            value={`${marketStats.btcDominance}%`}
            subtitle="Bitcoin market dominance"
            icon={<Timeline color="warning" />}
            color="warning"
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Speed />
                <Typography variant="h6" sx={{ ml: 1, fontWeight: 'medium' }}>
                  Fear & Greed
                </Typography>
              </Box>
              <Typography 
                variant="h4" 
                sx={{ 
                  fontWeight: 'bold', 
                  color: getFearGreedColor(marketStats.fearGreedIndex)
                }}
              >
                {marketStats.fearGreedIndex}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {getFearGreedLabel(marketStats.fearGreedIndex)}
              </Typography>
              <LinearProgress 
                variant="determinate" 
                value={marketStats.fearGreedIndex} 
                sx={{ 
                  mt: 1, 
                  height: 6, 
                  borderRadius: 3,
                  '& .MuiLinearProgress-bar': {
                    backgroundColor: getFearGreedColor(marketStats.fearGreedIndex)
                  }
                }}
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Top Gainers and Losers */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
              <TrendingUp color="success" />
              Top Gainers
            </Typography>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Asset</TableCell>
                    <TableCell align="right">Price</TableCell>
                    <TableCell align="right">24h Change</TableCell>
                    <TableCell align="right">Volume</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {topGainers.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={4} align="center" sx={{ py: 3 }}>
                        <Typography color="text.secondary">
                          No data available
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ) : (
                    topGainers.map((crypto, index) => (
                      <CryptoRow key={crypto.symbol || index} crypto={crypto} />
                    ))
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
              <TrendingDown color="error" />
              Top Losers
            </Typography>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Asset</TableCell>
                    <TableCell align="right">Price</TableCell>
                    <TableCell align="right">24h Change</TableCell>
                    <TableCell align="right">Volume</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {topLosers.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={4} align="center" sx={{ py: 3 }}>
                        <Typography color="text.secondary">
                          No data available
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ) : (
                    topLosers.map((crypto, index) => (
                      <CryptoRow key={crypto.symbol || index} crypto={crypto} />
                    ))
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default MarketOverview;