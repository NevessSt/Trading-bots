/**
 * Demo Data Service
 * Provides realistic fake trading data for demonstration purposes
 * Allows buyers to test the platform without Binance API connection
 */

class DemoDataService {
  constructor() {
    this.isDemo = true
    this.startTime = Date.now()
    this.basePortfolioValue = 125430.50
    this.tradingPairs = [
      { symbol: 'BTC/USD', name: 'Bitcoin', basePrice: 43250.75, volatility: 0.02 },
      { symbol: 'ETH/USD', name: 'Ethereum', basePrice: 2087.50, volatility: 0.03 },
      { symbol: 'ADA/USD', name: 'Cardano', basePrice: 1.266, volatility: 0.05 },
      { symbol: 'DOT/USD', name: 'Polkadot', basePrice: 7.85, volatility: 0.04 },
      { symbol: 'LINK/USD', name: 'Chainlink', basePrice: 14.23, volatility: 0.04 },
      { symbol: 'SOL/USD', name: 'Solana', basePrice: 98.45, volatility: 0.06 },
      { symbol: 'MATIC/USD', name: 'Polygon', basePrice: 0.89, volatility: 0.05 },
      { symbol: 'AVAX/USD', name: 'Avalanche', basePrice: 35.67, volatility: 0.05 }
    ]
    
    this.portfolioPositions = [
      { symbol: 'BTC/USD', amount: 2.5, entryPrice: 42800 },
      { symbol: 'ETH/USD', amount: 15.8, entryPrice: 2050 },
      { symbol: 'ADA/USD', amount: 5000, entryPrice: 1.20 },
      { symbol: 'DOT/USD', amount: 150, entryPrice: 7.60 },
      { symbol: 'LINK/USD', amount: 200, entryPrice: 13.80 }
    ]
    
    this.tradeHistory = this.generateTradeHistory()
    this.priceHistory = new Map()
    
    // Initialize price history for each pair
    this.tradingPairs.forEach(pair => {
      this.priceHistory.set(pair.symbol, this.generatePriceHistory(pair))
    })
    
    // Start real-time updates
    this.startRealTimeUpdates()
  }
  
  // Generate realistic price movements
  generatePriceMovement(basePrice, volatility, timeElapsed) {
    const trend = Math.sin(timeElapsed / 300000) * 0.01 // 5-minute trend cycle
    const noise = (Math.random() - 0.5) * volatility
    const momentum = (Math.random() - 0.5) * 0.005
    
    return basePrice * (1 + trend + noise + momentum)
  }
  
  // Generate historical price data
  generatePriceHistory(pair, hours = 24) {
    const history = []
    const now = Date.now()
    const interval = 5 * 60 * 1000 // 5 minutes
    
    for (let i = hours * 12; i >= 0; i--) {
      const timestamp = now - (i * interval)
      const price = this.generatePriceMovement(pair.basePrice, pair.volatility, timestamp - this.startTime)
      
      history.push({
        timestamp,
        price: Math.max(price, pair.basePrice * 0.8), // Prevent extreme drops
        volume: Math.random() * 1000000 + 500000
      })
    }
    
    return history
  }
  
  // Generate realistic trade history
  generateTradeHistory(count = 50) {
    const trades = []
    const now = Date.now()
    
    for (let i = 0; i < count; i++) {
      const pair = this.tradingPairs[Math.floor(Math.random() * this.tradingPairs.length)]
      const side = Math.random() > 0.5 ? 'buy' : 'sell'
      const amount = this.generateTradeAmount(pair.symbol)
      const price = this.generatePriceMovement(pair.basePrice, pair.volatility, now - (i * 300000))
      const total = amount * price
      const fee = total * 0.001 // 0.1% fee
      const pnl = (Math.random() - 0.4) * total * 0.1 // Slightly positive bias
      
      trades.push({
        id: i + 1,
        symbol: pair.symbol,
        side,
        amount: parseFloat(amount.toFixed(pair.symbol.includes('BTC') ? 4 : 2)),
        price: parseFloat(price.toFixed(2)),
        total: parseFloat(total.toFixed(2)),
        fee: parseFloat(fee.toFixed(2)),
        time: new Date(now - (i * 300000 + Math.random() * 240000)).toISOString(),
        status: 'completed',
        pnl: parseFloat(pnl.toFixed(2)),
        strategy: this.getRandomStrategy()
      })
    }
    
    return trades.sort((a, b) => new Date(b.time) - new Date(a.time))
  }
  
