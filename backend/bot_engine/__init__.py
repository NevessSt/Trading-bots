# Import main classes for easier access
from .trading_engine import TradingEngine
from .risk_manager import RiskManager
from .backtester import Backtester
from .strategies.rsi_strategy import RSIStrategy
from .strategies.macd_strategy import MACDStrategy
from .strategies.ema_crossover_strategy import EMACrossoverStrategy
from .strategies.strategy_factory import StrategyFactory

__all__ = ['TradingEngine', 'RiskManager', 'Backtester', 'RSIStrategy', 'MACDStrategy', 'EMACrossoverStrategy', 'StrategyFactory']