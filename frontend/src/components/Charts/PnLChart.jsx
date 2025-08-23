import React, { useEffect, useRef, useState, useMemo, useCallback, memo } from 'react';
import { createChart, ColorType } from 'lightweight-charts';
import { Box, Typography, FormControl, InputLabel, Select, MenuItem, Chip, Grid } from '@mui/material';
import { TrendingUp, TrendingDown, ShowChart } from '@mui/icons-material';

const PnLChart = ({ 
  data = [], 
  timeframe = '24h',
  onTimeframeChange,
  height = 300
}) => {
  const chartContainerRef = useRef();
  const chart = useRef();
  const pnlSeries = useRef();
  const [stats, setStats] = useState({
    totalPnL: 0,
    dailyPnL: 0,
    winRate: 0,
    totalTrades: 0
  });

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Create chart
    chart.current = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#ffffff' },
        textColor: '#333',
      },
      width: chartContainerRef.current.clientWidth,
      height: height,
      grid: {
        vertLines: {
          color: '#f0f0f0',
        },
        horzLines: {
          color: '#f0f0f0',
        },
      },
      crosshair: {
        mode: 1,
      },
      rightPriceScale: {
        borderColor: '#cccccc',
        scaleMargins: {
          top: 0.1,
          bottom: 0.1,
        },
      },
      timeScale: {
        borderColor: '#cccccc',
        timeVisible: true,
        secondsVisible: false,
      },
    });

    // Add P&L line series
    pnlSeries.current = chart.current.addLineSeries({
      color: '#2196f3',
      lineWidth: 2,
      crosshairMarkerVisible: true,
      crosshairMarkerRadius: 6,
      priceFormat: {
        type: 'price',
        precision: 2,
        minMove: 0.01,
      },
    });

    // Handle resize
    const handleResize = () => {
      if (chart.current && chartContainerRef.current) {
        chart.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (chart.current) {
        chart.current.remove();
      }
    };
  }, [height]);

  // Memoize P&L data processing and statistics calculation
  const { pnlData, calculatedStats } = useMemo(() => {
    if (!data || data.length === 0) {
      return {
        pnlData: [],
        calculatedStats: { totalPnL: 0, dailyPnL: 0, winRate: 0, totalTrades: 0 }
      };
    }

    // Calculate cumulative P&L
    let cumulativePnL = 0;
    const pnlData = data.map((trade) => {
      cumulativePnL += parseFloat(trade.pnl || trade.profit || 0);
      return {
        time: Math.floor(new Date(trade.timestamp || trade.created_at).getTime() / 1000),
        value: cumulativePnL,
      };
    });

    // Calculate statistics
    const totalPnL = pnlData[pnlData.length - 1]?.value || 0;
    const winningTrades = data.filter(trade => parseFloat(trade.pnl || trade.profit || 0) > 0).length;
    const totalTrades = data.length;
    const winRate = totalTrades > 0 ? (winningTrades / totalTrades) * 100 : 0;
    
    // Calculate daily P&L (last 24 hours)
    const oneDayAgo = Date.now() - 24 * 60 * 60 * 1000;
    const recentTrades = data.filter(trade => 
      new Date(trade.timestamp || trade.created_at).getTime() > oneDayAgo
    );
    const dailyPnL = recentTrades.reduce((sum, trade) => 
      sum + parseFloat(trade.pnl || trade.profit || 0), 0
    );

    return {
      pnlData,
      calculatedStats: { totalPnL, dailyPnL, winRate, totalTrades }
    };
  }, [data]);

  useEffect(() => {
    if (!pnlSeries.current || pnlData.length === 0) return;

    // Update series color based on overall performance
    const finalPnL = pnlData[pnlData.length - 1]?.value || 0;
    const seriesColor = finalPnL >= 0 ? '#4caf50' : '#f44336';
    
    pnlSeries.current.applyOptions({
      color: seriesColor,
    });

    // Set data
    pnlSeries.current.setData(pnlData);

    // Update stats
    setStats(calculatedStats);

    // Fit content
    chart.current.timeScale().fitContent();
  }, [pnlData, calculatedStats]);

  const handleTimeframeChange = useCallback((event) => {
    if (onTimeframeChange) {
      onTimeframeChange(event.target.value);
    }
  }, [onTimeframeChange]);

  const timeframes = useMemo(() => [
    { value: '1h', label: '1H' },
    { value: '24h', label: '24H' },
    { value: '7d', label: '7D' },
    { value: '30d', label: '30D' },
    { value: '90d', label: '90D' },
    { value: 'all', label: 'All' },
  ], []);

  const formatCurrency = useCallback((value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  }, []);

  const formatPercentage = useCallback((value) => {
    return `${value.toFixed(1)}%`;
  }, []);

  return (
    <Box sx={{ 
      border: 1,
      borderColor: 'divider',
      borderRadius: 1,
      bgcolor: 'background.paper'
    }}>
      {/* Chart Header */}
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        p: 2, 
        borderBottom: 1, 
        borderColor: 'divider' 
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <ShowChart color="primary" />
          <Typography variant="h6" component="h3">
            Profit & Loss
          </Typography>
        </Box>
        
        <FormControl size="small" sx={{ minWidth: 80 }}>
          <InputLabel>Period</InputLabel>
          <Select
            value={timeframe}
            label="Period"
            onChange={handleTimeframeChange}
          >
            {timeframes.map((tf) => (
              <MenuItem key={tf.value} value={tf.value}>
                {tf.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      {/* Statistics Cards */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Grid container spacing={2}>
          <Grid item xs={6} sm={3}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="caption" color="text.secondary">
                Total P&L
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.5 }}>
                {stats.totalPnL >= 0 ? (
                  <TrendingUp sx={{ fontSize: 16, color: 'success.main' }} />
                ) : (
                  <TrendingDown sx={{ fontSize: 16, color: 'error.main' }} />
                )}
                <Typography 
                  variant="h6" 
                  sx={{ 
                    fontWeight: 'bold',
                    color: stats.totalPnL >= 0 ? 'success.main' : 'error.main'
                  }}
                >
                  {formatCurrency(stats.totalPnL)}
                </Typography>
              </Box>
            </Box>
          </Grid>
          
          <Grid item xs={6} sm={3}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="caption" color="text.secondary">
                24h P&L
              </Typography>
              <Typography 
                variant="h6" 
                sx={{ 
                  fontWeight: 'bold',
                  color: stats.dailyPnL >= 0 ? 'success.main' : 'error.main'
                }}
              >
                {formatCurrency(stats.dailyPnL)}
              </Typography>
            </Box>
          </Grid>
          
          <Grid item xs={6} sm={3}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="caption" color="text.secondary">
                Win Rate
              </Typography>
              <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                {formatPercentage(stats.winRate)}
              </Typography>
            </Box>
          </Grid>
          
          <Grid item xs={6} sm={3}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="caption" color="text.secondary">
                Total Trades
              </Typography>
              <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                {stats.totalTrades.toLocaleString()}
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </Box>

      {/* Chart Container */}
      <Box 
        ref={chartContainerRef} 
        sx={{ 
          width: '100%', 
          height: height,
          position: 'relative'
        }} 
      />

      {/* Performance Indicators */}
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'center', 
        gap: 1, 
        p: 1, 
        bgcolor: 'grey.50' 
      }}>
        <Chip 
          label={`Total: ${formatCurrency(stats.totalPnL)}`}
          color={stats.totalPnL >= 0 ? 'success' : 'error'}
          size="small"
          variant="outlined"
        />
        <Chip 
          label={`Win Rate: ${formatPercentage(stats.winRate)}`}
          color={stats.winRate >= 60 ? 'success' : stats.winRate >= 40 ? 'warning' : 'error'}
          size="small"
          variant="outlined"
        />
        <Chip 
          label={`${stats.totalTrades} Trades`}
          color="primary"
          size="small"
          variant="outlined"
        />
      </Box>
    </Box>
  );
};

export default memo(PnLChart);