/**
 * Storage Service for managing local data persistence and caching
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import { MMKV } from 'react-native-mmkv';
import {
  User,
  Portfolio,
  Asset,
  Trade,
  Position,
  PriceAlert,
  TradingSettings,
  AppSettings,
  StorageKeys,
} from '../types';

// MMKV instance for high-performance storage
const storage = new MMKV({
  id: 'trading-bot-storage',
  encryptionKey: 'trading-bot-encryption-key-2024',
});

class StorageService {
  // Generic storage methods
  async setItem<T>(key: string, value: T): Promise<void> {
    try {
      const serializedValue = JSON.stringify(value);
      
      // Use MMKV for frequently accessed data
      if (this.isFrequentlyAccessedKey(key)) {
        storage.set(key, serializedValue);
      } else {
        await AsyncStorage.setItem(key, serializedValue);
      }
    } catch (error) {
      console.error(`Failed to store ${key}:`, error);
      throw error;
    }
  }

  async getItem<T>(key: string): Promise<T | null> {
    try {
      let serializedValue: string | null = null;
      
      // Use MMKV for frequently accessed data
      if (this.isFrequentlyAccessedKey(key)) {
        serializedValue = storage.getString(key) || null;
      } else {
        serializedValue = await AsyncStorage.getItem(key);
      }
      
      if (serializedValue === null) {
        return null;
      }
      
      return JSON.parse(serializedValue) as T;
    } catch (error) {
      console.error(`Failed to retrieve ${key}:`, error);
      return null;
    }
  }

  async removeItem(key: string): Promise<void> {
    try {
      if (this.isFrequentlyAccessedKey(key)) {
        storage.delete(key);
      } else {
        await AsyncStorage.removeItem(key);
      }
    } catch (error) {
      console.error(`Failed to remove ${key}:`, error);
      throw error;
    }
  }

  async clear(): Promise<void> {
    try {
      storage.clearAll();
      await AsyncStorage.clear();
    } catch (error) {
      console.error('Failed to clear storage:', error);
      throw error;
    }
  }

  private isFrequentlyAccessedKey(key: string): boolean {
    const frequentKeys = [
      StorageKeys.USER_PREFERENCES,
      StorageKeys.THEME_PREFERENCE,
      StorageKeys.WATCHLIST,
      StorageKeys.PORTFOLIO_CACHE,
      StorageKeys.PRICE_CACHE,
    ];
    return frequentKeys.includes(key as StorageKeys);
  }

  // Authentication & User Data
  async storeAuthToken(token: string): Promise<void> {
    await this.setItem(StorageKeys.AUTH_TOKEN, token);
  }

  async getAuthToken(): Promise<string | null> {
    return this.getItem<string>(StorageKeys.AUTH_TOKEN);
  }

  async removeAuthToken(): Promise<void> {
    await this.removeItem(StorageKeys.AUTH_TOKEN);
  }

  async storeUser(user: User): Promise<void> {
    await this.setItem(StorageKeys.USER_DATA, user);
  }

  async getUser(): Promise<User | null> {
    return this.getItem<User>(StorageKeys.USER_DATA);
  }

  async removeUser(): Promise<void> {
    await this.removeItem(StorageKeys.USER_DATA);
  }

  // Biometric Authentication
  async setBiometricEnabled(enabled: boolean): Promise<void> {
    await this.setItem(StorageKeys.BIOMETRIC_ENABLED, enabled);
  }

  async isBiometricEnabled(): Promise<boolean> {
    const enabled = await this.getItem<boolean>(StorageKeys.BIOMETRIC_ENABLED);
    return enabled ?? false;
  }

  // Setup Status
  async setSetupCompleted(completed: boolean): Promise<void> {
    await this.setItem(StorageKeys.SETUP_COMPLETED, completed);
  }

  async isSetupCompleted(): Promise<boolean> {
    const completed = await this.getItem<boolean>(StorageKeys.SETUP_COMPLETED);
    return completed ?? false;
  }

  // Portfolio & Trading Data
  async storePortfolio(portfolio: Portfolio): Promise<void> {
    await this.setItem(StorageKeys.PORTFOLIO_CACHE, {
      ...portfolio,
      lastUpdated: new Date().toISOString(),
    });
  }

  async getPortfolio(): Promise<Portfolio | null> {
    const cached = await this.getItem<Portfolio & { lastUpdated: string }>(StorageKeys.PORTFOLIO_CACHE);
    if (!cached) return null;

    // Check if cache is still valid (5 minutes)
    const lastUpdated = new Date(cached.lastUpdated);
    const now = new Date();
    const diffMinutes = (now.getTime() - lastUpdated.getTime()) / (1000 * 60);
    
    if (diffMinutes > 5) {
      return null; // Cache expired
    }

    const { lastUpdated: _, ...portfolio } = cached;
    return portfolio;
  }

  async storeWatchlist(watchlist: Asset[]): Promise<void> {
    await this.setItem(StorageKeys.WATCHLIST, watchlist);
  }

  async getWatchlist(): Promise<Asset[]> {
    const watchlist = await this.getItem<Asset[]>(StorageKeys.WATCHLIST);
    return watchlist ?? [];
  }

  async addToWatchlist(asset: Asset): Promise<void> {
    const watchlist = await this.getWatchlist();
    const exists = watchlist.find(item => item.symbol === asset.symbol);
    
    if (!exists) {
      watchlist.push(asset);
      await this.storeWatchlist(watchlist);
    }
  }

  async removeFromWatchlist(symbol: string): Promise<void> {
    const watchlist = await this.getWatchlist();
    const filtered = watchlist.filter(item => item.symbol !== symbol);
    await this.storeWatchlist(filtered);
  }

  // Price Cache
  async storePriceData(symbol: string, price: number): Promise<void> {
    const priceCache = await this.getItem<Record<string, { price: number; timestamp: string }>>(StorageKeys.PRICE_CACHE) ?? {};
    
    priceCache[symbol] = {
      price,
      timestamp: new Date().toISOString(),
    };
    
    await this.setItem(StorageKeys.PRICE_CACHE, priceCache);
  }

  async getPriceData(symbol: string): Promise<{ price: number; timestamp: Date } | null> {
    const priceCache = await this.getItem<Record<string, { price: number; timestamp: string }>>(StorageKeys.PRICE_CACHE);
    
    if (!priceCache || !priceCache[symbol]) {
      return null;
    }
    
    const data = priceCache[symbol];
    return {
      price: data.price,
      timestamp: new Date(data.timestamp),
    };
  }

  // Trading History
  async storeTradeHistory(trades: Trade[]): Promise<void> {
    await this.setItem(StorageKeys.TRADE_HISTORY, trades);
  }

  async getTradeHistory(): Promise<Trade[]> {
    const trades = await this.getItem<Trade[]>(StorageKeys.TRADE_HISTORY);
    return trades ?? [];
  }

  async addTrade(trade: Trade): Promise<void> {
    const trades = await this.getTradeHistory();
    trades.unshift(trade); // Add to beginning
    
    // Keep only last 1000 trades
    if (trades.length > 1000) {
      trades.splice(1000);
    }
    
    await this.storeTradeHistory(trades);
  }

  // Positions
  async storePositions(positions: Position[]): Promise<void> {
    await this.setItem(StorageKeys.POSITIONS_CACHE, {
      positions,
      lastUpdated: new Date().toISOString(),
    });
  }

  async getPositions(): Promise<Position[]> {
    const cached = await this.getItem<{ positions: Position[]; lastUpdated: string }>(StorageKeys.POSITIONS_CACHE);
    if (!cached) return [];

    // Check if cache is still valid (2 minutes)
    const lastUpdated = new Date(cached.lastUpdated);
    const now = new Date();
    const diffMinutes = (now.getTime() - lastUpdated.getTime()) / (1000 * 60);
    
    if (diffMinutes > 2) {
      return []; // Cache expired
    }

    return cached.positions;
  }

  // Price Alerts
  async storePriceAlerts(alerts: PriceAlert[]): Promise<void> {
    await this.setItem(StorageKeys.PRICE_ALERTS, alerts);
  }

  async getPriceAlerts(): Promise<PriceAlert[]> {
    const alerts = await this.getItem<PriceAlert[]>(StorageKeys.PRICE_ALERTS);
    return alerts ?? [];
  }

  async addPriceAlert(alert: PriceAlert): Promise<void> {
    const alerts = await this.getPriceAlerts();
    alerts.push(alert);
    await this.storePriceAlerts(alerts);
  }

  async removePriceAlert(alertId: string): Promise<void> {
    const alerts = await this.getPriceAlerts();
    const filtered = alerts.filter(alert => alert.id !== alertId);
    await this.storePriceAlerts(filtered);
  }

  async updatePriceAlert(alertId: string, updates: Partial<PriceAlert>): Promise<void> {
    const alerts = await this.getPriceAlerts();
    const index = alerts.findIndex(alert => alert.id === alertId);
    
    if (index !== -1) {
      alerts[index] = { ...alerts[index], ...updates };
      await this.storePriceAlerts(alerts);
    }
  }

  // Trading Settings
  async storeTradingSettings(settings: TradingSettings): Promise<void> {
    await this.setItem(StorageKeys.TRADING_SETTINGS, settings);
  }

  async getTradingSettings(): Promise<TradingSettings | null> {
    return this.getItem<TradingSettings>(StorageKeys.TRADING_SETTINGS);
  }

  // App Settings
  async storeAppSettings(settings: AppSettings): Promise<void> {
    await this.setItem(StorageKeys.APP_SETTINGS, settings);
  }

  async getAppSettings(): Promise<AppSettings | null> {
    return this.getItem<AppSettings>(StorageKeys.APP_SETTINGS);
  }

  // Theme Preference
  async setThemePreference(theme: 'light' | 'dark' | 'system'): Promise<void> {
    await this.setItem(StorageKeys.THEME_PREFERENCE, theme);
  }

  async getThemePreference(): Promise<'light' | 'dark' | 'system'> {
    const theme = await this.getItem<'light' | 'dark' | 'system'>(StorageKeys.THEME_PREFERENCE);
    return theme ?? 'system';
  }

  // User Preferences
  async storeUserPreferences(preferences: Record<string, any>): Promise<void> {
    await this.setItem(StorageKeys.USER_PREFERENCES, preferences);
  }

  async getUserPreferences(): Promise<Record<string, any>> {
    const preferences = await this.getItem<Record<string, any>>(StorageKeys.USER_PREFERENCES);
    return preferences ?? {};
  }

  async setUserPreference(key: string, value: any): Promise<void> {
    const preferences = await this.getUserPreferences();
    preferences[key] = value;
    await this.storeUserPreferences(preferences);
  }

  async getUserPreference<T>(key: string, defaultValue?: T): Promise<T | undefined> {
    const preferences = await this.getUserPreferences();
    return preferences[key] ?? defaultValue;
  }

  // Onboarding & Tutorial
  async setOnboardingCompleted(completed: boolean): Promise<void> {
    await this.setItem(StorageKeys.ONBOARDING_COMPLETED, completed);
  }

  async isOnboardingCompleted(): Promise<boolean> {
    const completed = await this.getItem<boolean>(StorageKeys.ONBOARDING_COMPLETED);
    return completed ?? false;
  }

  async setTutorialStep(step: string): Promise<void> {
    await this.setItem(StorageKeys.TUTORIAL_STEP, step);
  }

  async getTutorialStep(): Promise<string | null> {
    return this.getItem<string>(StorageKeys.TUTORIAL_STEP);
  }

  // Session Management
  async storeSessionData(data: Record<string, any>): Promise<void> {
    await this.setItem(StorageKeys.SESSION_DATA, data);
  }

  async getSessionData(): Promise<Record<string, any>> {
    const data = await this.getItem<Record<string, any>>(StorageKeys.SESSION_DATA);
    return data ?? {};
  }

  async clearSessionData(): Promise<void> {
    await this.removeItem(StorageKeys.SESSION_DATA);
  }

  // Cache Management
  async clearCache(): Promise<void> {
    const cacheKeys = [
      StorageKeys.PORTFOLIO_CACHE,
      StorageKeys.POSITIONS_CACHE,
      StorageKeys.PRICE_CACHE,
    ];
    
    await Promise.all(cacheKeys.map(key => this.removeItem(key)));
  }

  async getCacheSize(): Promise<number> {
    try {
      // This is an approximation since we can't get exact size easily
      const keys = [
        StorageKeys.PORTFOLIO_CACHE,
        StorageKeys.POSITIONS_CACHE,
        StorageKeys.PRICE_CACHE,
        StorageKeys.TRADE_HISTORY,
        StorageKeys.WATCHLIST,
      ];
      
      let totalSize = 0;
      
      for (const key of keys) {
        const value = await this.getItem(key);
        if (value) {
          totalSize += JSON.stringify(value).length;
        }
      }
      
      return totalSize;
    } catch (error) {
      console.error('Failed to calculate cache size:', error);
      return 0;
    }
  }

  // Backup & Restore
  async exportData(): Promise<Record<string, any>> {
    const exportKeys = [
      StorageKeys.WATCHLIST,
      StorageKeys.PRICE_ALERTS,
      StorageKeys.TRADING_SETTINGS,
      StorageKeys.APP_SETTINGS,
      StorageKeys.USER_PREFERENCES,
      StorageKeys.THEME_PREFERENCE,
    ];
    
    const exportData: Record<string, any> = {};
    
    for (const key of exportKeys) {
      const value = await this.getItem(key);
      if (value !== null) {
        exportData[key] = value;
      }
    }
    
    return {
      ...exportData,
      exportedAt: new Date().toISOString(),
      version: '1.0.0',
    };
  }

  async importData(data: Record<string, any>): Promise<void> {
    const { exportedAt, version, ...importData } = data;
    
    // Validate version compatibility if needed
    if (version && version !== '1.0.0') {
      console.warn('Import data version mismatch:', version);
    }
    
    for (const [key, value] of Object.entries(importData)) {
      await this.setItem(key, value);
    }
  }

  // Utility Methods
  async getAllKeys(): Promise<string[]> {
    try {
      const asyncStorageKeys = await AsyncStorage.getAllKeys();
      const mmkvKeys = storage.getAllKeys();
      return [...asyncStorageKeys, ...mmkvKeys];
    } catch (error) {
      console.error('Failed to get all keys:', error);
      return [];
    }
  }

  async getStorageInfo(): Promise<{
    totalKeys: number;
    cacheSize: number;
    lastCleared?: string;
  }> {
    const keys = await this.getAllKeys();
    const cacheSize = await this.getCacheSize();
    const lastCleared = await this.getItem<string>('last_cache_cleared');
    
    return {
      totalKeys: keys.length,
      cacheSize,
      lastCleared: lastCleared || undefined,
    };
  }
}

// Export singleton instance
export default new StorageService();
export { StorageService };