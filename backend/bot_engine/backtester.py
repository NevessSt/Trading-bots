import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from utils.logger import logger
from .strategies.strategy_factory import StrategyFactory
import ccxt

class Backtester:
    """Backtesting engine for trading strategies"""
    
    def __init__(self, exchange_id='binance'):
        """Initialize the backtester
        
        Args:
            exchange_id (str): Exchange identifier for CCXT
        """
        self.exchange_id = exchange_id
        self.exchange = getattr(ccxt, exchange_id)({
            'sandbox': True,  # Use sandbox mode for backtesting
            'enableRateLimit': True,
        })
    
    def fetch_historical_data(self, symbol, timeframe='1h', since=None, limit=1000):
        """Fetch historical OHLCV data
        
        Args:
            symbol (str): Trading symbol (e.g., 'BTC/USDT')
            timeframe (str): Timeframe (e.g., '1m', '5m', '1h', '1d')
            since (int, optional): Timestamp in milliseconds
            limit (int): Number of candles to fetch
            
        Returns:
            pd.DataFrame: Historical data with OHLCV columns
        """
        try:
            if since is None:
                # Default to 30 days ago
                since = int((datetime.now() - timedelta(days=30)).timestamp() * 1000)
            
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, since, limit)
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            logger.info(f"Fetched {len(df)} candles for {symbol} ({timeframe})")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def run_backtest(self, strategy_name, symbol, timeframe='1h', start_date=None, end_date=None, 
                    initial_balance=10000, trade_amount=100, take_profit=2.0, stop_loss=1.0):
        """Run a backtest for a given strategy
        
        Args:
            strategy_name (str): Name of the strategy to test
            symbol (str): Trading symbol
            timeframe (str): Timeframe for analysis
            start_date (datetime, optional): Start date for backtest
            end_date (datetime, optional): End date for backtest
            initial_balance (float): Starting balance
            trade_amount (float): Amount per trade
            take_profit (float): Take profit percentage
            stop_loss (float): Stop loss percentage
            
        Returns:
            dict: Backtest results with performance metrics
        """
        try:
            # Set default dates if not provided
            if end_date is None:
                end_date = datetime.now()
            if start_date is None:
                start_date = end_date - timedelta(days=30)
            
            # Fetch historical data
            since = int(start_date.timestamp() * 1000)
            df = self.fetch_historical_data(symbol, timeframe, since, 2000)
            
            if df.empty:
                return {'error': 'No historical data available'}
            
            # Filter data by date range
            df = df[(df.index >= start_date) & (df.index <= end_date)]
            
            if len(df) < 50:  # Need minimum data for strategy
                return {'error': 'Insufficient historical data for backtesting'}
            
            # Initialize strategy
            strategy = StrategyFactory.create_strategy(strategy_name)
            if not strategy:
                return {'error': f'Strategy {strategy_name} not found'}
            
            # Initialize backtest variables
            balance = initial_balance
            position = None
            trades = []
            equity_curve = []
            
            logger.info(f"Starting backtest: {strategy_name} on {symbol} from {start_date} to {end_date}")
            
            # Run backtest
            for i in range(50, len(df)):  # Start after enough data for indicators
                current_data = df.iloc[:i+1]
                current_price = current_data['close'].iloc[-1]
                current_time = current_data.index[-1]
                
                # Check for position exit signals first
                if position:
                    exit_signal = self._check_exit_conditions(position, current_price, take_profit, stop_loss)
                    if exit_signal:
                        # Close position
                        pnl = self._calculate_pnl(position, current_price)
                        balance += pnl
                        
                        trades.append({
                            'entry_time': position['entry_time'],
                            'exit_time': current_time,
                            'side': position['side'],
                            'entry_price': position['entry_price'],
                            'exit_price': current_price,
                            'quantity': position['quantity'],
                            'pnl': pnl,
                            'exit_reason': exit_signal
                        })
                        
                        position = None
                        logger.debug(f"Position closed: {exit_signal} at {current_price}, PnL: {pnl:.2f}")
                
                # Check for new entry signals if no position
                if not position:
                    signal = strategy.generate_signal(current_data)
                    
                    if signal and signal != 'hold':
                        # Check if we have enough balance
                        if balance >= trade_amount:
                            quantity = trade_amount / current_price
                            
                            position = {
                                'side': signal,
                                'entry_price': current_price,
                                'entry_time': current_time,
                                'quantity': quantity,
                                'amount': trade_amount
                            }
                            
                            balance -= trade_amount
                            logger.debug(f"Position opened: {signal} at {current_price}")
                
                # Record equity curve
                current_equity = balance
                if position:
                    current_equity += self._calculate_pnl(position, current_price) + position['amount']
                
                equity_curve.append({
                    'timestamp': current_time,
                    'equity': current_equity
                })
            
            # Close any remaining position
            if position:
                final_price = df['close'].iloc[-1]
                pnl = self._calculate_pnl(position, final_price)
                balance += pnl
                
                trades.append({
                    'entry_time': position['entry_time'],
                    'exit_time': df.index[-1],
                    'side': position['side'],
                    'entry_price': position['entry_price'],
                    'exit_price': final_price,
                    'quantity': position['quantity'],
                    'pnl': pnl,
                    'exit_reason': 'backtest_end'
                })
            
            # Calculate performance metrics
            results = self._calculate_performance_metrics(trades, initial_balance, balance, equity_curve)
            results['trades'] = trades
            results['equity_curve'] = equity_curve
            
            logger.info(f"Backtest completed: {len(trades)} trades, Final balance: ${balance:.2f}")
            return results
            
        except Exception as e:
            logger.error(f"Error running backtest: {str(e)}")
            return {'error': str(e)}
    
    def _check_exit_conditions(self, position, current_price, take_profit_pct, stop_loss_pct):
        """Check if position should be closed
        
        Args:
            position (dict): Current position
            current_price (float): Current market price
            take_profit_pct (float): Take profit percentage
            stop_loss_pct (float): Stop loss percentage
            
        Returns:
            str: Exit reason or None
        """
        entry_price = position['entry_price']
        side = position['side']
        
        if side == 'buy':
            # Long position
            take_profit_price = entry_price * (1 + take_profit_pct / 100)
            stop_loss_price = entry_price * (1 - stop_loss_pct / 100)
            
            if current_price >= take_profit_price:
                return 'take_profit'
            elif current_price <= stop_loss_price:
                return 'stop_loss'
        
        elif side == 'sell':
            # Short position
            take_profit_price = entry_price * (1 - take_profit_pct / 100)
            stop_loss_price = entry_price * (1 + stop_loss_pct / 100)
            
            if current_price <= take_profit_price:
                return 'take_profit'
            elif current_price >= stop_loss_price:
                return 'stop_loss'
        
        return None
    
    def _calculate_pnl(self, position, current_price):
        """Calculate profit/loss for a position
        
        Args:
            position (dict): Position details
            current_price (float): Current market price
            
        Returns:
            float: Profit/loss amount
        """
        entry_price = position['entry_price']
        quantity = position['quantity']
        side = position['side']
        
        if side == 'buy':
            return (current_price - entry_price) * quantity
        elif side == 'sell':
            return (entry_price - current_price) * quantity
        
        return 0
    
    def _calculate_performance_metrics(self, trades, initial_balance, final_balance, equity_curve):
        """Calculate performance metrics from trades
        
        Args:
            trades (list): List of completed trades
            initial_balance (float): Starting balance
            final_balance (float): Ending balance
            equity_curve (list): Equity curve data
            
        Returns:
            dict: Performance metrics
        """
        if not trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_return': 0,
                'total_return_pct': 0,
                'max_drawdown': 0,
                'sharpe_ratio': 0,
                'profit_factor': 0
            }
        
        # Basic metrics
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t['pnl'] > 0])
        losing_trades = len([t for t in trades if t['pnl'] < 0])
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        
        # Return metrics
        total_return = final_balance - initial_balance
        total_return_pct = (total_return / initial_balance) * 100
        
        # PnL analysis
        pnls = [t['pnl'] for t in trades]
        gross_profit = sum([pnl for pnl in pnls if pnl > 0])
        gross_loss = abs(sum([pnl for pnl in pnls if pnl < 0]))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Drawdown calculation
        max_drawdown = self._calculate_max_drawdown(equity_curve)
        
        # Sharpe ratio (simplified)
        if len(pnls) > 1:
            returns = np.array(pnls) / initial_balance
            sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
        else:
            sharpe_ratio = 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': round(win_rate, 2),
            'total_return': round(total_return, 2),
            'total_return_pct': round(total_return_pct, 2),
            'gross_profit': round(gross_profit, 2),
            'gross_loss': round(gross_loss, 2),
            'profit_factor': round(profit_factor, 2),
            'max_drawdown': round(max_drawdown, 2),
            'sharpe_ratio': round(sharpe_ratio, 2),
            'average_win': round(gross_profit / winning_trades, 2) if winning_trades > 0 else 0,
            'average_loss': round(gross_loss / losing_trades, 2) if losing_trades > 0 else 0,
            'initial_balance': initial_balance,
            'final_balance': round(final_balance, 2)
        }
    
    def _calculate_max_drawdown(self, equity_curve):
        """Calculate maximum drawdown from equity curve
        
        Args:
            equity_curve (list): List of equity values over time
            
        Returns:
            float: Maximum drawdown percentage
        """
        if not equity_curve:
            return 0
        
        equity_values = [point['equity'] for point in equity_curve]
        peak = equity_values[0]
        max_drawdown = 0
        
        for equity in equity_values:
            if equity > peak:
                peak = equity
            
            drawdown = (peak - equity) / peak * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        return max_drawdown
    
    def compare_strategies(self, strategies, symbol, timeframe='1h', start_date=None, end_date=None, 
                         initial_balance=10000, trade_amount=100):
        """Compare multiple strategies
        
        Args:
            strategies (list): List of strategy names to compare
            symbol (str): Trading symbol
            timeframe (str): Timeframe for analysis
            start_date (datetime, optional): Start date
            end_date (datetime, optional): End date
            initial_balance (float): Starting balance
            trade_amount (float): Amount per trade
            
        Returns:
            dict: Comparison results for all strategies
        """
        results = {}
        
        for strategy_name in strategies:
            logger.info(f"Running backtest for strategy: {strategy_name}")
            result = self.run_backtest(
                strategy_name, symbol, timeframe, start_date, end_date,
                initial_balance, trade_amount
            )
            results[strategy_name] = result
        
        return results