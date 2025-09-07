"""Portfolio Management Module

This module provides comprehensive portfolio management functionality including:
- Portfolio tracking and analytics
- Asset allocation management
- Performance metrics calculation
- Rebalancing strategies
- Multi-asset portfolio optimization
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict
import json

logger = logging.getLogger(__name__)

@dataclass
class Position:
    """Represents a portfolio position"""
    symbol: str
    quantity: float
    average_price: float
    current_price: float = 0.0
    market_value: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def update_market_data(self, current_price: float):
        """Update position with current market price"""
        self.current_price = current_price
        self.market_value = self.quantity * current_price
        self.unrealized_pnl = (current_price - self.average_price) * self.quantity
        self.last_updated = datetime.utcnow()

@dataclass
class PortfolioMetrics:
    """Portfolio performance metrics"""
    total_value: float
    total_invested: float
    total_pnl: float
    total_pnl_percentage: float
    daily_pnl: float
    daily_pnl_percentage: float
    positions_count: int
    largest_position_percentage: float
    cash_percentage: float
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0

class PortfolioManager:
    """Advanced Portfolio Management System
    
    Manages portfolio positions, tracks performance metrics,
    and provides portfolio optimization and rebalancing capabilities.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the portfolio manager
        
        Args:
            config: Portfolio configuration including:
                   - initial_balance: Starting portfolio balance
                   - base_currency: Base currency for calculations
                   - rebalance_threshold: Threshold for automatic rebalancing
                   - max_positions: Maximum number of positions
        """
        self.config = config
        self.initial_balance = config.get('initial_balance', 10000.0)
        self.base_currency = config.get('base_currency', 'USDT')
        self.rebalance_threshold = config.get('rebalance_threshold', 0.05)  # 5%
        self.max_positions = config.get('max_positions', 20)
        
        # Portfolio state
        self.positions: Dict[str, Position] = {}
        self.cash_balance = self.initial_balance
        self.trade_history = []
        self.daily_values = []  # For performance tracking
        
        # Performance tracking
        self.peak_value = self.initial_balance
        self.current_drawdown = 0.0
        self.max_drawdown = 0.0
        
        logger.info(f"Portfolio Manager initialized with ${self.initial_balance:,.2f} {self.base_currency}")
    
    async def update_position(self, signal, execution_result: Dict[str, Any]):
        """
        Update portfolio position based on trade execution
        
        Args:
            signal: Original trading signal
            execution_result: Result from trade execution
        """
        try:
            if not execution_result.get('success'):
                logger.warning(f"Trade execution failed, not updating position: {execution_result.get('error')}")
                return
            
            symbol = signal.symbol
            action = signal.action
            quantity = execution_result.get('quantity', signal.quantity)
            price = execution_result.get('price', signal.price)
            fees = execution_result.get('fees', 0.0)
            
            logger.info(f"Updating position for {symbol}: {action} {quantity} at ${price}")
            
            # Update cash balance
            trade_value = quantity * price
            if action == 'BUY':
                self.cash_balance -= (trade_value + fees)
            else:  # SELL
                self.cash_balance += (trade_value - fees)
            
            # Update or create position
            if symbol not in self.positions:
                if action == 'BUY':
                    self.positions[symbol] = Position(
                        symbol=symbol,
                        quantity=quantity,
                        average_price=price,
                        current_price=price
                    )
                # For SELL without existing position (short selling), handle separately
            else:
                position = self.positions[symbol]
                
                if action == 'BUY':
                    # Add to existing position (average down/up)
                    total_cost = (position.quantity * position.average_price) + (quantity * price)
                    position.quantity += quantity
                    position.average_price = total_cost / position.quantity if position.quantity > 0 else price
                else:  # SELL
                    # Reduce position
                    if quantity >= position.quantity:
                        # Complete position close
                        realized_pnl = (price - position.average_price) * position.quantity
                        position.realized_pnl += realized_pnl
                        
                        # Record trade for performance tracking
                        self._record_trade(symbol, position.quantity, position.average_price, price, 'CLOSE')
                        
                        # Remove position if completely closed
                        del self.positions[symbol]
                    else:
                        # Partial position close
                        realized_pnl = (price - position.average_price) * quantity
                        position.realized_pnl += realized_pnl
                        position.quantity -= quantity
                        
                        # Record partial trade
                        self._record_trade(symbol, quantity, position.average_price, price, 'PARTIAL_CLOSE')
            
            # Update position market data if it still exists
            if symbol in self.positions:
                self.positions[symbol].update_market_data(price)
            
            logger.info(f"Position updated successfully. Cash balance: ${self.cash_balance:,.2f}")
            
        except Exception as e:
            logger.error(f"Error updating position: {e}")
            raise
    
    def _record_trade(self, symbol: str, quantity: float, entry_price: float, exit_price: float, trade_type: str):
        """
        Record trade for performance analysis
        
        Args:
            symbol: Trading symbol
            quantity: Trade quantity
            entry_price: Entry price
            exit_price: Exit price
            trade_type: Type of trade (CLOSE, PARTIAL_CLOSE)
        """
        pnl = (exit_price - entry_price) * quantity
        pnl_percentage = (exit_price - entry_price) / entry_price * 100
        
        trade_record = {
            'timestamp': datetime.utcnow(),
            'symbol': symbol,
            'quantity': quantity,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'pnl': pnl,
            'pnl_percentage': pnl_percentage,
            'trade_type': trade_type
        }
        
        self.trade_history.append(trade_record)
        logger.info(f"Trade recorded: {symbol} P&L: ${pnl:.2f} ({pnl_percentage:.2f}%)")
    
    async def update_market_prices(self, price_data: Dict[str, float]):
        """
        Update all positions with current market prices
        
        Args:
            price_data: Dictionary of symbol -> current_price
        """
        try:
            for symbol, position in self.positions.items():
                if symbol in price_data:
                    position.update_market_data(price_data[symbol])
            
            # Update portfolio metrics
            await self._update_portfolio_metrics()
            
        except Exception as e:
            logger.error(f"Error updating market prices: {e}")
    
    async def _update_portfolio_metrics(self):
        """
        Update portfolio performance metrics
        """
        try:
            current_value = self.get_total_portfolio_value()
            
            # Update peak value and drawdown
            if current_value > self.peak_value:
                self.peak_value = current_value
                self.current_drawdown = 0.0
            else:
                self.current_drawdown = (self.peak_value - current_value) / self.peak_value
                self.max_drawdown = max(self.max_drawdown, self.current_drawdown)
            
            # Record daily value for performance tracking
            self.daily_values.append({
                'date': datetime.utcnow().date(),
                'value': current_value,
                'drawdown': self.current_drawdown
            })
            
            # Keep only last 365 days
            if len(self.daily_values) > 365:
                self.daily_values = self.daily_values[-365:]
            
        except Exception as e:
            logger.error(f"Error updating portfolio metrics: {e}")
    
    def get_total_portfolio_value(self) -> float:
        """
        Calculate total portfolio value (cash + positions)
        
        This method computes the total value of the portfolio by summing:
        - Current cash balance
        - Market value of all open positions
        
        Returns:
            Total portfolio value in base currency
        """
        try:
            # Sum up the market value of all positions
            # Each position's market_value = quantity * current_price
            positions_value = sum(pos.market_value for pos in self.positions.values())
            
            # Total portfolio value = available cash + value of all positions
            return self.cash_balance + positions_value
        except Exception as e:
            logger.error(f"Error calculating portfolio value: {e}")
            # Return only cash balance if calculation fails
            return self.cash_balance
    
    def get_portfolio_metrics(self) -> PortfolioMetrics:
        """
        Get comprehensive portfolio metrics
        
        This method calculates and returns detailed portfolio performance metrics including:
        - Total portfolio value and P&L (absolute and percentage)
        - Daily performance metrics
        - Position allocation statistics
        - Risk metrics (Sharpe ratio, drawdown, win rate)
        
        Returns:
            PortfolioMetrics object with current portfolio statistics
        """
        try:
            # Calculate basic portfolio values
            total_value = self.get_total_portfolio_value()
            total_invested = self.initial_balance
            total_pnl = total_value - total_invested  # Absolute profit/loss
            total_pnl_percentage = (total_pnl / total_invested * 100) if total_invested > 0 else 0
            
            # Calculate daily P&L if we have historical data (need at least 2 data points)
            daily_pnl = 0.0
            daily_pnl_percentage = 0.0
            if len(self.daily_values) >= 2:
                yesterday_value = self.daily_values[-2]['value']
                daily_pnl = total_value - yesterday_value  # Today's change in portfolio value
                daily_pnl_percentage = (daily_pnl / yesterday_value * 100) if yesterday_value > 0 else 0
            
            # Calculate position allocation statistics
            positions_count = len(self.positions)
            largest_position_percentage = 0.0
            if self.positions and total_value > 0:
                # Find the largest position by market value
                largest_position_value = max(pos.market_value for pos in self.positions.values())
                largest_position_percentage = (largest_position_value / total_value * 100)
            
            # Calculate cash allocation percentage
            cash_percentage = (self.cash_balance / total_value * 100) if total_value > 0 else 100
            
            # Performance metrics
            sharpe_ratio = self._calculate_sharpe_ratio()
            win_rate, avg_win, avg_loss = self._calculate_trade_statistics()
            
            return PortfolioMetrics(
                total_value=total_value,
                total_invested=total_invested,
                total_pnl=total_pnl,
                total_pnl_percentage=total_pnl_percentage,
                daily_pnl=daily_pnl,
                daily_pnl_percentage=daily_pnl_percentage,
                positions_count=positions_count,
                largest_position_percentage=largest_position_percentage,
                cash_percentage=cash_percentage,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=self.max_drawdown * 100,  # Convert to percentage
                win_rate=win_rate,
                avg_win=avg_win,
                avg_loss=avg_loss
            )
            
        except Exception as e:
            logger.error(f"Error calculating portfolio metrics: {e}")
            return PortfolioMetrics(
                total_value=self.cash_balance,
                total_invested=self.initial_balance,
                total_pnl=0.0,
                total_pnl_percentage=0.0,
                daily_pnl=0.0,
                daily_pnl_percentage=0.0,
                positions_count=0,
                largest_position_percentage=0.0,
                cash_percentage=100.0
            )
    
    def _calculate_sharpe_ratio(self) -> float:
        """
        Calculate Sharpe ratio based on daily returns
        
        The Sharpe ratio measures risk-adjusted returns by comparing the portfolio's
        excess return (above risk-free rate) to its volatility (standard deviation).
        Higher values indicate better risk-adjusted performance.
        
        Formula: (Portfolio Return - Risk-Free Rate) / Portfolio Standard Deviation
        
        Returns:
            Sharpe ratio (annualized)
        """
        try:
            # Need sufficient data for meaningful calculation (at least 30 days)
            if len(self.daily_values) < 30:
                return 0.0
            
            # Calculate daily returns as percentage changes
            returns = []
            for i in range(1, len(self.daily_values)):
                prev_value = self.daily_values[i-1]['value']
                curr_value = self.daily_values[i]['value']
                if prev_value > 0:
                    # Daily return = (today_value - yesterday_value) / yesterday_value
                    daily_return = (curr_value - prev_value) / prev_value
                    returns.append(daily_return)
            
            if not returns:
                return 0.0
            
            # Calculate statistical measures of returns
            mean_return = sum(returns) / len(returns)  # Average daily return
            variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)  # Variance
            std_dev = variance ** 0.5  # Standard deviation (volatility)
            
            # Cannot calculate Sharpe ratio if there's no volatility
            if std_dev == 0:
                return 0.0
            
            # Annualize the metrics (assuming 252 trading days per year)
            annual_return = mean_return * 252  # Annualized return
            annual_std = std_dev * (252 ** 0.5)  # Annualized volatility
            
            # Calculate Sharpe ratio using 2% risk-free rate (typical treasury rate)
            risk_free_rate = 0.02
            sharpe_ratio = (annual_return - risk_free_rate) / annual_std
            
            return sharpe_ratio
            
        except Exception as e:
            logger.error(f"Error calculating Sharpe ratio: {e}")
            return 0.0
    
    def _calculate_trade_statistics(self) -> Tuple[float, float, float]:
        """
        Calculate trade statistics (win rate, average win, average loss)
        
        Returns:
            Tuple of (win_rate, avg_win, avg_loss)
        """
        try:
            if not self.trade_history:
                return 0.0, 0.0, 0.0
            
            wins = [trade['pnl'] for trade in self.trade_history if trade['pnl'] > 0]
            losses = [trade['pnl'] for trade in self.trade_history if trade['pnl'] < 0]
            
            total_trades = len(self.trade_history)
            win_count = len(wins)
            
            win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0.0
            avg_win = sum(wins) / len(wins) if wins else 0.0
            avg_loss = sum(losses) / len(losses) if losses else 0.0
            
            return win_rate, avg_win, abs(avg_loss)  # Return absolute value for loss
            
        except Exception as e:
            logger.error(f"Error calculating trade statistics: {e}")
            return 0.0, 0.0, 0.0
    
    def get_positions_summary(self) -> List[Dict[str, Any]]:
        """
        Get summary of all current positions
        
        Returns:
            List of position summaries
        """
        try:
            positions_summary = []
            total_value = self.get_total_portfolio_value()
            
            for symbol, position in self.positions.items():
                position_percentage = (position.market_value / total_value * 100) if total_value > 0 else 0
                
                summary = {
                    'symbol': symbol,
                    'quantity': position.quantity,
                    'average_price': position.average_price,
                    'current_price': position.current_price,
                    'market_value': position.market_value,
                    'unrealized_pnl': position.unrealized_pnl,
                    'unrealized_pnl_percentage': (position.unrealized_pnl / (position.average_price * position.quantity) * 100) if position.quantity > 0 else 0,
                    'position_percentage': position_percentage,
                    'last_updated': position.last_updated
                }
                positions_summary.append(summary)
            
            # Sort by market value (largest first)
            positions_summary.sort(key=lambda x: x['market_value'], reverse=True)
            
            return positions_summary
            
        except Exception as e:
            logger.error(f"Error getting positions summary: {e}")
            return []
    
    def check_rebalancing_needed(self, target_allocations: Dict[str, float]) -> Dict[str, Any]:
        """
        Check if portfolio rebalancing is needed
        
        This method compares current portfolio allocations against target allocations
        and determines if rebalancing is needed based on the configured threshold.
        It provides specific recommendations for each position that needs adjustment.
        
        Args:
            target_allocations: Dictionary of symbol -> target_percentage (e.g., {'BTCUSDT': 50.0})
            
        Returns:
            Dictionary with rebalancing recommendations including:
            - rebalancing_needed: Boolean indicating if action is required
            - recommendations: List of specific actions to take
            - current_allocations: Current percentage allocation per symbol
            - target_allocations: Target percentage allocation per symbol
        """
        try:
            total_value = self.get_total_portfolio_value()
            current_allocations = {}
            
            # Calculate current allocation percentage for each position
            for symbol, position in self.positions.items():
                # Convert position value to percentage of total portfolio
                current_allocations[symbol] = (position.market_value / total_value * 100) if total_value > 0 else 0
            
            # Analyze deviations from target allocations
            rebalancing_needed = False
            recommendations = []
            
            for symbol, target_pct in target_allocations.items():
                current_pct = current_allocations.get(symbol, 0.0)  # Default to 0 if position doesn't exist
                deviation = abs(current_pct - target_pct)  # Absolute difference from target
                
                # Check if deviation exceeds the rebalancing threshold
                if deviation > self.rebalance_threshold * 100:  # Convert threshold to percentage
                    rebalancing_needed = True
                    
                    # Determine action needed and calculate amount
                    if current_pct > target_pct:
                        action = 'REDUCE'  # Need to sell some of this position
                        amount = (current_pct - target_pct) / 100 * total_value
                    else:
                        action = 'INCREASE'  # Need to buy more of this position
                        amount = (target_pct - current_pct) / 100 * total_value
                    
                    # Add detailed recommendation
                    recommendations.append({
                        'symbol': symbol,
                        'action': action,
                        'current_percentage': current_pct,
                        'target_percentage': target_pct,
                        'deviation': deviation,
                        'recommended_amount': amount  # Dollar amount to buy/sell
                    })
            
            return {
                'rebalancing_needed': rebalancing_needed,
                'recommendations': recommendations,
                'current_allocations': current_allocations,
                'target_allocations': target_allocations
            }
            
        except Exception as e:
            logger.error(f"Error checking rebalancing: {e}")
            return {
                'rebalancing_needed': False,
                'recommendations': [],
                'current_allocations': {},
                'target_allocations': target_allocations
            }
    
    def export_portfolio_data(self) -> Dict[str, Any]:
        """
        Export portfolio data for backup or analysis
        
        Returns:
            Dictionary containing all portfolio data
        """
        try:
            return {
                'config': self.config,
                'initial_balance': self.initial_balance,
                'cash_balance': self.cash_balance,
                'positions': {symbol: {
                    'symbol': pos.symbol,
                    'quantity': pos.quantity,
                    'average_price': pos.average_price,
                    'current_price': pos.current_price,
                    'realized_pnl': pos.realized_pnl
                } for symbol, pos in self.positions.items()},
                'trade_history': self.trade_history,
                'daily_values': self.daily_values,
                'peak_value': self.peak_value,
                'max_drawdown': self.max_drawdown,
                'export_timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error exporting portfolio data: {e}")
            return {}
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get portfolio manager status
        
        Returns:
            Dictionary with current status information
        """
        metrics = self.get_portfolio_metrics()
        
        return {
            'total_value': metrics.total_value,
            'cash_balance': self.cash_balance,
            'positions_count': metrics.positions_count,
            'total_pnl': metrics.total_pnl,
            'total_pnl_percentage': metrics.total_pnl_percentage,
            'max_drawdown': metrics.max_drawdown,
            'sharpe_ratio': metrics.sharpe_ratio,
            'win_rate': metrics.win_rate
        }

# Example usage
if __name__ == "__main__":
    # Example configuration
    config = {
        'initial_balance': 10000.0,
        'base_currency': 'USDT',
        'rebalance_threshold': 0.05,
        'max_positions': 20
    }
    
    portfolio_manager = PortfolioManager(config)
    
    # Example position update
    from core.trading_engine import TradeSignal
    
    signal = TradeSignal(
        symbol='BTCUSDT',
        action='BUY',
        quantity=0.1,
        price=50000.0
    )
    
    execution_result = {
        'success': True,
        'quantity': 0.1,
        'price': 50000.0,
        'fees': 5.0
    }
    
    # Update position
    asyncio.run(portfolio_manager.update_position(signal, execution_result))
    
    # Get metrics
    metrics = portfolio_manager.get_portfolio_metrics()
    print(f"Portfolio Value: ${metrics.total_value:,.2f}")
    print(f"Total P&L: ${metrics.total_pnl:,.2f} ({metrics.total_pnl_percentage:.2f}%)")