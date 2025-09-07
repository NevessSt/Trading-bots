#!/usr/bin/env python3
"""
Advanced Risk Management System
Handles stop-loss, take-profit, trailing stops, and position sizing
"""

import logging
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import numpy as np

class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    TRAILING_STOP = "trailing_stop"

class PositionSide(Enum):
    LONG = "long"
    SHORT = "short"

@dataclass
class RiskParameters:
    """Risk management parameters for trading"""
    max_position_size: float = 0.02  # 2% of portfolio per trade
    stop_loss_percentage: float = 0.02  # 2% stop loss
    take_profit_percentage: float = 0.04  # 4% take profit (2:1 ratio)
    trailing_stop_percentage: float = 0.015  # 1.5% trailing stop
    max_daily_loss: float = 0.05  # 5% max daily loss
    max_drawdown: float = 0.10  # 10% max drawdown
    risk_reward_ratio: float = 2.0  # Minimum risk/reward ratio
    max_open_positions: int = 5  # Maximum concurrent positions
    volatility_adjustment: bool = True  # Adjust position size based on volatility

@dataclass
class Position:
    """Trading position with risk management"""
    symbol: str
    side: PositionSide
    entry_price: float
    quantity: float
    timestamp: datetime
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    trailing_stop: Optional[float] = None
    highest_price: Optional[float] = None  # For trailing stop
    lowest_price: Optional[float] = None   # For trailing stop (short positions)
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    fees: float = 0.0
    status: str = "open"