  generateTradeAmount(symbol) {
    if (symbol.includes('BTC')) return Math.random() * 2 + 0.1
    if (symbol.includes('ETH')) return Math.random() * 10 + 1
    if (symbol.includes('SOL') || symbol.includes('AVAX')) return Math.random() * 50 + 5
    return Math.random() * 1000 + 100
  }
  
  getRandomStrategy() {
    const strategies = ['Scalping', 'Swing Trading', 'EMA Crossover', 'RSI Divergence', 'Manual']
    return strategies[Math.floor(Math.random() * strategies.length)]
  }
  
  // Get current market data
  getMarketData() {
    const now = Date.now()
    
    return this.tradingPairs.map(pair => {
      const currentPrice = this.generatePriceMovement(pair.basePrice, pair.volatility, now - this.startTime)
      const dayAgoPrice = pair.basePrice * (1 + (Math.random() - 0.5) * 0.05)
      const change = ((currentPrice - dayAgoPrice) / dayAgoPrice) * 100
      
      return {
        symbol: pair.symbol,
        name: pair.name,
        price: Math.max(currentPrice, pair.basePrice * 0.8),
        change: parseFloat(change.toFixed(2)),
        volume: Math.random() * 10000000 + 1000000,
        high24h: currentPrice * (1 + Math.random() * 0.05),
        low24h: currentPrice * (1 - Math.random() * 0.05),
        marketCap: currentPrice * (Math.random() * 1000000000 + 100000000)
      }
    })
  }
  
  // Get portfolio data with current values
  getPortfolioData() {
    const marketData = this.getMarketData()
    const marketPrices = new Map(marketData.map(item => [item.symbol, item.price]))
    
    let totalValue = 0
    let totalPnL = 0
    
    const positions = this.portfolioPositions.map(position => {
      const currentPrice = marketPrices.get(position.symbol) || position.entryPrice
      const value = position.amount * currentPrice
      const entryValue = position.amount * position.entryPrice
      const pnl = value - entryValue
      const change = ((currentPrice - position.entryPrice) / position.entryPrice) * 100
      
      totalValue += value
      totalPnL += pnl
      
      return {
        ...position,
        currentPrice: parseFloat(currentPrice.toFixed(2)),
        value: parseFloat(value.toFixed(2)),
        pnl: parseFloat(pnl.toFixed(2)),
        change: parseFloat(change.toFixed(2))
      }
    })
    
    // Add some cash balance
    const cashBalance = 15420.75
    totalValue += cashBalance
    
    const dailyChangePercent = (totalPnL / (totalValue - totalPnL)) * 100
    
    return {
      totalValue: parseFloat(totalValue.toFixed(2)),
      dailyChange: parseFloat(totalPnL.toFixed(2)),
      dailyChangePercent: parseFloat(dailyChangePercent.toFixed(2)),
      positions,
      cashBalance,
      totalPnL: parseFloat(totalPnL.toFixed(2))
    }
  }
  
  // Get trading chart data
  getChartData(symbol = 'BTC/USD', timeframe = '1H') {
    const history = this.priceHistory.get(symbol) || []
    const now = Date.now()
    
    // Filter based on timeframe
    let filteredHistory = history
    switch (timeframe) {
      case '1M':
        filteredHistory = history.slice(-60) // Last hour in 1-minute intervals
        break
      case '5M':
        filteredHistory = history.slice(-72) // Last 6 hours in 5-minute intervals
        break
      case '15M':
        filteredHistory = history.slice(-96) // Last day in 15-minute intervals
        break
      case '1H':
        filteredHistory = history.slice(-24) // Last day in 1-hour intervals
        break
      case '4H':
        filteredHistory = history.slice(-42) // Last week in 4-hour intervals
        break
      case '1D':
        filteredHistory = history.slice(-30) // Last month in 1-day intervals
        break
    }
    
    return {
      labels: filteredHistory.map(item => new Date(item.timestamp).toLocaleTimeString()),
      datasets: [{
        label: symbol,
        data: filteredHistory.map(item => item.price),
        borderColor: '#3B82F6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
        tension: 0.4
      }]
    }
  }
  
  // Get recent trades
  getRecentTrades(limit = 10) {
    return this.tradeHistory.slice(0, limit)
  }
  
  // Get trading statistics
  getTradingStats() {
    const trades = this.tradeHistory
    const winningTrades = trades.filter(t => t.pnl > 0)
    const totalVolume = trades.reduce((sum, t) => sum + t.total, 0)
    const totalPnL = trades.reduce((sum, t) => sum + t.pnl, 0)
    
    return {
      totalTrades: trades.length,
      winningTrades: winningTrades.length,
      winRate: (winningTrades.length / trades.length) * 100,
      totalVolume,
      totalPnL,
      avgTradeSize: totalVolume / trades.length,
      bestTrade: Math.max(...trades.map(t => t.pnl)),
      worstTrade: Math.min(...trades.map(t => t.pnl))
    }
  }
  
