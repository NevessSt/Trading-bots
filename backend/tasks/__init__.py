"""Celery tasks package for async processing."""

from .trading import *
from .notifications import *
from .analytics import *
from .maintenance import *

__all__ = [
    # Trading tasks
    'execute_trade_async',
    'update_market_data',
    'sync_portfolios',
    'process_order_book',
    'calculate_indicators',
    
    # Notification tasks
    'send_trade_notification',
    'send_alert_notification',
    'send_email_notification',
    'send_telegram_notification',
    
    # Analytics tasks
    'calculate_portfolio_metrics',
    'generate_performance_report',
    'update_trade_statistics',
    'process_backtest',
    
    # Maintenance tasks
    'cleanup_stale_orders',
    'system_health_check',
    'database_maintenance',
    'log_rotation',
]