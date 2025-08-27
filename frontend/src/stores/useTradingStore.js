import { create } from 'zustand';
import axios from 'axios';
import websocketService from '../services/websocketService';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const useTradingStore = create((set, get) => ({
  // State
  bots: [],
  activeBots: [],
  trades: [],
  symbols: [],
  strategies: [],
  performance: null,
  realTimeData: {},
  marketData: {},
  accountBalance: null,
  isLoading: false,
  error: null,
  
  // WebSocket state
  wsConnected: false,
  wsSubscriptions: new Set(),
  portfolioData: null,
  liveAlerts: [],
  
  // Pagination for trades
  tradePagination: {
    page: 1,
    limit: 10,
    total: 0
  },
  
  // Filters for trades
  tradeFilters: {
    symbol: '',
    botId: '',
    type: '',
    startDate: null,
    endDate: null
  },
  
  // Actions
  fetchBots: async () => {
    set({ isLoading: true, error: null });
    
    try {
      const response = await axios.get(`${API_URL}/trading/bots`);
      set({ bots: response.data.bots, isLoading: false });
      return response.data.bots;
    } catch (error) {
      const errorMessage = error.response?.data?.error || 'Failed to fetch bots';
      set({ isLoading: false, error: errorMessage });
      return [];
    }
  },
  
  fetchActiveBots: async () => {
    set({ isLoading: true, error: null });
    
    try {
      const response = await axios.get(`${API_URL}/trading/status`);
      set({ activeBots: response.data.active_bots, isLoading: false });
      return response.data.active_bots;
    } catch (error) {
      const errorMessage = error.response?.data?.error || 'Failed to fetch active bots';
      set({ isLoading: false, error: errorMessage });
      return [];
    }
  },
  
  fetchTrades: async (page = 1, limit = 10, filters = {}) => {
    set({ isLoading: true, error: null });
    
    // Merge with existing filters
    const currentFilters = get().tradeFilters;
    const mergedFilters = { ...currentFilters, ...filters };
    
    try {
      const queryParams = new URLSearchParams({
        page,
        limit,
        ...(mergedFilters.symbol && { symbol: mergedFilters.symbol }),
        ...(mergedFilters.botId && { bot_id: mergedFilters.botId }),
        ...(mergedFilters.type && { type: mergedFilters.type }),
        ...(mergedFilters.startDate && { start_date: mergedFilters.startDate.toISOString() }),
        ...(mergedFilters.endDate && { end_date: mergedFilters.endDate.toISOString() })
      });
      
      const response = await axios.get(`${API_URL}/trading/trades?${queryParams}`);
      
      set({
        trades: response.data.trades,
        tradePagination: {
          page,
          limit,
          total: response.data.total
        },
        tradeFilters: mergedFilters,
        isLoading: false
      });
      
      return response.data.trades;
    } catch (error) {
      const errorMessage = error.response?.data?.error || 'Failed to fetch trades';
      set({ isLoading: false, error: errorMessage });
      return [];
    }
  },
  
  fetchSymbols: async () => {
    set({ isLoading: true, error: null });
    
    try {
      const response = await axios.get(`${API_URL}/trading/symbols`);
      set({ symbols: response.data.symbols, isLoading: false });
      return response.data.symbols;
    } catch (error) {
      const errorMessage = error.response?.data?.error || 'Failed to fetch symbols';
      set({ isLoading: false, error: errorMessage });
      return [];
    }
  },
  
  fetchStrategies: async () => {
    set({ isLoading: true, error: null });
    
    try {
      const response = await axios.get(`${API_URL}/trading/strategies`);
      set({ strategies: response.data.strategies, isLoading: false });
      return response.data.strategies;
    } catch (error) {
      const errorMessage = error.response?.data?.error || 'Failed to fetch strategies';
      set({ isLoading: false, error: errorMessage });
      return [];
    }
  },
  
  fetchPerformance: async (timeframe = '30d', botId = null) => {
    set({ isLoading: true, error: null });
    
    try {
      const queryParams = new URLSearchParams({
        timeframe,
        ...(botId && { bot_id: botId })
      });
      
      const response = await axios.get(`${API_URL}/trading/performance?${queryParams}`);
      set({ performance: response.data, isLoading: false });
      return response.data;
    } catch (error) {
      const errorMessage = error.response?.data?.error || 'Failed to fetch performance data';
      set({ isLoading: false, error: errorMessage });
      return null;
    }
  },
  
  createBot: async (botData) => {
    set({ isLoading: true, error: null });
    
    try {
      const response = await axios.post(`${API_URL}/trading/bots`, botData);
      
      // Update bots list
      const currentBots = get().bots;
      set({
        bots: [...currentBots, response.data.bot],
        isLoading: false
      });
      
      return { success: true, bot: response.data.bot };
    } catch (error) {
      const errorMessage = error.response?.data?.error || 'Failed to create bot';
      set({ isLoading: false, error: errorMessage });
      return { success: false, error: errorMessage };
    }
  },
  
  updateBot: async (botId, botData) => {
    set({ isLoading: true, error: null });
    
    try {
      const response = await axios.put(`${API_URL}/trading/bots/${botId}`, botData);
      
      // Update bot in the list
      const currentBots = get().bots;
      const updatedBots = currentBots.map(bot => 
        bot.id === botId ? { ...bot, ...response.data.bot } : bot
      );
      
      set({
        bots: updatedBots,
        isLoading: false
      });
      
      return { success: true, bot: response.data.bot };
    } catch (error) {
      const errorMessage = error.response?.data?.error || 'Failed to update bot';
      set({ isLoading: false, error: errorMessage });
      return { success: false, error: errorMessage };
    }
  },
  
  startBot: async (botId) => {
    set({ isLoading: true, error: null });
    
    try {
      const response = await axios.post(`${API_URL}/trading/bots/${botId}/start`);
      
      // Update active bots
      const currentActiveBots = get().activeBots;
      set({
        activeBots: [...currentActiveBots, response.data.bot],
        isLoading: false
      });
      
      return { success: true };
    } catch (error) {
      const errorMessage = error.response?.data?.error || 'Failed to start bot';
      set({ isLoading: false, error: errorMessage });
      return { success: false, error: errorMessage };
    }
  },
  
  stopBot: async (botId) => {
    set({ isLoading: true, error: null });
    
    try {
      await axios.post(`${API_URL}/trading/bots/${botId}/stop`);
      
      // Update active bots
      const currentActiveBots = get().activeBots;
      set({
        activeBots: currentActiveBots.filter(bot => bot.id !== botId),
        isLoading: false
      });
      
      return { success: true };
    } catch (error) {
      const errorMessage = error.response?.data?.error || 'Failed to stop bot';
      set({ isLoading: false, error: errorMessage });
      return { success: false, error: errorMessage };
    }
  },
  
  deleteBot: async (botId) => {
    set({ isLoading: true, error: null });
    
    try {
      await axios.delete(`${API_URL}/trading/bots/${botId}`);
      
      // Update bots list
      const currentBots = get().bots;
      set({
        bots: currentBots.filter(bot => bot.id !== botId),
        isLoading: false
      });
      
      return { success: true };
    } catch (error) {
      const errorMessage = error.response?.data?.error || 'Failed to delete bot';
      set({ isLoading: false, error: errorMessage });
      return { success: false, error: errorMessage };
    }
  },
  
  runBacktest: async (backtestData) => {
    set({ isLoading: true, error: null });
    
    try {
      const response = await axios.post(`${API_URL}/trading/backtest`, backtestData);
      set({ isLoading: false });
      return { success: true, results: response.data.results };
    } catch (error) {
      const errorMessage = error.response?.data?.error || 'Failed to run backtest';
      set({ isLoading: false, error: errorMessage });
      return { success: false, error: errorMessage };
    }
  },
  
  setTradeFilters: (filters) => {
    set({ tradeFilters: { ...get().tradeFilters, ...filters } });
  },
  
  clearError: () => set({ error: null }),
  
  // Real-time data methods
  fetchRealTimeData: async (symbol) => {
    try {
      const response = await axios.get(`${API_URL}/trading/realtime/${symbol}`);
      const currentData = get().realTimeData;
      set({ 
        realTimeData: { 
          ...currentData, 
          [symbol]: response.data 
        } 
      });
      return response.data;
    } catch (error) {
      console.error(`Failed to fetch real-time data for ${symbol}:`, error);
      return null;
    }
  },
  
  fetchAllRealTimeData: async () => {
    try {
      const response = await axios.get(`${API_URL}/trading/realtime`);
      set({ realTimeData: response.data.data });
      return response.data.data;
    } catch (error) {
      console.error('Failed to fetch all real-time data:', error);
      return {};
    }
  },
  
  fetchMarketData: async (symbol, interval = '1h', limit = 100) => {
    try {
      const response = await axios.get(`${API_URL}/trading/market-data/${symbol}`, {
        params: { interval, limit }
      });
      const currentData = get().marketData;
      set({ 
        marketData: { 
          ...currentData, 
          [`${symbol}_${interval}`]: response.data 
        } 
      });
      return response.data;
    } catch (error) {
      console.error(`Failed to fetch market data for ${symbol}:`, error);
      return null;
    }
  },
  
  fetchAccountBalance: async () => {
    set({ isLoading: true, error: null });
    
    try {
      const response = await axios.get(`${API_URL}/trading/account/balance`);
      set({ accountBalance: response.data, isLoading: false });
      return response.data;
    } catch (error) {
      const errorMessage = error.response?.data?.error || 'Failed to fetch account balance';
      set({ isLoading: false, error: errorMessage });
      return null;
    }
  },
  
  // WebSocket methods
  initializeWebSocket: async (token = null) => {
    try {
      await websocketService.connect(token);
      set({ wsConnected: true });
      
      // Set up event handlers
      const store = get();
      store.setupWebSocketHandlers();
      
      return true;
    } catch (error) {
      console.error('Failed to initialize WebSocket:', error);
      set({ wsConnected: false });
      return false;
    }
  },

  disconnectWebSocket: () => {
    websocketService.disconnect();
    set({ 
      wsConnected: false, 
      wsSubscriptions: new Set(),
      portfolioData: null 
    });
  },

  setupWebSocketHandlers: () => {
    // Price updates
    websocketService.on('price_update', (data) => {
      const currentData = get().realTimeData;
      set({
        realTimeData: {
          ...currentData,
          [data.symbol]: {
            ...currentData[data.symbol],
            ...data,
            timestamp: Date.now()
          }
        }
      });
    });

    // Portfolio updates
    websocketService.on('portfolio_update', (data) => {
      set({ portfolioData: data });
    });

    // Bot status updates
    websocketService.on('bot_status_update', (data) => {
      const currentBots = get().bots;
      const updatedBots = currentBots.map(bot => 
        bot.id === data.bot_id ? { ...bot, status: data.status, updated_at: data.timestamp } : bot
      );
      set({ bots: updatedBots });
    });

    // Trade notifications
    websocketService.on('trade_notification', (data) => {
      const currentTrades = get().trades;
      set({ trades: [data, ...currentTrades.slice(0, 99)] }); // Keep last 100 trades
    });

    // Market alerts
    websocketService.on('market_alert', (data) => {
      const currentAlerts = get().liveAlerts;
      set({ liveAlerts: [data, ...currentAlerts.slice(0, 49)] }); // Keep last 50 alerts
    });

    // Dashboard updates
    websocketService.on('dashboard_update', (data) => {
      set({
        bots: data.bots || get().bots,
        trades: data.recent_trades || get().trades,
        portfolioData: data.portfolio || get().portfolioData
      });
    });

    // Connection status
    websocketService.on('connect', () => {
      set({ wsConnected: true });
    });

    websocketService.on('disconnect', () => {
      set({ wsConnected: false });
    });

    // Error handling
    websocketService.on('error', (error) => {
      console.error('WebSocket error:', error);
      set({ error: error.message || 'WebSocket connection error' });
    });
  },

  subscribeToSymbol: (symbol) => {
    const success = websocketService.subscribeToSymbol(symbol);
    if (success) {
      const currentSubscriptions = get().wsSubscriptions;
      currentSubscriptions.add(symbol);
      set({ wsSubscriptions: new Set(currentSubscriptions) });
    }
    return success;
  },

  unsubscribeFromSymbol: (symbol) => {
    const success = websocketService.unsubscribeFromSymbol(symbol);
    if (success) {
      const currentSubscriptions = get().wsSubscriptions;
      currentSubscriptions.delete(symbol);
      set({ wsSubscriptions: new Set(currentSubscriptions) });
    }
    return success;
  },

  requestPortfolioUpdate: () => {
    return websocketService.requestPortfolioUpdate();
  },

  requestPriceHistory: (symbol, timeframe = '1h', limit = 100) => {
    return websocketService.requestPriceHistory(symbol, timeframe, limit);
  },

  getWebSocketStatus: () => {
    return websocketService.getConnectionStatus();
  },

  startWebSocketStream: async (symbol) => {
    try {
      // Subscribe via WebSocket service
      const subscribed = get().subscribeToSymbol(symbol);
      if (subscribed) {
        // Also notify backend API
        await axios.post(`${API_URL}/websocket/subscribe`, { symbol });
      }
      return subscribed;
    } catch (error) {
      console.error(`Failed to start WebSocket stream for ${symbol}:`, error);
      return false;
    }
  },

  stopWebSocketStream: async (symbol) => {
    try {
      // Unsubscribe via WebSocket service
      const unsubscribed = get().unsubscribeFromSymbol(symbol);
      if (unsubscribed) {
        // Also notify backend API
        await axios.post(`${API_URL}/websocket/unsubscribe`, { symbol });
      }
      return unsubscribed;
    } catch (error) {
      console.error(`Failed to stop WebSocket stream for ${symbol}:`, error);
      return false;
    }
  },

  clearLiveAlerts: () => {
    set({ liveAlerts: [] });
  }
}));

export default useTradingStore;