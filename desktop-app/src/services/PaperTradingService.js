class PaperTradingService {
  constructor() {
    this.portfolio = {
      balance: 100000, // Start with $100,000 virtual money
      equity: 100000,
      positions: [],
      trades: [],
      totalPnL: 0,
      dayPnL: 0,
    };
    this.isInitialized = false;
    this.listeners = [];
  }

  async initialize() {
    if (this.isInitialized) return;

    try {
      const savedPortfolio = localStorage.getItem('paperTradingPortfolio');
      if (savedPortfolio) {
        this.portfolio = JSON.parse(savedPortfolio);
      }
      this.isInitialized = true;
      this.notifyListeners();
    } catch (error) {
      console.error('Failed to initialize paper trading service:', error);
    }
  }

  savePortfolio() {
    try {
      localStorage.setItem('paperTradingPortfolio', JSON.stringify(this.portfolio));
      this.notifyListeners();
    } catch (error) {
      console.error('Failed to save paper trading portfolio:', error);
    }
  }

  resetPortfolio() {
    this.portfolio = {
      balance: 100000,
      equity: 100000,
      positions: [],
      trades: [],
      totalPnL: 0,
      dayPnL: 0,
    };
    this.savePortfolio();
  }

  getPortfolio() {
    return { ...this.portfolio };
  }

  placePaperTrade(symbol, type, quantity, price) {
    const totalCost = quantity * price;
    const trade = {
      id: Date.now().toString(),
      symbol,
      type,
      quantity,
      price,
      timestamp: Date.now(),
      status: 'pending',
    };

    // Validate trade
    if (type === 'buy') {
      if (totalCost > this.portfolio.balance) {
        return {
          success: false,
          message: 'Insufficient balance for this trade',
        };
      }
    } else {
      const position = this.portfolio.positions.find(p => p.symbol === symbol);
      if (!position || position.quantity < quantity) {
        return {
          success: false,
          message: 'Insufficient shares to sell',
        };
      }
    }

    // Execute trade
    trade.status = 'filled';
    this.portfolio.trades.push(trade);

    if (type === 'buy') {
      this.portfolio.balance -= totalCost;
      this.addToPosition(symbol, quantity, price);
    } else {
      this.portfolio.balance += totalCost;
      this.removeFromPosition(symbol, quantity, price);
    }

    this.updateEquity();
    this.savePortfolio();

    return {
      success: true,
      message: `${type.toUpperCase()} order filled successfully`,
      trade,
    };
  }

  addToPosition(symbol, quantity, price) {
    const existingPosition = this.portfolio.positions.find(p => p.symbol === symbol);
    
    if (existingPosition) {
      const totalQuantity = existingPosition.quantity + quantity;
      const totalValue = (existingPosition.quantity * existingPosition.averagePrice) + (quantity * price);
      existingPosition.averagePrice = totalValue / totalQuantity;
      existingPosition.quantity = totalQuantity;
    } else {
      this.portfolio.positions.push({
        symbol,
        quantity,
        averagePrice: price,
        currentPrice: price,
        unrealizedPnL: 0,
        realizedPnL: 0,
      });
    }
  }

  removeFromPosition(symbol, quantity, sellPrice) {
    const position = this.portfolio.positions.find(p => p.symbol === symbol);
    if (!position) return;

    const realizedPnL = (sellPrice - position.averagePrice) * quantity;
    position.realizedPnL += realizedPnL;
    this.portfolio.totalPnL += realizedPnL;

    position.quantity -= quantity;
    
    if (position.quantity <= 0) {
      this.portfolio.positions = this.portfolio.positions.filter(p => p.symbol !== symbol);
    }
  }

  updatePrices(priceData) {
    this.portfolio.positions.forEach(position => {
      if (priceData[position.symbol]) {
        position.currentPrice = priceData[position.symbol];
        position.unrealizedPnL = (position.currentPrice - position.averagePrice) * position.quantity;
      }
    });

    this.updateEquity();
    this.savePortfolio();
  }

  updateEquity() {
    const positionsValue = this.portfolio.positions.reduce(
      (total, position) => total + (position.currentPrice * position.quantity),
      0
    );
    
    this.portfolio.equity = this.portfolio.balance + positionsValue;
    
    const unrealizedPnL = this.portfolio.positions.reduce(
      (total, position) => total + position.unrealizedPnL,
      0
    );
    
    this.portfolio.totalPnL = this.portfolio.positions.reduce(
      (total, position) => total + position.realizedPnL,
      0
    ) + unrealizedPnL;
  }

  getTradeHistory() {
    return [...this.portfolio.trades].sort((a, b) => b.timestamp - a.timestamp);
  }

  getPositions() {
    return [...this.portfolio.positions];
  }

  getPerformanceMetrics() {
    const totalReturn = ((this.portfolio.equity - 100000) / 100000) * 100;
    const winningTrades = this.portfolio.trades.filter(trade => {
      if (trade.type === 'sell') {
        const position = this.portfolio.positions.find(p => p.symbol === trade.symbol);
        return position && position.realizedPnL > 0;
      }
      return false;
    }).length;
    
    const totalTrades = this.portfolio.trades.filter(t => t.type === 'sell').length;
    const winRate = totalTrades > 0 ? (winningTrades / totalTrades) * 100 : 0;

    return {
      totalReturn,
      totalPnL: this.portfolio.totalPnL,
      winRate,
      totalTrades,
      winningTrades,
      equity: this.portfolio.equity,
      balance: this.portfolio.balance,
    };
  }

  enableDemoMode() {
    localStorage.setItem('tradingMode', 'demo');
    this.notifyListeners();
  }

  enableLiveMode() {
    localStorage.setItem('tradingMode', 'live');
    this.notifyListeners();
  }

  getTradingMode() {
    return localStorage.getItem('tradingMode') || 'demo';
  }

  isDemoMode() {
    return this.getTradingMode() === 'demo';
  }

  // Event listener system
  addListener(callback) {
    this.listeners.push(callback);
  }

  removeListener(callback) {
    this.listeners = this.listeners.filter(listener => listener !== callback);
  }

  notifyListeners() {
    this.listeners.forEach(callback => {
      try {
        callback(this.getPortfolio());
      } catch (error) {
        console.error('Error in portfolio listener:', error);
      }
    });
  }

  // Utility methods
  formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  }

  formatPercentage(value) {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  }

  formatDate(timestamp) {
    return new Date(timestamp).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }
}

// Create singleton instance
const paperTradingService = new PaperTradingService();

// Initialize on load
if (typeof window !== 'undefined') {
  window.addEventListener('load', () => {
    paperTradingService.initialize();
  });
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = paperTradingService;
} else if (typeof window !== 'undefined') {
  window.PaperTradingService = paperTradingService;
}