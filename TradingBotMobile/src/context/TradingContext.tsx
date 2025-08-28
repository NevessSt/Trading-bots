import React, {createContext, useContext, useState, useEffect, ReactNode} from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import {Alert} from 'react-native';
import NetInfo from '@react-native-community/netinfo';

interface Asset {
  symbol: string;
  name: string;
  price: number;
  change24h: number;
  changePercent24h: number;
  volume24h: number;
  marketCap: number;
  lastUpdated: string;
}

interface Position {
  id: string;
  symbol: string;
  quantity: number;
  averagePrice: number;
  currentPrice: number;
  totalValue: number;
  unrealizedPnL: number;
  unrealizedPnLPercent: number;
  side: 'long' | 'short';
  openedAt: string;
}

interface Trade {
  id: string;
  symbol: string;
  side: 'buy' | 'sell';
  quantity: number;
  price: number;
  total: number;
  fee: number;
  status: 'pending' | 'completed' | 'cancelled' | 'failed';
  timestamp: string;
}

interface Portfolio {
  totalValue: number;
  totalPnL: number;
  totalPnLPercent: number;
  availableBalance: number;
  positions: Position[];
  recentTrades: Trade[];
}

interface TradingSettings {
  riskLevel: 'conservative' | 'moderate' | 'aggressive';
  maxPositionSize: number;
  stopLossPercent: number;
  takeProfitPercent: number;
  autoTrade: boolean;
  notifications: {
    priceAlerts: boolean;
    tradeExecutions: boolean;
    portfolioUpdates: boolean;
  };
}

interface TradingContextType {
  // Market data
  assets: Asset[];
  watchlist: string[];
  isMarketDataLoading: boolean;
  
  // Portfolio
  portfolio: Portfolio;
  isPortfolioLoading: boolean;
  
  // Trading
  tradingSettings: TradingSettings;
  isConnected: boolean;
  
  // Actions
  refreshMarketData: () => Promise<void>;
  refreshPortfolio: () => Promise<void>;
  addToWatchlist: (symbol: string) => Promise<void>;
  removeFromWatchlist: (symbol: string) => Promise<void>;
  updateTradingSettings: (settings: Partial<TradingSettings>) => Promise<void>;
  executeTrade: (symbol: string, side: 'buy' | 'sell', quantity: number, price?: number) => Promise<boolean>;
  cancelTrade: (tradeId: string) => Promise<boolean>;
  setStopLoss: (positionId: string, stopLossPrice: number) => Promise<boolean>;
  setTakeProfit: (positionId: string, takeProfitPrice: number) => Promise<boolean>;
}

const TradingContext = createContext<TradingContextType | undefined>(undefined);

interface TradingProviderProps {
  children: ReactNode;
}

const STORAGE_KEYS = {
  WATCHLIST: 'watchlist',
  TRADING_SETTINGS: 'trading_settings',
  PORTFOLIO_CACHE: 'portfolio_cache',
  MARKET_DATA_CACHE: 'market_data_cache',
};

// Mock data for demonstration
const mockAssets: Asset[] = [
  {
    symbol: 'BTC',
    name: 'Bitcoin',
    price: 43250.00,
    change24h: 1250.50,
    changePercent24h: 2.98,
    volume24h: 28500000000,
    marketCap: 847000000000,
    lastUpdated: new Date().toISOString(),
  },
  {
    symbol: 'ETH',
    name: 'Ethereum',
    price: 2650.75,
    change24h: -85.25,
    changePercent24h: -3.11,
    volume24h: 15200000000,
    marketCap: 318000000000,
    lastUpdated: new Date().toISOString(),
  },
  {
    symbol: 'ADA',
    name: 'Cardano',
    price: 0.485,
    change24h: 0.025,
    changePercent24h: 5.43,
    volume24h: 850000000,
    marketCap: 17200000000,
    lastUpdated: new Date().toISOString(),
  },
];

const defaultTradingSettings: TradingSettings = {
  riskLevel: 'moderate',
  maxPositionSize: 1000,
  stopLossPercent: 5,
  takeProfitPercent: 10,
  autoTrade: false,
  notifications: {
    priceAlerts: true,
    tradeExecutions: true,
    portfolioUpdates: true,
  },
};

