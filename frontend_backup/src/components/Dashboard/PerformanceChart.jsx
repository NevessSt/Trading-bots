import React from 'react';
import {
  Box,
  Typography,
  ToggleButtonGroup,
  ToggleButton,
  CircularProgress,
  useTheme,
  Paper,
  Chip,
  alpha
} from '@mui/material';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip as RechartsTooltip, 
  ResponsiveContainer,
  Legend,
  Area,
  AreaChart,
  ReferenceLine
} from 'recharts';
import { format, parseISO } from 'date-fns';
import { TrendingUpIcon, TrendingDownIcon } from '@heroicons/react/24/outline';

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
      const value = payload[0]?.value || 0;
      const isPositive = value >= 0;
      
      return (
        <Paper
          elevation={8}
          sx={{
            p: 2,
            borderRadius: 2,
            background: `linear-gradient(135deg, ${alpha(theme.palette.background.paper, 0.95)} 0%, ${alpha(theme.palette.background.paper, 0.98)} 100%)`,
            backdropFilter: 'blur(10px)',
            border: `1px solid ${alpha(theme.palette.divider, 0.2)}`,
            minWidth: 200,
          }}
        >
          <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
            {format(date, 'MMM dd, yyyy HH:mm')}
          </Typography>
          {payload.map((entry) => (
            <Box key={entry.name} sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mt: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Box 
                  component="span" 
                  sx={{ 
                    display: 'inline-block', 
                    width: 12, 
                    height: 12, 
                    borderRadius: '50%', 
                    backgroundColor: entry.color,
                    mr: 1.5,
                    boxShadow: `0 0 8px ${alpha(entry.color, 0.4)}`
                  }} 
                />
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  {entry.name}
                </Typography>
              </Box>
              <Chip
                label={`${entry.value >= 0 ? '+' : ''}${entry.value.toFixed(2)}%`}
                size="small"
                color={entry.value >= 0 ? 'success' : 'error'}
                variant="outlined"
                sx={{ 
                  fontWeight: 600,
                  '& .MuiChip-label': { px: 1 }
                }}
              />
            </Box>
          ))}
        </Paper>
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

    const gradientId = `gradient-${Math.random().toString(36).substr(2, 9)}`;
    const benchmarkGradientId = `benchmark-gradient-${Math.random().toString(36).substr(2, 9)}`;
    
    return (
      <ResponsiveContainer width="100%" height={350}>
        <AreaChart
          data={performance.chart_data}
          margin={{ top: 20, right: 30, left: 0, bottom: 20 }}
        >
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={theme.palette.primary.main} stopOpacity={0.3}/>
              <stop offset="95%" stopColor={theme.palette.primary.main} stopOpacity={0.05}/>
            </linearGradient>
            <linearGradient id={benchmarkGradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={theme.palette.secondary.main} stopOpacity={0.2}/>
              <stop offset="95%" stopColor={theme.palette.secondary.main} stopOpacity={0.02}/>
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
            tickFormatter={formatXAxis} 
            stroke={theme.palette.text.secondary}
            tick={{ fontSize: 11, fill: theme.palette.text.secondary }}
            axisLine={false}
            tickLine={false}
            dy={10}
          />
          <YAxis 
            tickFormatter={(value) => `${value}%`}
            stroke={theme.palette.text.secondary}
            tick={{ fontSize: 11, fill: theme.palette.text.secondary }}
            axisLine={false}
            tickLine={false}
            dx={-10}
          />
          <RechartsTooltip content={<CustomTooltip />} />
          <ReferenceLine y={0} stroke={theme.palette.divider} strokeDasharray="2 2" />
          
          {performance.benchmark_data && (
            <Area
              type="monotone"
              dataKey="benchmark"
              name="Benchmark"
              stroke={theme.palette.secondary.main}
              strokeWidth={2}
              fill={`url(#${benchmarkGradientId})`}
              strokeDasharray="8 4"
              dot={false}
              activeDot={{ 
                r: 6, 
                fill: theme.palette.secondary.main,
                stroke: theme.palette.background.paper,
                strokeWidth: 2
              }}
            />
          )}
          
          <Area
            type="monotone"
            dataKey="profit_loss"
            name="Profit/Loss"
            stroke={theme.palette.primary.main}
            strokeWidth={3}
            fill={`url(#${gradientId})`}
            dot={false}
            activeDot={{ 
              r: 8, 
              fill: theme.palette.primary.main,
              stroke: theme.palette.background.paper,
              strokeWidth: 3,
              boxShadow: `0 0 12px ${alpha(theme.palette.primary.main, 0.4)}`
            }}
          />
        </AreaChart>
      </ResponsiveContainer>
    );
  };

  return (
    <Paper 
      elevation={0}
      sx={{ 
        p: 3, 
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
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="h5" component="h2" sx={{ fontWeight: 700, color: theme.palette.text.primary }}>
            Performance Analytics
          </Typography>
          {performance && performance.total_profit_loss !== null && performance.total_profit_loss !== undefined && (
            <Chip
              icon={performance.total_profit_loss >= 0 ? <TrendingUpIcon className="w-4 h-4" /> : <TrendingDownIcon className="w-4 h-4" />}
              label={`${performance.total_profit_loss >= 0 ? '+' : ''}${performance.total_profit_loss.toFixed(2)}%`}
              color={performance.total_profit_loss >= 0 ? 'success' : 'error'}
              variant="outlined"
              sx={{ fontWeight: 600 }}
            />
          )}
        </Box>
        <ToggleButtonGroup
          value={timeframe}
          exclusive
          onChange={handleTimeframeChange}
          size="small"
          sx={{
            '& .MuiToggleButton-root': {
              border: `1px solid ${alpha(theme.palette.divider, 0.3)}`,
              borderRadius: 2,
              px: 2,
              py: 0.5,
              fontWeight: 600,
              fontSize: '0.875rem',
              transition: 'all 0.2s ease-in-out',
              '&:hover': {
                backgroundColor: alpha(theme.palette.primary.main, 0.08),
                borderColor: alpha(theme.palette.primary.main, 0.3)
              },
              '&.Mui-selected': {
                backgroundColor: alpha(theme.palette.primary.main, 0.12),
                borderColor: theme.palette.primary.main,
                color: theme.palette.primary.main,
                '&:hover': {
                  backgroundColor: alpha(theme.palette.primary.main, 0.16)
                }
              }
            }
          }}
        >
          <ToggleButton value="24h">24H</ToggleButton>
          <ToggleButton value="7d">7D</ToggleButton>
          <ToggleButton value="30d">30D</ToggleButton>
          <ToggleButton value="all">All</ToggleButton>
        </ToggleButtonGroup>
      </Box>

      {isLoading ? (
        <Box sx={{ 
          display: 'flex', 
          flexDirection: 'column',
          justifyContent: 'center', 
          alignItems: 'center', 
          height: 350,
          gap: 2
        }}>
          <CircularProgress 
            size={48} 
            thickness={4}
            sx={{ 
              color: theme.palette.primary.main,
              '& .MuiCircularProgress-circle': {
                strokeLinecap: 'round'
              }
            }} 
          />
          <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500 }}>
            Loading performance data...
          </Typography>
        </Box>
      ) : (
        renderPerformanceData()
      )}

      {performance && (
        <Box sx={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', 
          gap: 3, 
          mt: 3,
          pt: 3,
          borderTop: `1px solid ${alpha(theme.palette.divider, 0.1)}`
        }}>
          <Box sx={{ 
            textAlign: 'center',
            p: 2,
            borderRadius: 2,
            background: alpha((performance.total_profit_loss || 0) >= 0 ? theme.palette.success.main : theme.palette.error.main, 0.05),
            border: `1px solid ${alpha((performance.total_profit_loss || 0) >= 0 ? theme.palette.success.main : theme.palette.error.main, 0.1)}`
          }}>
            <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500, mb: 1 }}>
              Total Profit/Loss
            </Typography>
            <Typography 
              variant="h5" 
              sx={{
                fontWeight: 700,
                color: (performance.total_profit_loss || 0) >= 0 ? 'success.main' : 'error.main'
              }}
            >
              {(performance.total_profit_loss || 0) >= 0 ? '+' : ''}
              {(performance.total_profit_loss || 0).toFixed(2)}%
            </Typography>
          </Box>
          
          <Box sx={{ 
            textAlign: 'center',
            p: 2,
            borderRadius: 2,
            background: alpha(theme.palette.info.main, 0.05),
            border: `1px solid ${alpha(theme.palette.info.main, 0.1)}`
          }}>
            <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500, mb: 1 }}>
              Win Rate
            </Typography>
            <Typography variant="h5" sx={{ fontWeight: 700, color: 'info.main' }}>
              {performance.win_rate?.toFixed(1)}%
            </Typography>
          </Box>
          
          <Box sx={{ 
            textAlign: 'center',
            p: 2,
            borderRadius: 2,
            background: alpha(theme.palette.primary.main, 0.05),
            border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`
          }}>
            <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500, mb: 1 }}>
              Total Trades
            </Typography>
            <Typography variant="h5" sx={{ fontWeight: 700, color: 'primary.main' }}>
              {performance.total_trades || 0}
            </Typography>
          </Box>
        </Box>
      )}
    </Paper>
  );
};

export default PerformanceChart;