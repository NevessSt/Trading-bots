/**
 * WebSocket Service for real-time market data and trading updates
 */

import { EventEmitter } from 'events';
import {
  WebSocketEvent,
  PriceUpdateEvent,
  OrderUpdateEvent,
  PositionUpdateEvent,
  MarketData,
} from '../types';

interface WebSocketMessage {
  type: string;
  channel?: string;
  data?: any;
  timestamp?: number;
}

interface SubscriptionOptions {
  symbols?: string[];
  channels?: string[];
}

class WebSocketService extends EventEmitter {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectInterval = 1000;
  private isConnecting = false;
  private subscriptions: Set<string> = new Set();
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private lastHeartbeat = 0;
  private authToken: string | null = null;

  constructor() {
    super();
    this.url = __DEV__ 
      ? 'ws://localhost:3000/ws' 
      : 'wss://ws.tradingbot.com';
  }

  // Connection Management
  connect(token?: string): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      if (this.isConnecting) {
        this.once('connected', resolve);
        this.once('error', reject);
        return;
      }

      this.isConnecting = true;
      this.authToken = token || this.authToken;

      try {
        const wsUrl = this.authToken 
          ? `${this.url}?token=${this.authToken}` 
          : this.url;
        
        this.ws = new WebSocket(wsUrl);
        this.setupEventHandlers();

        const timeout = setTimeout(() => {
          reject(new Error('WebSocket connection timeout'));
        }, 10000);

        this.once('connected', () => {
          clearTimeout(timeout);
          resolve();
        });

        this.once('error', (error) => {
          clearTimeout(timeout);
          reject(error);
        });
      } catch (error) {
        this.isConnecting = false;
        reject(error);
      }
    });
  }

  disconnect(): void {
    this.stopHeartbeat();
    this.subscriptions.clear();
    
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
    
    this.isConnecting = false;
    this.reconnectAttempts = 0;
  }

  private setupEventHandlers(): void {
    if (!this.ws) return;

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.isConnecting = false;
      this.reconnectAttempts = 0;
      this.startHeartbeat();
      this.resubscribeAll();
      this.emit('connected');
    };

    this.ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        this.handleMessage(message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
        this.emit('error', error);
      }
    };

    this.ws.onclose = (event) => {
      console.log('WebSocket disconnected:', event.code, event.reason);
      this.stopHeartbeat();
      this.ws = null;
      this.isConnecting = false;
      this.emit('disconnected', { code: event.code, reason: event.reason });
      
      // Auto-reconnect unless it was a clean close
      if (event.code !== 1000) {
        this.attemptReconnect();
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.emit('error', error);
    };
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      this.emit('maxReconnectAttemptsReached');
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(
      this.reconnectInterval * Math.pow(2, this.reconnectAttempts - 1),
      30000
    );

    console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
    
    setTimeout(() => {
      this.connect().catch((error) => {
        console.error('Reconnection failed:', error);
      });
    }, delay);
  }

  // Heartbeat Management
  private startHeartbeat(): void {
    this.stopHeartbeat();
    this.lastHeartbeat = Date.now();
    
    this.heartbeatInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.send({ type: 'ping', timestamp: Date.now() });
        
        // Check if we haven't received a pong in too long
        if (Date.now() - this.lastHeartbeat > 30000) {
          console.warn('Heartbeat timeout, reconnecting...');
          this.ws.close(1006, 'Heartbeat timeout');
        }
      }
    }, 15000);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  // Message Handling
  private handleMessage(message: WebSocketMessage): void {
    const { type, data, timestamp } = message;

    switch (type) {
      case 'pong':
        this.lastHeartbeat = Date.now();
        break;

      case 'price_update':
        this.handlePriceUpdate(data);
        break;

      case 'order_update':
        this.handleOrderUpdate(data);
        break;

      case 'position_update':
        this.handlePositionUpdate(data);
        break;

      case 'portfolio_update':
        this.emit('portfolioUpdate', data);
        break;

      case 'trade_executed':
        this.emit('tradeExecuted', data);
        break;

      case 'alert_triggered':
        this.emit('alertTriggered', data);
        break;

      case 'market_status':
        this.emit('marketStatus', data);
        break;

      case 'error':
        console.error('WebSocket server error:', data);
        this.emit('serverError', data);
        break;

      default:
        console.log('Unknown message type:', type, data);
        this.emit('message', message);
    }
  }

  private handlePriceUpdate(data: any): void {
    const priceUpdate: PriceUpdateEvent = {
      symbol: data.symbol,
      price: data.price,
      change: data.change,
      changePercent: data.changePercent,
      volume: data.volume,
      timestamp: new Date(data.timestamp),
    };
    
    this.emit('priceUpdate', priceUpdate);
  }

  private handleOrderUpdate(data: any): void {
    const orderUpdate: OrderUpdateEvent = {
      orderId: data.orderId,
      status: data.status,
      filledQuantity: data.filledQuantity,
      remainingQuantity: data.remainingQuantity,
      averagePrice: data.averagePrice,
      timestamp: new Date(data.timestamp),
    };
    
    this.emit('orderUpdate', orderUpdate);
  }

  private handlePositionUpdate(data: any): void {
    const positionUpdate: PositionUpdateEvent = {
      symbol: data.symbol,
      side: data.side,
      size: data.size,
      entryPrice: data.entryPrice,
      currentPrice: data.currentPrice,
      unrealizedPnL: data.unrealizedPnL,
      timestamp: new Date(data.timestamp),
    };
    
    this.emit('positionUpdate', positionUpdate);
  }

  // Subscription Management
  subscribe(channel: string, options?: SubscriptionOptions): void {
    const subscriptionKey = this.getSubscriptionKey(channel, options);
    
    if (this.subscriptions.has(subscriptionKey)) {
      return; // Already subscribed
    }

    const message: WebSocketMessage = {
      type: 'subscribe',
      channel,
      data: options,
    };

    if (this.send(message)) {
      this.subscriptions.add(subscriptionKey);
      console.log(`Subscribed to ${channel}:`, options);
    }
  }

  unsubscribe(channel: string, options?: SubscriptionOptions): void {
    const subscriptionKey = this.getSubscriptionKey(channel, options);
    
    if (!this.subscriptions.has(subscriptionKey)) {
      return; // Not subscribed
    }

    const message: WebSocketMessage = {
      type: 'unsubscribe',
      channel,
      data: options,
    };

    if (this.send(message)) {
      this.subscriptions.delete(subscriptionKey);
      console.log(`Unsubscribed from ${channel}:`, options);
    }
  }

  private getSubscriptionKey(channel: string, options?: SubscriptionOptions): string {
    return `${channel}:${JSON.stringify(options || {})}`;
  }

  private resubscribeAll(): void {
    // Re-establish all subscriptions after reconnection
    const subscriptions = Array.from(this.subscriptions);
    this.subscriptions.clear();
    
    subscriptions.forEach(subscriptionKey => {
      const [channel, optionsStr] = subscriptionKey.split(':');
      const options = optionsStr ? JSON.parse(optionsStr) : undefined;
      this.subscribe(channel, options);
    });
  }

  // Convenience Methods
  subscribeToPrices(symbols: string[]): void {
    this.subscribe('prices', { symbols });
  }

  subscribeToOrders(): void {
    this.subscribe('orders');
  }

  subscribeToPositions(): void {
    this.subscribe('positions');
  }

  subscribeToPortfolio(): void {
    this.subscribe('portfolio');
  }

  subscribeToTrades(): void {
    this.subscribe('trades');
  }

  subscribeToAlerts(): void {
    this.subscribe('alerts');
  }

  // Message Sending
  private send(message: WebSocketMessage): boolean {
    if (this.ws?.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(JSON.stringify(message));
        return true;
      } catch (error) {
        console.error('Failed to send WebSocket message:', error);
        this.emit('error', error);
        return false;
      }
    } else {
      console.warn('WebSocket not connected, message not sent:', message);
      return false;
    }
  }

  // Status Methods
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  getConnectionState(): string {
    if (!this.ws) return 'disconnected';
    
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING:
        return 'connecting';
      case WebSocket.OPEN:
        return 'connected';
      case WebSocket.CLOSING:
        return 'closing';
      case WebSocket.CLOSED:
        return 'closed';
      default:
        return 'unknown';
    }
  }

  getSubscriptions(): string[] {
    return Array.from(this.subscriptions);
  }

  // Configuration
  setMaxReconnectAttempts(attempts: number): void {
    this.maxReconnectAttempts = Math.max(0, attempts);
  }

  setReconnectInterval(interval: number): void {
    this.reconnectInterval = Math.max(1000, interval);
  }

  // Mock Data Methods (for development)
  startMockData(): void {
    if (!__DEV__) return;

    // Simulate price updates
    setInterval(() => {
      const symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT'];
      const symbol = symbols[Math.floor(Math.random() * symbols.length)];
      
      const basePrice = symbol === 'BTCUSDT' ? 47000 : symbol === 'ETHUSDT' ? 3200 : 1.25;
      const price = basePrice + (Math.random() - 0.5) * basePrice * 0.02;
      const change = (Math.random() - 0.5) * basePrice * 0.05;
      
      this.handlePriceUpdate({
        symbol,
        price: Math.round(price * 100) / 100,
        change: Math.round(change * 100) / 100,
        changePercent: Math.round((change / basePrice) * 10000) / 100,
        volume: Math.random() * 1000000000,
        timestamp: Date.now(),
      });
    }, 2000);

    // Simulate occasional order updates
    setInterval(() => {
      if (Math.random() < 0.3) {
        this.handleOrderUpdate({
          orderId: `order_${Date.now()}`,
          status: Math.random() < 0.7 ? 'filled' : 'partially_filled',
          filledQuantity: Math.random() * 10,
          remainingQuantity: Math.random() * 5,
          averagePrice: 47000 + (Math.random() - 0.5) * 1000,
          timestamp: Date.now(),
        });
      }
    }, 10000);
  }
}

// Export singleton instance
export default new WebSocketService();
export { WebSocketService };