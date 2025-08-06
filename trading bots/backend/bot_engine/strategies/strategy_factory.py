from bot_engine.strategies.rsi_strategy import RSIStrategy
from bot_engine.strategies.macd_strategy import MACDStrategy
from bot_engine.strategies.ema_crossover_strategy import EMACrossoverStrategy

class StrategyFactory:
    """Factory class for creating trading strategies"""
    
    @staticmethod
    def get_strategy(strategy_name, parameters=None):
        """Get a strategy instance by name
        
        Args:
            strategy_name (str): Name of the strategy
            parameters (dict, optional): Strategy parameters
            
        Returns:
            BaseStrategy: Strategy instance
        
        Raises:
            ValueError: If strategy name is not recognized
        """
        parameters = parameters or {}
        
        if strategy_name.lower() == 'rsi':
            strategy = RSIStrategy(
                rsi_period=parameters.get('rsi_period', 14),
                overbought=parameters.get('overbought', 70),
                oversold=parameters.get('oversold', 30)
            )
        elif strategy_name.lower() == 'macd':
            strategy = MACDStrategy(
                fast_period=parameters.get('fast_period', 12),
                slow_period=parameters.get('slow_period', 26),
                signal_period=parameters.get('signal_period', 9)
            )
        elif strategy_name.lower() == 'ema_crossover':
            strategy = EMACrossoverStrategy(
                fast_period=parameters.get('fast_period', 9),
                slow_period=parameters.get('slow_period', 21)
            )
        else:
            raise ValueError(f"Unknown strategy: {strategy_name}")
        
        return strategy
    
    @staticmethod
    def get_available_strategies():
        """Get a list of available strategies
        
        Returns:
            list: List of strategy information dictionaries
        """
        strategies = [
            {
                'id': 'rsi',
                'name': 'RSI Strategy',
                'description': 'Relative Strength Index strategy',
                'parameters': {
                    'rsi_period': {
                        'type': 'integer',
                        'default': 14,
                        'min': 2,
                        'max': 50,
                        'description': 'RSI period'
                    },
                    'overbought': {
                        'type': 'integer',
                        'default': 70,
                        'min': 50,
                        'max': 90,
                        'description': 'Overbought threshold'
                    },
                    'oversold': {
                        'type': 'integer',
                        'default': 30,
                        'min': 10,
                        'max': 50,
                        'description': 'Oversold threshold'
                    }
                }
            },
            {
                'id': 'macd',
                'name': 'MACD Strategy',
                'description': 'Moving Average Convergence Divergence strategy',
                'parameters': {
                    'fast_period': {
                        'type': 'integer',
                        'default': 12,
                        'min': 2,
                        'max': 50,
                        'description': 'Fast EMA period'
                    },
                    'slow_period': {
                        'type': 'integer',
                        'default': 26,
                        'min': 5,
                        'max': 100,
                        'description': 'Slow EMA period'
                    },
                    'signal_period': {
                        'type': 'integer',
                        'default': 9,
                        'min': 2,
                        'max': 50,
                        'description': 'Signal line period'
                    }
                }
            },
            {
                'id': 'ema_crossover',
                'name': 'EMA Crossover Strategy',
                'description': 'Exponential Moving Average Crossover strategy',
                'parameters': {
                    'fast_period': {
                        'type': 'integer',
                        'default': 9,
                        'min': 2,
                        'max': 50,
                        'description': 'Fast EMA period'
                    },
                    'slow_period': {
                        'type': 'integer',
                        'default': 21,
                        'min': 5,
                        'max': 100,
                        'description': 'Slow EMA period'
                    }
                }
            }
        ]
        
        return strategies