#!/usr/bin/env python3
"""
Enhanced Backtesting Module
Comprehensive backtesting with historical data simulation, multiple timeframes, and advanced analytics
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Import our risk manager
from .risk_manager import AdvancedRiskManager, RiskParameters, PositionSide, Position

class TimeFrame(Enum):
    """Supported timeframes for backtesting"""
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"
    HOUR_1 = "1h"
    HOUR_4 = "4h"
    HOUR_12 = "12h"
    DAY_1 = "1d"
    WEEK_1 = "1w"
    MONTH_1 = "1M"

@dataclass
class BacktestConfig:
    """Configuration for backtesting"""
    start_date: datetime
    end_date: datetime
    initial_balance: float = 10000.0
    commission: float = 0.001  # 0.1% commission
    slippage: float = 0.0005   # 0.05% slippage
    timeframe: TimeFrame = TimeFrame.HOUR_1
    symbols: List[str] = field(default_factory=lambda: ["BTCUSDT"])
    risk_params: RiskParameters = field(default_factory=RiskParameters)
    max_lookback_periods: int = 100
    enable_compound_returns: bool = True
    benchmark_symbol: str = "BTCUSDT"  # For comparison

@dataclass
class Trade:
    """Individual trade record"""
    symbol: str
    side: str
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    pnl_percentage: float
    commission: float
    slippage: float
    reason: str  # stop_loss, take_profit, trailing_stop, signal
    duration: timedelta
    max_favorable_excursion: float = 0.0  # MFE
    max_adverse_excursion: float = 0.0    # MAE

@dataclass
class BacktestResults:
    """Comprehensive backtesting results"""
    config: BacktestConfig
    trades: List[Trade]
    equity_curve: pd.DataFrame
    performance_metrics: Dict[str, float]
    risk_metrics: Dict[str, float]
    monthly_returns: pd.DataFrame
    drawdown_analysis: Dict[str, Any]
    trade_analysis: Dict[str, Any]
    benchmark_comparison: Dict[str, float]
    execution_time: float
    total_bars: int

class TechnicalIndicators:
    """Technical indicators for backtesting strategies"""
    
    @staticmethod
    def sma(data: pd.Series, period: int) -> pd.Series:
        """Simple Moving Average"""
        return data.rolling(window=period).mean()
    
    @staticmethod
    def ema(data: pd.Series, period: int) -> pd.Series:
        """Exponential Moving Average"""
        return data.ewm(span=period).mean()
    
    @staticmethod
    def rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """Relative Strength Index"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def bollinger_bands(data: pd.Series, period: int = 20, std_dev: float = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Bollinger Bands"""
        sma = data.rolling(window=period).mean()
        std = data.rolling(window=period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        return upper, sma, lower
    
    @staticmethod
    def macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """MACD Indicator"""
        ema_fast = data.ewm(span=fast).mean()
        ema_slow = data.ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Average True Range"""
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return true_range.rolling(window=period).mean()

class EnhancedBacktester:
    """Enhanced backtesting engine with advanced analytics"""
    
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.risk_manager = AdvancedRiskManager(config.risk_params)
        self.indicators = TechnicalIndicators()
        
        # Backtesting state
        self.current_balance = config.initial_balance
        self.equity_curve = []
        self.trades = []
        self.current_positions = {}
        self.daily_returns = []
        self.benchmark_returns = []
        
    def load_historical_data(self, symbol: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Load historical market data for backtesting
        
        Args:
            symbol: Trading symbol
            start_date: Start date for data
            end_date: End date for data
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            # In a real implementation, this would fetch from exchange API or database
            # For demo purposes, we'll generate synthetic data
            
            date_range = pd.date_range(start=start_date, end=end_date, freq='1H')
            np.random.seed(42)  # For reproducible results
            
            # Generate realistic price data with trend and volatility
            base_price = 50000 if 'BTC' in symbol else 3000
            returns = np.random.normal(0.0001, 0.02, len(date_range))  # Small positive drift with volatility
            
            prices = [base_price]
            for ret in returns[1:]:
                prices.append(prices[-1] * (1 + ret))
            
            # Create OHLCV data
            data = pd.DataFrame({
                'timestamp': date_range,
                'open': prices,
                'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
                'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
                'close': prices,
                'volume': np.random.uniform(1000, 10000, len(date_range))
            })
            
            # Ensure high >= close >= low and high >= open >= low
            data['high'] = data[['open', 'close', 'high']].max(axis=1)
            data['low'] = data[['open', 'close', 'low']].min(axis=1)
            
            data.set_index('timestamp', inplace=True)
            
            self.logger.info(f"Loaded {len(data)} bars for {symbol}")
            return data
            
        except Exception as e:
            self.logger.error(f"Error loading historical data: {e}")
            return pd.DataFrame()
    
    def add_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Add technical indicators to the dataset
        
        Args:
            data: OHLCV DataFrame
            
        Returns:
            DataFrame with technical indicators
        """
        try:
            df = data.copy()
            
            # Moving averages
            df['sma_20'] = self.indicators.sma(df['close'], 20)
            df['sma_50'] = self.indicators.sma(df['close'], 50)
            df['ema_12'] = self.indicators.ema(df['close'], 12)
            df['ema_26'] = self.indicators.ema(df['close'], 26)
            
            # RSI
            df['rsi'] = self.indicators.rsi(df['close'])
            
            # Bollinger Bands
            df['bb_upper'], df['bb_middle'], df['bb_lower'] = self.indicators.bollinger_bands(df['close'])
            
            # MACD
            df['macd'], df['macd_signal'], df['macd_histogram'] = self.indicators.macd(df['close'])
            
            # ATR
            df['atr'] = self.indicators.atr(df['high'], df['low'], df['close'])
            
            # Price position within Bollinger Bands
            df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
            
            # Volatility
            df['volatility'] = df['close'].pct_change().rolling(20).std() * np.sqrt(24)  # Annualized
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error adding technical indicators: {e}")
            return data
    
    def example_strategy(self, data: pd.DataFrame, current_idx: int) -> Tuple[Optional[str], Optional[PositionSide]]:
        """
        Example trading strategy for demonstration
        
        Args:
            data: DataFrame with market data and indicators
            current_idx: Current bar index
            
        Returns:
            Tuple of (signal, position_side) or (None, None)
        """
        try:
            if current_idx < 50:  # Need enough data for indicators
                return None, None
                
            current_bar = data.iloc[current_idx]
            prev_bar = data.iloc[current_idx - 1]
            
            # Example: RSI + Moving Average Crossover Strategy
            rsi = current_bar['rsi']
            sma_20 = current_bar['sma_20']
            sma_50 = current_bar['sma_50']
            close = current_bar['close']
            
            # Long signal: RSI oversold + price above SMA20 + SMA20 > SMA50
            if (rsi < 30 and 
                close > sma_20 and 
                sma_20 > sma_50 and 
                prev_bar['rsi'] >= 30):  # RSI just crossed below 30
                return "BUY", PositionSide.LONG
            
            # Short signal: RSI overbought + price below SMA20 + SMA20 < SMA50
            elif (rsi > 70 and 
                  close < sma_20 and 
                  sma_20 < sma_50 and 
                  prev_bar['rsi'] <= 70):  # RSI just crossed above 70
                return "SELL", PositionSide.SHORT
            
            return None, None
            
        except Exception as e:
            self.logger.error(f"Error in strategy: {e}")
            return None, None
    
    def execute_backtest(self, strategy_func: Callable = None) -> BacktestResults:
        """
        Execute the backtesting process
        
        Args:
            strategy_func: Custom strategy function (optional)
            
        Returns:
            BacktestResults object
        """
        start_time = datetime.now()
        
        try:
            self.logger.info("Starting enhanced backtesting...")
            
            # Use provided strategy or default example
            strategy = strategy_func or self.example_strategy
            
            # Load and prepare data for all symbols
            all_data = {}
            for symbol in self.config.symbols:
                data = self.load_historical_data(symbol, self.config.start_date, self.config.end_date)
                if not data.empty:
                    data = self.add_technical_indicators(data)
                    all_data[symbol] = data
            
            if not all_data:
                raise ValueError("No data loaded for backtesting")
            
            # Get the primary symbol for main loop
            primary_symbol = self.config.symbols[0]
            primary_data = all_data[primary_symbol]
            
            # Initialize tracking variables
            self.current_balance = self.config.initial_balance
            peak_balance = self.config.initial_balance
            max_drawdown = 0.0
            
            # Main backtesting loop
            for i in range(self.config.max_lookback_periods, len(primary_data)):
                current_time = primary_data.index[i]
                current_bar = primary_data.iloc[i]
                
                # Update positions with current prices
                for symbol in self.current_positions.keys():
                    if symbol in all_data:
                        current_price = all_data[symbol].iloc[i]['close']
                        
                        # Check if position should be closed
                        should_close, reason = self.risk_manager.should_close_position(symbol, current_price)
                        
                        if should_close:
                            self._close_position(symbol, current_price, current_time, reason)
                
                # Generate trading signals
                signal, side = strategy(primary_data, i)
                
                if signal and primary_symbol not in self.current_positions:
                    self._open_position(primary_symbol, side, current_bar['close'], current_time, all_data[primary_symbol].iloc[i])
                
                # Update equity curve
                total_equity = self._calculate_total_equity(all_data, i)
                self.equity_curve.append({
                    'timestamp': current_time,
                    'balance': self.current_balance,
                    'equity': total_equity,
                    'drawdown': (peak_balance - total_equity) / peak_balance if peak_balance > 0 else 0
                })
                
                # Update peak and drawdown
                if total_equity > peak_balance:
                    peak_balance = total_equity
                else:
                    current_drawdown = (peak_balance - total_equity) / peak_balance
                    max_drawdown = max(max_drawdown, current_drawdown)
            
            # Close any remaining positions
            for symbol in list(self.current_positions.keys()):
                final_price = all_data[symbol].iloc[-1]['close']
                self._close_position(symbol, final_price, primary_data.index[-1], "backtest_end")
            
            # Calculate results
            execution_time = (datetime.now() - start_time).total_seconds()
            results = self._calculate_results(execution_time, len(primary_data))
            
            self.logger.info(f"Backtesting completed in {execution_time:.2f} seconds")
            return results
            
        except Exception as e:
            self.logger.error(f"Error during backtesting: {e}")
            raise
    
    def _open_position(self, symbol: str, side: PositionSide, price: float, timestamp: datetime, bar_data: pd.Series):
        """
        Open a new position during backtesting
        """
        try:
            # Calculate position size
            stop_loss_price = self.risk_manager.set_stop_loss(symbol, price, side)
            position_size = self.risk_manager.calculate_position_size(
                symbol, price, stop_loss_price, self.current_balance
            )
            
            if position_size > 0:
                # Apply slippage
                slippage_factor = 1 + self.config.slippage if side == PositionSide.LONG else 1 - self.config.slippage
                actual_price = price * slippage_factor
                
                # Calculate commission
                position_value = position_size * actual_price
                commission = position_value * self.config.commission
                
                # Check if we have enough balance
                total_cost = position_value + commission
                if total_cost <= self.current_balance:
                    # Open position
                    success = self.risk_manager.open_position(symbol, side, actual_price, position_size)
                    
                    if success:
                        self.current_positions[symbol] = {
                            'entry_time': timestamp,
                            'entry_price': actual_price,
                            'quantity': position_size,
                            'side': side,
                            'commission': commission,
                            'max_favorable': 0.0,
                            'max_adverse': 0.0
                        }
                        
                        # Update balance
                        self.current_balance -= total_cost
                        
                        self.logger.debug(f"Opened {side.value} position: {symbol} @ {actual_price}")
                        
        except Exception as e:
            self.logger.error(f"Error opening position: {e}")
    
    def _close_position(self, symbol: str, price: float, timestamp: datetime, reason: str):
        """
        Close a position during backtesting
        """
        try:
            if symbol not in self.current_positions:
                return
                
            position = self.current_positions[symbol]
            
            # Apply slippage
            side = position['side']
            slippage_factor = 1 - self.config.slippage if side == PositionSide.LONG else 1 + self.config.slippage
            actual_price = price * slippage_factor
            
            # Calculate PnL
            pnl = self.risk_manager.close_position(symbol, actual_price, reason)
            
            if pnl is not None:
                # Calculate commission
                position_value = position['quantity'] * actual_price
                exit_commission = position_value * self.config.commission
                total_commission = position['commission'] + exit_commission
                
                # Net PnL after commissions
                net_pnl = pnl - total_commission
                
                # Update balance
                self.current_balance += position_value + net_pnl
                
                # Create trade record
                trade = Trade(
                    symbol=symbol,
                    side=side.value,
                    entry_time=position['entry_time'],
                    exit_time=timestamp,
                    entry_price=position['entry_price'],
                    exit_price=actual_price,
                    quantity=position['quantity'],
                    pnl=net_pnl,
                    pnl_percentage=(net_pnl / (position['quantity'] * position['entry_price'])) * 100,
                    commission=total_commission,
                    slippage=abs(price - actual_price) * position['quantity'],
                    reason=reason,
                    duration=timestamp - position['entry_time'],
                    max_favorable_excursion=position['max_favorable'],
                    max_adverse_excursion=position['max_adverse']
                )
                
                self.trades.append(trade)
                
                # Remove from current positions
                del self.current_positions[symbol]
                
                self.logger.debug(f"Closed {side.value} position: {symbol} @ {actual_price}, PnL: {net_pnl:.2f}")
                
        except Exception as e:
            self.logger.error(f"Error closing position: {e}")
    
    def _calculate_total_equity(self, all_data: Dict[str, pd.DataFrame], current_idx: int) -> float:
        """
        Calculate total equity including unrealized PnL
        """
        total_equity = self.current_balance
        
        for symbol, position in self.current_positions.items():
            if symbol in all_data and current_idx < len(all_data[symbol]):
                current_price = all_data[symbol].iloc[current_idx]['close']
                
                # Calculate unrealized PnL
                if position['side'] == PositionSide.LONG:
                    unrealized_pnl = (current_price - position['entry_price']) * position['quantity']
                else:
                    unrealized_pnl = (position['entry_price'] - current_price) * position['quantity']
                
                total_equity += unrealized_pnl
                
                # Update MFE and MAE
                if position['side'] == PositionSide.LONG:
                    favorable = (current_price - position['entry_price']) * position['quantity']
                    adverse = (position['entry_price'] - current_price) * position['quantity']
                else:
                    favorable = (position['entry_price'] - current_price) * position['quantity']
                    adverse = (current_price - position['entry_price']) * position['quantity']
                
                position['max_favorable'] = max(position['max_favorable'], favorable)
                position['max_adverse'] = max(position['max_adverse'], adverse)
        
        return total_equity
    
    def _calculate_results(self, execution_time: float, total_bars: int) -> BacktestResults:
        """
        Calculate comprehensive backtesting results
        """
        try:
            # Convert equity curve to DataFrame
            equity_df = pd.DataFrame(self.equity_curve)
            equity_df.set_index('timestamp', inplace=True)
            
            # Calculate returns
            equity_df['returns'] = equity_df['equity'].pct_change()
            equity_df['cumulative_returns'] = (1 + equity_df['returns']).cumprod() - 1
            
            # Performance metrics
            total_return = (equity_df['equity'].iloc[-1] / self.config.initial_balance) - 1
            annual_return = (1 + total_return) ** (365.25 / (self.config.end_date - self.config.start_date).days) - 1
            
            # Risk metrics
            returns = equity_df['returns'].dropna()
            volatility = returns.std() * np.sqrt(365.25 * 24)  # Annualized
            sharpe_ratio = (annual_return - 0.02) / volatility if volatility > 0 else 0  # Assuming 2% risk-free rate
            
            max_drawdown = equity_df['drawdown'].max()
            
            # Trade analysis
            winning_trades = [t for t in self.trades if t.pnl > 0]
            losing_trades = [t for t in self.trades if t.pnl < 0]
            
            win_rate = len(winning_trades) / len(self.trades) if self.trades else 0
            avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
            avg_loss = np.mean([t.pnl for t in losing_trades]) if losing_trades else 0
            profit_factor = abs(sum(t.pnl for t in winning_trades) / sum(t.pnl for t in losing_trades)) if losing_trades else float('inf')
            
            # Monthly returns
            monthly_returns = equity_df['returns'].resample('M').apply(lambda x: (1 + x).prod() - 1)
            
            performance_metrics = {
                'total_return': total_return,
                'annual_return': annual_return,
                'volatility': volatility,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'calmar_ratio': annual_return / max_drawdown if max_drawdown > 0 else 0,
                'win_rate': win_rate,
                'profit_factor': profit_factor,
                'total_trades': len(self.trades),
                'avg_trade_duration': np.mean([t.duration.total_seconds() / 3600 for t in self.trades]) if self.trades else 0
            }
            
            risk_metrics = {
                'var_95': np.percentile(returns, 5) if len(returns) > 0 else 0,
                'cvar_95': returns[returns <= np.percentile(returns, 5)].mean() if len(returns) > 0 else 0,
                'max_consecutive_losses': self._calculate_max_consecutive_losses(),
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'largest_win': max([t.pnl for t in self.trades]) if self.trades else 0,
                'largest_loss': min([t.pnl for t in self.trades]) if self.trades else 0
            }
            
            # Drawdown analysis
            drawdown_analysis = self._analyze_drawdowns(equity_df)
            
            # Trade analysis
            trade_analysis = {
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'avg_win_percentage': np.mean([t.pnl_percentage for t in winning_trades]) if winning_trades else 0,
                'avg_loss_percentage': np.mean([t.pnl_percentage for t in losing_trades]) if losing_trades else 0,
                'best_trade': max(self.trades, key=lambda x: x.pnl) if self.trades else None,
                'worst_trade': min(self.trades, key=lambda x: x.pnl) if self.trades else None
            }
            
            return BacktestResults(
                config=self.config,
                trades=self.trades,
                equity_curve=equity_df,
                performance_metrics=performance_metrics,
                risk_metrics=risk_metrics,
                monthly_returns=monthly_returns.to_frame('returns'),
                drawdown_analysis=drawdown_analysis,
                trade_analysis=trade_analysis,
                benchmark_comparison={},  # TODO: Implement benchmark comparison
                execution_time=execution_time,
                total_bars=total_bars
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating results: {e}")
            raise
    
    def _calculate_max_consecutive_losses(self) -> int:
        """Calculate maximum consecutive losing trades"""
        if not self.trades:
            return 0
            
        max_consecutive = 0
        current_consecutive = 0
        
        for trade in self.trades:
            if trade.pnl < 0:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
                
        return max_consecutive
    
    def _analyze_drawdowns(self, equity_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze drawdown periods"""
        try:
            drawdowns = equity_df['drawdown']
            
            # Find drawdown periods
            in_drawdown = drawdowns > 0
            drawdown_starts = in_drawdown & ~in_drawdown.shift(1, fill_value=False)
            drawdown_ends = ~in_drawdown & in_drawdown.shift(1, fill_value=False)
            
            periods = []
            start_idx = None
            
            for i, (start, end) in enumerate(zip(drawdown_starts, drawdown_ends)):
                if start:
                    start_idx = i
                elif end and start_idx is not None:
                    period_drawdowns = drawdowns.iloc[start_idx:i+1]
                    periods.append({
                        'start': equity_df.index[start_idx],
                        'end': equity_df.index[i],
                        'duration': equity_df.index[i] - equity_df.index[start_idx],
                        'max_drawdown': period_drawdowns.max(),
                        'recovery_time': None  # TODO: Calculate recovery time
                    })
                    start_idx = None
            
            return {
                'max_drawdown': drawdowns.max(),
                'avg_drawdown': drawdowns[drawdowns > 0].mean() if (drawdowns > 0).any() else 0,
                'drawdown_periods': len(periods),
                'longest_drawdown': max([p['duration'] for p in periods]) if periods else timedelta(0),
                'periods': periods
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing drawdowns: {e}")
            return {}
    
    def generate_report(self, results: BacktestResults, output_dir: str = "backtest_reports") -> str:
        """
        Generate comprehensive backtesting report
        
        Args:
            results: BacktestResults object
            output_dir: Output directory for reports
            
        Returns:
            Path to generated report
        """
        try:
            # Create output directory
            Path(output_dir).mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = f"{output_dir}/backtest_report_{timestamp}.html"
            
            # Generate HTML report
            html_content = self._generate_html_report(results)
            
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Generate charts
            self._generate_charts(results, output_dir, timestamp)
            
            self.logger.info(f"Backtest report generated: {report_file}")
            return report_file
            
        except Exception as e:
            self.logger.error(f"Error generating report: {e}")
            return ""
    
    def _generate_html_report(self, results: BacktestResults) -> str:
        """
        Generate HTML report content
        """
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Enhanced Backtesting Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
                .metric-card {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; border-left: 4px solid #007bff; }}
                .metric-value {{ font-size: 24px; font-weight: bold; color: #007bff; }}
                .metric-label {{ color: #666; margin-top: 5px; }}
                .section {{ margin: 30px 0; }}
                .trade-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                .trade-table th, .trade-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                .trade-table th {{ background-color: #f2f2f2; }}
                .positive {{ color: green; }}
                .negative {{ color: red; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Enhanced Backtesting Report</h1>
                <p><strong>Period:</strong> {results.config.start_date.strftime('%Y-%m-%d')} to {results.config.end_date.strftime('%Y-%m-%d')}</p>
                <p><strong>Initial Balance:</strong> ${results.config.initial_balance:,.2f}</p>
                <p><strong>Symbols:</strong> {', '.join(results.config.symbols)}</p>
                <p><strong>Execution Time:</strong> {results.execution_time:.2f} seconds</p>
            </div>
            
            <div class="section">
                <h2>Performance Metrics</h2>
                <div class="metrics">
        """
        
        # Add performance metrics
        for key, value in results.performance_metrics.items():
            if isinstance(value, float):
                if 'return' in key or 'ratio' in key:
                    formatted_value = f"{value:.2%}" if 'return' in key else f"{value:.2f}"
                else:
                    formatted_value = f"{value:.2f}"
            else:
                formatted_value = str(value)
                
            html += f"""
                    <div class="metric-card">
                        <div class="metric-value">{formatted_value}</div>
                        <div class="metric-label">{key.replace('_', ' ').title()}</div>
                    </div>
            """
        
        html += """
                </div>
            </div>
            
            <div class="section">
                <h2>Risk Metrics</h2>
                <div class="metrics">
        """
        
        # Add risk metrics
        for key, value in results.risk_metrics.items():
            if isinstance(value, float):
                formatted_value = f"{value:.2f}"
            else:
                formatted_value = str(value)
                
            html += f"""
                    <div class="metric-card">
                        <div class="metric-value">{formatted_value}</div>
                        <div class="metric-label">{key.replace('_', ' ').title()}</div>
                    </div>
            """
        
        # Add trade summary
        html += f"""
                </div>
            </div>
            
            <div class="section">
                <h2>Trade Summary</h2>
                <table class="trade-table">
                    <thead>
                        <tr>
                            <th>Symbol</th>
                            <th>Side</th>
                            <th>Entry Time</th>
                            <th>Exit Time</th>
                            <th>Entry Price</th>
                            <th>Exit Price</th>
                            <th>Quantity</th>
                            <th>PnL</th>
                            <th>PnL %</th>
                            <th>Duration</th>
                            <th>Reason</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        # Add recent trades (last 20)
        recent_trades = results.trades[-20:] if len(results.trades) > 20 else results.trades
        for trade in recent_trades:
            pnl_class = "positive" if trade.pnl > 0 else "negative"
            html += f"""
                        <tr>
                            <td>{trade.symbol}</td>
                            <td>{trade.side}</td>
                            <td>{trade.entry_time.strftime('%Y-%m-%d %H:%M')}</td>
                            <td>{trade.exit_time.strftime('%Y-%m-%d %H:%M')}</td>
                            <td>${trade.entry_price:.2f}</td>
                            <td>${trade.exit_price:.2f}</td>
                            <td>{trade.quantity:.6f}</td>
                            <td class="{pnl_class}">${trade.pnl:.2f}</td>
                            <td class="{pnl_class}">{trade.pnl_percentage:.2f}%</td>
                            <td>{str(trade.duration).split('.')[0]}</td>
                            <td>{trade.reason}</td>
                        </tr>
            """
        
        html += """
                    </tbody>
                </table>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_charts(self, results: BacktestResults, output_dir: str, timestamp: str):
        """
        Generate performance charts
        """
        try:
            plt.style.use('seaborn-v0_8')
            
            # Equity curve chart
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
            
            # Equity curve
            ax1.plot(results.equity_curve.index, results.equity_curve['equity'])
            ax1.set_title('Equity Curve')
            ax1.set_ylabel('Portfolio Value ($)')
            ax1.grid(True)
            
            # Drawdown
            ax2.fill_between(results.equity_curve.index, 0, -results.equity_curve['drawdown'] * 100, alpha=0.7, color='red')
            ax2.set_title('Drawdown')
            ax2.set_ylabel('Drawdown (%)')
            ax2.grid(True)
            
            # Monthly returns
            monthly_returns = results.monthly_returns['returns'] * 100
            colors = ['green' if x > 0 else 'red' for x in monthly_returns]
            ax3.bar(range(len(monthly_returns)), monthly_returns, color=colors)
            ax3.set_title('Monthly Returns')
            ax3.set_ylabel('Return (%)')
            ax3.set_xticks(range(len(monthly_returns)))
            ax3.set_xticklabels([d.strftime('%Y-%m') for d in monthly_returns.index], rotation=45)
            ax3.grid(True)
            
            # PnL distribution
            pnl_values = [trade.pnl for trade in results.trades]
            if pnl_values:
                ax4.hist(pnl_values, bins=20, alpha=0.7, edgecolor='black')
                ax4.axvline(x=0, color='red', linestyle='--', alpha=0.7)
                ax4.set_title('PnL Distribution')
                ax4.set_xlabel('PnL ($)')
                ax4.set_ylabel('Frequency')
                ax4.grid(True)
            
            plt.tight_layout()
            plt.savefig(f"{output_dir}/backtest_charts_{timestamp}.png", dpi=300, bbox_inches='tight')
            plt.close()
            
        except Exception as e:
            self.logger.error(f"Error generating charts: {e}")

# Example usage
if __name__ == "__main__":
    # Configure backtesting
    config = BacktestConfig(
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 12, 31),
        initial_balance=10000.0,
        symbols=["BTCUSDT"],
        commission=0.001,
        slippage=0.0005
    )
    
    # Run backtest
    backtester = EnhancedBacktester(config)
    results = backtester.execute_backtest()
    
    # Generate report
    report_path = backtester.generate_report(results)
    print(f"Backtest completed. Report saved to: {report_path}")
    
    # Print summary
    print(f"\nBacktest Summary:")
    print(f"Total Return: {results.performance_metrics['total_return']:.2%}")
    print(f"Sharpe Ratio: {results.performance_metrics['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {results.performance_metrics['max_drawdown']:.2%}")
    print(f"Win Rate: {results.performance_metrics['win_rate']:.2%}")
    print(f"Total Trades: {results.performance_metrics['total_trades']}")