"""Comprehensive logging service with structured logging and rotation."""

import os
import sys
import json
import logging
import logging.handlers
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, Union
from enum import Enum
import traceback
import threading
from contextlib import contextmanager


class LogLevel(Enum):
    """Log level enumeration."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogCategory(Enum):
    """Log category enumeration for better organization."""
    TRADING = "trading"
    API = "api"
    DATABASE = "database"
    SECURITY = "security"
    SYSTEM = "system"
    NOTIFICATION = "notification"
    BACKTEST = "backtest"
    STRATEGY = "strategy"
    USER = "user"
    PERFORMANCE = "performance"


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        # Base log structure
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "thread_name": record.threadName,
            "process": record.process
        }
        
        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields from record
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                'thread', 'threadName', 'processName', 'process', 'message'
            }:
                extra_fields[key] = value
        
        if extra_fields:
            log_entry["extra"] = extra_fields
        
        return json.dumps(log_entry, default=str, ensure_ascii=False)


class TradingBotLogger:
    """Comprehensive logging service for the trading bot."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the logging service."""
        self.config = config or self._get_default_config()
        self.loggers: Dict[str, logging.Logger] = {}
        self._setup_logging()
        self._lock = threading.Lock()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default logging configuration."""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "format": "structured",  # or "simple"
            "log_dir": str(log_dir),
            "max_file_size": 50 * 1024 * 1024,  # 50MB
            "backup_count": 10,
            "console_output": True,
            "file_output": True,
            "separate_error_log": True,
            "categories": {
                LogCategory.TRADING.value: {"level": "INFO", "file": "trading.log"},
                LogCategory.API.value: {"level": "INFO", "file": "api.log"},
                LogCategory.DATABASE.value: {"level": "WARNING", "file": "database.log"},
                LogCategory.SECURITY.value: {"level": "WARNING", "file": "security.log"},
                LogCategory.SYSTEM.value: {"level": "INFO", "file": "system.log"},
                LogCategory.NOTIFICATION.value: {"level": "INFO", "file": "notifications.log"},
                LogCategory.BACKTEST.value: {"level": "INFO", "file": "backtest.log"},
                LogCategory.STRATEGY.value: {"level": "INFO", "file": "strategy.log"},
                LogCategory.USER.value: {"level": "INFO", "file": "user.log"},
                LogCategory.PERFORMANCE.value: {"level": "INFO", "file": "performance.log"}
            }
        }
    
    def _setup_logging(self):
        """Setup logging configuration."""
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.config["level"]))
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Setup formatters
        if self.config["format"] == "structured":
            formatter = StructuredFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        # Console handler
        if self.config["console_output"]:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
        
        # Main log file handler
        if self.config["file_output"]:
            main_log_file = Path(self.config["log_dir"]) / "trading_bot.log"
            file_handler = logging.handlers.RotatingFileHandler(
                main_log_file,
                maxBytes=self.config["max_file_size"],
                backupCount=self.config["backup_count"],
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        
        # Separate error log
        if self.config["separate_error_log"]:
            error_log_file = Path(self.config["log_dir"]) / "errors.log"
            error_handler = logging.handlers.RotatingFileHandler(
                error_log_file,
                maxBytes=self.config["max_file_size"],
                backupCount=self.config["backup_count"],
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(formatter)
            root_logger.addHandler(error_handler)
        
        # Setup category-specific loggers
        for category, category_config in self.config["categories"].items():
            self._setup_category_logger(category, category_config, formatter)
    
    def _setup_category_logger(self, category: str, category_config: Dict[str, Any], formatter: logging.Formatter):
        """Setup logger for specific category."""
        logger = logging.getLogger(f"trading_bot.{category}")
        logger.setLevel(getattr(logging, category_config["level"]))
        
        # Category-specific file handler
        log_file = Path(self.config["log_dir"]) / category_config["file"]
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=self.config["max_file_size"],
            backupCount=self.config["backup_count"],
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Prevent propagation to avoid duplicate logs
        logger.propagate = False
        
        self.loggers[category] = logger
    
    def get_logger(self, category: Union[LogCategory, str]) -> logging.Logger:
        """Get logger for specific category."""
        if isinstance(category, LogCategory):
            category = category.value
        
        return self.loggers.get(category, logging.getLogger(f"trading_bot.{category}"))
    
    def log(self, category: Union[LogCategory, str], level: Union[LogLevel, str], 
            message: str, **kwargs):
        """Log message with category and level."""
        logger = self.get_logger(category)
        
        if isinstance(level, LogLevel):
            level = level.value
        
        # Add extra context
        extra = {
            'category': category.value if isinstance(category, LogCategory) else category,
            **kwargs
        }
        
        getattr(logger, level.lower())(message, extra=extra)
    
    def log_trade(self, trade_data: Dict[str, Any], level: LogLevel = LogLevel.INFO):
        """Log trading activity."""
        self.log(
            LogCategory.TRADING,
            level,
            f"Trade executed: {trade_data.get('action', 'UNKNOWN')} {trade_data.get('symbol', 'UNKNOWN')}",
            trade_id=trade_data.get('id'),
            symbol=trade_data.get('symbol'),
            action=trade_data.get('action'),
            quantity=trade_data.get('quantity'),
            price=trade_data.get('price'),
            pnl=trade_data.get('pnl'),
            timestamp=trade_data.get('timestamp')
        )
    
    def log_api_call(self, endpoint: str, method: str, status_code: int, 
                     response_time: float, error: Optional[str] = None):
        """Log API call details."""
        level = LogLevel.ERROR if error or status_code >= 400 else LogLevel.INFO
        message = f"API {method} {endpoint} - {status_code} ({response_time:.3f}s)"
        
        if error:
            message += f" - Error: {error}"
        
        self.log(
            LogCategory.API,
            level,
            message,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time=response_time,
            error=error
        )
    
    def log_security_event(self, event_type: str, details: Dict[str, Any], 
                          level: LogLevel = LogLevel.WARNING):
        """Log security-related events."""
        self.log(
            LogCategory.SECURITY,
            level,
            f"Security event: {event_type}",
            event_type=event_type,
            **details
        )
    
    def log_performance_metric(self, metric_name: str, value: float, 
                              context: Optional[Dict[str, Any]] = None):
        """Log performance metrics."""
        self.log(
            LogCategory.PERFORMANCE,
            LogLevel.INFO,
            f"Performance metric: {metric_name} = {value}",
            metric_name=metric_name,
            metric_value=value,
            context=context or {}
        )
    
    def log_backtest_result(self, strategy: str, results: Dict[str, Any]):
        """Log backtesting results."""
        self.log(
            LogCategory.BACKTEST,
            LogLevel.INFO,
            f"Backtest completed for strategy: {strategy}",
            strategy=strategy,
            total_return=results.get('total_return'),
            sharpe_ratio=results.get('sharpe_ratio'),
            max_drawdown=results.get('max_drawdown'),
            win_rate=results.get('win_rate'),
            total_trades=results.get('total_trades')
        )
    
    def log_error(self, category: Union[LogCategory, str], error: Exception, 
                  context: Optional[Dict[str, Any]] = None):
        """Log error with full context."""
        logger = self.get_logger(category)
        
        extra = {
            'category': category.value if isinstance(category, LogCategory) else category,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context or {}
        }
        
        logger.error(f"Error occurred: {str(error)}", exc_info=True, extra=extra)
    
    @contextmanager
    def log_execution_time(self, category: Union[LogCategory, str], operation: str):
        """Context manager to log execution time."""
        start_time = datetime.now()
        try:
            yield
        finally:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.log(
                category,
                LogLevel.INFO,
                f"Operation '{operation}' completed in {execution_time:.3f}s",
                operation=operation,
                execution_time=execution_time
            )
    
    def configure_external_loggers(self):
        """Configure external library loggers."""
        # Reduce noise from external libraries
        external_loggers = [
            'urllib3.connectionpool',
            'requests.packages.urllib3',
            'binance',
            'ccxt',
            'websocket',
            'asyncio'
        ]
        
        for logger_name in external_loggers:
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.WARNING)
    
    def get_log_stats(self) -> Dict[str, Any]:
        """Get logging statistics."""
        log_dir = Path(self.config["log_dir"])
        stats = {
            "log_directory": str(log_dir),
            "total_log_files": len(list(log_dir.glob("*.log*"))),
            "log_files": {},
            "total_size_mb": 0
        }
        
        for log_file in log_dir.glob("*.log*"):
            if log_file.is_file():
                size_mb = log_file.stat().st_size / (1024 * 1024)
                stats["log_files"][log_file.name] = {
                    "size_mb": round(size_mb, 2),
                    "modified": datetime.fromtimestamp(log_file.stat().st_mtime).isoformat()
                }
                stats["total_size_mb"] += size_mb
        
        stats["total_size_mb"] = round(stats["total_size_mb"], 2)
        return stats
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Clean up old log files."""
        log_dir = Path(self.config["log_dir"])
        cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
        
        cleaned_files = []
        for log_file in log_dir.glob("*.log.*"):  # Rotated log files
            if log_file.is_file() and log_file.stat().st_mtime < cutoff_time:
                try:
                    log_file.unlink()
                    cleaned_files.append(str(log_file))
                except OSError as e:
                    self.log_error(LogCategory.SYSTEM, e, {"file": str(log_file)})
        
        if cleaned_files:
            self.log(
                LogCategory.SYSTEM,
                LogLevel.INFO,
                f"Cleaned up {len(cleaned_files)} old log files",
                cleaned_files=cleaned_files
            )


