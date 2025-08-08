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
  CircularProgress
} from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  CandlestickChart,
  ReferenceLine
} from 'recharts';
import useTradingStore from '../../stores/useTradingStore';

const MarketDataChart = ({ symbol = 'BTCUSDT' }) => {
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
      return (
        <Box
          sx={{
            bgcolor: 'background.paper',
            p: 2,
            border: 1,
            borderColor: 'divider',
            borderRadius: 1,
            boxShadow: 2
          }}
        >
          <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
            {label}
          </Typography>
          <Typography variant="body2" color="primary">
            Open: ${data.open?.toFixed(4)}
          </Typography>
          <Typography variant="body2" color="success.main">
            High: ${data.high?.toFixed(4)}
          </Typography>
          <Typography variant="body2" color="error.main">
            Low: ${data.low?.toFixed(4)}
          </Typography>
          <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
            Close: ${data.close?.toFixed(4)}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Volume: {data.volume?.toLocaleString()}
          </Typography>
        </Box>
      );
    }
    return null;
  };
  
  return (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">
            {symbol.replace('USDT', '/USDT')} Price Chart
          </Typography>
          
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
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
            <CircularProgress />
          </Box>
        ) : formattedData.length > 0 ? (
          <Box sx={{ height: 400 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={formattedData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                <XAxis 
                  dataKey="timestamp" 
                  stroke="#666"
                  fontSize={12}
                  interval="preserveStartEnd"
                />
                <YAxis 
                  stroke="#666"
                  fontSize={12}
                  domain={['dataMin - 10', 'dataMax + 10']}
                  tickFormatter={(value) => `$${value.toFixed(2)}`}
                />
                <Tooltip content={<CustomTooltip />} />
                
                {/* Price Lines */}
                <Line 
                  type="monotone" 
                  dataKey="close" 
                  stroke="#2196f3" 
                  strokeWidth={2}
                  dot={false}
                  name="Close Price"
                />
                <Line 
                  type="monotone" 
                  dataKey="high" 
                  stroke="#4caf50" 
                  strokeWidth={1}
                  dot={false}
                  strokeDasharray="5 5"
                  name="High"
                />
                <Line 
                  type="monotone" 
                  dataKey="low" 
                  stroke="#f44336" 
                  strokeWidth={1}
                  dot={false}
                  strokeDasharray="5 5"
                  name="Low"
                />
              </LineChart>
            </ResponsiveContainer>
          </Box>
        ) : (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
            <Typography color="text.secondary">
              No market data available for {symbol}
            </Typography>
          </Box>
        )}
        
        {formattedData.length > 0 && (
          <Grid container spacing={2} sx={{ mt: 2 }}>
            <Grid item xs={3}>
              <Typography variant="body2" color="text.secondary">
                Current Price
              </Typography>
              <Typography variant="h6" color="primary">
                ${formattedData[formattedData.length - 1]?.close?.toFixed(4)}
              </Typography>
            </Grid>
            <Grid item xs={3}>
              <Typography variant="body2" color="text.secondary">
                24h High
              </Typography>
              <Typography variant="h6" color="success.main">
                ${Math.max(...formattedData.map(d => d.high)).toFixed(4)}
              </Typography>
            </Grid>
            <Grid item xs={3}>
              <Typography variant="body2" color="text.secondary">
                24h Low
              </Typography>
              <Typography variant="h6" color="error.main">
                ${Math.min(...formattedData.map(d => d.low)).toFixed(4)}
              </Typography>
            </Grid>
            <Grid item xs={3}>
              <Typography variant="body2" color="text.secondary">
                Avg Volume
              </Typography>
              <Typography variant="h6">
                {(formattedData.reduce((sum, d) => sum + d.volume, 0) / formattedData.length).toLocaleString()}
              </Typography>
            </Grid>
          </Grid>
        )}
      </CardContent>
    </Card>
  );
};

export default MarketDataChart;