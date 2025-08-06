# Import strategies for easier access
from bot_engine.strategies.rsi_strategy import RSIStrategy
from bot_engine.strategies.macd_strategy import MACDStrategy
from bot_engine.strategies.ema_crossover_strategy import EMACrossoverStrategy
from bot_engine.strategies.strategy_factory import StrategyFactory

__all__ = ['RSIStrategy', 'MACDStrategy', 'EMACrossoverStrategy', 'StrategyFactory']