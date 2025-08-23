import { create } from 'zustand';
import { tradingAPI } from '../services/api';
import { toast } from 'react-hot-toast';

export const useTradingStore = create((set, get) => ({
  // State - ensure bots is always initialized as an array
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
      const response = await tradingAPI.getBots();
      console.log('API Response:', response); // Debug log
      
      // Handle different response structures
      let botsData = [];
      if (response && response.data) {
        botsData = Array.isArray(response.data) ? response.data : [];
      } else if (Array.isArray(response)) {
        botsData = response;
      }
      
      console.log('Processed bots data:', botsData); // Debug log
      set({ bots: botsData, isLoading: false });
      return botsData;
    } catch (error) {
      console.error('Fetch bots error:', error);
      const errorMessage = error.response?.data?.message || error.message || 'Failed to fetch bots';
      set({ error: errorMessage, isLoading: false, bots: [] }); // Always ensure bots is an array
      toast.error(errorMessage);
      return [];
    }
  },
  
  // Add the missing fetchPerformance function
  fetchPerformance: async (timeframe = '30d', botId = null) => {
    set({ isLoading: true, error: null });
    try {
      const response = await tradingAPI.getPerformance(timeframe, botId);
      const performanceData = response.data || response;
      set({ performance: performanceData, isLoading: false });
      return performanceData;
    } catch (error) {
      console.error('Fetch performance error:', error);
      const errorMessage = error.response?.data?.message || error.message || 'Failed to fetch performance data';
      set({ error: errorMessage, isLoading: false, performance: null });
      toast.error(errorMessage);
      throw error;
    }
  },
  
  fetchBotStatus: async (botId) => {
    try {
      const response = await tradingAPI.getBotStatus(botId);
      set(state => ({
        botStatus: {
          ...state.botStatus,
          [botId]: response.data || response
        }
      }));
      return response.data || response;
    } catch (error) {
      console.error('Failed to fetch bot status:', error);
      throw error;
    }
  },
  
  createBot: async (botData) => {
    set({ isLoading: true, error: null });
    try {
      const response = await tradingAPI.createBot(botData);
      const newBot = response.data || response;
      set(state => ({
        bots: Array.isArray(state.bots) ? [...state.bots, newBot] : [newBot],
        isLoading: false
      }));
      toast.success('Bot created successfully!');
      return newBot;
    } catch (error) {
      const errorMessage = error.response?.data?.message || error.message || 'Failed to create bot';
      set({ error: errorMessage, isLoading: false });
      toast.error(errorMessage);
      throw error;
    }
  },

  startBot: async (botId) => {
    try {
      await tradingAPI.startBot(botId);
      set(state => ({
        bots: Array.isArray(state.bots) ? state.bots.map(bot => 
          bot.id === botId ? { ...bot, status: 'running' } : bot
        ) : []
      }));
      toast.success('Bot started successfully!');
    } catch (error) {
      const errorMessage = error.response?.data?.message || error.message || 'Failed to start bot';
      toast.error(errorMessage);
      throw error;
    }
  },

  stopBot: async (botId) => {
    try {
      await tradingAPI.stopBot(botId);
      set(state => ({
        bots: Array.isArray(state.bots) ? state.bots.map(bot => 
          bot.id === botId ? { ...bot, status: 'stopped' } : bot
        ) : []
      }));
      toast.success('Bot stopped successfully!');
    } catch (error) {
      const errorMessage = error.response?.data?.message || error.message || 'Failed to stop bot';
      toast.error(errorMessage);
      throw error;
    }
  },

  deleteBot: async (botId) => {
    try {
      await tradingAPI.deleteBot(botId);
      set(state => ({
        bots: Array.isArray(state.bots) ? state.bots.filter(bot => bot.id !== botId) : []
      }));
      toast.success('Bot deleted successfully!');
    } catch (error) {
      const errorMessage = error.response?.data?.message || error.message || 'Failed to delete bot';
      toast.error(errorMessage);
      throw error;
    }
  },

  setActiveBotId: (botId) => {
    set({ activeBotId: botId });
  },

  // Additional helper methods
  clearError: () => set({ error: null }),
  resetBots: () => set({ bots: [], error: null, isLoading: false })
}));