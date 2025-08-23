import axios from 'axios';
import useAuthStore from '../stores/useAuthStore';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

// Create axios instance with base URL
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token;
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Add response interceptor to handle token expiration
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle 401 Unauthorized errors (token expired)
    if (error.response && error.response.status === 401) {
      useAuthStore.getState().logout();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
const authAPI = {
  login: (email, password) => api.post('/auth/login', { email, password }),
  register: (username, email, password) => api.post('/auth/register', { username, email, password }),
  verifyToken: () => api.get('/auth/verify'),
  updateProfile: (userData) => api.put('/user/profile', userData),
  changePassword: (currentPassword, newPassword) => api.put('/user/password', { current_password: currentPassword, new_password: newPassword }),
};

// Trading API
const tradingAPI = {
  // Bots
  getBots: () => api.get('/trading/bots'),
  getBot: (botId) => api.get(`/trading/bots/${botId}`),
  createBot: (botData) => api.post('/trading/bots', botData),
  updateBot: (botId, botData) => api.put(`/trading/bots/${botId}`, botData),
  deleteBot: (botId) => api.delete(`/trading/bots/${botId}`),
  startBot: (botId) => api.post(`/trading/bots/${botId}/start`),
  stopBot: (botId) => api.post(`/trading/bots/${botId}/stop`),
  
  // Trades
  getTrades: (page = 1, limit = 10, filters = {}) => {
    const params = new URLSearchParams({
      page,
      limit,
      ...(filters.symbol && { symbol: filters.symbol }),
      ...(filters.botId && { bot_id: filters.botId }),
      ...(filters.type && { type: filters.type }),
      ...(filters.startDate && { start_date: filters.startDate.toISOString() }),
      ...(filters.endDate && { end_date: filters.endDate.toISOString() })
    });
    return api.get(`/trading/trades?${params}`);
  },
  
  // Performance
  getPerformance: (timeframe = '30d', botId = null) => {
    const params = new URLSearchParams({
      period: timeframe,  // Changed from 'timeframe' to 'period'
      ...(botId && { bot_id: botId })
    });
    return api.get(`/performance?${params}`);  // Changed from '/trading/performance' to '/performance'
  },
  
  // Symbols and Strategies
  getSymbols: () => api.get('/trading/symbols'),
  getStrategies: () => api.get('/trading/strategies'),
  
  // Backtest
  runBacktest: (backtestData) => api.post('/trading/backtest', backtestData),
  
  // Trading Status
  getTradingStatus: () => api.get('/trading/status')
};

export {
  api as default,
  authAPI,
  tradingAPI
};