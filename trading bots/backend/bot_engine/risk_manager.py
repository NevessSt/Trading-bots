from datetime import datetime, timedelta
from models.trade import Trade
from models.user import User

class RiskManager:
    """Risk management system for trading operations"""
    
    def __init__(self, user_id=None):
        """Initialize the risk manager
        
        Args:
            user_id (str, optional): User ID
        """
        self.user_id = user_id
    
    def can_trade(self, user_id, symbol, amount, is_buy):
        """Check if a trade is allowed based on risk management rules
        
        Args:
            user_id (str): User ID
            symbol (str): Trading symbol
            amount (float): Trade amount
            is_buy (bool): True if buy, False if sell
            
        Returns:
            bool: True if trade is allowed, False otherwise
        """
        # Get user settings
        user = User.find_by_id(user_id)
        if not user:
            return False
        
        risk_settings = user.get('settings', {}).get('risk_management', {})
        
        # Check max daily loss
        if not self._check_max_daily_loss(user_id, risk_settings.get('max_daily_loss', 5.0)):
            return False
        
        # Check max trade size
        if not self._check_max_trade_size(user_id, amount, risk_settings.get('max_trade_size', 10.0)):
            return False
        
        # Check max open positions
        if not self._check_max_open_positions(user_id, symbol, is_buy, risk_settings.get('max_open_positions', 5)):
            return False
        
        # Check max trades per day
        if not self._check_max_trades_per_day(user_id, risk_settings.get('max_trades_per_day', 10)):
            return False
        
        return True
    
    def _check_max_daily_loss(self, user_id, max_daily_loss_pct):
        """Check if daily loss limit has been reached
        
        Args:
            user_id (str): User ID
            max_daily_loss_pct (float): Maximum daily loss percentage
            
        Returns:
            bool: True if within limit, False if limit reached
        """
        # Calculate start of day
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Get today's trades
        today_trades = Trade.get_trades_by_date_range(user_id, today, datetime.utcnow())
        
        # Calculate today's profit/loss
        today_pl = sum(trade.get('profit_loss', 0) for trade in today_trades)
        
        # Get account balance
        user = User.find_by_id(user_id)
        account_balance = user.get('account_balance', 0)
        
        # Calculate max allowed loss
        max_loss_amount = account_balance * (max_daily_loss_pct / 100)
        
        # Check if daily loss limit reached
        return today_pl > -max_loss_amount
    
    def _check_max_trade_size(self, user_id, amount, max_trade_size_pct):
        """Check if trade size is within limit
        
        Args:
            user_id (str): User ID
            amount (float): Trade amount
            max_trade_size_pct (float): Maximum trade size percentage
            
        Returns:
            bool: True if within limit, False if limit exceeded
        """
        # Get account balance
        user = User.find_by_id(user_id)
        account_balance = user.get('account_balance', 0)
        
        # Calculate max allowed trade size
        max_trade_amount = account_balance * (max_trade_size_pct / 100)
        
        # Check if trade size is within limit
        return amount <= max_trade_amount
    
    def _check_max_open_positions(self, user_id, symbol, is_buy, max_open_positions):
        """Check if maximum number of open positions has been reached
        
        Args:
            user_id (str): User ID
            symbol (str): Trading symbol
            is_buy (bool): True if buy, False if sell
            max_open_positions (int): Maximum number of open positions
            
        Returns:
            bool: True if within limit, False if limit reached
        """
        # Get open positions
        open_positions = self._get_open_positions(user_id)
        
        # Check if already have an open position for this symbol in the same direction
        for position in open_positions:
            if position['symbol'] == symbol and position['is_buy'] == is_buy:
                # Already have an open position for this symbol in the same direction
                return False
        
        # Check if max open positions reached
        return len(open_positions) < max_open_positions
    
    def _check_max_trades_per_day(self, user_id, max_trades_per_day):
        """Check if maximum number of trades per day has been reached
        
        Args:
            user_id (str): User ID
            max_trades_per_day (int): Maximum number of trades per day
            
        Returns:
            bool: True if within limit, False if limit reached
        """
        # Calculate start of day
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Get today's trades
        today_trades = Trade.get_trades_by_date_range(user_id, today, datetime.utcnow())
        
        # Check if max trades per day reached
        return len(today_trades) < max_trades_per_day
    
    def _get_open_positions(self, user_id):
        """Get open positions for a user
        
        Args:
            user_id (str): User ID
            
        Returns:
            list: List of open positions
        """
        # In a real implementation, this would query the exchange for open positions
        # For now, we'll return a placeholder
        return []
    
    def calculate_position_size(self, user_id, symbol, risk_per_trade_pct=1.0):
        """Calculate position size based on risk per trade
        
        Args:
            user_id (str): User ID
            symbol (str): Trading symbol
            risk_per_trade_pct (float): Risk per trade percentage
            
        Returns:
            float: Position size
        """
        # Get account balance
        user = User.find_by_id(user_id)
        account_balance = user.get('account_balance', 0)
        
        # Calculate risk amount
        risk_amount = account_balance * (risk_per_trade_pct / 100)
        
        # In a real implementation, this would calculate position size based on stop loss distance
        # For now, we'll return a placeholder
        return risk_amount
    
    def update_risk_settings(self, user_id, risk_settings):
        """Update risk management settings for a user
        
        Args:
            user_id (str): User ID
            risk_settings (dict): Risk management settings
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        return User.update(user_id, {'settings.risk_management': risk_settings})