class AdvancedRiskManager:
    """Advanced Risk Management System for Trading Bot"""
    
    def __init__(self, risk_params: RiskParameters = None):
        self.logger = logging.getLogger(__name__)
        self.risk_params = risk_params or RiskParameters()
        self.positions: Dict[str, Position] = {}
        self.daily_pnl = 0.0
        self.total_pnl = 0.0
        self.max_drawdown_reached = 0.0
        self.daily_trades = 0
        self.last_reset_date = datetime.now().date()
        
    def calculate_position_size(self, 
                              symbol: str, 
                              entry_price: float, 
                              stop_loss_price: float, 
                              account_balance: float,
                              volatility: float = None) -> float:
        """
        Calculate optimal position size based on risk parameters
        
        Args:
            symbol: Trading symbol
            entry_price: Entry price for the position
            stop_loss_price: Stop loss price
            account_balance: Current account balance
            volatility: Asset volatility (optional)
            
        Returns:
            Optimal position size
        """
        try:
            # Calculate risk per share
            risk_per_share = abs(entry_price - stop_loss_price)
            
            # Maximum risk amount (percentage of balance)
            max_risk_amount = account_balance * self.risk_params.max_position_size
            
            # Base position size
            base_position_size = max_risk_amount / risk_per_share
            
            # Adjust for volatility if provided
            if volatility and self.risk_params.volatility_adjustment:
                # Reduce position size for high volatility assets
                volatility_adjustment = 1 / (1 + volatility)
                base_position_size *= volatility_adjustment
                
            # Ensure minimum position size
            min_position_size = account_balance * 0.001  # 0.1% minimum
            position_size = max(base_position_size, min_position_size)
            
            # Cap at maximum position size
            max_position_value = account_balance * self.risk_params.max_position_size
            max_quantity = max_position_value / entry_price
            position_size = min(position_size, max_quantity)
            
            self.logger.info(f"Calculated position size for {symbol}: {position_size:.6f}")
            return round(position_size, 6)
            
        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return 0.0
    
    def set_stop_loss(self, symbol: str, entry_price: float, side: PositionSide) -> float:
        """
        Calculate stop loss price based on risk parameters
        
        Args:
            symbol: Trading symbol
            entry_price: Entry price
            side: Position side (long/short)
            
        Returns:
            Stop loss price
        """
        try:
            if side == PositionSide.LONG:
                stop_loss = entry_price * (1 - self.risk_params.stop_loss_percentage)
            else:  # SHORT
                stop_loss = entry_price * (1 + self.risk_params.stop_loss_percentage)
                
            self.logger.info(f"Set stop loss for {symbol} {side.value}: {stop_loss:.6f}")
            return round(stop_loss, 6)
            
        except Exception as e:
            self.logger.error(f"Error setting stop loss: {e}")
            return entry_price
    
    def set_take_profit(self, symbol: str, entry_price: float, side: PositionSide) -> float:
        """
        Calculate take profit price based on risk parameters
        
        Args:
            symbol: Trading symbol
            entry_price: Entry price
            side: Position side (long/short)
            
        Returns:
            Take profit price
        """
        try:
            if side == PositionSide.LONG:
                take_profit = entry_price * (1 + self.risk_params.take_profit_percentage)
            else:  # SHORT
                take_profit = entry_price * (1 - self.risk_params.take_profit_percentage)
                
            self.logger.info(f"Set take profit for {symbol} {side.value}: {take_profit:.6f}")
            return round(take_profit, 6)
            
        except Exception as e:
            self.logger.error(f"Error setting take profit: {e}")
            return entry_price
    
    def update_trailing_stop(self, symbol: str, current_price: float) -> Optional[float]:
        """
        Update trailing stop for a position
        
        Args:
            symbol: Trading symbol
            current_price: Current market price
            
        Returns:
            New trailing stop price or None
        """
        try:
            if symbol not in self.positions:
                return None
                
            position = self.positions[symbol]
            
            if position.side == PositionSide.LONG:
                # Update highest price
                if position.highest_price is None or current_price > position.highest_price:
                    position.highest_price = current_price
                    
                # Calculate new trailing stop
                new_trailing_stop = position.highest_price * (1 - self.risk_params.trailing_stop_percentage)
                
                # Only update if new stop is higher (for long positions)
                if position.trailing_stop is None or new_trailing_stop > position.trailing_stop:
                    position.trailing_stop = round(new_trailing_stop, 6)
                    self.logger.info(f"Updated trailing stop for {symbol}: {position.trailing_stop}")
                    return position.trailing_stop
                    
            else:  # SHORT position
                # Update lowest price
                if position.lowest_price is None or current_price < position.lowest_price:
                    position.lowest_price = current_price
                    
                # Calculate new trailing stop
                new_trailing_stop = position.lowest_price * (1 + self.risk_params.trailing_stop_percentage)
                
                # Only update if new stop is lower (for short positions)
                if position.trailing_stop is None or new_trailing_stop < position.trailing_stop:
                    position.trailing_stop = round(new_trailing_stop, 6)
                    self.logger.info(f"Updated trailing stop for {symbol}: {position.trailing_stop}")
                    return position.trailing_stop
                    
            return position.trailing_stop
            
        except Exception as e:
            self.logger.error(f"Error updating trailing stop: {e}")
            return None
    
    def check_risk_limits(self, account_balance: float) -> Dict[str, bool]:
        """
        Check if current positions violate risk limits
        
        Args:
            account_balance: Current account balance
            
        Returns:
            Dictionary of risk limit checks
        """
        try:
            # Reset daily counters if new day
            current_date = datetime.now().date()
            if current_date != self.last_reset_date:
                self.daily_pnl = 0.0
                self.daily_trades = 0
                self.last_reset_date = current_date
            
            checks = {
                'max_positions': len(self.positions) < self.risk_params.max_open_positions,
                'daily_loss_limit': self.daily_pnl > -(account_balance * self.risk_params.max_daily_loss),
                'max_drawdown_limit': self.max_drawdown_reached < self.risk_params.max_drawdown,
                'account_balance_positive': account_balance > 0
            }
            
            # Log violations
            for check, passed in checks.items():
                if not passed:
                    self.logger.warning(f"Risk limit violation: {check}")
                    
            return checks
            
        except Exception as e:
            self.logger.error(f"Error checking risk limits: {e}")
            return {'error': False}
    
    def open_position(self, 
                     symbol: str, 
                     side: PositionSide, 
                     entry_price: float, 
                     quantity: float) -> bool:
        """
        Open a new position with risk management
        
        Args:
            symbol: Trading symbol
            side: Position side
            entry_price: Entry price
            quantity: Position quantity
            
        Returns:
            True if position opened successfully
        """
        try:
            # Create position
            position = Position(
                symbol=symbol,
                side=side,
                entry_price=entry_price,
                quantity=quantity,
                timestamp=datetime.now()
            )
            
            # Set stop loss and take profit
            position.stop_loss = self.set_stop_loss(symbol, entry_price, side)
            position.take_profit = self.set_take_profit(symbol, entry_price, side)
            
            # Initialize trailing stop
            if side == PositionSide.LONG:
                position.highest_price = entry_price
            else:
                position.lowest_price = entry_price
                
            position.trailing_stop = self.set_stop_loss(symbol, entry_price, side)
            
            # Store position
            self.positions[symbol] = position
            self.daily_trades += 1
            
            self.logger.info(f"Opened {side.value} position for {symbol}: {quantity} @ {entry_price}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error opening position: {e}")
            return False
    
    def close_position(self, symbol: str, exit_price: float, reason: str = "manual") -> Optional[float]:
        """
        Close a position and calculate PnL
        
        Args:
            symbol: Trading symbol
            exit_price: Exit price
            reason: Reason for closing
            
        Returns:
            Realized PnL or None
        """
        try:
            if symbol not in self.positions:
                self.logger.warning(f"No position found for {symbol}")
                return None
                
            position = self.positions[symbol]
            
            # Calculate PnL
            if position.side == PositionSide.LONG:
                pnl = (exit_price - position.entry_price) * position.quantity
            else:  # SHORT
                pnl = (position.entry_price - exit_price) * position.quantity
                
            # Update totals
            position.realized_pnl = pnl
            position.status = "closed"
            self.daily_pnl += pnl
            self.total_pnl += pnl
            
            # Update drawdown
            if pnl < 0:
                self.max_drawdown_reached = max(self.max_drawdown_reached, abs(pnl))
            
            self.logger.info(f"Closed {position.side.value} position for {symbol}: PnL = {pnl:.6f} ({reason})")
            
            # Remove from active positions
            del self.positions[symbol]
            
            return pnl
            
        except Exception as e:
            self.logger.error(f"Error closing position: {e}")
            return None
    
    def should_close_position(self, symbol: str, current_price: float) -> Tuple[bool, str]:
        """
        Check if a position should be closed based on risk management rules
        
        Args:
            symbol: Trading symbol
            current_price: Current market price
            
        Returns:
            Tuple of (should_close, reason)
        """
        try:
            if symbol not in self.positions:
                return False, "no_position"
                
            position = self.positions[symbol]
            
            # Update trailing stop
            self.update_trailing_stop(symbol, current_price)
            
            if position.side == PositionSide.LONG:
                # Check stop loss
                if current_price <= position.stop_loss:
                    return True, "stop_loss"
                    
                # Check take profit
                if current_price >= position.take_profit:
                    return True, "take_profit"
                    
                # Check trailing stop
                if position.trailing_stop and current_price <= position.trailing_stop:
                    return True, "trailing_stop"
                    
            else:  # SHORT position
                # Check stop loss
                if current_price >= position.stop_loss:
                    return True, "stop_loss"
                    
                # Check take profit
                if current_price <= position.take_profit:
                    return True, "take_profit"
                    
                # Check trailing stop
                if position.trailing_stop and current_price >= position.trailing_stop:
                    return True, "trailing_stop"
            
            return False, "hold"
            
        except Exception as e:
            self.logger.error(f"Error checking position closure: {e}")
            return False, "error"
    
    def get_position_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a position
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Position information dictionary
        """
        try:
            if symbol not in self.positions:
                return None
                
            position = self.positions[symbol]
            
            return {
                'symbol': position.symbol,
                'side': position.side.value,
                'entry_price': position.entry_price,
                'quantity': position.quantity,
                'stop_loss': position.stop_loss,
                'take_profit': position.take_profit,
                'trailing_stop': position.trailing_stop,
                'unrealized_pnl': position.unrealized_pnl,
                'timestamp': position.timestamp.isoformat(),
                'status': position.status
            }
            
        except Exception as e:
            self.logger.error(f"Error getting position info: {e}")
            return None
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive risk management summary
        
        Returns:
            Risk summary dictionary
        """
        try:
            return {
                'active_positions': len(self.positions),
                'daily_pnl': self.daily_pnl,
                'total_pnl': self.total_pnl,
                'max_drawdown': self.max_drawdown_reached,
                'daily_trades': self.daily_trades,
                'risk_parameters': {
                    'max_position_size': self.risk_params.max_position_size,
                    'stop_loss_percentage': self.risk_params.stop_loss_percentage,
                    'take_profit_percentage': self.risk_params.take_profit_percentage,
                    'trailing_stop_percentage': self.risk_params.trailing_stop_percentage,
                    'max_daily_loss': self.risk_params.max_daily_loss,
                    'max_drawdown': self.risk_params.max_drawdown,
                    'risk_reward_ratio': self.risk_params.risk_reward_ratio,
                    'max_open_positions': self.risk_params.max_open_positions
                },
                'positions': [self.get_position_info(symbol) for symbol in self.positions.keys()]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting risk summary: {e}")
            return {'error': str(e)}

# Example usage and testing
if __name__ == "__main__":
    # Initialize risk manager
    risk_params = RiskParameters(
        max_position_size=0.02,  # 2% per trade
        stop_loss_percentage=0.02,  # 2% stop loss
        take_profit_percentage=0.04,  # 4% take profit
        trailing_stop_percentage=0.015  # 1.5% trailing stop
    )
    
    risk_manager = AdvancedRiskManager(risk_params)
    
    # Example: Open a long position
    account_balance = 10000.0
    entry_price = 50000.0
    stop_loss_price = 49000.0
    
    # Calculate position size
    position_size = risk_manager.calculate_position_size(
        "BTCUSDT", entry_price, stop_loss_price, account_balance
    )
    
    print(f"Recommended position size: {position_size}")
    
    # Open position
    risk_manager.open_position("BTCUSDT", PositionSide.LONG, entry_price, position_size)
    
    # Check position status
    should_close, reason = risk_manager.should_close_position("BTCUSDT", 48500.0)
    print(f"Should close: {should_close}, Reason: {reason}")
    
    # Get risk summary
    summary = risk_manager.get_risk_summary()
    print(f"Risk Summary: {summary}")