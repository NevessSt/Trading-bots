import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

class TradingLogger:
    """Centralized logging for the trading bot"""
    
    def __init__(self, name='trading_bot'):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup logging handlers"""
        # Create logs directory if it doesn't exist
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        
        # File handler for general logs
        file_handler = RotatingFileHandler(
            os.path.join(logs_dir, 'trading_bot.log'),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.INFO)
        
        # File handler for trade logs
        trade_handler = RotatingFileHandler(
            os.path.join(logs_dir, 'trades.log'),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=10
        )
        trade_handler.setLevel(logging.INFO)
        
        # File handler for error logs
        error_handler = RotatingFileHandler(
            os.path.join(logs_dir, 'errors.log'),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        
        # Console handler for development
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO if os.getenv('FLASK_ENV') == 'development' else logging.WARNING)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        
        # Apply formatter to all handlers
        for handler in [file_handler, trade_handler, error_handler, console_handler]:
            handler.setFormatter(formatter)
        
        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Create separate loggers for trades and errors
        self.trade_logger = logging.getLogger('trades')
        self.trade_logger.setLevel(logging.INFO)
        self.trade_logger.addHandler(trade_handler)
        
        self.error_logger = logging.getLogger('errors')
        self.error_logger.setLevel(logging.ERROR)
        self.error_logger.addHandler(error_handler)
    
    def info(self, message, extra=None):
        """Log info message"""
        self.logger.info(message, extra=extra)
    
    def warning(self, message, extra=None):
        """Log warning message"""
        self.logger.warning(message, extra=extra)
    
    def error(self, message, extra=None):
        """Log error message"""
        self.logger.error(message, extra=extra)
        self.error_logger.error(message, extra=extra)
    
    def debug(self, message, extra=None):
        """Log debug message"""
        self.logger.debug(message, extra=extra)
    
    def log_trade(self, user_id, bot_id, symbol, side, amount, price, status, order_id=None, error=None):
        """Log trade execution"""
        trade_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'bot_id': bot_id,
            'symbol': symbol,
            'side': side,
            'amount': amount,
            'price': price,
            'status': status,
            'order_id': order_id,
            'error': error
        }
        
        message = f"TRADE - User: {user_id}, Bot: {bot_id}, {side.upper()} {amount} {symbol} at {price}, Status: {status}"
        if error:
            message += f", Error: {error}"
        
        self.trade_logger.info(message, extra=trade_data)
    
    def log_bot_action(self, user_id, bot_id, action, status, details=None):
        """Log bot actions (start, stop, etc.)"""
        message = f"BOT ACTION - User: {user_id}, Bot: {bot_id}, Action: {action}, Status: {status}"
        if details:
            message += f", Details: {details}"
        
        self.info(message)
    
    def log_api_error(self, endpoint, error, user_id=None):
        """Log API errors"""
        message = f"API ERROR - Endpoint: {endpoint}, Error: {str(error)}"
        if user_id:
            message += f", User: {user_id}"
        
        self.error(message)
    
    def log_security_event(self, event_type, user_id, details):
        """Log security events"""
        message = f"SECURITY - Type: {event_type}, User: {user_id}, Details: {details}"
        self.warning(message)

# Global logger instance
logger = TradingLogger()