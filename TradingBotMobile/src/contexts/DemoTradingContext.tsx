import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import PaperTradingService, { PaperPortfolio, PaperTrade, PaperPosition } from '../services/PaperTradingService';

interface DemoTradingContextType {
  isDemoMode: boolean;
  portfolio: PaperPortfolio | null;
  isLoading: boolean;
  error: string | null;
  toggleDemoMode: () => Promise<void>;
  placeTrade: (symbol: string, type: 'buy' | 'sell', quantity: number, price: number) => Promise<{ success: boolean; message: string }>;
  updatePrices: (priceData: { [symbol: string]: number }) => Promise<void>;
  resetPortfolio: () => Promise<void>;
  refreshPortfolio: () => Promise<void>;
  getTradeHistory: () => PaperTrade[];
  getPositions: () => PaperPosition[];
  getPerformanceMetrics: () => any;
}

const DemoTradingContext = createContext<DemoTradingContextType | undefined>(undefined);

interface DemoTradingProviderProps {
  children: ReactNode;
}

export const DemoTradingProvider: React.FC<DemoTradingProviderProps> = ({ children }) => {
  const [isDemoMode, setIsDemoMode] = useState(true);
  const [portfolio, setPortfolio] = useState<PaperPortfolio | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const paperTradingService = PaperTradingService.getInstance();

  useEffect(() => {
    initializeService();
  }, []);

  const initializeService = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      await paperTradingService.initialize();
      const mode = await paperTradingService.getTradingMode();
      setIsDemoMode(mode === 'demo');
      
      const currentPortfolio = paperTradingService.getPortfolio();
      setPortfolio(currentPortfolio);
    } catch (err) {
      setError('Failed to initialize demo trading service');
      console.error('Demo trading initialization error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleDemoMode = async () => {
    try {
      setError(null);
      const newMode = !isDemoMode;
      
      if (newMode) {
        await paperTradingService.enableDemoMode();
      } else {
        await paperTradingService.enableLiveMode();
      }
      
      setIsDemoMode(newMode);
    } catch (err) {
      setError('Failed to toggle trading mode');
      console.error('Toggle demo mode error:', err);
    }
  };

  const placeTrade = async (
    symbol: string,
    type: 'buy' | 'sell',
    quantity: number,
    price: number
  ) => {
    try {
      setError(null);
      
      if (!isDemoMode) {
        return {
          success: false,
          message: 'Live trading not implemented in demo version'
        };
      }
      
      const result = await paperTradingService.placePaperTrade(symbol, type, quantity, price);
      
      if (result.success) {
        // Refresh portfolio after successful trade
        const updatedPortfolio = paperTradingService.getPortfolio();
        setPortfolio(updatedPortfolio);
      }
      
      return result;
    } catch (err) {
      const errorMessage = 'Failed to place trade';
      setError(errorMessage);
      console.error('Place trade error:', err);
      return {
        success: false,
        message: errorMessage
      };
    }
  };

  const updatePrices = async (priceData: { [symbol: string]: number }) => {
    try {
      setError(null);
      
      if (isDemoMode) {
        await paperTradingService.updatePrices(priceData);
        const updatedPortfolio = paperTradingService.getPortfolio();
        setPortfolio(updatedPortfolio);
      }
    } catch (err) {
      setError('Failed to update prices');
      console.error('Update prices error:', err);
    }
  };

  const resetPortfolio = async () => {
    try {
      setError(null);
      
      if (isDemoMode) {
        await paperTradingService.resetPortfolio();
        const updatedPortfolio = paperTradingService.getPortfolio();
        setPortfolio(updatedPortfolio);
      }
    } catch (err) {
      setError('Failed to reset portfolio');
      console.error('Reset portfolio error:', err);
    }
  };

  const refreshPortfolio = async () => {
    try {
      setError(null);
      const updatedPortfolio = paperTradingService.getPortfolio();
      setPortfolio(updatedPortfolio);
    } catch (err) {
      setError('Failed to refresh portfolio');
      console.error('Refresh portfolio error:', err);
    }
  };

  const getTradeHistory = () => {
    return paperTradingService.getTradeHistory();
  };

  const getPositions = () => {
    return paperTradingService.getPositions();
  };

  const getPerformanceMetrics = () => {
    return paperTradingService.getPerformanceMetrics();
  };

  const contextValue: DemoTradingContextType = {
    isDemoMode,
    portfolio,
    isLoading,
    error,
    toggleDemoMode,
    placeTrade,
    updatePrices,
    resetPortfolio,
    refreshPortfolio,
    getTradeHistory,
    getPositions,
    getPerformanceMetrics,
  };

  return (
    <DemoTradingContext.Provider value={contextValue}>
      {children}
    </DemoTradingContext.Provider>
  );
};

export const useDemoTrading = (): DemoTradingContextType => {
  const context = useContext(DemoTradingContext);
  if (context === undefined) {
    throw new Error('useDemoTrading must be used within a DemoTradingProvider');
  }
  return context;
};

export default DemoTradingContext;