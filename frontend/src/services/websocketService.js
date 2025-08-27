import { io } from 'socket.io-client';

class WebSocketService {
  constructor() {
    this.socket = null;
    this.isConnected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;
    this.subscriptions = new Set();
    this.eventHandlers = new Map();
    
    // Configuration
    this.serverUrl = process.env.REACT_APP_WS_URL || 'http://localhost:5000';
  }

  /**
   * Initialize WebSocket connection
   */
  connect(token = null) {
    if (this.socket && this.isConnected) {
      console.log('WebSocket already connected');
      return Promise.resolve();
    }

    return new Promise((resolve, reject) => {
      try {
        // Socket.IO connection options
        const options = {
          transports: ['websocket', 'polling'],
          upgrade: true,
          rememberUpgrade: true,
          timeout: 10000,
          forceNew: true
        };

        // Add authentication if token provided
        if (token) {
          options.auth = { token };
          options.query = { token };
        }

        this.socket = io(this.serverUrl, options);

        // Connection event handlers
        this.socket.on('connect', () => {
          console.log('WebSocket connected:', this.socket.id);
          this.isConnected = true;
          this.reconnectAttempts = 0;
          this.resubscribeToSymbols();
          resolve();
        });

        this.socket.on('disconnect', (reason) => {
          console.log('WebSocket disconnected:', reason);
          this.isConnected = false;
          this.handleDisconnection();
        });

        this.socket.on('connect_error', (error) => {
          console.error('WebSocket connection error:', error);
          this.isConnected = false;
          reject(error);
        });

        // Set up event listeners for real-time data
        this.setupEventListeners();

      } catch (error) {
        console.error('Failed to initialize WebSocket:', error);
        reject(error);
      }
    });
  }

  /**
   * Disconnect WebSocket
   */
  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      this.isConnected = false;
      this.subscriptions.clear();
      this.eventHandlers.clear();
      console.log('WebSocket disconnected');
    }
  }

  /**
   * Set up event listeners for real-time data
   */
  setupEventListeners() {
    if (!this.socket) return;

    // Price updates
    this.socket.on('price_update', (data) => {
      this.handleEvent('price_update', data);
    });

    // Portfolio updates
    this.socket.on('portfolio_update', (data) => {
      this.handleEvent('portfolio_update', data);
    });

    // Bot status updates
    this.socket.on('bot_status_update', (data) => {
      this.handleEvent('bot_status_update', data);
    });

    // Trade notifications
    this.socket.on('trade_notification', (data) => {
      this.handleEvent('trade_notification', data);
    });

    // Market alerts
    this.socket.on('market_alert', (data) => {
      this.handleEvent('market_alert', data);
    });

    // Dashboard updates
    this.socket.on('dashboard_update', (data) => {
      this.handleEvent('dashboard_update', data);
    });

    // Connection statistics
    this.socket.on('connection_stats', (data) => {
      this.handleEvent('connection_stats', data);
    });

    // System status
    this.socket.on('system_status', (data) => {
      this.handleEvent('system_status', data);
    });

    // Error handling
    this.socket.on('error', (error) => {
      console.error('WebSocket error:', error);
      this.handleEvent('error', error);
    });
  }

  /**
   * Handle WebSocket events
   */
  handleEvent(eventType, data) {
    const handlers = this.eventHandlers.get(eventType) || [];
    handlers.forEach(handler => {
      try {
        handler(data);
      } catch (error) {
        console.error(`Error in ${eventType} handler:`, error);
      }
    });
  }

  /**
   * Subscribe to event
   */
  on(eventType, handler) {
    if (!this.eventHandlers.has(eventType)) {
      this.eventHandlers.set(eventType, []);
    }
    this.eventHandlers.get(eventType).push(handler);
  }

  /**
   * Unsubscribe from event
   */
  off(eventType, handler) {
    if (this.eventHandlers.has(eventType)) {
      const handlers = this.eventHandlers.get(eventType);
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  /**
   * Subscribe to symbol price updates
   */
  subscribeToSymbol(symbol) {
    if (!this.socket || !this.isConnected) {
      console.warn('WebSocket not connected, cannot subscribe to symbol:', symbol);
      return false;
    }

    this.socket.emit('subscribe_symbol', { symbol });
    this.subscriptions.add(symbol);
    console.log(`Subscribed to ${symbol}`);
    return true;
  }

  /**
   * Unsubscribe from symbol price updates
   */
  unsubscribeFromSymbol(symbol) {
    if (!this.socket || !this.isConnected) {
      console.warn('WebSocket not connected, cannot unsubscribe from symbol:', symbol);
      return false;
    }

    this.socket.emit('unsubscribe_symbol', { symbol });
    this.subscriptions.delete(symbol);
    console.log(`Unsubscribed from ${symbol}`);
    return true;
  }

  /**
   * Request portfolio update
   */
  requestPortfolioUpdate() {
    if (!this.socket || !this.isConnected) {
      console.warn('WebSocket not connected, cannot request portfolio update');
      return false;
    }

    this.socket.emit('portfolio_update_request');
    return true;
  }

  /**
   * Request price history
   */
  requestPriceHistory(symbol, timeframe = '1h', limit = 100) {
    if (!this.socket || !this.isConnected) {
      console.warn('WebSocket not connected, cannot request price history');
      return false;
    }

    this.socket.emit('price_history_request', {
      symbol,
      timeframe,
      limit
    });
    return true;
  }

  /**
   * Get current connection status
   */
  getConnectionStatus() {
    return {
      connected: this.isConnected,
      socketId: this.socket?.id || null,
      subscriptions: Array.from(this.subscriptions),
      reconnectAttempts: this.reconnectAttempts
    };
  }

  /**
   * Handle disconnection and attempt reconnection
   */
  handleDisconnection() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
      
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts}) in ${delay}ms`);
      
      setTimeout(() => {
        if (!this.isConnected) {
          this.connect();
        }
      }, delay);
    } else {
      console.error('Max reconnection attempts reached');
      this.handleEvent('max_reconnect_attempts_reached', {
        attempts: this.reconnectAttempts
      });
    }
  }

  /**
   * Resubscribe to all symbols after reconnection
   */
  resubscribeToSymbols() {
    this.subscriptions.forEach(symbol => {
      this.socket.emit('subscribe_symbol', { symbol });
    });
    
    if (this.subscriptions.size > 0) {
      console.log(`Resubscribed to ${this.subscriptions.size} symbols`);
    }
  }

  /**
   * Send test message (for debugging)
   */
  sendTestMessage(message) {
    if (!this.socket || !this.isConnected) {
      console.warn('WebSocket not connected, cannot send test message');
      return false;
    }

    this.socket.emit('test_message', { message, timestamp: Date.now() });
    return true;
  }

  /**
   * Get WebSocket statistics
   */
  getStatistics() {
    if (!this.socket || !this.isConnected) {
      return null;
    }

    return {
      connected: this.isConnected,
      socketId: this.socket.id,
      subscriptions: this.subscriptions.size,
      eventHandlers: this.eventHandlers.size,
      reconnectAttempts: this.reconnectAttempts,
      serverUrl: this.serverUrl
    };
  }
}

// Create singleton instance
const websocketService = new WebSocketService();

export default websocketService;