  // Simulate placing a new trade
  placeTrade(orderData) {
    const { symbol, side, amount, orderType, price } = orderData
    const pair = this.tradingPairs.find(p => p.symbol === symbol)
    if (!pair) return { success: false, error: 'Invalid trading pair' }
    
    const marketData = this.getMarketData()
    const currentPrice = marketData.find(m => m.symbol === symbol)?.price || pair.basePrice
    const executionPrice = orderType === 'market' ? currentPrice : price
    const total = amount * executionPrice
    const fee = total * 0.001
    
    const newTrade = {
      id: this.tradeHistory.length + 1,
      symbol,
      side,
      amount: parseFloat(amount),
      price: parseFloat(executionPrice.toFixed(2)),
      total: parseFloat(total.toFixed(2)),
      fee: parseFloat(fee.toFixed(2)),
      time: new Date().toISOString(),
      status: 'completed',
      pnl: 0, // Will be calculated later
      strategy: 'Manual'
    }
    
    this.tradeHistory.unshift(newTrade)
    
    // Update portfolio positions
    const existingPosition = this.portfolioPositions.find(p => p.symbol === symbol)
    if (existingPosition) {
      if (side === 'buy') {
        const totalAmount = existingPosition.amount + amount
        const totalValue = (existingPosition.amount * existingPosition.entryPrice) + (amount * executionPrice)
        existingPosition.entryPrice = totalValue / totalAmount
        existingPosition.amount = totalAmount
      } else {
        existingPosition.amount = Math.max(0, existingPosition.amount - amount)
      }
    } else if (side === 'buy') {
      this.portfolioPositions.push({
        symbol,
        amount,
        entryPrice: executionPrice
      })
    }
    
    return { success: true, trade: newTrade }
  }
  
  // Start real-time updates
  startRealTimeUpdates() {
    setInterval(() => {
      const now = Date.now()
      
      // Update price history for all pairs
      this.tradingPairs.forEach(pair => {
        const history = this.priceHistory.get(pair.symbol)
        if (history) {
          const newPrice = this.generatePriceMovement(pair.basePrice, pair.volatility, now - this.startTime)
          history.push({
            timestamp: now,
            price: Math.max(newPrice, pair.basePrice * 0.8),
            volume: Math.random() * 1000000 + 500000
          })
          
          // Keep only last 24 hours of data
          if (history.length > 288) { // 24 hours * 12 (5-minute intervals)
            history.shift()
          }
        }
      })
      
      // Occasionally add new trades
      if (Math.random() < 0.1) { // 10% chance every update
        this.generateRandomTrade()
      }
    }, 5000) // Update every 5 seconds
  }
  
  generateRandomTrade() {
    const pair = this.tradingPairs[Math.floor(Math.random() * this.tradingPairs.length)]
    const side = Math.random() > 0.5 ? 'buy' : 'sell'
    const amount = this.generateTradeAmount(pair.symbol)
    const marketData = this.getMarketData()
    const price = marketData.find(m => m.symbol === pair.symbol)?.price || pair.basePrice
    
    const orderData = {
      symbol: pair.symbol,
      side,
      amount,
      orderType: 'market',
      price
    }
    
    this.placeTrade(orderData)
  }
  
  // Get bot performance metrics
  getBotMetrics() {
    const stats = this.getTradingStats()
    const portfolio = this.getPortfolioData()
    
    return {
      status: 'active',
      uptime: Math.floor((Date.now() - this.startTime) / 1000),
      totalTrades: stats.totalTrades,
      winRate: stats.winRate,
      totalPnL: stats.totalPnL,
      portfolioValue: portfolio.totalValue,
      dailyReturn: portfolio.dailyChangePercent,
      activeStrategies: ['Scalping', 'EMA Crossover'],
      riskLevel: 'Medium',
      maxDrawdown: -5.2
    }
  }
  
  // Demo mode indicator
  isDemoMode() {
    return this.isDemo
  }
  
  // Get demo banner message
  getDemoBannerMessage() {
    return {
      title: 'Demo Mode Active',
      message: 'You are viewing simulated trading data. Connect your exchange API to start live trading.',
      type: 'info'
    }
  }
}

// Export singleton instance
export default new DemoDataService()