"""Comprehensive logging utilities for trading bot operations.

This module provides structured logging, performance monitoring,
and integration with error handling systems.
"""

import logging
import json
import time
import functools
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timedelta
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from dataclasses import dataclass, asdict
from threading import Lock
from contextlib import contextmanager

@dataclass
class LogContext:
    """Context information for structured logging"""
    user_id: Optional[str] = None
    trade_id: Optional[str] = None
    exchange: Optional[str] = None
    symbol: Optional[str] = None
    strategy: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values"""
        return {k: v for k, v in asdict(self).items() if v is not None}

class StructuredJSONFormatter(logging.Formatter):
    """Enhanced JSON formatter with trading-specific fields"""
    
    def __init__(self, include_context: bool = True):
        super().__init__()
        self.include_context = include_context
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage(),
            'thread': record.thread,
            'process': record.process
        }
        
        # Add trading-specific context if available
        if self.include_context:
            context_fields = [
                'user_id', 'trade_id', 'exchange', 'symbol', 'strategy',
                'session_id', 'request_id', 'execution_time', 'response_time',
                'api_endpoint', 'error_code', 'order_id', 'position_id',
                'portfolio_value', 'pnl', 'risk_score'
            ]
            
            for field in context_fields:
                if hasattr(record, field) and getattr(record, field) is not None:
                    log_entry[field] = getattr(record, field)
        
        # Add exception information if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': self.formatException(record.exc_info)
            }
        
        # Add extra fields from record
        if hasattr(record, 'extra_data') and isinstance(record.extra_data, dict):
            log_entry.update(record.extra_data)
        
        return json.dumps(log_entry, default=str, ensure_ascii=False)

class PerformanceTracker:
    """Track and log performance metrics"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self._metrics: Dict[str, List[float]] = {}
        self._lock = Lock()
    
    @contextmanager
    def track_operation(self, operation_name: str, **context):
        """Context manager to track operation performance"""
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        try:
            yield
            success = True
        except Exception as e:
            success = False
            context['error'] = str(e)
            raise
        finally:
            end_time = time.time()
            end_memory = self._get_memory_usage()
            
            execution_time = end_time - start_time
            memory_delta = end_memory - start_memory if end_memory and start_memory else None
            
            # Store metrics
            with self._lock:
                if operation_name not in self._metrics:
                    self._metrics[operation_name] = []
                self._metrics[operation_name].append(execution_time)
                
                # Keep only last 1000 measurements
                if len(self._metrics[operation_name]) > 1000:
                    self._metrics[operation_name] = self._metrics[operation_name][-1000:]
            
            # Log performance
            self.logger.info(
                f"Performance: {operation_name} completed",
                extra={
                    'operation': operation_name,
                    'execution_time': execution_time,
                    'memory_delta': memory_delta,
                    'success': success,
                    **context
                }
            )
    
    def _get_memory_usage(self) -> Optional[float]:
        """Get current memory usage in MB"""
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024  # Convert to MB
        except ImportError:
            return None
    
    def get_performance_stats(self, operation_name: str) -> Dict[str, float]:
        """Get performance statistics for an operation"""
        with self._lock:
            if operation_name not in self._metrics:
                return {}
            
            times = self._metrics[operation_name]
            if not times:
                return {}
            
            return {
                'count': len(times),
                'avg_time': sum(times) / len(times),
                'min_time': min(times),
                'max_time': max(times),
                'total_time': sum(times),
                'p95_time': sorted(times)[int(len(times) * 0.95)] if len(times) > 20 else max(times),
                'p99_time': sorted(times)[int(len(times) * 0.99)] if len(times) > 100 else max(times)
            }
    
    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """Get performance statistics for all operations"""
        return {op: self.get_performance_stats(op) for op in self._metrics.keys()}

