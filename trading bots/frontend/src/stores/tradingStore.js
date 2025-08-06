import { create } from 'zustand';
import axios from 'axios';
import { toast } from 'react-hot-toast';

export const useTradingStore = create((set, get) => ({
  // State
  bots: [],
  activeBotId: null,
  botStatus: {},
  tradeHistory: [],
  performance: null,
  availableSymbols: [],
  availableStrategies: [],
  isLoading: false,
  error: null,
  
  // Actions
  fetchBots: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await axios.get('/api/trading/bots');
      set({ bots: response.data, isLoading: false });
      return response.data;
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Failed to fetch bots';
      set({ error: errorMessage, isLoading: false });
      toast.error(errorMessage);
      throw error;
    }
  },
  
  fetchBotStatus: async (botId) => {
    try {
      const response = await axios.get(`/api/trading/bots/${botId}/status`);
      set(state => ({
        botStatus: {
          ...state.botStatus,
          [botId]: response.data
        }
      }));
      return response.data;
    } catch (error) {
      console.error('Failed to fetch bot status:', error);
      throw error;
    }
  },
  
  createBot: async (botData) => {
    set({ isLoading: true, error: null });
    try {
      const response = await axios.post('/api/trading/bots', botData);
      set(state => ({
        bots: [...state.bots, response.data],
        isLoading: false
      }));
      toast.success('Bot created successfully!');
      return response.data;
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Failed to create bot';
      set({ error: errorMessage, isLoading: false });
      toast.error(errorMessage);
      throw error;
    }
  },
  
  updateBot: async (botId, botData) => {
    set({ isLoading: true, error: null });
    try {
      const response = await axios.put(`/api/trading/bots/${botId}`, botData);
      set(state => ({
        bots: state.bots.map(bot => bot._id === botId ? response.data : bot),
        isLoading: false
      }));
      toast.success('Bot updated successfully!');
      return response.data;
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Failed to update bot';
      set({ error: errorMessage, isLoading: false });
      toast.error(errorMessage);
      throw error;
    }
  },
  
  deleteBot: async (botId) => {
    set({ isLoading: true, error: null });
    try {
      await axios.delete(`/api/trading/bots/${botId}`);
      set(state => ({
        bots: state.bots.filter(bot => bot._id !== botId),
        isLoading: false
      }));
      toast.success('Bot deleted successfully!');
      return true;
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Failed to delete bot';
      set({ error: errorMessage, isLoading: false });
      toast.error(errorMessage);
      throw error;
    }
  },
  
  startBot: async (botId) => {
    try {
      await axios.post(`/api/trading/bots/${botId}/start`);
      set(state => ({
        botStatus: {
          ...state.botStatus,
          [botId]: { ...state.botStatus[botId], status: 'running' }
        }
      }));
      toast.success('Bot started successfully!');
      return true;
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Failed to start bot';
      toast.error(errorMessage);
      throw error;
    }
  },
  
  stopBot: async (botId) => {
    try {
      await axios.post(`/api/trading/bots/${botId}/stop`);
      set(state => ({
        botStatus: {
          ...state.botStatus,
          [botId]: { ...state.botStatus[botId], status: 'stopped' }
        }
      }));
      toast.success('Bot stopped successfully!');
      return true;
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Failed to stop bot';
      toast.error(errorMessage);
      throw error;
    }
  },
  
  fetchTradeHistory: async (filters = {}) => {
    set({ isLoading: true, error: null });
    try {
      const response = await axios.get('/api/trading/history', { params: filters });
      set({ tradeHistory: response.data, isLoading: false });
      return response.data;
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Failed to fetch trade history';
      set({ error: errorMessage, isLoading: false });
      toast.error(errorMessage);
      throw error;
    }
  },
  
  fetchPerformance: async (period = '1m') => {
    set({ isLoading: true, error: null });
    try {
      const response = await axios.get(`/api/trading/performance?period=${period}`);
      set({ performance: response.data, isLoading: false });
      return response.data;
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Failed to fetch performance data';
      set({ error: errorMessage, isLoading: false });
      toast.error(errorMessage);
      throw error;
    }
  },
  
  fetchAvailableSymbols: async () => {
    try {
      const response = await axios.get('/api/trading/symbols');
      set({ availableSymbols: response.data });
      return response.data;
    } catch (error) {
      console.error('Failed to fetch available symbols:', error);
      throw error;
    }
  },
  
  fetchAvailableStrategies: async () => {
    try {
      const response = await axios.get('/api/trading/strategies');
      set({ availableStrategies: response.data });
      return response.data;
    } catch (error) {
      console.error('Failed to fetch available strategies:', error);
      throw error;
    }
  },
  
  backtest: async (botConfig) => {
    set({ isLoading: true, error: null });
    try {
      const response = await axios.post('/api/trading/backtest', botConfig);
      set({ isLoading: false });
      return response.data;
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Backtest failed';
      set({ error: errorMessage, isLoading: false });
      toast.error(errorMessage);
      throw error;
    }
  },
  
  setActiveBotId: (botId) => {
    set({ activeBotId: botId });
  },
}));