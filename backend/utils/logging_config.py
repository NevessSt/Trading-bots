import logging
import os
import json
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Dict, Any, Optional

class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage(),
            'thread': record.thread,
            'process': record.process
        }
        
        # Add extra fields if present
        if hasattr(record, 'trade_id'):
            log_entry['trade_id'] = record.trade_id
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'exchange'):
            log_entry['exchange'] = record.exchange
        if hasattr(record, 'symbol'):
            log_entry['symbol'] = record.symbol
        if hasattr(record, 'error_code'):
            log_entry['error_code'] = record.error_code
        if hasattr(record, 'execution_time'):
            log_entry['execution_time'] = record.execution_time
        if hasattr(record, 'api_endpoint'):
            log_entry['api_endpoint'] = record.api_endpoint
        if hasattr(record, 'response_time'):
            log_entry['response_time'] = record.response_time
            
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_entry)

class MonitoringLogHandler(logging.Handler):
    """Custom log handler that sends logs to monitoring system"""
    
    def __init__(self):
        super().__init__()
        self._metrics_collector = None
        
    def set_metrics_collector(self, metrics_collector):
        """Set the metrics collector for monitoring integration"""
        self._metrics_collector = metrics_collector
        
    def emit(self, record):
        """Send log record to monitoring system"""
        if self._metrics_collector:
            try:
                # Count log entries by level
                self._metrics_collector.increment_counter(
                    f'logs_{record.levelname.lower()}',
                    labels={'logger': record.name, 'module': record.module}
                )
                
                # Track errors specifically
                if record.levelname in ['ERROR', 'CRITICAL']:
                    error_data = {
                        'timestamp': datetime.utcnow().isoformat(),
                        'level': record.levelname,
                        'message': record.getMessage(),
                        'logger': record.name,
                        'module': record.module,
                        'function': record.funcName,
                        'line': record.lineno
                    }
                    
                    # Add context if available
                    if hasattr(record, 'trade_id'):
                        error_data['trade_id'] = record.trade_id
                    if hasattr(record, 'user_id'):
                        error_data['user_id'] = record.user_id
                    if hasattr(record, 'exchange'):
                        error_data['exchange'] = record.exchange
                    if hasattr(record, 'error_code'):
                        error_data['error_code'] = record.error_code
                        
                    if record.exc_info:
                        error_data['exception'] = self.format(record)
                        
                    self._metrics_collector.record_error('logging', error_data)
                    
            except Exception as e:
                # Don't let monitoring errors break logging
                print(f"Error in monitoring log handler: {e}")

def setup_logging(level=logging.INFO, enable_monitoring=True):
    """
    Setup enhanced logging configuration with monitoring integration
    """
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Create formatters
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    structured_formatter = StructuredFormatter()
    
    # Create handlers
    handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    handlers.append(console_handler)
    
    # File handlers with rotation
    # General log file
    general_handler = RotatingFileHandler(
        os.path.join(logs_dir, 'trading_bot.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    general_handler.setFormatter(structured_formatter)
    handlers.append(general_handler)
    
    # Error log file
    error_handler = RotatingFileHandler(
        os.path.join(logs_dir, 'errors.log'),
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(structured_formatter)
    handlers.append(error_handler)
    
    # Trade log file
    trade_handler = RotatingFileHandler(
        os.path.join(logs_dir, 'trades.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=10
    )
    trade_handler.setFormatter(structured_formatter)
    # Only add trade logs to this handler
    trade_handler.addFilter(lambda record: hasattr(record, 'trade_id'))
    handlers.append(trade_handler)
    
    # API log file
    api_handler = RotatingFileHandler(
        os.path.join(logs_dir, 'api.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    api_handler.setFormatter(structured_formatter)
    # Only add API logs to this handler
    api_handler.addFilter(lambda record: hasattr(record, 'api_endpoint'))
    handlers.append(api_handler)
    
    # Monitoring handler
    monitoring_handler = None
    if enable_monitoring:
        monitoring_handler = MonitoringLogHandler()
        handlers.append(monitoring_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        handlers=handlers,
        force=True  # Override any existing configuration
    )
    
    # Return logger and monitoring handler for integration
    logger = logging.getLogger(__name__)
    return logger, monitoring_handler

def get_trade_logger(trade_id: str, user_id: Optional[str] = None, 
                    exchange: Optional[str] = None, symbol: Optional[str] = None):
    """Get a logger with trade context"""
    logger = logging.getLogger('trading')
    
    # Create a custom adapter that adds trade context
    class TradeLoggerAdapter(logging.LoggerAdapter):
        def process(self, msg, kwargs):
            extra = kwargs.get('extra', {})
            extra.update({
                'trade_id': trade_id,
                'user_id': user_id,
                'exchange': exchange,
                'symbol': symbol
            })
            kwargs['extra'] = extra
            return msg, kwargs
    
    return TradeLoggerAdapter(logger, {})

def get_api_logger(endpoint: str, method: str = 'GET'):
    """Get a logger with API context"""
    logger = logging.getLogger('api')
    
    class APILoggerAdapter(logging.LoggerAdapter):
        def process(self, msg, kwargs):
            extra = kwargs.get('extra', {})
            extra.update({
                'api_endpoint': endpoint,
                'http_method': method
            })
            kwargs['extra'] = extra
            return msg, kwargs
    
    return APILoggerAdapter(logger, {})

def log_performance(func_name: str, execution_time: float, **context):
    """Log performance metrics"""
    logger = logging.getLogger('performance')
    extra = {'execution_time': execution_time, 'function': func_name}
    extra.update(context)
    logger.info(f"Function {func_name} executed in {execution_time:.4f}s", extra=extra)