import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json
from scipy.optimize import minimize
from scipy.stats import norm
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
import warnings
warnings.filterwarnings('ignore')

@dataclass
class Position:
    """Individual position in portfolio"""
    symbol: str
    side: str  # 'long' or 'short'
    quantity: float
    avg_price: float
    current_price: float
    market_value: float
    cost_basis: float
    unrealized_pnl: float
    realized_pnl: float
    entry_time: datetime
    last_update: datetime
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    trailing_stop: Optional[float] = None
    max_favorable_excursion: float = 0.0
    max_adverse_excursion: float = 0.0
    
    def update_price(self, new_price: float):
        """Update position with new market price"""
        self.current_price = new_price
        self.market_value = self.quantity * new_price
        
        if self.side == 'long':
            self.unrealized_pnl = self.market_value - self.cost_basis
            excursion = (new_price - self.avg_price) / self.avg_price
        else:
            self.unrealized_pnl = self.cost_basis - self.market_value
            excursion = (self.avg_price - new_price) / self.avg_price
        
        # Update MFE and MAE
        if excursion > self.max_favorable_excursion:
            self.max_favorable_excursion = excursion
        if excursion < self.max_adverse_excursion:
            self.max_adverse_excursion = excursion
        
        self.last_update = datetime.now()
    
    def get_return_pct(self) -> float:
        """Get position return percentage"""
        if self.cost_basis == 0:
            return 0.0
        return self.unrealized_pnl / self.cost_basis
    
    def should_close(self) -> Tuple[bool, str]:
        """Check if position should be closed based on stop loss/take profit"""
        if self.side == 'long':
            if self.stop_loss and self.current_price <= self.stop_loss:
                return True, 'stop_loss'
            if self.take_profit and self.current_price >= self.take_profit:
                return True, 'take_profit'
        else:
            if self.stop_loss and self.current_price >= self.stop_loss:
                return True, 'stop_loss'
            if self.take_profit and self.current_price <= self.take_profit:
                return True, 'take_profit'
        
        return False, ''

@dataclass
class PortfolioMetrics:
    """Portfolio performance metrics"""
    total_value: float
    cash: float
    positions_value: float
    total_pnl: float
    unrealized_pnl: float
    realized_pnl: float
    daily_return: float
    total_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    num_positions: int
    leverage: float
    margin_used: float
    available_margin: float
    risk_score: float
    
