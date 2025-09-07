"""Core Trading Logic Module

This module contains the core trading functionality including:
- Trading engines and execution logic
- Risk management systems
- Portfolio management
- Exchange integrations
- Strategy execution framework
"""

__version__ = "1.0.0"
__author__ = "TradingBot Pro Team"

from .trading_engine import TradingEngine
from .risk_manager import RiskManager
from .portfolio_manager import PortfolioManager
from .exchange_manager import ExchangeManager

__all__ = [
    'TradingEngine',
    'RiskManager', 
    'PortfolioManager',
    'ExchangeManager'
]