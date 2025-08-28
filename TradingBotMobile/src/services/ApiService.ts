/**
 * API Service for handling HTTP requests and WebSocket connections
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import {
  ApiResponse,
  User,
  Portfolio,
  Asset,
  Trade,
  Position,
  Order,
  OrderRequest,
  PriceAlert,
  MarketData,
  TradingSettings,
} from '../types';

class ApiService {
  private baseUrl: string;
  private wsUrl: string;
  private authToken: string | null = null;
  private wsConnection: WebSocket | null = null;
  private wsReconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private wsEventListeners: Map<string, ((data: any) => void)[]> = new Map();

  constructor() {
    // In production, these would come from environment variables
    this.baseUrl = __DEV__ 
      ? 'http://localhost:3000/api' 
      : 'https://api.tradingbot.com';
    this.wsUrl = __DEV__ 
      ? 'ws://localhost:3000/ws' 
      : 'wss://ws.tradingbot.com';
    
    this.loadAuthToken();
  }

  // Authentication Methods
  private async loadAuthToken(): Promise<void> {
    try {
      this.authToken = await AsyncStorage.getItem('auth_token');
    } catch (error) {
      console.error('Failed to load auth token:', error);
    }
  }

  private async saveAuthToken(token: string): Promise<void> {
    try {
      this.authToken = token;
      await AsyncStorage.setItem('auth_token', token);
    } catch (error) {
      console.error('Failed to save auth token:', error);
    }
  }

  private async clearAuthToken(): Promise<void> {
    try {
      this.authToken = null;
      await AsyncStorage.removeItem('auth_token');
    } catch (error) {
      console.error('Failed to clear auth token:', error);
    }
  }

  // HTTP Request Helper
  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const url = `${this.baseUrl}${endpoint}`;
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
        ...options.headers,
      };

      if (this.authToken) {
        headers.Authorization = `Bearer ${this.authToken}`;
      }

      const response = await fetch(url, {
        ...options,
        headers,
      });

      const data = await response.json();

      if (!response.ok) {
        return {
          success: false,
          error: data.message || 'Request failed',
        };
      }

      return {
        success: true,
        data: data.data || data,
      };
    } catch (error) {
      console.error('API Request failed:', error);
      return {
        success: false,
        error: 'Network error occurred',
      };
    }
  }

  // Authentication API
  async login(email: string, password: string): Promise<ApiResponse<{ user: User; token: string }>> {
    const response = await this.makeRequest<{ user: User; token: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });

    if (response.success && response.data?.token) {
      await this.saveAuthToken(response.data.token);
    }

    return response;
  }

  async register(email: string, password: string, displayName: string): Promise<ApiResponse<{ user: User; token: string }>> {
    const response = await this.makeRequest<{ user: User; token: string }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, displayName }),
    });

    if (response.success && response.data?.token) {
      await this.saveAuthToken(response.data.token);
    }

    return response;
  }

  async logout(): Promise<ApiResponse<void>> {
    const response = await this.makeRequest<void>('/auth/logout', {
      method: 'POST',
    });

    await this.clearAuthToken();
    this.disconnectWebSocket();

    return response;
  }

  async refreshToken(): Promise<ApiResponse<{ token: string }>> {
    const response = await this.makeRequest<{ token: string }>('/auth/refresh', {
      method: 'POST',
    });

    if (response.success && response.data?.token) {
      await this.saveAuthToken(response.data.token);
    }

    return response;
  }

  // User API
  async getProfile(): Promise<ApiResponse<User>> {
    return this.makeRequest<User>('/user/profile');
  }

  async updateProfile(updates: Partial<User>): Promise<ApiResponse<User>> {
    return this.makeRequest<User>('/user/profile', {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  // Trading API
  async getPortfolio(): Promise<ApiResponse<Portfolio>> {
    return this.makeRequest<Portfolio>('/trading/portfolio');
  }

  async getWatchlist(): Promise<ApiResponse<Asset[]>> {
    return this.makeRequest<Asset[]>('/trading/watchlist');
  }

  async addToWatchlist(symbol: string): Promise<ApiResponse<void>> {
    return this.makeRequest<void>('/trading/watchlist', {
      method: 'POST',
      body: JSON.stringify({ symbol }),
    });
  }

  async removeFromWatchlist(symbol: string): Promise<ApiResponse<void>> {
    return this.makeRequest<void>(`/trading/watchlist/${symbol}`, {
      method: 'DELETE',
    });
  }

  async getRecentTrades(): Promise<ApiResponse<Trade[]>> {
    return this.makeRequest<Trade[]>('/trading/trades');
  }

  async getActivePositions(): Promise<ApiResponse<Position[]>> {
    return this.makeRequest<Position[]>('/trading/positions');
  }

  async placeOrder(orderRequest: OrderRequest): Promise<ApiResponse<Order>> {
    return this.makeRequest<Order>('/trading/orders', {
      method: 'POST',
      body: JSON.stringify(orderRequest),
    });
  }

  async cancelOrder(orderId: string): Promise<ApiResponse<void>> {
    return this.makeRequest<void>(`/trading/orders/${orderId}`, {
      method: 'DELETE',
    });
  }

  async getOrders(): Promise<ApiResponse<Order[]>> {
    return this.makeRequest<Order[]>('/trading/orders');
  }

  // Market Data API
  async getMarketData(symbols: string[]): Promise<ApiResponse<MarketData[]>> {
    const symbolsParam = symbols.join(',');
    return this.makeRequest<MarketData[]>(`/market/data?symbols=${symbolsParam}`);
  }

  async getAssetPrice(symbol: string): Promise<ApiResponse<{ price: number }>> {
    return this.makeRequest<{ price: number }>(`/market/price/${symbol}`);
  }

  async searchAssets(query: string): Promise<ApiResponse<Asset[]>> {
    return this.makeRequest<Asset[]>(`/market/search?q=${encodeURIComponent(query)}`);
  }

  // Price Alerts API
  async getPriceAlerts(): Promise<ApiResponse<PriceAlert[]>> {
    return this.makeRequest<PriceAlert[]>('/alerts');
  }

  async createPriceAlert(alert: Omit<PriceAlert, 'id' | 'createdAt'>): Promise<ApiResponse<PriceAlert>> {
    return this.makeRequest<PriceAlert>('/alerts', {
      method: 'POST',
      body: JSON.stringify(alert),
    });
  }

  async deletePriceAlert(alertId: string): Promise<ApiResponse<void>> {
    return this.makeRequest<void>(`/alerts/${alertId}`, {
      method: 'DELETE',
    });
  }

  // Settings API
  async getTradingSettings(): Promise<ApiResponse<TradingSettings>> {
    return this.makeRequest<TradingSettings>('/settings/trading');
  }

  async updateTradingSettings(settings: Partial<TradingSettings>): Promise<ApiResponse<TradingSettings>> {
    return this.makeRequest<TradingSettings>('/settings/trading', {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
  }

  // WebSocket Methods
  connectWebSocket(): void {
    if (this.wsConnection?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    try {
      const wsUrl = this.authToken 
        ? `${this.wsUrl}?token=${this.authToken}` 
        : this.wsUrl;
      
      this.wsConnection = new WebSocket(wsUrl);

      this.wsConnection.onopen = () => {
        console.log('WebSocket connected');
        this.wsReconnectAttempts = 0;
        this.subscribeToDefaultChannels();
      };

      this.wsConnection.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          this.handleWebSocketMessage(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.wsConnection.onclose = () => {
        console.log('WebSocket disconnected');
        this.attemptReconnect();
      };

      this.wsConnection.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
    }
  }

  disconnectWebSocket(): void {
    if (this.wsConnection) {
      this.wsConnection.close();
      this.wsConnection = null;
    }
  }

  private attemptReconnect(): void {
    if (this.wsReconnectAttempts < this.maxReconnectAttempts) {
      this.wsReconnectAttempts++;
      const delay = Math.pow(2, this.wsReconnectAttempts) * 1000; // Exponential backoff
      
      setTimeout(() => {
        console.log(`Attempting WebSocket reconnection (${this.wsReconnectAttempts}/${this.maxReconnectAttempts})`);
        this.connectWebSocket();
      }, delay);
    }
  }

  private subscribeToDefaultChannels(): void {
    // Subscribe to price updates for watchlist
    this.sendWebSocketMessage({
      type: 'subscribe',
      channel: 'prices',
    });

    // Subscribe to portfolio updates
    this.sendWebSocketMessage({
      type: 'subscribe',
      channel: 'portfolio',
    });

    // Subscribe to order updates
    this.sendWebSocketMessage({
      type: 'subscribe',
      channel: 'orders',
    });
  }

  private sendWebSocketMessage(message: any): void {
    if (this.wsConnection?.readyState === WebSocket.OPEN) {
      this.wsConnection.send(JSON.stringify(message));
    }
  }

  private handleWebSocketMessage(message: any): void {
    const { type, data } = message;
    const listeners = this.wsEventListeners.get(type) || [];
    
    listeners.forEach(listener => {
      try {
        listener(data);
      } catch (error) {
        console.error('WebSocket event listener error:', error);
      }
    });
  }

  // Event Subscription Methods
  addEventListener(eventType: string, listener: (data: any) => void): void {
    if (!this.wsEventListeners.has(eventType)) {
      this.wsEventListeners.set(eventType, []);
    }
    this.wsEventListeners.get(eventType)!.push(listener);
  }

  removeEventListener(eventType: string, listener: (data: any) => void): void {
    const listeners = this.wsEventListeners.get(eventType);
    if (listeners) {
      const index = listeners.indexOf(listener);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    }
  }

  // Utility Methods
  isAuthenticated(): boolean {
    return !!this.authToken;
  }

  getAuthToken(): string | null {
    return this.authToken;
  }

  // Mock Data Methods (for development/testing)
  async getMockPortfolio(): Promise<Portfolio> {
    return {
      totalValue: 125000,
      availableBalance: 25000,
      unrealizedPnL: 5000,
      realizedPnL: 15000,
      totalPnL: 20000,
      totalPnLPercent: 19.05,
      positions: [
        {
          id: '1',
          symbol: 'BTCUSDT',
          side: 'long',
          size: 2.5,
          entryPrice: 45000,
          currentPrice: 47000,
          unrealizedPnL: 5000,
          unrealizedPnLPercent: 4.44,
          margin: 11250,
          leverage: 10,
          openedAt: new Date(Date.now() - 86400000),
        },
      ],
      assets: [
        {
          symbol: 'BTC',
          name: 'Bitcoin',
          balance: 2.5,
          value: 117500,
          allocation: 94,
          averagePrice: 45000,
          currentPrice: 47000,
          pnl: 5000,
          pnlPercent: 4.44,
        },
        {
          symbol: 'USDT',
          name: 'Tether',
          balance: 7500,
          value: 7500,
          allocation: 6,
          averagePrice: 1,
          currentPrice: 1,
          pnl: 0,
          pnlPercent: 0,
        },
      ],
    };
  }

  async getMockWatchlist(): Promise<Asset[]> {
    return [
      {
        symbol: 'BTCUSDT',
        name: 'Bitcoin',
        price: 47000,
        change: 2000,
        changePercent: 4.44,
        volume: 28500000000,
        high24h: 48000,
        low24h: 44500,
        lastUpdated: new Date(),
      },
      {
        symbol: 'ETHUSDT',
        name: 'Ethereum',
        price: 3200,
        change: -150,
        changePercent: -4.48,
        volume: 15200000000,
        high24h: 3400,
        low24h: 3150,
        lastUpdated: new Date(),
      },
      {
        symbol: 'ADAUSDT',
        name: 'Cardano',
        price: 1.25,
        change: 0.08,
        changePercent: 6.84,
        volume: 2100000000,
        high24h: 1.28,
        low24h: 1.15,
        lastUpdated: new Date(),
      },
    ];
  }
}

// Export singleton instance
export default new ApiService();