import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
import threading
from decimal import Decimal, ROUND_DOWN
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
safety_logger = logging.getLogger('trading_safety')
risk_logger = logging.getLogger('risk_management')

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TradeAction(Enum):
    ALLOW = "allow"
    BLOCK = "block"
    REQUIRE_APPROVAL = "require_approval"
    REDUCE_SIZE = "reduce_size"

@dataclass
class RiskLimits:
    """Risk management limits configuration"""
    max_daily_loss: float = 1000.0  # Maximum daily loss in USD
    max_position_size: float = 10000.0  # Maximum position size in USD
    max_leverage: float = 3.0  # Maximum leverage allowed
    max_drawdown_percent: float = 20.0  # Maximum drawdown percentage
    max_trades_per_hour: int = 50  # Maximum trades per hour
    max_trades_per_day: int = 500  # Maximum trades per day
    min_account_balance: float = 100.0  # Minimum account balance to trade
    max_risk_per_trade: float = 2.0  # Maximum risk per trade as % of account
    stop_loss_required: bool = True  # Require stop loss for all trades
    max_open_positions: int = 10  # Maximum number of open positions
    blacklisted_symbols: List[str] = None  # Symbols not allowed for trading
    
    def __post_init__(self):
        if self.blacklisted_symbols is None:
            self.blacklisted_symbols = []

@dataclass
class TradeRequest:
    """Trading request with all necessary information"""
    user_id: int
    bot_id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    amount: float
    price: Optional[float] = None
    order_type: str = 'market'
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    leverage: Optional[float] = None
    strategy: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

@dataclass
class RiskAssessment:
    """Risk assessment result"""
    action: TradeAction
    risk_level: RiskLevel
    reasons: List[str]
    recommended_amount: Optional[float] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []

class TradingSafetySystem:
    """Comprehensive trading safety and risk management system"""
    
    def __init__(self, risk_limits: Optional[RiskLimits] = None):
        self.risk_limits = risk_limits or RiskLimits()
        self.user_stats = {}  # Track user trading statistics
        self.daily_stats = {}  # Track daily statistics
        self.position_tracker = {}  # Track open positions
        self.trade_history = {}  # Recent trade history
        self.emergency_stop = False  # Emergency stop flag
        self.lock = threading.Lock()
        
        # Initialize logging
        self.setup_logging()
    
    def setup_logging(self):
        """Setup comprehensive logging for safety system"""
        # Create formatters
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # File handlers
        safety_handler = logging.FileHandler('logs/trading_safety.log')
        safety_handler.setFormatter(formatter)
        safety_logger.addHandler(safety_handler)
        
        risk_handler = logging.FileHandler('logs/risk_management.log')
        risk_handler.setFormatter(formatter)
        risk_logger.addHandler(risk_handler)
    
    def assess_trade_risk(self, trade_request: TradeRequest, account_balance: float, 
                         open_positions: List[Dict], market_data: Dict) -> RiskAssessment:
        """Comprehensive trade risk assessment"""
        reasons = []
        warnings = []
        risk_level = RiskLevel.LOW
        action = TradeAction.ALLOW
        recommended_amount = trade_request.amount
        
        try:
            # Emergency stop check
            if self.emergency_stop:
                return RiskAssessment(
                    action=TradeAction.BLOCK,
                    risk_level=RiskLevel.CRITICAL,
                    reasons=["Emergency stop activated"]
                )
            
            # Basic validation checks
            validation_issues = self._validate_trade_request(trade_request)
            if validation_issues:
                return RiskAssessment(
                    action=TradeAction.BLOCK,
                    risk_level=RiskLevel.HIGH,
                    reasons=validation_issues
                )
            
            # Account balance checks
            balance_check = self._check_account_balance(account_balance, trade_request)
            if balance_check['action'] != TradeAction.ALLOW:
                return RiskAssessment(
                    action=balance_check['action'],
                    risk_level=balance_check['risk_level'],
                    reasons=balance_check['reasons']
                )
            
            # Position size and risk checks
            position_check = self._check_position_limits(trade_request, account_balance, open_positions)
            if position_check['action'] != TradeAction.ALLOW:
                if position_check['action'] == TradeAction.REDUCE_SIZE:
                    recommended_amount = position_check['recommended_amount']
                    warnings.extend(position_check['warnings'])
                    risk_level = RiskLevel.MEDIUM
                else:
                    return RiskAssessment(
                        action=position_check['action'],
                        risk_level=position_check['risk_level'],
                        reasons=position_check['reasons']
                    )
            
            # Daily limits check
            daily_check = self._check_daily_limits(trade_request)
            if daily_check['action'] != TradeAction.ALLOW:
                return RiskAssessment(
                    action=daily_check['action'],
                    risk_level=daily_check['risk_level'],
                    reasons=daily_check['reasons']
                )
            
            # Market condition checks
            market_check = self._check_market_conditions(trade_request, market_data)
            if market_check['warnings']:
                warnings.extend(market_check['warnings'])
                if market_check['risk_level'].value > risk_level.value:
                    risk_level = market_check['risk_level']
            
            # Symbol-specific checks
            symbol_check = self._check_symbol_restrictions(trade_request)
            if symbol_check['action'] != TradeAction.ALLOW:
                return RiskAssessment(
                    action=symbol_check['action'],
                    risk_level=symbol_check['risk_level'],
                    reasons=symbol_check['reasons']
                )
            
            # Stop loss validation
            if self.risk_limits.stop_loss_required and not trade_request.stop_loss:
                warnings.append("Stop loss is recommended for risk management")
                risk_level = RiskLevel.MEDIUM
            
            # Log the assessment
            self._log_risk_assessment(trade_request, risk_level, action, reasons, warnings)
            
            return RiskAssessment(
                action=action,
                risk_level=risk_level,
                reasons=reasons,
                recommended_amount=recommended_amount,
                warnings=warnings
            )
            
        except Exception as e:
            safety_logger.error(f"Error in risk assessment: {str(e)}")
            return RiskAssessment(
                action=TradeAction.BLOCK,
                risk_level=RiskLevel.CRITICAL,
                reasons=[f"Risk assessment failed: {str(e)}"]
            )
    
    def _validate_trade_request(self, trade_request: TradeRequest) -> List[str]:
        """Basic validation of trade request"""
        issues = []
        
        # Check required fields
        if not trade_request.symbol:
            issues.append("Symbol is required")
        
        if not trade_request.side or trade_request.side not in ['buy', 'sell']:
            issues.append("Valid side (buy/sell) is required")
        
        if not trade_request.amount or trade_request.amount <= 0:
            issues.append("Valid amount is required")
        
        # Check amount precision
        if trade_request.amount and len(str(trade_request.amount).split('.')[-1]) > 8:
            issues.append("Amount precision too high (max 8 decimal places)")
        
        # Check leverage limits
        if trade_request.leverage and trade_request.leverage > self.risk_limits.max_leverage:
            issues.append(f"Leverage {trade_request.leverage} exceeds maximum {self.risk_limits.max_leverage}")
        
        return issues
    
    def _check_account_balance(self, account_balance: float, trade_request: TradeRequest) -> Dict:
        """Check account balance requirements"""
        if account_balance < self.risk_limits.min_account_balance:
            return {
                'action': TradeAction.BLOCK,
                'risk_level': RiskLevel.HIGH,
                'reasons': [f"Account balance {account_balance} below minimum {self.risk_limits.min_account_balance}"]
            }
        
        # Calculate trade value
        trade_value = trade_request.amount * (trade_request.price or 1)
        
        # Check if sufficient balance for trade
        if trade_value > account_balance * 0.95:  # Leave 5% buffer
            return {
                'action': TradeAction.BLOCK,
                'risk_level': RiskLevel.HIGH,
                'reasons': ["Insufficient account balance for trade"]
            }
        
        return {'action': TradeAction.ALLOW}
    
    def _check_position_limits(self, trade_request: TradeRequest, account_balance: float, 
                              open_positions: List[Dict]) -> Dict:
        """Check position size and risk limits"""
        trade_value = trade_request.amount * (trade_request.price or 1)
        
        # Check maximum position size
        if trade_value > self.risk_limits.max_position_size:
            max_amount = self.risk_limits.max_position_size / (trade_request.price or 1)
            return {
                'action': TradeAction.REDUCE_SIZE,
                'risk_level': RiskLevel.MEDIUM,
                'reasons': [f"Position size {trade_value} exceeds maximum {self.risk_limits.max_position_size}"],
                'recommended_amount': max_amount,
                'warnings': [f"Reducing position size to {max_amount}"]
            }
        
        # Check risk per trade
        risk_percent = (trade_value / account_balance) * 100
        if risk_percent > self.risk_limits.max_risk_per_trade:
            max_amount = (account_balance * self.risk_limits.max_risk_per_trade / 100) / (trade_request.price or 1)
            return {
                'action': TradeAction.REDUCE_SIZE,
                'risk_level': RiskLevel.MEDIUM,
                'reasons': [f"Risk per trade {risk_percent:.2f}% exceeds maximum {self.risk_limits.max_risk_per_trade}%"],
                'recommended_amount': max_amount,
                'warnings': [f"Reducing position size to limit risk to {self.risk_limits.max_risk_per_trade}%"]
            }
        
        # Check maximum open positions
        if len(open_positions) >= self.risk_limits.max_open_positions:
            return {
                'action': TradeAction.BLOCK,
                'risk_level': RiskLevel.MEDIUM,
                'reasons': [f"Maximum open positions ({self.risk_limits.max_open_positions}) reached"]
            }
        
        return {'action': TradeAction.ALLOW}
    
    def _check_daily_limits(self, trade_request: TradeRequest) -> Dict:
        """Check daily trading limits"""
        today = datetime.utcnow().date()
        user_id = trade_request.user_id
        
        with self.lock:
            # Initialize daily stats if needed
            if user_id not in self.daily_stats:
                self.daily_stats[user_id] = {}
            
            if today not in self.daily_stats[user_id]:
                self.daily_stats[user_id][today] = {
                    'trades': 0,
                    'loss': 0.0,
                    'last_trade_time': None
                }
            
            daily_data = self.daily_stats[user_id][today]
            
            # Check daily trade count
            if daily_data['trades'] >= self.risk_limits.max_trades_per_day:
                return {
                    'action': TradeAction.BLOCK,
                    'risk_level': RiskLevel.MEDIUM,
                    'reasons': [f"Daily trade limit ({self.risk_limits.max_trades_per_day}) reached"]
                }
            
            # Check hourly trade count
            current_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
            hourly_trades = self._count_hourly_trades(user_id, current_hour)
            
            if hourly_trades >= self.risk_limits.max_trades_per_hour:
                return {
                    'action': TradeAction.BLOCK,
                    'risk_level': RiskLevel.MEDIUM,
                    'reasons': [f"Hourly trade limit ({self.risk_limits.max_trades_per_hour}) reached"]
                }
            
            # Check daily loss limit
            if daily_data['loss'] >= self.risk_limits.max_daily_loss:
                return {
                    'action': TradeAction.BLOCK,
                    'risk_level': RiskLevel.HIGH,
                    'reasons': [f"Daily loss limit ({self.risk_limits.max_daily_loss}) reached"]
                }
        
        return {'action': TradeAction.ALLOW}
    
    def _check_market_conditions(self, trade_request: TradeRequest, market_data: Dict) -> Dict:
        """Check market conditions for additional risk factors"""
        warnings = []
        risk_level = RiskLevel.LOW
        
        if not market_data:
            warnings.append("No market data available for risk assessment")
            return {'warnings': warnings, 'risk_level': RiskLevel.MEDIUM}
        
        symbol = trade_request.symbol
        
        # Check volatility
        if symbol in market_data and 'volatility' in market_data[symbol]:
            volatility = market_data[symbol]['volatility']
            if volatility > 0.1:  # 10% volatility threshold
                warnings.append(f"High volatility detected ({volatility:.2%})")
                risk_level = RiskLevel.HIGH
            elif volatility > 0.05:  # 5% volatility threshold
                warnings.append(f"Moderate volatility detected ({volatility:.2%})")
                risk_level = RiskLevel.MEDIUM
        
        # Check spread
        if symbol in market_data and 'spread' in market_data[symbol]:
            spread = market_data[symbol]['spread']
            if spread > 0.005:  # 0.5% spread threshold
                warnings.append(f"Wide spread detected ({spread:.3%})")
                if risk_level.value < RiskLevel.MEDIUM.value:
                    risk_level = RiskLevel.MEDIUM
        
        # Check volume
        if symbol in market_data and 'volume' in market_data[symbol]:
            volume = market_data[symbol]['volume']
            avg_volume = market_data[symbol].get('avg_volume', volume)
            
            if volume < avg_volume * 0.3:  # Low volume threshold
                warnings.append("Low trading volume detected")
                if risk_level.value < RiskLevel.MEDIUM.value:
                    risk_level = RiskLevel.MEDIUM
        
        return {'warnings': warnings, 'risk_level': risk_level}
    
    def _check_symbol_restrictions(self, trade_request: TradeRequest) -> Dict:
        """Check symbol-specific restrictions"""
        symbol = trade_request.symbol.upper()
        
        # Check blacklisted symbols
        if symbol in self.risk_limits.blacklisted_symbols:
            return {
                'action': TradeAction.BLOCK,
                'risk_level': RiskLevel.HIGH,
                'reasons': [f"Symbol {symbol} is blacklisted"]
            }
        
        # Check symbol format
        if not self._is_valid_symbol_format(symbol):
            return {
                'action': TradeAction.BLOCK,
                'risk_level': RiskLevel.HIGH,
                'reasons': [f"Invalid symbol format: {symbol}"]
            }
        
        return {'action': TradeAction.ALLOW}
    
    def _is_valid_symbol_format(self, symbol: str) -> bool:
        """Validate symbol format"""
        import re
        # Basic symbol validation (extend as needed)
        pattern = r'^[A-Z]{2,10}[/\-][A-Z]{2,10}$'
        return bool(re.match(pattern, symbol))
    
    def _count_hourly_trades(self, user_id: int, current_hour: datetime) -> int:
        """Count trades in the current hour"""
        if user_id not in self.trade_history:
            return 0
        
        count = 0
        for trade_time in self.trade_history[user_id]:
            if trade_time >= current_hour and trade_time < current_hour + timedelta(hours=1):
                count += 1
        
        return count
    
    def record_trade(self, trade_request: TradeRequest, result: Dict):
        """Record completed trade for tracking"""
        with self.lock:
            user_id = trade_request.user_id
            today = datetime.utcnow().date()
            
            # Initialize tracking structures
            if user_id not in self.trade_history:
                self.trade_history[user_id] = []
            
            if user_id not in self.daily_stats:
                self.daily_stats[user_id] = {}
            
            if today not in self.daily_stats[user_id]:
                self.daily_stats[user_id][today] = {
                    'trades': 0,
                    'loss': 0.0,
                    'last_trade_time': None
                }
            
            # Record trade
            self.trade_history[user_id].append(datetime.utcnow())
            self.daily_stats[user_id][today]['trades'] += 1
            self.daily_stats[user_id][today]['last_trade_time'] = datetime.utcnow()
            
            # Record loss if applicable
            if result.get('pnl', 0) < 0:
                self.daily_stats[user_id][today]['loss'] += abs(result['pnl'])
            
            # Clean old trade history (keep only last 24 hours)
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            self.trade_history[user_id] = [
                t for t in self.trade_history[user_id] if t > cutoff_time
            ]
        
        # Log trade record
        safety_logger.info(f"Trade recorded for user {user_id}: {trade_request.symbol} {trade_request.side} {trade_request.amount}")
    
    def _log_risk_assessment(self, trade_request: TradeRequest, risk_level: RiskLevel, 
                           action: TradeAction, reasons: List[str], warnings: List[str]):
        """Log risk assessment details"""
        log_data = {
            'user_id': trade_request.user_id,
            'bot_id': trade_request.bot_id,
            'symbol': trade_request.symbol,
            'side': trade_request.side,
            'amount': trade_request.amount,
            'risk_level': risk_level.value,
            'action': action.value,
            'reasons': reasons,
            'warnings': warnings,
            'timestamp': trade_request.timestamp.isoformat()
        }
        
        if action == TradeAction.BLOCK:
            risk_logger.warning(f"Trade blocked: {json.dumps(log_data)}")
        elif warnings:
            risk_logger.info(f"Trade allowed with warnings: {json.dumps(log_data)}")
        else:
            risk_logger.info(f"Trade approved: {json.dumps(log_data)}")
    
    def activate_emergency_stop(self, reason: str):
        """Activate emergency stop for all trading"""
        self.emergency_stop = True
        safety_logger.critical(f"EMERGENCY STOP ACTIVATED: {reason}")
        risk_logger.critical(f"All trading halted due to: {reason}")
    
    def deactivate_emergency_stop(self, reason: str):
        """Deactivate emergency stop"""
        self.emergency_stop = False
        safety_logger.info(f"Emergency stop deactivated: {reason}")
        risk_logger.info(f"Trading resumed: {reason}")
    
    def get_safety_stats(self) -> Dict:
        """Get comprehensive safety statistics"""
        with self.lock:
            return {
                'emergency_stop': self.emergency_stop,
                'total_users_tracked': len(self.daily_stats),
                'daily_stats': dict(self.daily_stats),
                'risk_limits': {
                    'max_daily_loss': self.risk_limits.max_daily_loss,
                    'max_position_size': self.risk_limits.max_position_size,
                    'max_trades_per_day': self.risk_limits.max_trades_per_day,
                    'max_risk_per_trade': self.risk_limits.max_risk_per_trade
                }
            }
    
    def update_risk_limits(self, new_limits: RiskLimits):
        """Update risk management limits"""
        old_limits = self.risk_limits
        self.risk_limits = new_limits
        
        safety_logger.info(f"Risk limits updated from {old_limits} to {new_limits}")

# Global safety system instance
trading_safety = TradingSafetySystem()