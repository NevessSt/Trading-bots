# Import main classes for easier access
from bot_engine.trading_engine import TradingEngine
from bot_engine.risk_manager import RiskManager
from bot_engine.strategies import RSIStrategy, MACDStrategy, EMACrossoverStrategy, StrategyFactory

__all__ = ['TradingEngine', 'RiskManager', 'RSIStrategy', 'MACDStrategy', 'EMACrossoverStrategy', 'StrategyFactory']