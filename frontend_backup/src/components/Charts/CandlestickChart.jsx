import React, { useEffect, useRef, useState } from 'react';
import { createChart, ColorType } from 'lightweight-charts';
import { Box, Typography, FormControl, InputLabel, Select, MenuItem, IconButton, Tooltip } from '@mui/material';
import { Fullscreen, FullscreenExit, Settings } from '@mui/icons-material';

const CandlestickChart = ({ 
  data = [], 
  symbol = 'BTCUSDT', 
  height = 400,
  showVolume = true,
  showIndicators = true,
  onIntervalChange,
  interval = '1h'
}) => {
  const chartContainerRef = useRef();
  const chart = useRef();
  const candlestickSeries = useRef();
  const volumeSeries = useRef();
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [chartHeight, setChartHeight] = useState(height);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Create chart
    chart.current = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#ffffff' },
        textColor: '#333',
      },
      width: chartContainerRef.current.clientWidth,
      height: chartHeight,
      grid: {
        vertLines: {
          color: '#f0f0f0',
        },
        horzLines: {
          color: '#f0f0f0',
        },
      },
      crosshair: {
        mode: 1, // Normal crosshair mode
      },
      rightPriceScale: {
        borderColor: '#cccccc',
        scaleMargins: {
          top: 0.1,
          bottom: showVolume ? 0.4 : 0.1,
        },
      },
      timeScale: {
        borderColor: '#cccccc',
        timeVisible: true,
        secondsVisible: false,
      },
    });

    // Add candlestick series
    candlestickSeries.current = chart.current.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    });

    // Add volume series if enabled
    if (showVolume) {
      volumeSeries.current = chart.current.addHistogramSeries({
        color: '#26a69a',
        priceFormat: {
          type: 'volume',
        },
        priceScaleId: 'volume',
        scaleMargins: {
          top: 0.7,
          bottom: 0,
        },
      });
    }

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
  }, [chartHeight, showVolume]);

  useEffect(() => {
    if (!candlestickSeries.current || !data || data.length === 0) return;

    // Format data for candlestick chart
    const candlestickData = data.map(item => ({
      time: Math.floor(item[0] / 1000), // Convert to seconds
      open: parseFloat(item[1]),
      high: parseFloat(item[2]),
      low: parseFloat(item[3]),
      close: parseFloat(item[4]),
    }));

    // Format volume data
    const volumeData = showVolume ? data.map(item => ({
      time: Math.floor(item[0] / 1000),
      value: parseFloat(item[5]),
      color: parseFloat(item[4]) >= parseFloat(item[1]) ? '#26a69a80' : '#ef535080',
    })) : [];

    // Set data
    candlestickSeries.current.setData(candlestickData);
    if (volumeSeries.current && volumeData.length > 0) {
      volumeSeries.current.setData(volumeData);
    }

    // Fit content
    chart.current.timeScale().fitContent();
  }, [data, showVolume]);

  const handleIntervalChange = (event) => {
    if (onIntervalChange) {
      onIntervalChange(event.target.value);
    }
  };

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
    setChartHeight(isFullscreen ? height : window.innerHeight - 100);
  };

  const intervals = [
    { value: '1m', label: '1m' },
    { value: '5m', label: '5m' },
    { value: '15m', label: '15m' },
    { value: '30m', label: '30m' },
    { value: '1h', label: '1h' },
    { value: '4h', label: '4h' },
    { value: '1d', label: '1d' },
    { value: '1w', label: '1w' },
  ];

  return (
    <Box sx={{ 
      position: isFullscreen ? 'fixed' : 'relative',
      top: isFullscreen ? 0 : 'auto',
      left: isFullscreen ? 0 : 'auto',
      width: isFullscreen ? '100vw' : '100%',
      height: isFullscreen ? '100vh' : 'auto',
      zIndex: isFullscreen ? 9999 : 'auto',
      bgcolor: 'background.paper',
      border: 1,
      borderColor: 'divider',
      borderRadius: isFullscreen ? 0 : 1,
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
        <Typography variant="h6" component="h3">
          {symbol.replace('USDT', '/USDT')} Chart
        </Typography>
        
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <FormControl size="small" sx={{ minWidth: 80 }}>
            <InputLabel>Interval</InputLabel>
            <Select
              value={interval}
              label="Interval"
              onChange={handleIntervalChange}
            >
              {intervals.map((int) => (
                <MenuItem key={int.value} value={int.value}>
                  {int.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          
          <Tooltip title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}>
            <IconButton onClick={toggleFullscreen} size="small">
              {isFullscreen ? <FullscreenExit /> : <Fullscreen />}
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Chart Settings">
            <IconButton size="small">
              <Settings />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Chart Container */}
      <Box 
        ref={chartContainerRef} 
        sx={{ 
          width: '100%', 
          height: chartHeight,
          position: 'relative'
        }} 
      />

      {/* Chart Info */}
      {data && data.length > 0 && (
        <Box sx={{ 
          display: 'flex', 
          justifyContent: 'space-around', 
          p: 1, 
          bgcolor: 'grey.50',
          borderTop: 1,
          borderColor: 'divider'
        }}>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="caption" color="text.secondary">Open</Typography>
            <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
              ${parseFloat(data[data.length - 1]?.[1]).toFixed(4)}
            </Typography>
          </Box>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="caption" color="text.secondary">High</Typography>
            <Typography variant="body2" sx={{ fontWeight: 'bold', color: 'success.main' }}>
              ${parseFloat(data[data.length - 1]?.[2]).toFixed(4)}
            </Typography>
          </Box>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="caption" color="text.secondary">Low</Typography>
            <Typography variant="body2" sx={{ fontWeight: 'bold', color: 'error.main' }}>
              ${parseFloat(data[data.length - 1]?.[3]).toFixed(4)}
            </Typography>
          </Box>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="caption" color="text.secondary">Close</Typography>
            <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
              ${parseFloat(data[data.length - 1]?.[4]).toFixed(4)}
            </Typography>
          </Box>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="caption" color="text.secondary">Volume</Typography>
            <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
              {parseFloat(data[data.length - 1]?.[5]).toLocaleString()}
            </Typography>
          </Box>
        </Box>
      )}
    </Box>
  );
};

export default CandlestickChart;