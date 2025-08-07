import React from 'react';
import {
  Box,
  Typography,
  ToggleButtonGroup,
  ToggleButton,
  CircularProgress,
  useTheme
} from '@mui/material';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip as RechartsTooltip, 
  ResponsiveContainer,
  Legend
} from 'recharts';
import { format, parseISO } from 'date-fns';

const PerformanceChart = ({ performance, isLoading, timeframe, onTimeframeChange }) => {
  const theme = useTheme();

  const handleTimeframeChange = (event, newTimeframe) => {
    if (newTimeframe !== null) {
      onTimeframeChange(newTimeframe);
    }
  };

  const formatXAxis = (tickItem) => {
    const date = parseISO(tickItem);
    // Format based on timeframe
    if (timeframe === '24h') {
      return format(date, 'HH:mm');
    } else if (timeframe === '7d') {
      return format(date, 'EEE');
    } else {
      return format(date, 'MMM dd');
    }
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const date = parseISO(label);
      return (
        <Box
          sx={{
            backgroundColor: 'background.paper',
            p: 1.5,
            border: `1px solid ${theme.palette.divider}`,
            borderRadius: 1,
            boxShadow: 1,
          }}
        >
          <Typography variant="subtitle2">
            {format(date, 'MMM dd, yyyy HH:mm')}
          </Typography>
          {payload.map((entry) => (
            <Typography 
              key={entry.name} 
              variant="body2" 
              sx={{ 
                color: entry.color,
                display: 'flex',
                alignItems: 'center',
                mt: 0.5
              }}
            >
              <Box 
                component="span" 
                sx={{ 
                  display: 'inline-block', 
                  width: 10, 
                  height: 10, 
                  borderRadius: '50%', 
                  backgroundColor: entry.color,
                  mr: 1
                }} 
              />
              {entry.name}: {entry.value.toFixed(2)}%
            </Typography>
          ))}
        </Box>
      );
    }
    return null;
  };

  const renderPerformanceData = () => {
    if (!performance || !performance.chart_data || performance.chart_data.length === 0) {
      return (
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 300 }}>
          <Typography variant="body1" color="text.secondary">
            No performance data available
          </Typography>
        </Box>
      );
    }

    return (
      <ResponsiveContainer width="100%" height={300}>
        <LineChart
          data={performance.chart_data}
          margin={{ top: 5, right: 30, left: 0, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
          <XAxis 
            dataKey="timestamp" 
            tickFormatter={formatXAxis} 
            stroke={theme.palette.text.secondary}
            tick={{ fontSize: 12 }}
          />
          <YAxis 
            tickFormatter={(value) => `${value}%`}
            stroke={theme.palette.text.secondary}
            tick={{ fontSize: 12 }}
          />
          <RechartsTooltip content={<CustomTooltip />} />
          <Legend />
          <Line
            type="monotone"
            dataKey="profit_loss"
            name="Profit/Loss"
            stroke={theme.palette.primary.main}
            activeDot={{ r: 8 }}
            strokeWidth={2}
          />
          {performance.benchmark_data && (
            <Line
              type="monotone"
              dataKey="benchmark"
              name="Benchmark"
              stroke={theme.palette.secondary.main}
              strokeWidth={2}
              strokeDasharray="5 5"
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    );
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6" component="h2">
          Performance
        </Typography>
        <ToggleButtonGroup
          value={timeframe}
          exclusive
          onChange={handleTimeframeChange}
          size="small"
        >
          <ToggleButton value="24h">
            24H
          </ToggleButton>
          <ToggleButton value="7d">
            7D
          </ToggleButton>
          <ToggleButton value="30d">
            30D
          </ToggleButton>
          <ToggleButton value="all">
            All
          </ToggleButton>
        </ToggleButtonGroup>
      </Box>

      {isLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 300 }}>
          <CircularProgress />
        </Box>
      ) : (
        renderPerformanceData()
      )}

      {performance && (
        <Box sx={{ display: 'flex', justifyContent: 'space-around', mt: 2 }}>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              Total Profit/Loss
            </Typography>
            <Typography 
              variant="h6" 
              color={performance.total_profit_loss >= 0 ? 'success.main' : 'error.main'}
            >
              {performance.total_profit_loss >= 0 ? '+' : ''}
              {performance.total_profit_loss?.toFixed(2)}%
            </Typography>
          </Box>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              Win Rate
            </Typography>
            <Typography variant="h6">
              {performance.win_rate?.toFixed(2)}%
            </Typography>
          </Box>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              Total Trades
            </Typography>
            <Typography variant="h6">
              {performance.total_trades || 0}
            </Typography>
          </Box>
        </Box>
      )}
    </Box>
  );
};

export default PerformanceChart;