class TradingBotLogger:
    """Comprehensive logging system for trading bot"""
    
    def __init__(self, name: str = "trading_bot", log_dir: str = "logs", 
                 max_file_size: int = 50*1024*1024, backup_count: int = 10):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Configuration
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        
        # Initialize loggers
        self.loggers = self._setup_loggers()
        
        # Performance tracking
        self.performance_tracker = PerformanceTracker(self.loggers['performance'])
        
        # Context management
        self._context_stack: List[LogContext] = []
        self._lock = Lock()
    
    def _setup_loggers(self) -> Dict[str, logging.Logger]:
        """Setup all specialized loggers"""
        loggers = {}
        
        # Logger configurations: (name, filename, level, use_json)
        logger_configs = [
            ('main', 'trading_bot.log', logging.INFO, True),
            ('trades', 'trades.log', logging.INFO, True),
            ('orders', 'orders.log', logging.INFO, True),
            ('positions', 'positions.log', logging.INFO, True),
            ('portfolio', 'portfolio.log', logging.INFO, True),
            ('strategies', 'strategies.log', logging.INFO, True),
            ('risk', 'risk_management.log', logging.INFO, True),
            ('api', 'api_calls.log', logging.INFO, True),
            ('errors', 'errors.log', logging.WARNING, True),
            ('performance', 'performance.log', logging.INFO, True),
            ('audit', 'audit.log', logging.INFO, True),
            ('debug', 'debug.log', logging.DEBUG, False)
        ]
        
        for logger_name, filename, level, use_json in logger_configs:
            logger = self._create_logger(logger_name, filename, level, use_json)
            loggers[logger_name] = logger
        
        return loggers
    
    def _create_logger(self, logger_name: str, filename: str, 
                      level: int, use_json: bool = True) -> logging.Logger:
        """Create individual logger with appropriate handlers"""
        full_name = f"{self.name}.{logger_name}"
        logger = logging.getLogger(full_name)
        logger.setLevel(level)
        
        # Clear existing handlers
        logger.handlers.clear()
        logger.propagate = False
        
        # File handler with rotation
        file_handler = RotatingFileHandler(
            self.log_dir / filename,
            maxBytes=self.max_file_size,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        
        if use_json:
            file_handler.setFormatter(StructuredJSONFormatter())
        else:
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            ))
        
        logger.addHandler(file_handler)
        
        # Console handler for important loggers
        if logger_name in ['main', 'errors', 'trades']:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.WARNING if logger_name == 'errors' else logging.INFO)
            console_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            ))
            logger.addHandler(console_handler)
        
        return logger
    
    @contextmanager
    def context(self, **context_data):
        """Context manager for adding context to all log messages"""
        context = LogContext(**context_data)
        
        with self._lock:
            self._context_stack.append(context)
        
        try:
            yield context
        finally:
            with self._lock:
                if self._context_stack:
                    self._context_stack.pop()
    
    def _get_current_context(self) -> Dict[str, Any]:
        """Get current logging context"""
        with self._lock:
            if not self._context_stack:
                return {}
            
            # Merge all contexts in stack
            merged_context = {}
            for context in self._context_stack:
                merged_context.update(context.to_dict())
            
            return merged_context
    
    def _log_with_context(self, logger: logging.Logger, level: int, 
                         message: str, **extra_data):
        """Log message with current context"""
        context = self._get_current_context()
        context.update(extra_data)
        
        logger.log(level, message, extra=context)
    
    # Trading-specific logging methods
    def log_trade_execution(self, action: str, symbol: str, quantity: float, 
                           price: float, order_id: str, **context):
        """Log trade execution"""
        self._log_with_context(
            self.loggers['trades'], logging.INFO,
            f"Trade executed: {action} {quantity} {symbol} @ {price}",
            action=action, symbol=symbol, quantity=quantity, 
            price=price, order_id=order_id, **context
        )
    
    def log_order_placement(self, order_type: str, symbol: str, quantity: float,
                           price: Optional[float], order_id: str, **context):
        """Log order placement"""
        price_str = f" @ {price}" if price else " (market)"
        self._log_with_context(
            self.loggers['orders'], logging.INFO,
            f"Order placed: {order_type} {quantity} {symbol}{price_str}",
            order_type=order_type, symbol=symbol, quantity=quantity,
            price=price, order_id=order_id, **context
        )
    
    def log_position_update(self, symbol: str, position_size: float, 
                           avg_price: float, unrealized_pnl: float, **context):
        """Log position updates"""
        self._log_with_context(
            self.loggers['positions'], logging.INFO,
            f"Position update: {symbol} size={position_size} avg_price={avg_price} pnl={unrealized_pnl}",
            symbol=symbol, position_size=position_size, 
            avg_price=avg_price, unrealized_pnl=unrealized_pnl, **context
        )
    
    def log_portfolio_update(self, total_value: float, available_balance: float,
                            total_pnl: float, **context):
        """Log portfolio updates"""
        self._log_with_context(
            self.loggers['portfolio'], logging.INFO,
            f"Portfolio update: value={total_value} balance={available_balance} pnl={total_pnl}",
            total_value=total_value, available_balance=available_balance,
            total_pnl=total_pnl, **context
        )
    
    def log_strategy_signal(self, strategy: str, symbol: str, signal: str,
                           confidence: float, **context):
        """Log strategy signals"""
        self._log_with_context(
            self.loggers['strategies'], logging.INFO,
            f"Strategy signal: {strategy} -> {signal} for {symbol} (confidence: {confidence})",
            strategy=strategy, symbol=symbol, signal=signal,
            confidence=confidence, **context
        )
    
    def log_risk_event(self, event_type: str, severity: str, message: str, **context):
        """Log risk management events"""
        log_level = {
            'low': logging.INFO,
            'medium': logging.WARNING,
            'high': logging.ERROR,
            'critical': logging.CRITICAL
        }.get(severity.lower(), logging.WARNING)
        
        self._log_with_context(
            self.loggers['risk'], log_level,
            f"Risk event [{event_type}]: {message}",
            event_type=event_type, severity=severity, **context
        )
    
    def log_api_call(self, endpoint: str, method: str, status_code: int,
                     response_time: float, **context):
        """Log API calls"""
        log_level = logging.INFO if status_code < 400 else logging.WARNING
        
        self._log_with_context(
            self.loggers['api'], log_level,
            f"API call: {method} {endpoint} -> {status_code} ({response_time:.3f}s)",
            endpoint=endpoint, method=method, status_code=status_code,
            response_time=response_time, **context
        )
    
    def log_error(self, error: Exception, context_message: str = "", **context):
        """Log errors with full context"""
        error_message = f"{context_message}: {str(error)}" if context_message else str(error)
        
        self._log_with_context(
            self.loggers['errors'], logging.ERROR,
            error_message,
            error_type=type(error).__name__,
            error_message=str(error),
            **context
        )
        
        # Also log to main logger for visibility
        self._log_with_context(
            self.loggers['main'], logging.ERROR,
            f"Error occurred: {error_message}",
            error_type=type(error).__name__,
            **context
        )
    
    def log_audit_event(self, event_type: str, user_id: str, action: str, **context):
        """Log audit events for compliance"""
        self._log_with_context(
            self.loggers['audit'], logging.INFO,
            f"Audit: {event_type} - User {user_id} performed {action}",
            event_type=event_type, user_id=user_id, action=action, **context
        )
    
    # Performance tracking methods
    def track_performance(self, operation_name: str, **context):
        """Context manager for performance tracking"""
        return self.performance_tracker.track_operation(operation_name, **context)
    
    def get_performance_stats(self, operation_name: Optional[str] = None) -> Dict[str, Any]:
        """Get performance statistics"""
        if operation_name:
            return self.performance_tracker.get_performance_stats(operation_name)
        else:
            return self.performance_tracker.get_all_stats()
    
    # Utility methods
    def info(self, message: str, **context):
        """Log info message to main logger"""
        self._log_with_context(self.loggers['main'], logging.INFO, message, **context)
    
    def warning(self, message: str, **context):
        """Log warning message to main logger"""
        self._log_with_context(self.loggers['main'], logging.WARNING, message, **context)
    
    def error(self, message: str, **context):
        """Log error message to main logger"""
        self._log_with_context(self.loggers['main'], logging.ERROR, message, **context)
    
    def debug(self, message: str, **context):
        """Log debug message"""
        self._log_with_context(self.loggers['debug'], logging.DEBUG, message, **context)

