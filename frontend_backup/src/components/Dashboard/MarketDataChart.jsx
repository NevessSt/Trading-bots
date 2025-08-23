import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  CircularProgress,
  useTheme,
  alpha,
  Paper,
  Chip
} from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  ReferenceLine
} from 'recharts';
import { TrendingUpIcon, TrendingDownIcon, ChartBarIcon } from '@heroicons/react/24/outline';
import useTradingStore from '../../stores/useTradingStore';

const MarketDataChart = ({ symbol = 'BTCUSDT' }) => {
  const theme = useTheme();
  const { marketData, fetchMarketData } = useTradingStore();
  const [interval, setInterval] = useState('1h');
  const [limit, setLimit] = useState(100);
  const [isLoading, setIsLoading] = useState(false);
  
  const dataKey = `${symbol}_${interval}`;
  const chartData = marketData[dataKey];
  
  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true);
      await fetchMarketData(symbol, interval, limit);
      setIsLoading(false);
    };
    
    loadData();
  }, [symbol, interval, limit, fetchMarketData]);
  
  const handleIntervalChange = (event) => {
    setInterval(event.target.value);
  };
  
  const handleLimitChange = (event) => {
    setLimit(event.target.value);
  };
  
  const formatChartData = (data) => {
    if (!data || !Array.isArray(data)) return [];
    
    return data.map((item, index) => ({
      timestamp: new Date(item[0]).toLocaleTimeString(),
      open: parseFloat(item[1]),
      high: parseFloat(item[2]),
      low: parseFloat(item[3]),
      close: parseFloat(item[4]),
      volume: parseFloat(item[5]),
      index
    }));
  };
  
  const formattedData = formatChartData(chartData);
  
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      const priceChange = data.close - data.open;
      const priceChangePercent = ((priceChange / data.open) * 100);
      const isPositive = priceChange >= 0;
      
      return (
        <Paper
          elevation={8}
          sx={{
            p: 2.5,
            borderRadius: 2,
            background: `linear-gradient(135deg, ${alpha(theme.palette.background.paper, 0.95)} 0%, ${alpha(theme.palette.background.paper, 0.98)} 100%)`,
            backdropFilter: 'blur(10px)',
            border: `1px solid ${alpha(theme.palette.divider, 0.2)}`,
            minWidth: 220,
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
              {label}
            </Typography>
            <Chip
              icon={isPositive ? <TrendingUpIcon className="w-3 h-3" /> : <TrendingDownIcon className="w-3 h-3" />}
              label={`${isPositive ? '+' : ''}${priceChangePercent.toFixed(2)}%`}
              size="small"
              color={isPositive ? 'success' : 'error'}
              variant="outlined"
              sx={{ fontWeight: 600 }}
            />
          </Box>
          
          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1.5 }}>
            <Box>
              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 500 }}>
                Open
              </Typography>
              <Typography variant="body2" sx={{ fontWeight: 600, color: 'primary.main' }}>
                ${data.open?.toFixed(4)}
              </Typography>
            </Box>
            
            <Box>
              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 500 }}>
                Close
              </Typography>
              <Typography variant="body2" sx={{ fontWeight: 600, color: isPositive ? 'success.main' : 'error.main' }}>
                ${data.close?.toFixed(4)}
              </Typography>
            </Box>
            
            <Box>
              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 500 }}>
                High
              </Typography>
              <Typography variant="body2" sx={{ fontWeight: 600, color: 'success.main' }}>
                ${data.high?.toFixed(4)}
              </Typography>
            </Box>
            
            <Box>
              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 500 }}>
                Low
              </Typography>
              <Typography variant="body2" sx={{ fontWeight: 600, color: 'error.main' }}>
                ${data.low?.toFixed(4)}
              </Typography>
            </Box>
          </Box>
          
          <Box sx={{ mt: 2, pt: 1.5, borderTop: `1px solid ${alpha(theme.palette.divider, 0.1)}` }}>
            <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 500 }}>
              Volume
            </Typography>
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              {data.volume?.toLocaleString()}
            </Typography>
          </Box>
        </Paper>
      );
    }
    return null;
  };
  
  const currentPrice = formattedData.length > 0 ? formattedData[formattedData.length - 1]?.close : 0;
  const previousPrice = formattedData.length > 1 ? formattedData[formattedData.length - 2]?.close : currentPrice;
  const priceChange = currentPrice - previousPrice;
  const priceChangePercent = previousPrice ? ((priceChange / previousPrice) * 100) : 0;
  const isPositive = priceChange >= 0;
  
  return (
    <Paper 
      elevation={0}
      sx={{ 
        mb: 3,
        borderRadius: 3,
        background: `linear-gradient(135deg, ${alpha(theme.palette.background.paper, 0.8)} 0%, ${alpha(theme.palette.background.paper, 0.95)} 100%)`,
        backdropFilter: 'blur(20px)',
        border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
        position: 'relative',
        overflow: 'hidden',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '1px',
          background: `linear-gradient(90deg, transparent 0%, ${alpha(theme.palette.primary.main, 0.3)} 50%, transparent 100%)`
        }
      }}
    >
      <Box sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <ChartBarIcon className="w-6 h-6" style={{ color: theme.palette.primary.main }} />
            <Box>
              <Typography variant="h5" sx={{ fontWeight: 700, color: theme.palette.text.primary }}>
                {symbol.replace('USDT', '/USDT')}
              </Typography>
              {currentPrice > 0 && (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    ${currentPrice.toFixed(4)}
                  </Typography>
                  <Chip
                    icon={isPositive ? <TrendingUpIcon className="w-3 h-3" /> : <TrendingDownIcon className="w-3 h-3" />}
                    label={`${isPositive ? '+' : ''}${priceChangePercent.toFixed(2)}%`}
                    size="small"
                    color={isPositive ? 'success' : 'error'}
                    variant="outlined"
                    sx={{ fontWeight: 600 }}
                  />
                </Box>
              )}
            </Box>
          </Box>
          
          <Box sx={{ display: 'flex', gap: 2 }}>
            <FormControl size="small" sx={{ minWidth: 100 }}>
              <InputLabel>Interval</InputLabel>
              <Select
                value={interval}
                label="Interval"
                onChange={handleIntervalChange}
              >
                <MenuItem value="1m">1m</MenuItem>
                <MenuItem value="5m">5m</MenuItem>
                <MenuItem value="15m">15m</MenuItem>
                <MenuItem value="1h">1h</MenuItem>
                <MenuItem value="4h">4h</MenuItem>
                <MenuItem value="1d">1d</MenuItem>
              </Select>
            </FormControl>
            
            <FormControl size="small" sx={{ minWidth: 100 }}>
              <InputLabel>Candles</InputLabel>
              <Select
                value={limit}
                label="Candles"
                onChange={handleLimitChange}
              >
                <MenuItem value={50}>50</MenuItem>
                <MenuItem value={100}>100</MenuItem>
                <MenuItem value={200}>200</MenuItem>
                <MenuItem value={500}>500</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </Box>
        
        {isLoading ? (
          <Box sx={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', height: 400, gap: 2 }}>
            <CircularProgress 
              size={48} 
              thickness={4} 
              sx={{ color: theme.palette.primary.main }}
            />
            <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500 }}>
              Loading market data...
            </Typography>
          </Box>
        ) : formattedData.length > 0 ? (
          <Box sx={{ position: 'relative' }}>
            <ResponsiveContainer width="100%" height={450}>
              <AreaChart data={formattedData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                <defs>
                  <linearGradient id="closeGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={theme.palette.primary.main} stopOpacity={0.3}/>
                    <stop offset="95%" stopColor={theme.palette.primary.main} stopOpacity={0.05}/>
                  </linearGradient>
                  <linearGradient id="highGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={theme.palette.success.main} stopOpacity={0.2}/>
                    <stop offset="95%" stopColor={theme.palette.success.main} stopOpacity={0.02}/>
                  </linearGradient>
                  <linearGradient id="lowGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={theme.palette.error.main} stopOpacity={0.2}/>
                    <stop offset="95%" stopColor={theme.palette.error.main} stopOpacity={0.02}/>
                  </linearGradient>
                </defs>
                <CartesianGrid 
                  strokeDasharray="3 3" 
                  stroke={alpha(theme.palette.divider, 0.3)}
                  horizontal={true}
                  vertical={false}
                />
                <XAxis 
                  dataKey="timestamp" 
                  tick={{ fontSize: 11, fill: theme.palette.text.secondary }}
                  axisLine={false}
                  tickLine={false}
                  dy={10}
                  interval="preserveStartEnd"
                />
                <YAxis 
                  domain={['dataMin - 10', 'dataMax + 10']}
                  tick={{ fontSize: 11, fill: theme.palette.text.secondary }}
                  axisLine={false}
                  tickLine={false}
                  dx={-10}
                  tickFormatter={(value) => `$${value.toFixed(2)}`}
                />
                <Tooltip content={<CustomTooltip />} />
                
                {/* Price Areas */}
                <Area 
                  type="monotone" 
                  dataKey="close" 
                  stroke={theme.palette.primary.main}
                  strokeWidth={3}
                  fill="url(#closeGradient)"
                  name="Close Price"
                  dot={false}
                  activeDot={{ 
                    r: 6, 
                    fill: theme.palette.primary.main,
                    stroke: theme.palette.background.paper,
                    strokeWidth: 2,
                    filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.2))'
                  }}
                />
                <Area 
                  type="monotone" 
                  dataKey="high" 
                  stroke={theme.palette.success.main}
                  strokeWidth={2}
                  fill="url(#highGradient)"
                  name="High"
                  dot={false}
                  activeDot={{ 
                    r: 4, 
                    fill: theme.palette.success.main,
                    stroke: theme.palette.background.paper,
                    strokeWidth: 1
                  }}
                />
                <Area 
                  type="monotone" 
                  dataKey="low" 
                  stroke={theme.palette.error.main}
                  strokeWidth={2}
                  fill="url(#lowGradient)"
                  name="Low"
                  dot={false}
                  activeDot={{ 
                    r: 4, 
                    fill: theme.palette.error.main,
                    stroke: theme.palette.background.paper,
                    strokeWidth: 1
                  }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </Box>
        ) : (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
            <Typography color="text.secondary" sx={{ fontWeight: 500 }}>
              No market data available for {symbol}
            </Typography>
          </Box>
        )}
        
        {formattedData.length > 0 && (
          <Box sx={{ mt: 4 }}>
            <Typography variant="h6" sx={{ mb: 2, fontWeight: 600, color: theme.palette.text.primary }}>
              Market Statistics
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={3}>
                <Box sx={{ 
                  p: 2.5, 
                  borderRadius: 2,
                  background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.05)} 0%, ${alpha(theme.palette.primary.main, 0.02)} 100%)`,
                  border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
                  transition: 'all 0.2s ease-in-out',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: `0 8px 25px ${alpha(theme.palette.primary.main, 0.15)}`
                  }
                }}>
                  <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500, mb: 1 }}>
                    Current Price
                  </Typography>
                  <Typography variant="h5" sx={{ fontWeight: 700, color: theme.palette.primary.main }}>
                    ${currentPrice.toFixed(4)}
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Box sx={{ 
                  p: 2.5, 
                  borderRadius: 2,
                  background: `linear-gradient(135deg, ${alpha(theme.palette.success.main, 0.05)} 0%, ${alpha(theme.palette.success.main, 0.02)} 100%)`,
                  border: `1px solid ${alpha(theme.palette.success.main, 0.1)}`,
                  transition: 'all 0.2s ease-in-out',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: `0 8px 25px ${alpha(theme.palette.success.main, 0.15)}`
                  }
                }}>
                  <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500, mb: 1 }}>
                    24h High
                  </Typography>
                  <Typography variant="h5" sx={{ fontWeight: 700, color: theme.palette.success.main }}>
                    ${Math.max(...formattedData.map(d => d.high)).toFixed(4)}
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Box sx={{ 
                  p: 2.5, 
                  borderRadius: 2,
                  background: `linear-gradient(135deg, ${alpha(theme.palette.error.main, 0.05)} 0%, ${alpha(theme.palette.error.main, 0.02)} 100%)`,
                  border: `1px solid ${alpha(theme.palette.error.main, 0.1)}`,
                  transition: 'all 0.2s ease-in-out',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: `0 8px 25px ${alpha(theme.palette.error.main, 0.15)}`
                  }
                }}>
                  <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500, mb: 1 }}>
                    24h Low
                  </Typography>
                  <Typography variant="h5" sx={{ fontWeight: 700, color: theme.palette.error.main }}>
                    ${Math.min(...formattedData.map(d => d.low)).toFixed(4)}
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Box sx={{ 
                  p: 2.5, 
                  borderRadius: 2,
                  background: `linear-gradient(135deg, ${alpha(theme.palette.info.main, 0.05)} 0%, ${alpha(theme.palette.info.main, 0.02)} 100%)`,
                  border: `1px solid ${alpha(theme.palette.info.main, 0.1)}`,
                  transition: 'all 0.2s ease-in-out',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: `0 8px 25px ${alpha(theme.palette.info.main, 0.15)}`
                  }
                }}>
                  <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500, mb: 1 }}>
                    Avg Volume
                  </Typography>
                  <Typography variant="h5" sx={{ fontWeight: 700, color: theme.palette.info.main }}>
                    {(formattedData.reduce((sum, d) => sum + d.volume, 0) / formattedData.length).toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </Box>
        )}
      </Box>
    </Paper>
  );
};

export default MarketDataChart;