# Global logger instance
_logger_instance: Optional[TradingBotLogger] = None


def get_logger(category: Union[LogCategory, str] = LogCategory.SYSTEM) -> logging.Logger:
    """Get global logger instance."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = TradingBotLogger()
        _logger_instance.configure_external_loggers()
    
    return _logger_instance.get_logger(category)


def setup_logging(config: Optional[Dict[str, Any]] = None) -> TradingBotLogger:
    """Setup global logging configuration."""
    global _logger_instance
    _logger_instance = TradingBotLogger(config)
    _logger_instance.configure_external_loggers()
    return _logger_instance


def log_trade(trade_data: Dict[str, Any], level: LogLevel = LogLevel.INFO):
    """Convenience function to log trades."""
    if _logger_instance:
        _logger_instance.log_trade(trade_data, level)


def log_api_call(endpoint: str, method: str, status_code: int, 
                 response_time: float, error: Optional[str] = None):
    """Convenience function to log API calls."""
    if _logger_instance:
        _logger_instance.log_api_call(endpoint, method, status_code, response_time, error)


def log_error(category: Union[LogCategory, str], error: Exception, 
              context: Optional[Dict[str, Any]] = None):
    """Convenience function to log errors."""
    if _logger_instance:
        _logger_instance.log_error(category, error, context)