import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

class RiskLevel(Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    CUSTOM = "custom"

@dataclass
class RiskMetrics:
    """Risk metrics for portfolio analysis"""
    var_95: float  # Value at Risk (95%)
    var_99: float  # Value at Risk (99%)
    expected_shortfall: float  # Conditional VaR
    max_drawdown: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    volatility: float
    beta: float

@dataclass
class PositionRisk:
    """Risk assessment for individual positions"""
    symbol: str
    position_size: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    risk_amount: float
    position_risk_pct: float
    correlation_risk: float
    liquidity_risk: float

class AdvancedRiskManager:
    """Advanced Risk Management System with portfolio optimization and dynamic risk controls"""
    
    def __init__(self,
                 initial_capital: float = 10000,
                 risk_level: RiskLevel = RiskLevel.MODERATE,
                 max_portfolio_risk: float = 0.02,  # 2% max portfolio risk
                 max_position_risk: float = 0.01,   # 1% max position risk
                 max_correlation_exposure: float = 0.3,  # 30% max correlated exposure
                 max_drawdown_limit: float = 0.15,  # 15% max drawdown
                 var_confidence: float = 0.95,      # 95% VaR confidence
                 rebalance_threshold: float = 0.05,  # 5% rebalance threshold
                 volatility_lookback: int = 30,      # 30 days volatility lookback
                 correlation_lookback: int = 60):    # 60 days correlation lookback
        """
        Initialize Advanced Risk Manager
        
        Args:
            initial_capital: Initial portfolio capital
            risk_level: Risk level (conservative, moderate, aggressive, custom)
            max_portfolio_risk: Maximum portfolio risk percentage
            max_position_risk: Maximum individual position risk percentage
            max_correlation_exposure: Maximum exposure to correlated assets
            max_drawdown_limit: Maximum allowed drawdown
            var_confidence: Value at Risk confidence level
            rebalance_threshold: Portfolio rebalance threshold
            volatility_lookback: Days to look back for volatility calculation
            correlation_lookback: Days to look back for correlation calculation
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.risk_level = risk_level
        self.max_portfolio_risk = max_portfolio_risk
        self.max_position_risk = max_position_risk
        self.max_correlation_exposure = max_correlation_exposure
        self.max_drawdown_limit = max_drawdown_limit
        self.var_confidence = var_confidence
        self.rebalance_threshold = rebalance_threshold
        self.volatility_lookback = volatility_lookback
        self.correlation_lookback = correlation_lookback
        
        # Risk parameters based on risk level
        self._set_risk_parameters()
        
        # Portfolio tracking
        self.positions = {}
        self.trade_history = []
        self.daily_returns = []
        self.portfolio_values = []
        self.correlation_matrix = pd.DataFrame()
        
        # Risk monitoring
        self.risk_alerts = []
        self.drawdown_periods = []
        self.current_drawdown = 0.0
        self.max_drawdown_reached = 0.0
        
        self.logger = logging.getLogger(__name__)
        
    def _set_risk_parameters(self):
        """Set risk parameters based on risk level"""
        if self.risk_level == RiskLevel.CONSERVATIVE:
            self.max_portfolio_risk = min(self.max_portfolio_risk, 0.015)  # 1.5%
            self.max_position_risk = min(self.max_position_risk, 0.005)    # 0.5%
            self.max_correlation_exposure = min(self.max_correlation_exposure, 0.2)  # 20%
            self.max_drawdown_limit = min(self.max_drawdown_limit, 0.1)    # 10%
        elif self.risk_level == RiskLevel.MODERATE:
            self.max_portfolio_risk = min(self.max_portfolio_risk, 0.02)   # 2%
            self.max_position_risk = min(self.max_position_risk, 0.01)     # 1%
            self.max_correlation_exposure = min(self.max_correlation_exposure, 0.3)  # 30%
            self.max_drawdown_limit = min(self.max_drawdown_limit, 0.15)   # 15%
        elif self.risk_level == RiskLevel.AGGRESSIVE:
            self.max_portfolio_risk = min(self.max_portfolio_risk, 0.03)   # 3%
            self.max_position_risk = min(self.max_position_risk, 0.015)    # 1.5%
            self.max_correlation_exposure = min(self.max_correlation_exposure, 0.4)  # 40%
            self.max_drawdown_limit = min(self.max_drawdown_limit, 0.2)    # 20%
    
    def calculate_position_size(self, 
                              symbol: str, 
                              entry_price: float, 
                              stop_loss_price: float, 
                              strategy_confidence: float = 1.0,
                              market_data: Optional[pd.DataFrame] = None) -> float:
        """Calculate optimal position size using Kelly Criterion and risk management
        
        Args:
            symbol: Trading symbol
            entry_price: Entry price
            stop_loss_price: Stop loss price
            strategy_confidence: Strategy confidence (0-1)
            market_data: Historical market data for volatility calculation
            
        Returns:
            Optimal position size in base currency
        """
        # Calculate risk per share
        risk_per_share = abs(entry_price - stop_loss_price)
        risk_percentage = risk_per_share / entry_price
        
        # Maximum position risk amount
        max_risk_amount = self.current_capital * self.max_position_risk
        
        # Calculate base position size
        base_position_size = max_risk_amount / risk_per_share
        
        # Apply Kelly Criterion if we have historical data
        if market_data is not None:
            kelly_fraction = self._calculate_kelly_fraction(symbol, market_data)
            kelly_position_size = self.current_capital * kelly_fraction / entry_price
            base_position_size = min(base_position_size, kelly_position_size)
        
        # Apply volatility adjustment
        if market_data is not None:
            volatility_adj = self._calculate_volatility_adjustment(market_data)
            base_position_size *= volatility_adj
        
        # Apply strategy confidence
        adjusted_position_size = base_position_size * strategy_confidence
        
        # Apply correlation adjustment
        correlation_adj = self._calculate_correlation_adjustment(symbol)
        final_position_size = adjusted_position_size * correlation_adj
        
        # Ensure we don't exceed portfolio limits
        max_portfolio_position = self.current_capital * 0.2  # Max 20% in single position
        final_position_size = min(final_position_size, max_portfolio_position / entry_price)
        
        return max(0, final_position_size)
    
    def _calculate_kelly_fraction(self, symbol: str, market_data: pd.DataFrame) -> float:
        """Calculate Kelly Criterion fraction"""
        if len(market_data) < 30:
            return 0.1  # Conservative default
        
        # Calculate returns
        returns = market_data['close'].pct_change().dropna()
        
        # Estimate win probability and average win/loss
        positive_returns = returns[returns > 0]
        negative_returns = returns[returns < 0]
        
        if len(positive_returns) == 0 or len(negative_returns) == 0:
            return 0.1
        
        win_prob = len(positive_returns) / len(returns)
        avg_win = positive_returns.mean()
        avg_loss = abs(negative_returns.mean())
        
        # Kelly fraction = (bp - q) / b
        # where b = avg_win/avg_loss, p = win_prob, q = 1-win_prob
        if avg_loss == 0:
            return 0.1
        
        b = avg_win / avg_loss
        kelly_fraction = (b * win_prob - (1 - win_prob)) / b
        
        # Cap Kelly fraction to prevent over-leveraging
        return max(0, min(kelly_fraction, 0.25))
    
    def _calculate_volatility_adjustment(self, market_data: pd.DataFrame) -> float:
        """Calculate volatility-based position size adjustment"""
        if len(market_data) < self.volatility_lookback:
            return 1.0
        
        # Calculate recent volatility
        returns = market_data['close'].pct_change().dropna()
        recent_vol = returns.tail(self.volatility_lookback).std() * np.sqrt(252)  # Annualized
        
        # Calculate long-term volatility
        long_term_vol = returns.std() * np.sqrt(252)
        
        if long_term_vol == 0:
            return 1.0
        
        # Adjust position size inversely to volatility ratio
        vol_ratio = recent_vol / long_term_vol
        adjustment = 1 / (1 + vol_ratio - 1)  # Reduce size when volatility increases
        
        return max(0.5, min(1.5, adjustment))  # Cap adjustment between 0.5x and 1.5x
    
    def _calculate_correlation_adjustment(self, symbol: str) -> float:
        """Calculate correlation-based position size adjustment"""
        if symbol not in self.correlation_matrix.columns or len(self.positions) == 0:
            return 1.0
        
        # Calculate correlation exposure
        total_correlation_exposure = 0
        
        for pos_symbol, position in self.positions.items():
            if pos_symbol != symbol and pos_symbol in self.correlation_matrix.columns:
                correlation = abs(self.correlation_matrix.loc[symbol, pos_symbol])
                position_weight = position['market_value'] / self.current_capital
                total_correlation_exposure += correlation * position_weight
        
        # Reduce position size if correlation exposure is high
        if total_correlation_exposure > self.max_correlation_exposure:
            adjustment = self.max_correlation_exposure / total_correlation_exposure
            return max(0.1, adjustment)
        
        return 1.0
    
    def assess_trade_risk(self, 
                         symbol: str, 
                         side: str, 
                         quantity: float, 
                         entry_price: float,
                         stop_loss: Optional[float] = None,
                         take_profit: Optional[float] = None) -> Dict:
        """Assess risk for a potential trade
        
        Args:
            symbol: Trading symbol
            side: 'buy' or 'sell'
            quantity: Trade quantity
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            
        Returns:
            Risk assessment dictionary
        """
        trade_value = quantity * entry_price
        
        # Calculate potential loss
        if stop_loss:
            if side == 'buy':
                max_loss = (entry_price - stop_loss) * quantity
            else:
                max_loss = (stop_loss - entry_price) * quantity
        else:
            max_loss = trade_value * 0.1  # Assume 10% max loss if no stop loss
        
        # Calculate risk metrics
        position_risk_pct = max_loss / self.current_capital
        trade_risk_pct = max_loss / trade_value
        
        # Check portfolio concentration
        position_concentration = trade_value / self.current_capital
        
        # Risk assessment
        risk_level = "LOW"
        if position_risk_pct > self.max_position_risk:
            risk_level = "HIGH"
        elif position_risk_pct > self.max_position_risk * 0.7:
            risk_level = "MEDIUM"
        
        # Generate recommendations
        recommendations = []
        if position_risk_pct > self.max_position_risk:
            recommended_quantity = (self.current_capital * self.max_position_risk) / (abs(entry_price - (stop_loss or entry_price * 0.9)))
            recommendations.append(f"Reduce position size to {recommended_quantity:.6f} to stay within risk limits")
        
        if position_concentration > 0.2:
            recommendations.append("Position represents >20% of portfolio - consider reducing size")
        
        if not stop_loss:
            recommendations.append("Consider setting a stop loss to limit downside risk")
        
        return {
            'symbol': symbol,
            'trade_value': trade_value,
            'max_loss': max_loss,
            'position_risk_pct': position_risk_pct * 100,
            'trade_risk_pct': trade_risk_pct * 100,
            'position_concentration': position_concentration * 100,
            'risk_level': risk_level,
            'approved': position_risk_pct <= self.max_position_risk,
            'recommendations': recommendations
        }
    
    def update_portfolio(self, positions: Dict, market_prices: Dict):
        """Update portfolio positions and calculate risk metrics
        
        Args:
            positions: Dictionary of current positions
            market_prices: Current market prices
        """
        self.positions = positions.copy()
        
        # Calculate current portfolio value
        total_value = 0
        for symbol, position in positions.items():
            if symbol in market_prices:
                market_value = position['quantity'] * market_prices[symbol]
                position['market_value'] = market_value
                position['unrealized_pnl'] = market_value - (position['quantity'] * position['avg_price'])
                total_value += market_value
        
        # Add cash balance
        cash_balance = self.current_capital - sum([pos.get('market_value', 0) for pos in positions.values()])
        total_value += cash_balance
        
        self.current_capital = total_value
        self.portfolio_values.append({
            'timestamp': datetime.now(),
            'value': total_value,
            'cash': cash_balance
        })
        
        # Calculate daily return
        if len(self.portfolio_values) > 1:
            prev_value = self.portfolio_values[-2]['value']
            daily_return = (total_value - prev_value) / prev_value
            self.daily_returns.append(daily_return)
        
        # Update drawdown
        self._update_drawdown(total_value)
        
        # Check risk limits
        self._check_risk_limits()
    
    def _update_drawdown(self, current_value: float):
        """Update drawdown calculations"""
        if not self.portfolio_values:
            return
        
        # Find peak value
        peak_value = max([pv['value'] for pv in self.portfolio_values])
        
        # Calculate current drawdown
        self.current_drawdown = (peak_value - current_value) / peak_value
        
        # Update max drawdown
        if self.current_drawdown > self.max_drawdown_reached:
            self.max_drawdown_reached = self.current_drawdown
    
    def _check_risk_limits(self):
        """Check if any risk limits are breached"""
        alerts = []
        
        # Check drawdown limit
        if self.current_drawdown > self.max_drawdown_limit:
            alerts.append({
                'type': 'DRAWDOWN_LIMIT',
                'message': f'Portfolio drawdown ({self.current_drawdown:.2%}) exceeds limit ({self.max_drawdown_limit:.2%})',
                'severity': 'CRITICAL',
                'timestamp': datetime.now()
            })
        
        # Check position concentration
        for symbol, position in self.positions.items():
            concentration = position.get('market_value', 0) / self.current_capital
            if concentration > 0.25:  # 25% concentration limit
                alerts.append({
                    'type': 'CONCENTRATION_RISK',
                    'message': f'{symbol} represents {concentration:.2%} of portfolio',
                    'severity': 'WARNING',
                    'timestamp': datetime.now()
                })
        
        # Check portfolio risk
        portfolio_var = self.calculate_portfolio_var()
        if portfolio_var > self.max_portfolio_risk * self.current_capital:
            alerts.append({
                'type': 'PORTFOLIO_RISK',
                'message': f'Portfolio VaR ({portfolio_var:.2f}) exceeds risk limit',
                'severity': 'HIGH',
                'timestamp': datetime.now()
            })
        
        self.risk_alerts.extend(alerts)
        
        # Log critical alerts
        for alert in alerts:
            if alert['severity'] == 'CRITICAL':
                self.logger.critical(alert['message'])
            elif alert['severity'] == 'HIGH':
                self.logger.warning(alert['message'])
    
    def calculate_portfolio_var(self, confidence: float = None) -> float:
        """Calculate Portfolio Value at Risk
        
        Args:
            confidence: Confidence level (default uses instance setting)
            
        Returns:
            Value at Risk amount
        """
        if confidence is None:
            confidence = self.var_confidence
        
        if len(self.daily_returns) < 30:
            return 0.0
        
        # Calculate VaR using historical simulation
        returns_array = np.array(self.daily_returns)
        var_percentile = (1 - confidence) * 100
        var_return = np.percentile(returns_array, var_percentile)
        
        return abs(var_return * self.current_capital)
    
    def calculate_risk_metrics(self) -> RiskMetrics:
        """Calculate comprehensive risk metrics"""
        if len(self.daily_returns) < 30:
            return RiskMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0)
        
        returns = np.array(self.daily_returns)
        
        # VaR calculations
        var_95 = abs(np.percentile(returns, 5) * self.current_capital)
        var_99 = abs(np.percentile(returns, 1) * self.current_capital)
        
        # Expected Shortfall (Conditional VaR)
        var_95_return = np.percentile(returns, 5)
        expected_shortfall = abs(returns[returns <= var_95_return].mean() * self.current_capital)
        
        # Volatility
        volatility = np.std(returns) * np.sqrt(252)  # Annualized
        
        # Sharpe Ratio (assuming 0% risk-free rate)
        mean_return = np.mean(returns) * 252  # Annualized
        sharpe_ratio = mean_return / volatility if volatility > 0 else 0
        
        # Sortino Ratio
        downside_returns = returns[returns < 0]
        downside_deviation = np.std(downside_returns) * np.sqrt(252) if len(downside_returns) > 0 else 0
        sortino_ratio = mean_return / downside_deviation if downside_deviation > 0 else 0
        
        # Calmar Ratio
        calmar_ratio = mean_return / self.max_drawdown_reached if self.max_drawdown_reached > 0 else 0
        
        # Beta (assuming market return of 10% annually)
        market_return = 0.10 / 252  # Daily market return
        covariance = np.cov(returns, [market_return] * len(returns))[0, 1]
        market_variance = (0.15 / np.sqrt(252)) ** 2  # Assuming 15% market volatility
        beta = covariance / market_variance
        
        return RiskMetrics(
            var_95=var_95,
            var_99=var_99,
            expected_shortfall=expected_shortfall,
            max_drawdown=self.max_drawdown_reached,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            volatility=volatility,
            beta=beta
        )
    
    def get_position_risks(self, market_prices: Dict) -> List[PositionRisk]:
        """Get risk assessment for all positions"""
        position_risks = []
        
        for symbol, position in self.positions.items():
            if symbol not in market_prices:
                continue
            
            current_price = market_prices[symbol]
            market_value = position['quantity'] * current_price
            unrealized_pnl = market_value - (position['quantity'] * position['avg_price'])
            
            # Calculate position risk
            position_risk_pct = market_value / self.current_capital
            
            # Estimate risk amount (using 10% as default risk)
            risk_amount = market_value * 0.1
            
            # Calculate correlation risk
            correlation_risk = self._calculate_correlation_risk(symbol)
            
            # Estimate liquidity risk (simplified)
            liquidity_risk = 0.05  # 5% default liquidity risk
            
            position_risks.append(PositionRisk(
                symbol=symbol,
                position_size=position['quantity'],
                entry_price=position['avg_price'],
                current_price=current_price,
                unrealized_pnl=unrealized_pnl,
                risk_amount=risk_amount,
                position_risk_pct=position_risk_pct * 100,
                correlation_risk=correlation_risk,
                liquidity_risk=liquidity_risk
            ))
        
        return position_risks
    
    def _calculate_correlation_risk(self, symbol: str) -> float:
        """Calculate correlation risk for a symbol"""
        if symbol not in self.correlation_matrix.columns:
            return 0.0
        
        # Calculate weighted average correlation with other positions
        total_correlation = 0
        total_weight = 0
        
        for other_symbol, position in self.positions.items():
            if other_symbol != symbol and other_symbol in self.correlation_matrix.columns:
                correlation = abs(self.correlation_matrix.loc[symbol, other_symbol])
                weight = position.get('market_value', 0) / self.current_capital
                total_correlation += correlation * weight
                total_weight += weight
        
        return total_correlation / total_weight if total_weight > 0 else 0.0
    
    def should_rebalance(self) -> bool:
        """Check if portfolio should be rebalanced"""
        if len(self.positions) < 2:
            return False
        
        # Calculate current weights
        total_value = sum([pos.get('market_value', 0) for pos in self.positions.values()])
        
        if total_value == 0:
            return False
        
        # Check if any position has deviated significantly from target
        target_weight = 1.0 / len(self.positions)  # Equal weight target
        
        for position in self.positions.values():
            current_weight = position.get('market_value', 0) / total_value
            weight_deviation = abs(current_weight - target_weight)
            
            if weight_deviation > self.rebalance_threshold:
                return True
        
        return False
    
    def get_rebalancing_recommendations(self) -> List[Dict]:
        """Get portfolio rebalancing recommendations"""
        if not self.should_rebalance():
            return []
        
        recommendations = []
        total_value = sum([pos.get('market_value', 0) for pos in self.positions.values()])
        target_weight = 1.0 / len(self.positions)
        
        for symbol, position in self.positions.items():
            current_weight = position.get('market_value', 0) / total_value
            target_value = total_value * target_weight
            current_value = position.get('market_value', 0)
            
            if abs(current_value - target_value) > total_value * 0.01:  # 1% threshold
                action = 'BUY' if current_value < target_value else 'SELL'
                amount = abs(current_value - target_value)
                
                recommendations.append({
                    'symbol': symbol,
                    'action': action,
                    'amount': amount,
                    'current_weight': current_weight * 100,
                    'target_weight': target_weight * 100,
                    'deviation': (current_weight - target_weight) * 100
                })
        
        return recommendations
    
    def get_risk_summary(self) -> Dict:
        """Get comprehensive risk summary"""
        risk_metrics = self.calculate_risk_metrics()
        portfolio_var = self.calculate_portfolio_var()
        
        return {
            'portfolio_value': self.current_capital,
            'total_return': (self.current_capital - self.initial_capital) / self.initial_capital * 100,
            'current_drawdown': self.current_drawdown * 100,
            'max_drawdown': self.max_drawdown_reached * 100,
            'portfolio_var_95': portfolio_var,
            'var_as_pct_of_portfolio': portfolio_var / self.current_capital * 100,
            'sharpe_ratio': risk_metrics.sharpe_ratio,
            'sortino_ratio': risk_metrics.sortino_ratio,
            'volatility': risk_metrics.volatility * 100,
            'number_of_positions': len(self.positions),
            'risk_level': self.risk_level.value,
            'active_alerts': len([alert for alert in self.risk_alerts if 
                                (datetime.now() - alert['timestamp']).days < 1]),
            'needs_rebalancing': self.should_rebalance()
        }