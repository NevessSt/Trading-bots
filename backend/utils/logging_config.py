import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging(level=logging.INFO):
    """
    Setup logging configuration for the trading bot
    """
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        handlers=[
            RotatingFileHandler(
                os.path.join(logs_dir, 'trading_bot.log'),
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            ),
            logging.StreamHandler()  # Console output
        ]
    )
    
    return logging.getLogger(__name__)