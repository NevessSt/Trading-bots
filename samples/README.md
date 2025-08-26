# Sample Data and Screenshots

This directory contains sample data and screenshots for demonstration purposes. These files showcase the capabilities and user interface of the TradingBot Pro platform.

## Directory Structure

```
samples/
├── backtests/          # Sample backtest results and visualizations
│   ├── sma_crossover_backtest.csv
│   ├── rsi_strategy_backtest.csv
│   ├── sma_crossover_performance.svg
│   └── rsi_strategy_performance.svg
├── live/               # Live trading interface screenshots
│   ├── dashboard_screenshot.svg
│   ├── bot_management_screenshot.svg
│   └── trading_interface_screenshot.svg
└── README.md           # This file
```

## Backtest Samples

### CSV Files

#### `sma_crossover_backtest.csv`
Sample backtest results for a Simple Moving Average (SMA) crossover strategy on BTC/USDT:
- **Strategy**: 20/50 SMA Crossover
- **Period**: 2023-01-01 to 2023-12-31
- **Initial Capital**: $10,000
- **Final Value**: $12,450
- **Total Return**: 24.5%
- **Max Drawdown**: -8.2%
- **Sharpe Ratio**: 1.85

#### `rsi_strategy_backtest.csv`
Sample backtest results for an RSI-based trading strategy on ETH/USDT:
- **Strategy**: RSI Oversold/Overbought (30/70 levels)
- **Period**: 2023-01-01 to 2023-12-31
- **Initial Capital**: $10,000
- **Final Value**: $11,890
- **Total Return**: 18.9%
- **Max Drawdown**: -12.1%
- **Sharpe Ratio**: 1.42

### Performance Charts

#### `sma_crossover_performance.svg`
Visualization of the SMA crossover strategy performance showing:
- Portfolio value over time
- Buy/sell signal markers
- Performance metrics summary
- Drawdown periods highlighted

#### `rsi_strategy_performance.svg`
Visualization of the RSI strategy performance showing:
- Portfolio value progression
- RSI overbought/oversold zones
- Entry/exit points
- Risk-adjusted returns

## Live Interface Screenshots

### `dashboard_screenshot.svg`
Main dashboard interface showing:
- Portfolio summary cards (Total Balance, Active Bots, Today's P&L, Success Rate)
- Performance chart with portfolio growth over time
- Active bots list with real-time status
- Recent trades table
- Quick action buttons

### `bot_management_screenshot.svg`
Bot management interface displaying:
- Grid view of all trading bots with status indicators
- Individual bot performance metrics
- Quick bot setup panel with strategy selection
- Risk level configuration options
- Portfolio summary with aggregated statistics

### `trading_interface_screenshot.svg`
Live trading interface featuring:
- Real-time price chart with technical indicators
- Order book with bid/ask levels
- Manual trading controls (Buy/Sell panels)
- Bot status monitoring
- Emergency stop functionality
- Portfolio holdings and recent orders

## Usage

These sample files can be used for:

1. **Documentation**: Include in README files and documentation to show platform capabilities
2. **Demonstrations**: Use during presentations or product demos
3. **Testing**: Load sample data for UI testing and development
4. **Marketing**: Showcase the platform's features and user interface
5. **Training**: Help new users understand the platform's functionality

## Data Format

The CSV files follow this structure:
- `Date`: Trading date (YYYY-MM-DD)
- `Portfolio_Value`: Total portfolio value in USD
- `Daily_Return`: Daily percentage return
- `Cumulative_Return`: Cumulative percentage return since start
- `Drawdown`: Current drawdown percentage
- `Trades`: Number of trades executed that day
- `Win_Rate`: Percentage of winning trades

## Screenshots Format

All screenshots are provided in SVG format for:
- **Scalability**: Vector graphics that look crisp at any size
- **Small file size**: Efficient storage and fast loading
- **Editability**: Can be modified with any vector graphics editor
- **Web compatibility**: Display perfectly in browsers and documentation

## Disclaimer

⚠️ **Important**: These are sample/demo files for illustration purposes only. They do not represent actual trading results or guarantee future performance. Past performance does not indicate future results.

## License

These sample files are provided under the same license as the main project. See the main README.md for license details.