class PortfolioManager:
    """Advanced portfolio management system"""
    
    def __init__(self,
                 initial_capital: float = 100000,
                 max_positions: int = 20,
                 max_position_size: float = 0.1,  # 10% max per position
                 max_sector_allocation: float = 0.3,  # 30% max per sector
                 max_leverage: float = 2.0,
                 risk_free_rate: float = 0.02,
                 rebalance_threshold: float = 0.05,  # 5% deviation triggers rebalance
                 db_path: str = 'portfolio.db'):
        """
        Initialize portfolio manager
        
        Args:
            initial_capital: Starting capital
            max_positions: Maximum number of positions
            max_position_size: Maximum position size as fraction of portfolio
            max_sector_allocation: Maximum allocation per sector
            max_leverage: Maximum leverage allowed
            risk_free_rate: Risk-free rate for Sharpe ratio calculation
            rebalance_threshold: Threshold for triggering rebalancing
            db_path: Database path for persistence
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.max_positions = max_positions
        self.max_position_size = max_position_size
        self.max_sector_allocation = max_sector_allocation
        self.max_leverage = max_leverage
        self.risk_free_rate = risk_free_rate
        self.rebalance_threshold = rebalance_threshold
        self.db_path = db_path
        
        # Portfolio state
        self.positions: Dict[str, Position] = {}
        self.closed_positions: List[Position] = []
        self.equity_curve: List[Dict] = []
        self.daily_returns: List[float] = []
        
        # Risk management
        self.margin_used = 0.0
        self.max_daily_loss = 0.05  # 5% max daily loss
        self.max_drawdown_limit = 0.20  # 20% max drawdown
        
        # Sector allocations (for diversification)
        self.sector_allocations: Dict[str, float] = {}
        self.symbol_sectors: Dict[str, str] = {}  # Symbol to sector mapping
        
        # Performance tracking
        self.peak_equity = initial_capital
        self.current_drawdown = 0.0
        self.max_drawdown = 0.0
        
        self.logger = logging.getLogger(__name__)
        self.lock = threading.Lock()
        
        # Initialize database
        self._initialize_database()
        
        # Load existing positions if any
        self._load_portfolio_state()
    
    def _initialize_database(self):
        """Initialize SQLite database for portfolio persistence"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Positions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    avg_price REAL NOT NULL,
                    current_price REAL NOT NULL,
                    entry_time TIMESTAMP NOT NULL,
                    stop_loss REAL,
                    take_profit REAL,
                    trailing_stop REAL,
                    status TEXT DEFAULT 'open',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Portfolio history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS portfolio_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP NOT NULL,
                    total_value REAL NOT NULL,
                    cash REAL NOT NULL,
                    positions_value REAL NOT NULL,
                    unrealized_pnl REAL NOT NULL,
                    realized_pnl REAL NOT NULL,
                    num_positions INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Trades table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    price REAL NOT NULL,
                    value REAL NOT NULL,
                    commission REAL NOT NULL,
                    pnl REAL,
                    trade_type TEXT NOT NULL,  -- 'open' or 'close'
                    timestamp TIMESTAMP NOT NULL,
                    strategy TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            
            self.logger.info("Portfolio database initialized")
            
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
    
    def add_position(self, 
                    symbol: str, 
                    side: str, 
                    quantity: float, 
                    price: float,
                    stop_loss: Optional[float] = None,
                    take_profit: Optional[float] = None,
                    sector: Optional[str] = None) -> bool:
        """Add new position to portfolio
        
        Args:
            symbol: Trading symbol
            side: 'long' or 'short'
            quantity: Position quantity
            price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            sector: Asset sector for diversification
            
        Returns:
            True if position added successfully
        """
        with self.lock:
            try:
                # Check position limits
                if len(self.positions) >= self.max_positions:
                    self.logger.warning("Maximum positions limit reached")
                    return False
                
                # Calculate position value
                position_value = quantity * price
                
                # Check if we have enough cash
                if position_value > self.cash:
                    self.logger.warning(f"Insufficient cash for position: {position_value} > {self.cash}")
                    return False
                
                # Check position size limit
                portfolio_value = self.get_total_value()
                if position_value > portfolio_value * self.max_position_size:
                    self.logger.warning(f"Position size exceeds limit: {position_value / portfolio_value:.2%}")
                    return False
                
                # Check sector allocation if specified
                if sector:
                    current_sector_allocation = self.sector_allocations.get(sector, 0)
                    new_sector_allocation = (current_sector_allocation + position_value) / portfolio_value
                    if new_sector_allocation > self.max_sector_allocation:
                        self.logger.warning(f"Sector allocation exceeds limit: {new_sector_allocation:.2%}")
                        return False
                    
                    self.symbol_sectors[symbol] = sector
                
                # Create position
                position = Position(
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    avg_price=price,
                    current_price=price,
                    market_value=position_value,
                    cost_basis=position_value,
                    unrealized_pnl=0.0,
                    realized_pnl=0.0,
                    entry_time=datetime.now(),
                    last_update=datetime.now(),
                    stop_loss=stop_loss,
                    take_profit=take_profit
                )
                
                # Add to portfolio
                position_key = f"{symbol}_{side}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                self.positions[position_key] = position
                
                # Update cash
                self.cash -= position_value
                
                # Update sector allocation
                if sector:
                    self.sector_allocations[sector] = self.sector_allocations.get(sector, 0) + position_value
                
                # Save to database
                self._save_position(position)
                self._record_trade(symbol, side, quantity, price, position_value, 0, 'open')
                
                self.logger.info(f"Added position: {symbol} {side} {quantity} @ {price}")
                return True
                
            except Exception as e:
                self.logger.error(f"Error adding position: {e}")
                return False
    
    def close_position(self, position_key: str, price: float, reason: str = 'manual') -> bool:
        """Close existing position
        
        Args:
            position_key: Position identifier
            price: Exit price
            reason: Reason for closing
            
        Returns:
            True if position closed successfully
        """
        with self.lock:
            try:
                if position_key not in self.positions:
                    self.logger.warning(f"Position not found: {position_key}")
                    return False
                
                position = self.positions[position_key]
                
                # Calculate exit value and P&L
                exit_value = position.quantity * price
                
                if position.side == 'long':
                    pnl = exit_value - position.cost_basis
                else:
                    pnl = position.cost_basis - exit_value
                
                # Update cash
                self.cash += exit_value
                
                # Update sector allocation
                sector = self.symbol_sectors.get(position.symbol)
                if sector:
                    self.sector_allocations[sector] = max(0, self.sector_allocations[sector] - position.cost_basis)
                
                # Update position with final values
                position.current_price = price
                position.realized_pnl = pnl
                position.unrealized_pnl = 0.0
                
                # Move to closed positions
                self.closed_positions.append(position)
                del self.positions[position_key]
                
                # Record trade
                self._record_trade(position.symbol, position.side, position.quantity, price, exit_value, 0, 'close', pnl)
                
                self.logger.info(f"Closed position: {position.symbol} {position.side} P&L: {pnl:.2f} ({reason})")
                return True
                
            except Exception as e:
                self.logger.error(f"Error closing position: {e}")
                return False
    
    def update_prices(self, price_data: Dict[str, float]):
        """Update all positions with current market prices
        
        Args:
            price_data: Dictionary mapping symbols to current prices
        """
        with self.lock:
            try:
                positions_to_close = []
                
                for position_key, position in self.positions.items():
                    if position.symbol in price_data:
                        new_price = price_data[position.symbol]
                        position.update_price(new_price)
                        
                        # Check if position should be closed
                        should_close, reason = position.should_close()
                        if should_close:
                            positions_to_close.append((position_key, new_price, reason))
                
                # Close positions that hit stop loss or take profit
                for position_key, price, reason in positions_to_close:
                    self.close_position(position_key, price, reason)
                
                # Update portfolio metrics
                self._update_portfolio_metrics()
                
            except Exception as e:
                self.logger.error(f"Error updating prices: {e}")
    
    def get_total_value(self) -> float:
        """Get total portfolio value"""
        positions_value = sum([pos.market_value for pos in self.positions.values()])
        return self.cash + positions_value
    
    def get_positions_value(self) -> float:
        """Get total value of all positions"""
        return sum([pos.market_value for pos in self.positions.values()])
    
    def get_unrealized_pnl(self) -> float:
        """Get total unrealized P&L"""
        return sum([pos.unrealized_pnl for pos in self.positions.values()])
    
    def get_realized_pnl(self) -> float:
        """Get total realized P&L"""
        return sum([pos.realized_pnl for pos in self.closed_positions])
    
    def get_portfolio_metrics(self) -> PortfolioMetrics:
        """Get comprehensive portfolio metrics"""
        total_value = self.get_total_value()
        positions_value = self.get_positions_value()
        unrealized_pnl = self.get_unrealized_pnl()
        realized_pnl = self.get_realized_pnl()
        total_pnl = unrealized_pnl + realized_pnl
        
        # Calculate returns
        total_return = (total_value - self.initial_capital) / self.initial_capital
        daily_return = self.daily_returns[-1] if self.daily_returns else 0.0
        
        # Calculate volatility and Sharpe ratio
        volatility = np.std(self.daily_returns) * np.sqrt(252) if len(self.daily_returns) > 1 else 0.0
        sharpe_ratio = (total_return - self.risk_free_rate) / volatility if volatility > 0 else 0.0
        
        # Calculate win rate and profit factor
        closed_trades = [pos for pos in self.closed_positions if pos.realized_pnl != 0]
        winning_trades = [pos for pos in closed_trades if pos.realized_pnl > 0]
        losing_trades = [pos for pos in closed_trades if pos.realized_pnl < 0]
        
        win_rate = len(winning_trades) / len(closed_trades) if closed_trades else 0.0
        
        gross_profit = sum([pos.realized_pnl for pos in winning_trades])
        gross_loss = abs(sum([pos.realized_pnl for pos in losing_trades]))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Calculate leverage and margin
        leverage = positions_value / total_value if total_value > 0 else 0.0
        available_margin = max(0, total_value * self.max_leverage - positions_value)
        
        # Calculate risk score (0-100, higher is riskier)
        risk_score = self._calculate_risk_score()
        
        return PortfolioMetrics(
            total_value=total_value,
            cash=self.cash,
            positions_value=positions_value,
            total_pnl=total_pnl,
            unrealized_pnl=unrealized_pnl,
            realized_pnl=realized_pnl,
            daily_return=daily_return,
            total_return=total_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=self.max_drawdown,
            win_rate=win_rate,
            profit_factor=profit_factor,
            num_positions=len(self.positions),
            leverage=leverage,
            margin_used=self.margin_used,
            available_margin=available_margin,
            risk_score=risk_score
        )
    
    def calculate_position_size(self, 
                               symbol: str, 
                               price: float, 
                               risk_amount: float,
                               stop_loss_price: Optional[float] = None,
                               method: str = 'fixed_risk') -> float:
        """Calculate optimal position size
        
        Args:
            symbol: Trading symbol
            price: Entry price
            risk_amount: Amount to risk (in dollars or as percentage)
            stop_loss_price: Stop loss price
            method: Position sizing method ('fixed_risk', 'kelly', 'volatility')
            
        Returns:
            Optimal position size
        """
        try:
            portfolio_value = self.get_total_value()
            
            if method == 'fixed_risk':
                if stop_loss_price:
                    risk_per_share = abs(price - stop_loss_price)
                    if risk_per_share > 0:
                        return risk_amount / risk_per_share
                
                # Fallback to percentage of portfolio
                max_position_value = portfolio_value * self.max_position_size
                return max_position_value / price
            
            elif method == 'kelly':
                # Kelly Criterion based sizing
                win_rate, avg_win, avg_loss = self._get_historical_performance(symbol)
                if avg_loss > 0:
                    kelly_fraction = win_rate - ((1 - win_rate) / (avg_win / avg_loss))
                    kelly_fraction = max(0, min(kelly_fraction, 0.25))  # Cap at 25%
                    position_value = portfolio_value * kelly_fraction
                    return position_value / price
            
            elif method == 'volatility':
                # Volatility-based sizing
                volatility = self._get_symbol_volatility(symbol)
                if volatility > 0:
                    # Inverse volatility weighting
                    base_allocation = self.max_position_size
                    vol_adjusted_allocation = base_allocation / (1 + volatility)
                    position_value = portfolio_value * vol_adjusted_allocation
                    return position_value / price
            
            # Default fallback
            max_position_value = portfolio_value * self.max_position_size
            return max_position_value / price
            
        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return 0.0
    
    def optimize_portfolio(self, 
                          expected_returns: Dict[str, float],
                          covariance_matrix: pd.DataFrame,
                          method: str = 'max_sharpe') -> Dict[str, float]:
        """Optimize portfolio allocation using modern portfolio theory
        
        Args:
            expected_returns: Expected returns for each asset
            covariance_matrix: Covariance matrix of returns
            method: Optimization method ('max_sharpe', 'min_variance', 'max_return')
            
        Returns:
            Optimal weights for each asset
        """
        try:
            symbols = list(expected_returns.keys())
            n_assets = len(symbols)
            
            if n_assets == 0:
                return {}
            
            # Convert to numpy arrays
            returns = np.array([expected_returns[symbol] for symbol in symbols])
            cov_matrix = covariance_matrix.loc[symbols, symbols].values
            
            # Constraints
            constraints = [
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},  # Weights sum to 1
            ]
            
            # Bounds (0 to max_position_size for each asset)
            bounds = [(0, self.max_position_size) for _ in range(n_assets)]
            
            # Initial guess (equal weights)
            x0 = np.array([1/n_assets] * n_assets)
            
            if method == 'max_sharpe':
                # Maximize Sharpe ratio
                def objective(weights):
                    portfolio_return = np.dot(weights, returns)
                    portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
                    if portfolio_vol == 0:
                        return -np.inf
                    return -(portfolio_return - self.risk_free_rate) / portfolio_vol
                
            elif method == 'min_variance':
                # Minimize portfolio variance
                def objective(weights):
                    return np.dot(weights.T, np.dot(cov_matrix, weights))
                
            elif method == 'max_return':
                # Maximize expected return
                def objective(weights):
                    return -np.dot(weights, returns)
            
            # Optimize
            result = minimize(objective, x0, method='SLSQP', bounds=bounds, constraints=constraints)
            
            if result.success:
                optimal_weights = dict(zip(symbols, result.x))
                # Filter out very small weights
                optimal_weights = {k: v for k, v in optimal_weights.items() if v > 0.01}
                return optimal_weights
            else:
                self.logger.warning("Portfolio optimization failed")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error in portfolio optimization: {e}")
            return {}
    
    def rebalance_portfolio(self, target_weights: Dict[str, float], current_prices: Dict[str, float]):
        """Rebalance portfolio to target weights
        
        Args:
            target_weights: Target allocation weights
            current_prices: Current market prices
        """
        try:
            portfolio_value = self.get_total_value()
            current_weights = self._get_current_weights()
            
            # Calculate required trades
            trades_needed = []
            
            for symbol, target_weight in target_weights.items():
                if symbol not in current_prices:
                    continue
                
                current_weight = current_weights.get(symbol, 0)
                weight_diff = target_weight - current_weight
                
                # Only rebalance if difference exceeds threshold
                if abs(weight_diff) > self.rebalance_threshold:
                    target_value = portfolio_value * target_weight
                    current_value = portfolio_value * current_weight
                    trade_value = target_value - current_value
                    
                    if trade_value > 0:  # Buy
                        quantity = trade_value / current_prices[symbol]
                        trades_needed.append((symbol, 'buy', quantity, current_prices[symbol]))
                    else:  # Sell
                        quantity = abs(trade_value) / current_prices[symbol]
                        trades_needed.append((symbol, 'sell', quantity, current_prices[symbol]))
            
            # Execute trades
            for symbol, action, quantity, price in trades_needed:
                if action == 'buy':
                    self.add_position(symbol, 'long', quantity, price)
                else:
                    # Find and close positions to sell
                    self._reduce_position(symbol, quantity, price)
            
            self.logger.info(f"Rebalanced portfolio with {len(trades_needed)} trades")
            
        except Exception as e:
            self.logger.error(f"Error rebalancing portfolio: {e}")
    
    def _update_portfolio_metrics(self):
        """Update portfolio performance metrics"""
        try:
            current_value = self.get_total_value()
            
            # Update equity curve
            self.equity_curve.append({
                'timestamp': datetime.now(),
                'total_value': current_value,
                'cash': self.cash,
                'positions_value': self.get_positions_value(),
                'unrealized_pnl': self.get_unrealized_pnl(),
                'realized_pnl': self.get_realized_pnl()
            })
            
            # Calculate daily return
            if len(self.equity_curve) > 1:
                prev_value = self.equity_curve[-2]['total_value']
                daily_return = (current_value - prev_value) / prev_value
                self.daily_returns.append(daily_return)
            
            # Update drawdown
            if current_value > self.peak_equity:
                self.peak_equity = current_value
                self.current_drawdown = 0.0
            else:
                self.current_drawdown = (self.peak_equity - current_value) / self.peak_equity
                if self.current_drawdown > self.max_drawdown:
                    self.max_drawdown = self.current_drawdown
            
            # Save to database
            self._save_portfolio_snapshot()
            
        except Exception as e:
            self.logger.error(f"Error updating portfolio metrics: {e}")
    
    def _calculate_risk_score(self) -> float:
        """Calculate portfolio risk score (0-100)"""
        try:
            risk_factors = []
            
            # Concentration risk
            if self.positions:
                position_weights = [pos.market_value / self.get_total_value() for pos in self.positions.values()]
                max_weight = max(position_weights)
                concentration_risk = min(max_weight * 100, 50)  # Cap at 50
                risk_factors.append(concentration_risk)
            
            # Leverage risk
            leverage = self.get_positions_value() / self.get_total_value() if self.get_total_value() > 0 else 0
            leverage_risk = min(leverage * 25, 30)  # Cap at 30
            risk_factors.append(leverage_risk)
            
            # Drawdown risk
            drawdown_risk = self.current_drawdown * 100
            risk_factors.append(drawdown_risk)
            
            # Volatility risk
            if len(self.daily_returns) > 10:
                volatility = np.std(self.daily_returns) * np.sqrt(252)
                volatility_risk = min(volatility * 50, 20)  # Cap at 20
                risk_factors.append(volatility_risk)
            
            return min(sum(risk_factors), 100)
            
        except Exception as e:
            self.logger.error(f"Error calculating risk score: {e}")
            return 50  # Default moderate risk
    
    def _get_current_weights(self) -> Dict[str, float]:
        """Get current portfolio weights"""
        total_value = self.get_total_value()
        if total_value == 0:
            return {}
        
        weights = {}
        for position in self.positions.values():
            symbol = position.symbol
            if symbol in weights:
                weights[symbol] += position.market_value / total_value
            else:
                weights[symbol] = position.market_value / total_value
        
        return weights
    
    def _get_historical_performance(self, symbol: str) -> Tuple[float, float, float]:
        """Get historical performance metrics for a symbol"""
        symbol_trades = [pos for pos in self.closed_positions if pos.symbol == symbol and pos.realized_pnl != 0]
        
        if not symbol_trades:
            return 0.5, 0.0, 0.0  # Default values
        
        winning_trades = [pos for pos in symbol_trades if pos.realized_pnl > 0]
        losing_trades = [pos for pos in symbol_trades if pos.realized_pnl < 0]
        
        win_rate = len(winning_trades) / len(symbol_trades)
        avg_win = np.mean([pos.realized_pnl for pos in winning_trades]) if winning_trades else 0.0
        avg_loss = abs(np.mean([pos.realized_pnl for pos in losing_trades])) if losing_trades else 0.0
        
        return win_rate, avg_win, avg_loss
    
    def _get_symbol_volatility(self, symbol: str) -> float:
        """Get historical volatility for a symbol"""
        # This would typically fetch historical price data and calculate volatility
        # For now, return a default value
        return 0.2  # 20% annual volatility
    
    def _reduce_position(self, symbol: str, quantity: float, price: float):
        """Reduce position size by selling specified quantity"""
        remaining_quantity = quantity
        positions_to_close = []
        
        for position_key, position in self.positions.items():
            if position.symbol == symbol and position.side == 'long' and remaining_quantity > 0:
                if position.quantity <= remaining_quantity:
                    # Close entire position
                    positions_to_close.append(position_key)
                    remaining_quantity -= position.quantity
                else:
                    # Partially close position
                    close_quantity = remaining_quantity
                    close_value = close_quantity * price
                    
                    # Calculate partial P&L
                    partial_pnl = close_value - (position.cost_basis * close_quantity / position.quantity)
                    
                    # Update position
                    position.quantity -= close_quantity
                    position.cost_basis -= (position.cost_basis * close_quantity / (position.quantity + close_quantity))
                    position.market_value = position.quantity * price
                    position.realized_pnl += partial_pnl
                    
                    # Update cash
                    self.cash += close_value
                    
                    remaining_quantity = 0
        
        # Close full positions
        for position_key in positions_to_close:
            self.close_position(position_key, price, 'rebalance')
    
    def _save_position(self, position: Position):
        """Save position to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO positions 
                (symbol, side, quantity, avg_price, current_price, entry_time, stop_loss, take_profit, trailing_stop)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                position.symbol, position.side, position.quantity, position.avg_price,
                position.current_price, position.entry_time, position.stop_loss,
                position.take_profit, position.trailing_stop
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error saving position: {e}")
    
    def _record_trade(self, symbol: str, side: str, quantity: float, price: float, 
                     value: float, commission: float, trade_type: str, pnl: float = None):
        """Record trade in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO trades 
                (symbol, side, quantity, price, value, commission, pnl, trade_type, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                symbol, side, quantity, price, value, commission, pnl, trade_type, datetime.now()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error recording trade: {e}")
    
    def _save_portfolio_snapshot(self):
        """Save portfolio snapshot to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            metrics = self.get_portfolio_metrics()
            
            cursor.execute('''
                INSERT INTO portfolio_history 
                (timestamp, total_value, cash, positions_value, unrealized_pnl, realized_pnl, num_positions)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now(), metrics.total_value, metrics.cash, metrics.positions_value,
                metrics.unrealized_pnl, metrics.realized_pnl, metrics.num_positions
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error saving portfolio snapshot: {e}")
    
    def _load_portfolio_state(self):
        """Load existing portfolio state from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Load open positions
            cursor.execute('''
                SELECT symbol, side, quantity, avg_price, current_price, entry_time, 
                       stop_loss, take_profit, trailing_stop
                FROM positions 
                WHERE status = 'open'
            ''')
            
            for row in cursor.fetchall():
                symbol, side, quantity, avg_price, current_price, entry_time, stop_loss, take_profit, trailing_stop = row
                
                position = Position(
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    avg_price=avg_price,
                    current_price=current_price,
                    market_value=quantity * current_price,
                    cost_basis=quantity * avg_price,
                    unrealized_pnl=(quantity * current_price) - (quantity * avg_price) if side == 'long' else (quantity * avg_price) - (quantity * current_price),
                    realized_pnl=0.0,
                    entry_time=datetime.fromisoformat(entry_time),
                    last_update=datetime.now(),
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    trailing_stop=trailing_stop
                )
                
                position_key = f"{symbol}_{side}_{entry_time}"
                self.positions[position_key] = position
            
            conn.close()
            self.logger.info(f"Loaded {len(self.positions)} existing positions")
            
        except Exception as e:
            self.logger.error(f"Error loading portfolio state: {e}")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        metrics = self.get_portfolio_metrics()
        
        # Calculate additional metrics
        total_trades = len(self.closed_positions)
        winning_trades = len([pos for pos in self.closed_positions if pos.realized_pnl > 0])
        losing_trades = total_trades - winning_trades
        
        avg_win = np.mean([pos.realized_pnl for pos in self.closed_positions if pos.realized_pnl > 0]) if winning_trades > 0 else 0
        avg_loss = np.mean([pos.realized_pnl for pos in self.closed_positions if pos.realized_pnl < 0]) if losing_trades > 0 else 0
        
        # Best and worst trades
        best_trade = max(self.closed_positions, key=lambda x: x.realized_pnl) if self.closed_positions else None
        worst_trade = min(self.closed_positions, key=lambda x: x.realized_pnl) if self.closed_positions else None
        
        return {
            'portfolio_metrics': asdict(metrics),
            'trade_statistics': {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': metrics.win_rate,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'profit_factor': metrics.profit_factor,
                'best_trade': {
                    'symbol': best_trade.symbol,
                    'pnl': best_trade.realized_pnl,
                    'return_pct': best_trade.get_return_pct()
                } if best_trade else None,
                'worst_trade': {
                    'symbol': worst_trade.symbol,
                    'pnl': worst_trade.realized_pnl,
                    'return_pct': worst_trade.get_return_pct()
                } if worst_trade else None
            },
            'risk_metrics': {
                'max_drawdown': metrics.max_drawdown,
                'current_drawdown': self.current_drawdown,
                'volatility': metrics.volatility,
                'sharpe_ratio': metrics.sharpe_ratio,
                'risk_score': metrics.risk_score
            },
            'allocation': {
                'cash_pct': metrics.cash / metrics.total_value if metrics.total_value > 0 else 0,
                'positions_pct': metrics.positions_value / metrics.total_value if metrics.total_value > 0 else 0,
                'leverage': metrics.leverage,
                'num_positions': metrics.num_positions
            }
        }
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            # Close all positions at current market prices (if needed)
            # Save final state to database
            self._save_portfolio_snapshot()
            self.logger.info("Portfolio manager cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")