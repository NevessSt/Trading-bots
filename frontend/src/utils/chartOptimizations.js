import { useMemo, useCallback, useRef, useEffect, useState } from 'react';

/**
 * Custom hook for optimizing chart data processing
 * Implements data throttling and memoization for better performance
 */
export const useOptimizedChartData = (data, maxDataPoints = 1000) => {
  return useMemo(() => {
    if (!data || data.length === 0) return [];
    
    // If data is within limits, return as is
    if (data.length <= maxDataPoints) return data;
    
    // Downsample data to improve performance
    const step = Math.ceil(data.length / maxDataPoints);
    return data.filter((_, index) => index % step === 0);
  }, [data, maxDataPoints]);
};

/**
 * Custom hook for debounced chart updates
 * Prevents excessive re-renders during rapid data updates
 */
export const useDebouncedChartUpdate = (callback, delay = 300) => {
  const timeoutRef = useRef(null);
  
  return useCallback((...args) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    
    timeoutRef.current = setTimeout(() => {
      callback(...args);
    }, delay);
  }, [callback, delay]);
};

/**
 * Custom hook for lazy loading chart components
 * Only renders charts when they're visible in viewport
 */
export const useIntersectionObserver = (options = {}) => {
  const elementRef = useRef(null);
  const [isVisible, setIsVisible] = useState(false);
  
  useEffect(() => {
    const element = elementRef.current;
    if (!element) return;
    
    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsVisible(entry.isIntersecting);
      },
      {
        threshold: 0.1,
        rootMargin: '50px',
        ...options
      }
    );
    
    observer.observe(element);
    
    return () => {
      observer.unobserve(element);
    };
  }, [options]);
  
  return [elementRef, isVisible];
};

/**
 * Utility function to format large numbers for chart display
 */
export const formatChartNumber = (value, decimals = 2) => {
  if (value === null || value === undefined) return '0';
  
  const num = parseFloat(value);
  if (isNaN(num)) return '0';
  
  if (Math.abs(num) >= 1e9) {
    return (num / 1e9).toFixed(decimals) + 'B';
  } else if (Math.abs(num) >= 1e6) {
    return (num / 1e6).toFixed(decimals) + 'M';
  } else if (Math.abs(num) >= 1e3) {
    return (num / 1e3).toFixed(decimals) + 'K';
  }
  
  return num.toFixed(decimals);
};

/**
 * Utility function to calculate chart dimensions based on container
 */
export const useChartDimensions = (containerRef, aspectRatio = 16/9) => {
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const { clientWidth } = containerRef.current;
        setDimensions({
          width: clientWidth,
          height: clientWidth / aspectRatio
        });
      }
    };
    
    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    
    return () => {
      window.removeEventListener('resize', updateDimensions);
    };
  }, [aspectRatio]);
  
  return dimensions;
};

/**
 * Performance monitoring hook for charts
 */
export const useChartPerformance = (chartName) => {
  const renderCount = useRef(0);
  const lastRenderTime = useRef(Date.now());
  
  useEffect(() => {
    renderCount.current += 1;
    const now = Date.now();
    const timeSinceLastRender = now - lastRenderTime.current;
    
    if (process.env.NODE_ENV === 'development') {
      console.log(`Chart ${chartName} - Render #${renderCount.current}, Time since last: ${timeSinceLastRender}ms`);
    }
    
    lastRenderTime.current = now;
  });
  
  return {
    renderCount: renderCount.current,
    resetCount: () => { renderCount.current = 0; }
  };
};

/**
 * Color palette for consistent chart theming
 */
export const chartColors = {
  primary: '#2196f3',
  success: '#4caf50',
  error: '#f44336',
  warning: '#ff9800',
  info: '#00bcd4',
  buy: '#26a69a',
  sell: '#ef5350',
  profit: '#4caf50',
  loss: '#f44336',
  neutral: '#9e9e9e',
  background: '#ffffff',
  grid: '#f0f0f0',
  text: '#333333'
};

/**
 * Default chart configuration for consistency
 */
export const defaultChartConfig = {
  layout: {
    background: { type: 'solid', color: chartColors.background },
    textColor: chartColors.text,
  },
  grid: {
    vertLines: { color: chartColors.grid },
    horzLines: { color: chartColors.grid },
  },
  crosshair: {
    mode: 1, // Normal crosshair mode
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
};