"""Risk Management Module

This module provides comprehensive risk management functionality including:
- Position sizing calculations
- Stop-loss and take-profit management
- Portfolio risk assessment
- Maximum drawdown protection
- Risk-adjusted position sizing
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    """Risk levels for different trading scenarios"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class RiskMetrics:
    """Container for risk assessment metrics"""
    portfolio_risk: float
    position_risk: float
    daily_pnl: float
    max_drawdown: float
    risk_level: RiskLevel
    recommendations: List[str]

class RiskManager:
    """Advanced Risk Management System
    
    Provides comprehensive risk management including position sizing,
    stop-loss management, portfolio risk assessment, and drawdown protection.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the risk manager with configuration
        
        Args:
            config: Risk management configuration including:
                   - max_position_size: Maximum position size as % of portfolio
                   - max_daily_loss: Maximum daily loss as % of portfolio
                   - stop_loss_percentage: Default stop loss percentage
                   - take_profit_percentage: Default take profit percentage
                   - max_drawdown: Maximum allowed drawdown
        """
        self.config = config
        self.daily_pnl = 0.0
        self.max_drawdown_reached = 0.0
        self.trade_history = []
        self.active_positions = {}
        
        # Risk parameters
        self.max_position_size = config.get('max_position_size', 0.1)  # 10%
        self.max_daily_loss = config.get('max_daily_loss', 0.05)  # 5%
        self.stop_loss_percentage = config.get('stop_loss_percentage', 0.02)  # 2%
        self.take_profit_percentage = config.get('take_profit_percentage', 0.04)  # 4%
        self.max_drawdown = config.get('max_drawdown', 0.15)  # 15%
        
        logger.info("Risk Manager initialized with parameters:")
        logger.info(f"  Max position size: {self.max_position_size*100}%")
        logger.info(f"  Max daily loss: {self.max_daily_loss*100}%")
        logger.info(f"  Default stop loss: {self.stop_loss_percentage*100}%")
        logger.info(f"  Default take profit: {self.take_profit_percentage*100}%")
    
    async def check_trade_risk(self, signal) -> Dict[str, Any]:
        """
        Comprehensive risk assessment for a trading signal
        
        Args:
            signal: TradeSignal object to assess
            
        Returns:
            Dictionary with approval status and risk assessment
        """
        try:
            logger.info(f"Assessing risk for {signal.action} {signal.quantity} {signal.symbol}")
            
            # Get current portfolio metrics
            portfolio_value = await self._get_portfolio_value()
            
            # Calculate position size risk
            position_risk = self._calculate_position_risk(signal, portfolio_value)
            
            # Check daily loss limits
            daily_loss_check = self._check_daily_loss_limit()
            
            # Check maximum drawdown
            drawdown_check = self._check_drawdown_limit()
            
            # Check position concentration
            concentration_check = self._check_position_concentration(signal, portfolio_value)
            
            # Aggregate all risk checks
            risk_checks = {
                'position_risk': position_risk,
                'daily_loss': daily_loss_check,
                'drawdown': drawdown_check,
                'concentration': concentration_check
            }
            
            # Determine overall approval
            approved = all(check['approved'] for check in risk_checks.values())
            
            # Compile reasons if rejected
            rejection_reasons = []
            for check_name, check_result in risk_checks.items():
                if not check_result['approved']:
                    rejection_reasons.append(f"{check_name}: {check_result['reason']}")
            
            result = {
                'approved': approved,
                'reason': '; '.join(rejection_reasons) if rejection_reasons else 'Trade approved',
                'risk_checks': risk_checks,
                'recommended_position_size': self._calculate_optimal_position_size(signal, portfolio_value)
            }
            
            logger.info(f"Risk assessment result: {'APPROVED' if approved else 'REJECTED'}")
            if not approved:
                logger.warning(f"Rejection reasons: {result['reason']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in risk assessment: {e}")
            return {
                'approved': False,
                'reason': f'Risk assessment error: {str(e)}',
                'risk_checks': {},
                'recommended_position_size': 0.0
            }
    
    def _calculate_position_risk(self, signal, portfolio_value: float) -> Dict[str, Any]:
        """
        Calculate position-specific risk metrics
        
        Args:
            signal: Trading signal
            portfolio_value: Current portfolio value
            
        Returns:
            Dictionary with position risk assessment
        """
        try:
            # Calculate position value
            position_value = signal.quantity * (signal.price or 0)
            position_percentage = position_value / portfolio_value if portfolio_value > 0 else 0
            
            # Check if position size exceeds limits
            approved = position_percentage <= self.max_position_size
            
            return {
                'approved': approved,
                'reason': f'Position size {position_percentage*100:.2f}% exceeds limit {self.max_position_size*100}%' if not approved else 'Position size within limits',
                'position_value': position_value,
                'position_percentage': position_percentage,
                'max_allowed': self.max_position_size
            }
            
        except Exception as e:
            logger.error(f"Error calculating position risk: {e}")
            return {
                'approved': False,
                'reason': f'Position risk calculation error: {str(e)}',
                'position_value': 0,
                'position_percentage': 0,
                'max_allowed': self.max_position_size
            }
    
    def _check_daily_loss_limit(self) -> Dict[str, Any]:
        """
        Check if daily loss limit would be exceeded
        
        Returns:
            Dictionary with daily loss check results
        """
        try:
            daily_loss_percentage = abs(self.daily_pnl) if self.daily_pnl < 0 else 0
            approved = daily_loss_percentage <= self.max_daily_loss
            
            return {
                'approved': approved,
                'reason': f'Daily loss {daily_loss_percentage*100:.2f}% exceeds limit {self.max_daily_loss*100}%' if not approved else 'Daily loss within limits',
                'current_daily_pnl': self.daily_pnl,
                'daily_loss_percentage': daily_loss_percentage,
                'max_allowed': self.max_daily_loss
            }
            
        except Exception as e:
            logger.error(f"Error checking daily loss limit: {e}")
            return {
                'approved': False,
                'reason': f'Daily loss check error: {str(e)}',
                'current_daily_pnl': self.daily_pnl,
                'daily_loss_percentage': 0,
                'max_allowed': self.max_daily_loss
            }
    
    def _check_drawdown_limit(self) -> Dict[str, Any]:
        """
        Check if maximum drawdown limit would be exceeded
        
        Returns:
            Dictionary with drawdown check results
        """
        try:
            approved = self.max_drawdown_reached <= self.max_drawdown
            
            return {
                'approved': approved,
                'reason': f'Max drawdown {self.max_drawdown_reached*100:.2f}% exceeds limit {self.max_drawdown*100}%' if not approved else 'Drawdown within limits',
                'current_drawdown': self.max_drawdown_reached,
                'max_allowed': self.max_drawdown
            }
            
        except Exception as e:
            logger.error(f"Error checking drawdown limit: {e}")
            return {
                'approved': False,
                'reason': f'Drawdown check error: {str(e)}',
                'current_drawdown': self.max_drawdown_reached,
                'max_allowed': self.max_drawdown
            }
    
    def _check_position_concentration(self, signal, portfolio_value: float) -> Dict[str, Any]:
        """
        Check for position concentration risk
        
        Args:
            signal: Trading signal
            portfolio_value: Current portfolio value
            
        Returns:
            Dictionary with concentration check results
        """
        try:
            # Get current position in the same symbol
            current_position = self.active_positions.get(signal.symbol, 0)
            new_position_value = signal.quantity * (signal.price or 0)
            
            if signal.action == 'BUY':
                total_position_value = current_position + new_position_value
            else:  # SELL
                total_position_value = max(0, current_position - new_position_value)
            
            concentration_percentage = total_position_value / portfolio_value if portfolio_value > 0 else 0
            
            # Allow up to 20% concentration in a single symbol
            max_concentration = 0.20
            approved = concentration_percentage <= max_concentration
            
            return {
                'approved': approved,
                'reason': f'Symbol concentration {concentration_percentage*100:.2f}% exceeds limit {max_concentration*100}%' if not approved else 'Concentration within limits',
                'current_position': current_position,
                'new_position_value': new_position_value,
                'total_position_value': total_position_value,
                'concentration_percentage': concentration_percentage,
                'max_allowed': max_concentration
            }
            
        except Exception as e:
            logger.error(f"Error checking position concentration: {e}")
            return {
                'approved': False,
                'reason': f'Concentration check error: {str(e)}',
                'concentration_percentage': 0,
                'max_allowed': 0.20
            }
    
    def _calculate_optimal_position_size(self, signal, portfolio_value: float) -> float:
        """
        Calculate optimal position size based on risk parameters
        
        Args:
            signal: Trading signal
            portfolio_value: Current portfolio value
            
        Returns:
            Recommended position size
        """
        try:
            # Use Kelly Criterion or fixed percentage approach
            # For simplicity, using fixed percentage with risk adjustment
            
            base_position_percentage = self.max_position_size * 0.5  # Conservative approach
            
            # Adjust based on signal confidence if available
            if hasattr(signal, 'confidence') and signal.confidence:
                confidence_multiplier = min(signal.confidence, 1.0)
                base_position_percentage *= confidence_multiplier
            
            # Calculate position size in base currency
            optimal_position_value = portfolio_value * base_position_percentage
            
            # Convert to quantity if price is available
            if signal.price and signal.price > 0:
                optimal_quantity = optimal_position_value / signal.price
                return min(optimal_quantity, signal.quantity)  # Don't exceed requested quantity
            
            return signal.quantity * 0.5  # Conservative fallback
            
        except Exception as e:
            logger.error(f"Error calculating optimal position size: {e}")
            return signal.quantity * 0.1  # Very conservative fallback
    
    async def _get_portfolio_value(self) -> float:
        """
        Get current portfolio value
        
        Returns:
            Current portfolio value in base currency
        """
        try:
            # This would typically interface with portfolio manager
            # For now, return a placeholder value
            return 10000.0  # $10,000 default portfolio
            
        except Exception as e:
            logger.error(f"Error getting portfolio value: {e}")
            return 10000.0  # Fallback value
    
    def calculate_stop_loss(self, entry_price: float, action: str, custom_percentage: Optional[float] = None) -> float:
        """
        Calculate stop-loss price
        
        Args:
            entry_price: Entry price for the position
            action: 'BUY' or 'SELL'
            custom_percentage: Custom stop-loss percentage (optional)
            
        Returns:
            Stop-loss price
        """
        try:
            stop_loss_pct = custom_percentage or self.stop_loss_percentage
            
            if action == 'BUY':
                # For long positions, stop loss is below entry price
                stop_loss = entry_price * (1 - stop_loss_pct)
            else:  # SELL
                # For short positions, stop loss is above entry price
                stop_loss = entry_price * (1 + stop_loss_pct)
            
            logger.info(f"Calculated stop loss: {stop_loss:.6f} for {action} at {entry_price:.6f}")
            return stop_loss
            
        except Exception as e:
            logger.error(f"Error calculating stop loss: {e}")
            return entry_price  # Fallback to entry price
    
    def calculate_take_profit(self, entry_price: float, action: str, custom_percentage: Optional[float] = None) -> float:
        """
        Calculate take-profit price
        
        Args:
            entry_price: Entry price for the position
            action: 'BUY' or 'SELL'
            custom_percentage: Custom take-profit percentage (optional)
            
        Returns:
            Take-profit price
        """
        try:
            take_profit_pct = custom_percentage or self.take_profit_percentage
            
            if action == 'BUY':
                # For long positions, take profit is above entry price
                take_profit = entry_price * (1 + take_profit_pct)
            else:  # SELL
                # For short positions, take profit is below entry price
                take_profit = entry_price * (1 - take_profit_pct)
            
            logger.info(f"Calculated take profit: {take_profit:.6f} for {action} at {entry_price:.6f}")
            return take_profit
            
        except Exception as e:
            logger.error(f"Error calculating take profit: {e}")
            return entry_price  # Fallback to entry price
    
    def update_daily_pnl(self, pnl_change: float):
        """
        Update daily P&L tracking
        
        Args:
            pnl_change: Change in P&L (positive for profit, negative for loss)
        """
        self.daily_pnl += pnl_change
        logger.info(f"Daily P&L updated: {self.daily_pnl:.2f}")
    
    def update_position(self, symbol: str, position_value: float):
        """
        Update active position tracking
        
        Args:
            symbol: Trading symbol
            position_value: Current position value
        """
        self.active_positions[symbol] = position_value
        logger.info(f"Position updated for {symbol}: {position_value:.2f}")
    
    def get_risk_metrics(self) -> RiskMetrics:
        """
        Get comprehensive risk metrics
        
        Returns:
            RiskMetrics object with current risk assessment
        """
        try:
            # Calculate portfolio risk
            total_position_value = sum(self.active_positions.values())
            portfolio_value = asyncio.run(self._get_portfolio_value())
            portfolio_risk = total_position_value / portfolio_value if portfolio_value > 0 else 0
            
            # Determine risk level
            if portfolio_risk > 0.8:
                risk_level = RiskLevel.CRITICAL
            elif portfolio_risk > 0.6:
                risk_level = RiskLevel.HIGH
            elif portfolio_risk > 0.4:
                risk_level = RiskLevel.MEDIUM
            else:
                risk_level = RiskLevel.LOW
            
            # Generate recommendations
            recommendations = self._generate_risk_recommendations(portfolio_risk)
            
            return RiskMetrics(
                portfolio_risk=portfolio_risk,
                position_risk=max(self.active_positions.values()) / portfolio_value if self.active_positions and portfolio_value > 0 else 0,
                daily_pnl=self.daily_pnl,
                max_drawdown=self.max_drawdown_reached,
                risk_level=risk_level,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Error calculating risk metrics: {e}")
            return RiskMetrics(
                portfolio_risk=0.0,
                position_risk=0.0,
                daily_pnl=0.0,
                max_drawdown=0.0,
                risk_level=RiskLevel.LOW,
                recommendations=["Error calculating risk metrics"]
            )
    
    def _generate_risk_recommendations(self, portfolio_risk: float) -> List[str]:
        """
        Generate risk management recommendations
        
        Args:
            portfolio_risk: Current portfolio risk level
            
        Returns:
            List of risk management recommendations
        """
        recommendations = []
        
        if portfolio_risk > 0.7:
            recommendations.append("Consider reducing position sizes - portfolio risk is high")
        
        if self.daily_pnl < -self.max_daily_loss * 0.8:
            recommendations.append("Approaching daily loss limit - consider stopping trading")
        
        if self.max_drawdown_reached > self.max_drawdown * 0.8:
            recommendations.append("Approaching maximum drawdown limit - review strategy")
        
        if len(self.active_positions) > 10:
            recommendations.append("High number of active positions - consider consolidation")
        
        if not recommendations:
            recommendations.append("Risk levels are within acceptable limits")
        
        return recommendations

# Example usage
if __name__ == "__main__":
    # Example configuration
    config = {
        'max_position_size': 0.1,  # 10%
        'max_daily_loss': 0.05,    # 5%
        'stop_loss_percentage': 0.02,  # 2%
        'take_profit_percentage': 0.04,  # 4%
        'max_drawdown': 0.15  # 15%
    }
    
    risk_manager = RiskManager(config)
    
    # Example stop-loss calculation
    entry_price = 50000.0
    stop_loss = risk_manager.calculate_stop_loss(entry_price, 'BUY')
    take_profit = risk_manager.calculate_take_profit(entry_price, 'BUY')
    
    print(f"Entry: ${entry_price}")
    print(f"Stop Loss: ${stop_loss:.2f}")
    print(f"Take Profit: ${take_profit:.2f}")