export function TradingProvider({children}: TradingProviderProps) {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [watchlist, setWatchlist] = useState<string[]>(['BTC', 'ETH']);
  const [portfolio, setPortfolio] = useState<Portfolio>({
    totalValue: 0,
    totalPnL: 0,
    totalPnLPercent: 0,
    availableBalance: 10000,
    positions: [],
    recentTrades: [],
  });
  const [tradingSettings, setTradingSettings] = useState<TradingSettings>(defaultTradingSettings);
  const [isMarketDataLoading, setIsMarketDataLoading] = useState(false);
  const [isPortfolioLoading, setIsPortfolioLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(true);

  useEffect(() => {
    initializeTradingData();
    setupNetworkListener();
  }, []);

  const setupNetworkListener = () => {
    const unsubscribe = NetInfo.addEventListener(state => {
      setIsConnected(state.isConnected ?? false);
    });

    return unsubscribe;
  };

  const initializeTradingData = async () => {
    try {
      // Load cached data
      const [cachedWatchlist, cachedSettings, cachedPortfolio, cachedMarketData] = await Promise.all([
        AsyncStorage.getItem(STORAGE_KEYS.WATCHLIST),
        AsyncStorage.getItem(STORAGE_KEYS.TRADING_SETTINGS),
        AsyncStorage.getItem(STORAGE_KEYS.PORTFOLIO_CACHE),
        AsyncStorage.getItem(STORAGE_KEYS.MARKET_DATA_CACHE),
      ]);

      if (cachedWatchlist) {
        setWatchlist(JSON.parse(cachedWatchlist));
      }

      if (cachedSettings) {
        setTradingSettings(JSON.parse(cachedSettings));
      }

      if (cachedPortfolio) {
        setPortfolio(JSON.parse(cachedPortfolio));
      }

      if (cachedMarketData) {
        const marketData = JSON.parse(cachedMarketData);
        // Check if data is not too old (5 minutes)
        const dataAge = Date.now() - new Date(marketData.timestamp).getTime();
        if (dataAge < 5 * 60 * 1000) {
          setAssets(marketData.assets);
        }
      }

      // Refresh data
      await Promise.all([
        refreshMarketData(),
        refreshPortfolio(),
      ]);
    } catch (error) {
      console.error('Failed to initialize trading data:', error);
    }
  };

  const refreshMarketData = async (): Promise<void> => {
    try {
      setIsMarketDataLoading(true);
      
      // In a real app, this would fetch from an API
      // For demo, we'll use mock data with some randomization
      const updatedAssets = mockAssets.map(asset => ({
        ...asset,
        price: asset.price * (0.98 + Math.random() * 0.04), // ±2% variation
        change24h: asset.change24h * (0.8 + Math.random() * 0.4), // ±20% variation
        lastUpdated: new Date().toISOString(),
      }));
      
      setAssets(updatedAssets);
      
      // Cache the data
      await AsyncStorage.setItem(STORAGE_KEYS.MARKET_DATA_CACHE, JSON.stringify({
        assets: updatedAssets,
        timestamp: new Date().toISOString(),
      }));
    } catch (error) {
      console.error('Failed to refresh market data:', error);
      Alert.alert('Error', 'Failed to refresh market data');
    } finally {
      setIsMarketDataLoading(false);
    }
  };

  const refreshPortfolio = async (): Promise<void> => {
    try {
      setIsPortfolioLoading(true);
      
      // In a real app, this would fetch from an API
      // For demo, we'll simulate some portfolio data
      const mockPositions: Position[] = [
        {
          id: '1',
          symbol: 'BTC',
          quantity: 0.25,
          averagePrice: 42000,
          currentPrice: assets.find(a => a.symbol === 'BTC')?.price || 43250,
          totalValue: 0,
          unrealizedPnL: 0,
          unrealizedPnLPercent: 0,
          side: 'long',
          openedAt: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
        },
      ];
      
      // Calculate values
      mockPositions.forEach(position => {
        position.totalValue = position.quantity * position.currentPrice;
        position.unrealizedPnL = position.totalValue - (position.quantity * position.averagePrice);
        position.unrealizedPnLPercent = (position.unrealizedPnL / (position.quantity * position.averagePrice)) * 100;
      });
      
      const totalValue = mockPositions.reduce((sum, pos) => sum + pos.totalValue, 0) + 5000; // + available balance
      const totalPnL = mockPositions.reduce((sum, pos) => sum + pos.unrealizedPnL, 0);
      
      const updatedPortfolio: Portfolio = {
        totalValue,
        totalPnL,
        totalPnLPercent: totalPnL > 0 ? (totalPnL / (totalValue - totalPnL)) * 100 : 0,
        availableBalance: 5000,
        positions: mockPositions,
        recentTrades: [],
      };
      
      setPortfolio(updatedPortfolio);
      
      // Cache the data
      await AsyncStorage.setItem(STORAGE_KEYS.PORTFOLIO_CACHE, JSON.stringify(updatedPortfolio));
    } catch (error) {
      console.error('Failed to refresh portfolio:', error);
      Alert.alert('Error', 'Failed to refresh portfolio data');
    } finally {
      setIsPortfolioLoading(false);
    }
  };

  const addToWatchlist = async (symbol: string): Promise<void> => {
    try {
      if (!watchlist.includes(symbol)) {
        const updatedWatchlist = [...watchlist, symbol];
        setWatchlist(updatedWatchlist);
        await AsyncStorage.setItem(STORAGE_KEYS.WATCHLIST, JSON.stringify(updatedWatchlist));
      }
    } catch (error) {
      console.error('Failed to add to watchlist:', error);
    }
  };

  const removeFromWatchlist = async (symbol: string): Promise<void> => {
    try {
      const updatedWatchlist = watchlist.filter(s => s !== symbol);
      setWatchlist(updatedWatchlist);
      await AsyncStorage.setItem(STORAGE_KEYS.WATCHLIST, JSON.stringify(updatedWatchlist));
    } catch (error) {
      console.error('Failed to remove from watchlist:', error);
    }
  };

  const updateTradingSettings = async (settings: Partial<TradingSettings>): Promise<void> => {
    try {
      const updatedSettings = { ...tradingSettings, ...settings };
      setTradingSettings(updatedSettings);
      await AsyncStorage.setItem(STORAGE_KEYS.TRADING_SETTINGS, JSON.stringify(updatedSettings));
    } catch (error) {
      console.error('Failed to update trading settings:', error);
      Alert.alert('Error', 'Failed to save trading settings');
    }
  };

  const executeTrade = async (symbol: string, side: 'buy' | 'sell', quantity: number, price?: number): Promise<boolean> => {
    try {
      // In a real app, this would make an API call to execute the trade
      // For demo, we'll simulate trade execution
      const asset = assets.find(a => a.symbol === symbol);
      if (!asset) {
        Alert.alert('Error', 'Asset not found');
        return false;
      }
      
      const tradePrice = price || asset.price;
      const total = quantity * tradePrice;
      
      if (side === 'buy' && total > portfolio.availableBalance) {
        Alert.alert('Insufficient Balance', 'You do not have enough balance for this trade');
        return false;
      }
      
      // Simulate trade execution delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      Alert.alert('Trade Executed', `${side.toUpperCase()} ${quantity} ${symbol} at $${tradePrice.toFixed(2)}`);
      
      // Refresh portfolio after trade
      await refreshPortfolio();
      
      return true;
    } catch (error) {
      console.error('Failed to execute trade:', error);
      Alert.alert('Trade Failed', 'Failed to execute trade. Please try again.');
      return false;
    }
  };

  const cancelTrade = async (tradeId: string): Promise<boolean> => {
    try {
      // In a real app, this would make an API call to cancel the trade
      Alert.alert('Trade Cancelled', 'Your trade has been cancelled');
      return true;
    } catch (error) {
      console.error('Failed to cancel trade:', error);
      return false;
    }
  };

  const setStopLoss = async (positionId: string, stopLossPrice: number): Promise<boolean> => {
    try {
      // In a real app, this would set a stop loss order
      Alert.alert('Stop Loss Set', `Stop loss set at $${stopLossPrice.toFixed(2)}`);
      return true;
    } catch (error) {
      console.error('Failed to set stop loss:', error);
      return false;
    }
  };

  const setTakeProfit = async (positionId: string, takeProfitPrice: number): Promise<boolean> => {
    try {
      // In a real app, this would set a take profit order
      Alert.alert('Take Profit Set', `Take profit set at $${takeProfitPrice.toFixed(2)}`);
      return true;
    } catch (error) {
      console.error('Failed to set take profit:', error);
      return false;
    }
  };

  const contextValue: TradingContextType = {
    assets,
    watchlist,
    isMarketDataLoading,
    portfolio,
    isPortfolioLoading,
    tradingSettings,
    isConnected,
    refreshMarketData,
    refreshPortfolio,
    addToWatchlist,
    removeFromWatchlist,
    updateTradingSettings,
    executeTrade,
    cancelTrade,
    setStopLoss,
    setTakeProfit,
  };

  return (
    <TradingContext.Provider value={contextValue}>
      {children}
    </TradingContext.Provider>
  );
}

export function useTrading(): TradingContextType {
  const context = useContext(TradingContext);
  if (context === undefined) {
    throw new Error('useTrading must be used within a TradingProvider');
  }
  return context;
}

export type {Asset, Position, Trade, Portfolio, TradingSettings, TradingContextType};