# Decorators for automatic logging
def log_function_calls(logger: TradingBotLogger, log_args: bool = False, log_result: bool = False):
    """Decorator to automatically log function calls"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            func_name = f"{func.__module__}.{func.__qualname__}"
            
            # Prepare context
            context = {'function': func_name}
            if log_args:
                context['args'] = str(args)[:200]  # Truncate for logging
                context['kwargs'] = {k: str(v)[:100] for k, v in kwargs.items()}
            
            with logger.track_performance(func_name, **context):
                try:
                    result = func(*args, **kwargs)
                    
                    if log_result:
                        context['result'] = str(result)[:200]  # Truncate for logging
                    
                    logger.debug(f"Function call completed: {func_name}", **context)
                    return result
                    
                except Exception as e:
                    logger.log_error(e, f"Function call failed: {func_name}", **context)
                    raise
        
        return wrapper
    return decorator

# Global logger instance
trading_bot_logger = TradingBotLogger()

# Convenience functions
def get_logger(name: str = "trading_bot") -> TradingBotLogger:
    """Get or create a trading bot logger"""
    return TradingBotLogger(name)

def log_trade(action: str, symbol: str, quantity: float, price: float, **context):
    """Quick function to log trades"""
    trading_bot_logger.log_trade_execution(action, symbol, quantity, price, **context)

def log_error(error: Exception, message: str = "", **context):
    """Quick function to log errors"""
    trading_bot_logger.log_error(error, message, **context)

def log_performance(operation_name: str, **context):
    """Quick function for performance tracking"""
    return trading_bot_logger.track_performance(operation_name, **context)