import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json
import matplotlib.pyplot as plt
import seaborn as sns
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
warnings.filterwarnings('ignore')

@dataclass
class BacktestTrade:
    """Individual trade in backtest"""
    entry_time: datetime
    exit_time: datetime
    symbol: str
    side: str  # 'long' or 'short'
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    pnl_pct: float
    commission: float
    slippage: float
    strategy: str
    reason: str  # exit reason
    duration: timedelta
    max_favorable_excursion: float  # MFE
    max_adverse_excursion: float    # MAE

@dataclass
class BacktestResults:
    """Comprehensive backtest results"""
    # Basic metrics
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_return: float
    annualized_return: float
    
    # Trade statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    
    # Risk metrics
    max_drawdown: float
    max_drawdown_duration: int
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    var_95: float
    
    # Advanced metrics
    expectancy: float
    kelly_criterion: float
    recovery_factor: float
    payoff_ratio: float
    
    # Detailed data
    trades: List[BacktestTrade]
    equity_curve: pd.DataFrame
    drawdown_curve: pd.DataFrame
    monthly_returns: pd.DataFrame
    
class BacktestingEngine:
    """Advanced backtesting engine with realistic market simulation"""
    
    def __init__(self,
                 initial_capital: float = 10000,
                 commission_rate: float = 0.001,  # 0.1% commission
                 slippage_rate: float = 0.0005,   # 0.05% slippage
                 min_trade_amount: float = 10,    # Minimum trade amount
                 max_positions: int = 10,         # Maximum concurrent positions
                 margin_requirement: float = 1.0, # Margin requirement (1.0 = no leverage)
                 interest_rate: float = 0.05):    # Annual interest rate for margin
        """
        Initialize backtesting engine
        
        Args:
            initial_capital: Starting capital
            commission_rate: Commission rate per trade
            slippage_rate: Slippage rate per trade
            min_trade_amount: Minimum trade amount
            max_positions: Maximum concurrent positions
            margin_requirement: Margin requirement (0.5 = 2x leverage)
            interest_rate: Annual interest rate for borrowed funds
        """
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        self.min_trade_amount = min_trade_amount
        self.max_positions = max_positions
        self.margin_requirement = margin_requirement
        self.interest_rate = interest_rate
        
        self.logger = logging.getLogger(__name__)
        
    def run_backtest(self, 
                    strategy,
                    data: pd.DataFrame,
                    start_date: Optional[datetime] = None,
                    end_date: Optional[datetime] = None,
                    symbols: Optional[List[str]] = None,
                    rebalance_frequency: str = 'daily') -> BacktestResults:
        """Run comprehensive backtest
        
        Args:
            strategy: Trading strategy instance
            data: Historical market data
            start_date: Backtest start date
            end_date: Backtest end date
            symbols: List of symbols to trade
            rebalance_frequency: Portfolio rebalancing frequency
            
        Returns:
            Comprehensive backtest results
        """
        # Prepare data
        if start_date:
            data = data[data.index >= start_date]
        if end_date:
            data = data[data.index <= end_date]
        
        if data.empty:
            raise ValueError("No data available for the specified date range")
        
        # Initialize backtest state
        portfolio = {
            'cash': self.initial_capital,
            'positions': {},
            'equity': self.initial_capital,
            'margin_used': 0.0
        }
        
        trades = []
        equity_curve = []
        drawdown_curve = []
        
        # Track performance
        peak_equity = self.initial_capital
        max_drawdown = 0.0
        max_dd_duration = 0
        current_dd_duration = 0
        
        self.logger.info(f"Starting backtest from {data.index[0]} to {data.index[-1]}")
        
        # Main backtest loop
        for current_time, row in data.iterrows():
            # Update portfolio with current prices
            self._update_portfolio_value(portfolio, row, current_time)
            
            # Generate trading signals
            signals_df = strategy.generate_signals(data.loc[:current_time].tail(100))  # Use last 100 bars
            
            if not signals_df.empty:
                latest_signals = signals_df.iloc[-1]
                
                # Process signals
                if latest_signals.get('signal', 0) != 0:
                    trade = self._execute_signal(
                        portfolio, 
                        latest_signals, 
                        row, 
                        current_time, 
                        strategy.name
                    )
                    if trade:
                        trades.append(trade)
            
            # Check for exit conditions on existing positions
            exits = self._check_exit_conditions(portfolio, row, current_time, strategy)
            trades.extend(exits)
            
            # Update equity curve
            current_equity = portfolio['equity']
            equity_curve.append({
                'timestamp': current_time,
                'equity': current_equity,
                'cash': portfolio['cash'],
                'positions_value': current_equity - portfolio['cash']
            })
            
            # Update drawdown
            if current_equity > peak_equity:
                peak_equity = current_equity
                current_dd_duration = 0
            else:
                current_drawdown = (peak_equity - current_equity) / peak_equity
                if current_drawdown > max_drawdown:
                    max_drawdown = current_drawdown
                current_dd_duration += 1
                if current_dd_duration > max_dd_duration:
                    max_dd_duration = current_dd_duration
            
            drawdown_curve.append({
                'timestamp': current_time,
                'drawdown': (peak_equity - current_equity) / peak_equity,
                'peak_equity': peak_equity
            })
        
        # Calculate final results
        results = self._calculate_results(
            trades, 
            equity_curve, 
            drawdown_curve, 
            data.index[0], 
            data.index[-1]
        )
        
        self.logger.info(f"Backtest completed. Total return: {results.total_return:.2%}")
        return results
    
    def _update_portfolio_value(self, portfolio: Dict, market_data: pd.Series, timestamp: datetime):
        """Update portfolio value with current market prices"""
        total_positions_value = 0
        
        for symbol, position in portfolio['positions'].items():
            if symbol in market_data.index or 'close' in market_data:
                current_price = market_data.get('close', market_data.get(symbol, position['avg_price']))
                position['current_price'] = current_price
                position['market_value'] = position['quantity'] * current_price
                position['unrealized_pnl'] = position['market_value'] - position['cost_basis']
                total_positions_value += position['market_value']
        
        portfolio['equity'] = portfolio['cash'] + total_positions_value
    
    def _execute_signal(self, 
                       portfolio: Dict, 
                       signal: pd.Series, 
                       market_data: pd.Series, 
                       timestamp: datetime,
                       strategy_name: str) -> Optional[BacktestTrade]:
        """Execute trading signal"""
        signal_value = signal.get('signal', 0)
        if signal_value == 0:
            return None
        
        # Determine trade parameters
        symbol = signal.get('symbol', 'DEFAULT')
        side = 'long' if signal_value > 0 else 'short'
        entry_price = market_data.get('close', market_data.get('open', 0))
        
        if entry_price <= 0:
            return None
        
        # Calculate position size
        position_size = self._calculate_position_size(
            portfolio, 
            entry_price, 
            signal.get('confidence', 1.0)
        )
        
        if position_size < self.min_trade_amount / entry_price:
            return None
        
        # Check if we can open new position
        if len(portfolio['positions']) >= self.max_positions:
            return None
        
        # Apply slippage and commission
        slippage = entry_price * self.slippage_rate
        if side == 'long':
            execution_price = entry_price + slippage
        else:
            execution_price = entry_price - slippage
        
        trade_value = position_size * execution_price
        commission = trade_value * self.commission_rate
        total_cost = trade_value + commission
        
        # Check if we have enough capital
        required_margin = total_cost * self.margin_requirement
        if portfolio['cash'] < required_margin:
            return None
        
        # Execute trade
        portfolio['cash'] -= required_margin
        portfolio['margin_used'] += total_cost - required_margin
        
        position_id = f"{symbol}_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        portfolio['positions'][position_id] = {
            'symbol': symbol,
            'side': side,
            'quantity': position_size,
            'avg_price': execution_price,
            'cost_basis': trade_value,
            'commission': commission,
            'entry_time': timestamp,
            'current_price': execution_price,
            'market_value': trade_value,
            'unrealized_pnl': 0,
            'max_favorable_excursion': 0,
            'max_adverse_excursion': 0
        }
        
        return None  # Trade will be recorded when position is closed
    
    def _check_exit_conditions(self, 
                              portfolio: Dict, 
                              market_data: pd.Series, 
                              timestamp: datetime,
                              strategy) -> List[BacktestTrade]:
        """Check exit conditions for existing positions"""
        trades = []
        positions_to_close = []
        
        for position_id, position in portfolio['positions'].items():
            current_price = market_data.get('close', position['current_price'])
            entry_price = position['avg_price']
            side = position['side']
            
            # Update MFE and MAE
            if side == 'long':
                excursion = (current_price - entry_price) / entry_price
            else:
                excursion = (entry_price - current_price) / entry_price
            
            if excursion > position['max_favorable_excursion']:
                position['max_favorable_excursion'] = excursion
            if excursion < position['max_adverse_excursion']:
                position['max_adverse_excursion'] = excursion
            
            # Check exit conditions (simplified - in practice, use strategy-specific logic)
            should_exit = False
            exit_reason = 'unknown'
            
            # Time-based exit (example: hold for max 30 periods)
            if hasattr(strategy, 'max_holding_period'):
                holding_period = timestamp - position['entry_time']
                if holding_period.total_seconds() > getattr(strategy, 'max_holding_period', 86400):  # 1 day default
                    should_exit = True
                    exit_reason = 'time_exit'
            
            # Profit/Loss based exits
            if hasattr(strategy, 'take_profit') and excursion >= getattr(strategy, 'take_profit', 0.1):
                should_exit = True
                exit_reason = 'take_profit'
            elif hasattr(strategy, 'stop_loss') and excursion <= -getattr(strategy, 'stop_loss', 0.05):
                should_exit = True
                exit_reason = 'stop_loss'
            
            if should_exit:
                trade = self._close_position(portfolio, position_id, current_price, timestamp, exit_reason)
                if trade:
                    trades.append(trade)
                positions_to_close.append(position_id)
        
        # Remove closed positions
        for position_id in positions_to_close:
            del portfolio['positions'][position_id]
        
        return trades
    
    def _close_position(self, 
                       portfolio: Dict, 
                       position_id: str, 
                       exit_price: float, 
                       timestamp: datetime,
                       exit_reason: str) -> Optional[BacktestTrade]:
        """Close a position and record the trade"""
        if position_id not in portfolio['positions']:
            return None
        
        position = portfolio['positions'][position_id]
        
        # Apply slippage and commission
        slippage = exit_price * self.slippage_rate
        if position['side'] == 'long':
            execution_price = exit_price - slippage
        else:
            execution_price = exit_price + slippage
        
        trade_value = position['quantity'] * execution_price
        commission = trade_value * self.commission_rate
        
        # Calculate P&L
        if position['side'] == 'long':
            pnl = trade_value - position['cost_basis'] - commission - position['commission']
        else:
            pnl = position['cost_basis'] - trade_value - commission - position['commission']
        
        pnl_pct = pnl / position['cost_basis']
        
        # Update portfolio
        portfolio['cash'] += trade_value - commission
        portfolio['margin_used'] -= max(0, position['cost_basis'] - position['cost_basis'] * self.margin_requirement)
        
        # Create trade record
        trade = BacktestTrade(
            entry_time=position['entry_time'],
            exit_time=timestamp,
            symbol=position['symbol'],
            side=position['side'],
            entry_price=position['avg_price'],
            exit_price=execution_price,
            quantity=position['quantity'],
            pnl=pnl,
            pnl_pct=pnl_pct,
            commission=commission + position['commission'],
            slippage=slippage * position['quantity'],
            strategy=position.get('strategy', 'unknown'),
            reason=exit_reason,
            duration=timestamp - position['entry_time'],
            max_favorable_excursion=position['max_favorable_excursion'],
            max_adverse_excursion=position['max_adverse_excursion']
        )
        
        return trade
    
    def _calculate_position_size(self, portfolio: Dict, price: float, confidence: float = 1.0) -> float:
        """Calculate position size based on available capital and risk management"""
        available_capital = portfolio['cash']
        max_position_value = available_capital * 0.1 * confidence  # Max 10% per position, adjusted by confidence
        
        return max_position_value / price
    
    def _calculate_results(self, 
                          trades: List[BacktestTrade], 
                          equity_curve: List[Dict], 
                          drawdown_curve: List[Dict],
                          start_date: datetime, 
                          end_date: datetime) -> BacktestResults:
        """Calculate comprehensive backtest results"""
        if not trades:
            # Return minimal results if no trades
            return BacktestResults(
                start_date=start_date,
                end_date=end_date,
                initial_capital=self.initial_capital,
                final_capital=self.initial_capital,
                total_return=0.0,
                annualized_return=0.0,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0.0,
                avg_win=0.0,
                avg_loss=0.0,
                profit_factor=0.0,
                max_drawdown=0.0,
                max_drawdown_duration=0,
                volatility=0.0,
                sharpe_ratio=0.0,
                sortino_ratio=0.0,
                calmar_ratio=0.0,
                var_95=0.0,
                expectancy=0.0,
                kelly_criterion=0.0,
                recovery_factor=0.0,
                payoff_ratio=0.0,
                trades=[],
                equity_curve=pd.DataFrame(),
                drawdown_curve=pd.DataFrame(),
                monthly_returns=pd.DataFrame()
            )
        
        # Convert to DataFrames
        equity_df = pd.DataFrame(equity_curve).set_index('timestamp')
        drawdown_df = pd.DataFrame(drawdown_curve).set_index('timestamp')
        
        # Basic metrics
        final_capital = equity_df['equity'].iloc[-1]
        total_return = (final_capital - self.initial_capital) / self.initial_capital
        
        # Annualized return
        days = (end_date - start_date).days
        years = days / 365.25
        annualized_return = (final_capital / self.initial_capital) ** (1 / years) - 1 if years > 0 else 0
        
        # Trade statistics
        winning_trades = [t for t in trades if t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl < 0]
        
        win_rate = len(winning_trades) / len(trades) if trades else 0
        avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([abs(t.pnl) for t in losing_trades]) if losing_trades else 0
        
        gross_profit = sum([t.pnl for t in winning_trades])
        gross_loss = sum([abs(t.pnl) for t in losing_trades])
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Risk metrics
        returns = equity_df['equity'].pct_change().dropna()
        max_drawdown = drawdown_df['drawdown'].max()
        max_dd_duration = self._calculate_max_drawdown_duration(drawdown_df)
        
        volatility = returns.std() * np.sqrt(252) if len(returns) > 1 else 0  # Annualized
        sharpe_ratio = (annualized_return - 0.02) / volatility if volatility > 0 else 0  # Assuming 2% risk-free rate
        
        # Sortino ratio
        downside_returns = returns[returns < 0]
        downside_deviation = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0
        sortino_ratio = (annualized_return - 0.02) / downside_deviation if downside_deviation > 0 else 0
        
        # Calmar ratio
        calmar_ratio = annualized_return / max_drawdown if max_drawdown > 0 else 0
        
        # VaR 95%
        var_95 = abs(np.percentile(returns, 5) * final_capital) if len(returns) > 0 else 0
        
        # Advanced metrics
        expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
        
        # Kelly Criterion
        if avg_loss > 0:
            kelly_criterion = win_rate - ((1 - win_rate) / (avg_win / avg_loss))
        else:
            kelly_criterion = 0
        
        recovery_factor = total_return / max_drawdown if max_drawdown > 0 else 0
        payoff_ratio = avg_win / avg_loss if avg_loss > 0 else 0
        
        # Monthly returns
        monthly_returns = self._calculate_monthly_returns(equity_df)
        
        return BacktestResults(
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.initial_capital,
            final_capital=final_capital,
            total_return=total_return,
            annualized_return=annualized_return,
            total_trades=len(trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            max_drawdown=max_drawdown,
            max_drawdown_duration=max_dd_duration,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            var_95=var_95,
            expectancy=expectancy,
            kelly_criterion=kelly_criterion,
            recovery_factor=recovery_factor,
            payoff_ratio=payoff_ratio,
            trades=trades,
            equity_curve=equity_df,
            drawdown_curve=drawdown_df,
            monthly_returns=monthly_returns
        )
    
    def _calculate_max_drawdown_duration(self, drawdown_df: pd.DataFrame) -> int:
        """Calculate maximum drawdown duration in days"""
        if drawdown_df.empty:
            return 0
        
        max_duration = 0
        current_duration = 0
        
        for drawdown in drawdown_df['drawdown']:
            if drawdown > 0:
                current_duration += 1
                max_duration = max(max_duration, current_duration)
            else:
                current_duration = 0
        
        return max_duration
    
    def _calculate_monthly_returns(self, equity_df: pd.DataFrame) -> pd.DataFrame:
        """Calculate monthly returns"""
        if equity_df.empty:
            return pd.DataFrame()
        
        monthly_equity = equity_df['equity'].resample('M').last()
        monthly_returns = monthly_equity.pct_change().dropna()
        
        return pd.DataFrame({
            'return': monthly_returns,
            'cumulative_return': (1 + monthly_returns).cumprod() - 1
        })
    
    def generate_report(self, results: BacktestResults, save_path: Optional[str] = None) -> str:
        """Generate comprehensive backtest report"""
        report = f"""
# Backtest Report

## Summary
- **Period**: {results.start_date.strftime('%Y-%m-%d')} to {results.end_date.strftime('%Y-%m-%d')}
- **Initial Capital**: ${results.initial_capital:,.2f}
- **Final Capital**: ${results.final_capital:,.2f}
- **Total Return**: {results.total_return:.2%}
- **Annualized Return**: {results.annualized_return:.2%}

## Trade Statistics
- **Total Trades**: {results.total_trades}
- **Winning Trades**: {results.winning_trades}
- **Losing Trades**: {results.losing_trades}
- **Win Rate**: {results.win_rate:.2%}
- **Average Win**: ${results.avg_win:.2f}
- **Average Loss**: ${results.avg_loss:.2f}
- **Profit Factor**: {results.profit_factor:.2f}

## Risk Metrics
- **Maximum Drawdown**: {results.max_drawdown:.2%}
- **Max Drawdown Duration**: {results.max_drawdown_duration} days
- **Volatility**: {results.volatility:.2%}
- **Sharpe Ratio**: {results.sharpe_ratio:.2f}
- **Sortino Ratio**: {results.sortino_ratio:.2f}
- **Calmar Ratio**: {results.calmar_ratio:.2f}
- **VaR (95%)**: ${results.var_95:.2f}

## Advanced Metrics
- **Expectancy**: ${results.expectancy:.2f}
- **Kelly Criterion**: {results.kelly_criterion:.2%}
- **Recovery Factor**: {results.recovery_factor:.2f}
- **Payoff Ratio**: {results.payoff_ratio:.2f}
"""
        
        if save_path:
            with open(save_path, 'w') as f:
                f.write(report)
        
        return report
    
    def plot_results(self, results: BacktestResults, save_path: Optional[str] = None):
        """Plot backtest results"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # Equity curve
        axes[0, 0].plot(results.equity_curve.index, results.equity_curve['equity'])
        axes[0, 0].set_title('Equity Curve')
        axes[0, 0].set_ylabel('Portfolio Value ($)')
        axes[0, 0].grid(True)
        
        # Drawdown curve
        axes[0, 1].fill_between(results.drawdown_curve.index, 
                               results.drawdown_curve['drawdown'] * 100, 
                               0, alpha=0.3, color='red')
        axes[0, 1].set_title('Drawdown Curve')
        axes[0, 1].set_ylabel('Drawdown (%)')
        axes[0, 1].grid(True)
        
        # Monthly returns
        if not results.monthly_returns.empty:
            axes[1, 0].bar(range(len(results.monthly_returns)), 
                          results.monthly_returns['return'] * 100)
            axes[1, 0].set_title('Monthly Returns')
            axes[1, 0].set_ylabel('Return (%)')
            axes[1, 0].grid(True)
        
        # Trade P&L distribution
        trade_pnls = [trade.pnl for trade in results.trades]
        if trade_pnls:
            axes[1, 1].hist(trade_pnls, bins=20, alpha=0.7)
            axes[1, 1].set_title('Trade P&L Distribution')
            axes[1, 1].set_xlabel('P&L ($)')
            axes[1, 1].set_ylabel('Frequency')
            axes[1, 1].grid(True)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        plt.show()
    
    def optimize_parameters(self, 
                           strategy_class, 
                           data: pd.DataFrame, 
                           parameter_ranges: Dict[str, List],
                           optimization_metric: str = 'sharpe_ratio',
                           max_workers: int = 4) -> Dict:
        """Optimize strategy parameters using grid search
        
        Args:
            strategy_class: Strategy class to optimize
            data: Historical data
            parameter_ranges: Dictionary of parameter ranges to test
            optimization_metric: Metric to optimize
            max_workers: Number of parallel workers
            
        Returns:
            Best parameters and results
        """
        from itertools import product
        
        # Generate parameter combinations
        param_names = list(parameter_ranges.keys())
        param_values = list(parameter_ranges.values())
        param_combinations = list(product(*param_values))
        
        self.logger.info(f"Testing {len(param_combinations)} parameter combinations")
        
        best_result = None
        best_params = None
        best_metric = float('-inf')
        
        def test_parameters(params):
            try:
                # Create strategy with parameters
                param_dict = dict(zip(param_names, params))
                strategy = strategy_class(**param_dict)
                
                # Run backtest
                results = self.run_backtest(strategy, data)
                
                # Get optimization metric
                metric_value = getattr(results, optimization_metric, 0)
                
                return param_dict, results, metric_value
            except Exception as e:
                self.logger.error(f"Error testing parameters {params}: {e}")
                return None, None, float('-inf')
        
        # Run optimization in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(test_parameters, params) for params in param_combinations]
            
            for future in as_completed(futures):
                param_dict, results, metric_value = future.result()
                
                if metric_value > best_metric:
                    best_metric = metric_value
                    best_params = param_dict
                    best_result = results
        
        self.logger.info(f"Best parameters: {best_params}")
        self.logger.info(f"Best {optimization_metric}: {best_metric:.4f}")
        
        return {
            'best_parameters': best_params,
            'best_results': best_result,
            'best_metric_value': best_metric,
            'optimization_metric': optimization_metric
        }