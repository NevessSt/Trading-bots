import AsyncStorage from '@react-native-async-storage/async-storage';

interface PaperTrade {
  id: string;
  symbol: string;
  type: 'buy' | 'sell';
  quantity: number;
  price: number;
  timestamp: number;
  status: 'pending' | 'filled' | 'cancelled';
}

interface PaperPosition {
  symbol: string;
  quantity: number;
  averagePrice: number;
  currentPrice: number;
  unrealizedPnL: number;
  realizedPnL: number;
}

interface PaperPortfolio {
  balance: number;
  equity: number;
  positions: PaperPosition[];
  trades: PaperTrade[];
  totalPnL: number;
  dayPnL: number;
}

class PaperTradingService {
  private static instance: PaperTradingService;
  private portfolio: PaperPortfolio;
  private isInitialized = false;

  private constructor() {
    this.portfolio = {
      balance: 100000, // Start with $100,000 virtual money
      equity: 100000,
      positions: [],
      trades: [],
      totalPnL: 0,
      dayPnL: 0,
    };
  }

  static getInstance(): PaperTradingService {
    if (!PaperTradingService.instance) {
      PaperTradingService.instance = new PaperTradingService();
    }
    return PaperTradingService.instance;
  }

  async initialize(): Promise<void> {
    if (this.isInitialized) return;

    try {
      const savedPortfolio = await AsyncStorage.getItem('paperTradingPortfolio');
      if (savedPortfolio) {
        this.portfolio = JSON.parse(savedPortfolio);
      }
      this.isInitialized = true;
    } catch (error) {
      console.error('Failed to initialize paper trading service:', error);
    }
  }

  async savePortfolio(): Promise<void> {
    try {
      await AsyncStorage.setItem('paperTradingPortfolio', JSON.stringify(this.portfolio));
    } catch (error) {
      console.error('Failed to save paper trading portfolio:', error);
    }
  }

  async resetPortfolio(): Promise<void> {
    this.portfolio = {
      balance: 100000,
      equity: 100000,
      positions: [],
      trades: [],
      totalPnL: 0,
      dayPnL: 0,
    };
    await this.savePortfolio();
  }

  getPortfolio(): PaperPortfolio {
    return { ...this.portfolio };
  }

  async placePaperTrade(
    symbol: string,
    type: 'buy' | 'sell',
    quantity: number,
    price: number
  ): Promise<{ success: boolean; message: string; trade?: PaperTrade }> {
    await this.initialize();

    const totalCost = quantity * price;
    const trade: PaperTrade = {
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

    await this.updateEquity();
    await this.savePortfolio();

    return {
      success: true,
      message: `${type.toUpperCase()} order filled successfully`,
      trade,
    };
  }

  private addToPosition(symbol: string, quantity: number, price: number): void {
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

  private removeFromPosition(symbol: string, quantity: number, sellPrice: number): void {
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

  async updatePrices(priceData: { [symbol: string]: number }): Promise<void> {
    await this.initialize();

    this.portfolio.positions.forEach(position => {
      if (priceData[position.symbol]) {
        position.currentPrice = priceData[position.symbol];
        position.unrealizedPnL = (position.currentPrice - position.averagePrice) * position.quantity;
      }
    });

    await this.updateEquity();
    await this.savePortfolio();
  }

  private async updateEquity(): Promise<void> {
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

  getTradeHistory(): PaperTrade[] {
    return [...this.portfolio.trades].sort((a, b) => b.timestamp - a.timestamp);
  }

  getPositions(): PaperPosition[] {
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

  async enableDemoMode(): Promise<void> {
    await AsyncStorage.setItem('tradingMode', 'demo');
  }

  async enableLiveMode(): Promise<void> {
    await AsyncStorage.setItem('tradingMode', 'live');
  }

  async getTradingMode(): Promise<'demo' | 'live'> {
    const mode = await AsyncStorage.getItem('tradingMode');
    return (mode as 'demo' | 'live') || 'demo';
  }
}

export default PaperTradingService;
export type { PaperTrade, PaperPosition, PaperPortfolio };