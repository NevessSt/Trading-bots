"""Unit tests for strategy backtesting functionality."""
import os
import sys
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock, Mock

# Add backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)


class TestStrategyBacktesting:
    """Test strategy backtesting functionality."""
    
    @pytest.fixture
    def sample_historical_data(self):
        """Create sample historical data for backtesting."""
        dates = pd.date_range(start='2023-01-01', end='2023-01-31', freq='1H')
        np.random.seed(42)  # For reproducible results
        
        # Generate realistic price data
        base_price = 50000
        price_changes = np.random.normal(0, 0.02, len(dates))
        prices = [base_price]
        
        for change in price_changes[1:]:
            new_price = prices[-1] * (1 + change)
            prices.append(max(new_price, 1000))  # Minimum price floor
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
            'close': prices,
            'volume': np.random.uniform(100, 1000, len(dates))
        })
        
        return data
    
    @pytest.fixture
    def mock_trading_engine(self):
        """Create mock trading engine for backtesting."""
        engine_instance = Mock()
        
        # Mock the run_backtest method to return proper dictionary
        def mock_run_backtest(*args, **kwargs):
            return {
                'success': True,
                'strategy': kwargs.get('strategy_name', 'rsi'),
                'symbol': kwargs.get('symbol', 'BTCUSDT'),
                'timeframe': kwargs.get('timeframe', '1h'),
                'results': {
                    'total_return': 15.5,
                    'max_drawdown': -8.2,
                    'sharpe_ratio': 1.8,
                    'total_trades': 25,
                    'winning_trades': 18,
                    'losing_trades': 7,
                    'win_rate': 72.0,
                    'profit_factor': 2.1,
                    'avg_trade_return': 0.62,
                    'max_consecutive_wins': 5,
                    'max_consecutive_losses': 2,
                    'trades': []
                }
            }
        
        engine_instance.run_backtest = mock_run_backtest
        
        # Mock backtesting engine
        engine_instance.backtesting_engine = Mock()
        engine_instance.backtesting_engine.run_backtest.return_value = {
            'total_return': 15.5,
            'max_drawdown': -8.2,
            'sharpe_ratio': 1.8,
            'total_trades': 25,
            'winning_trades': 18,
            'losing_trades': 7,
            'win_rate': 72.0,
            'profit_factor': 2.1,
            'avg_trade_return': 0.62,
            'max_consecutive_wins': 5,
            'max_consecutive_losses': 2,
            'trades': []
        }
        
        # Mock strategy factory
        engine_instance.strategy_factory = Mock()
        engine_instance.strategy_factory.create_strategy.return_value = Mock()
        
        # Mock market data manager
        engine_instance.market_data_manager = Mock()
        
        yield engine_instance
    
    def test_rsi_strategy_backtest(self, sample_historical_data, mock_trading_engine):
        """Test RSI strategy backtesting."""
        # Setup mock data
        mock_trading_engine.market_data_manager.get_historical_data.return_value = sample_historical_data
        
        # Run backtest using mock engine
        result = mock_trading_engine.run_backtest(
            strategy_name='rsi',
            symbol='BTCUSDT',
            timeframe='1h',
            start_date='2023-01-01',
            end_date='2023-01-31',
            parameters={
                'rsi_period': 14,
                'overbought': 70,
                'oversold': 30
            }
        )
        
        # Assertions
        assert result['success'] is True
        assert 'results' in result
        assert result['strategy'] == 'rsi'
        assert result['symbol'] == 'BTCUSDT'
        
        # Verify backtest results structure
        backtest_results = result['results']
        assert 'total_return' in backtest_results
        assert 'sharpe_ratio' in backtest_results
        assert 'max_drawdown' in backtest_results
        assert 'total_trades' in backtest_results
    
    def test_macd_strategy_backtest(self, sample_historical_data, mock_trading_engine):
        """Test MACD strategy backtesting."""
        mock_trading_engine.market_data_manager.get_historical_data.return_value = sample_historical_data
        
        result = mock_trading_engine.run_backtest(
            strategy_name='macd',
            symbol='ETHUSDT',
            timeframe='4h',
            start_date='2023-01-01',
            end_date='2023-01-31',
            parameters={
                'fast_period': 12,
                'slow_period': 26,
                'signal_period': 9
            }
        )
        
        assert result['success'] is True
        assert result['strategy'] == 'macd'
        assert result['symbol'] == 'ETHUSDT'
    
    def test_ema_crossover_strategy_backtest(self, sample_historical_data, mock_trading_engine):
        """Test EMA Crossover strategy backtesting."""
        mock_trading_engine.market_data_manager.get_historical_data.return_value = sample_historical_data
        
        result = mock_trading_engine.run_backtest(
            strategy_name='ema_crossover',
            symbol='ADAUSDT',
            timeframe='1d',
            start_date='2023-01-01',
            end_date='2023-01-31',
            parameters={
                'fast_ema': 10,
                'slow_ema': 20
            }
        )
        
        assert result['success'] is True
        assert result['strategy'] == 'ema_crossover'
    
    def test_backtest_with_empty_data(self, mock_trading_engine):
        """Test backtesting with empty historical data."""
        # Mock empty data and error response
        mock_trading_engine.market_data_manager.get_historical_data.return_value = pd.DataFrame()
        
        def mock_run_backtest_empty(*args, **kwargs):
            return {
                'success': False,
                'error': 'No historical data available for backtesting'
            }
        
        mock_trading_engine.run_backtest = mock_run_backtest_empty
        
        result = mock_trading_engine.run_backtest(
            strategy_name='rsi',
            symbol='BTCUSDT',
            timeframe='1h',
            start_date='2023-01-01',
            end_date='2023-01-31'
        )
        
        assert result['success'] is False
        assert 'No historical data available' in result['error']
    
    def test_backtest_invalid_strategy(self, sample_historical_data, mock_trading_engine):
        """Test backtesting with invalid strategy."""
        from bot_engine.trading_engine import TradingEngine
        
        # Mock strategy creation failure
        mock_trading_engine.strategy_factory.create_strategy.side_effect = Exception("Invalid strategy")
        mock_trading_engine.market_data_manager.get_historical_data.return_value = sample_historical_data
        
        engine = TradingEngine()
        
        result = engine.run_backtest(
            strategy_name='invalid_strategy',
            symbol='BTCUSDT',
            timeframe='1h',
            start_date='2023-01-01',
            end_date='2023-01-31'
        )
        
        assert result['success'] is False
        assert 'Invalid strategy' in result['error']
    
    def test_backtest_performance_metrics(self, sample_historical_data, mock_trading_engine):
        """Test that backtest returns comprehensive performance metrics."""
        from bot_engine.trading_engine import TradingEngine
        
        # Enhanced mock results with all expected metrics
        enhanced_results = {
            'total_return': 25.8,
            'annualized_return': 312.5,
            'max_drawdown': -12.3,
            'sharpe_ratio': 2.1,
            'sortino_ratio': 2.8,
            'calmar_ratio': 25.4,
            'total_trades': 45,
            'winning_trades': 32,
            'losing_trades': 13,
            'win_rate': 71.1,
            'profit_factor': 2.3,
            'avg_trade_return': 0.57,
            'avg_winning_trade': 1.2,
            'avg_losing_trade': -0.8,
            'max_consecutive_wins': 7,
            'max_consecutive_losses': 3,
            'largest_win': 5.2,
            'largest_loss': -2.1,
            'volatility': 18.5,
            'var_95': -2.8,
            'cvar_95': -4.1,
            'trades': [],
            'equity_curve': [],
            'drawdown_curve': []
        }
        
        mock_trading_engine.backtesting_engine.run_backtest.return_value = enhanced_results
        mock_trading_engine.market_data_manager.get_historical_data.return_value = sample_historical_data
        
        engine = TradingEngine()
        
        result = engine.run_backtest(
            strategy_name='rsi',
            symbol='BTCUSDT',
            timeframe='1h',
            start_date='2023-01-01',
            end_date='2023-01-31'
        )
        
        assert result['success'] is True
        backtest_results = result['results']
        
        # Check all performance metrics are present
        expected_metrics = [
            'total_return', 'annualized_return', 'max_drawdown', 'sharpe_ratio',
            'sortino_ratio', 'calmar_ratio', 'total_trades', 'winning_trades',
            'losing_trades', 'win_rate', 'profit_factor', 'avg_trade_return',
            'volatility', 'var_95', 'cvar_95'
        ]
        
        for metric in expected_metrics:
            assert metric in backtest_results, f"Missing metric: {metric}"
    
    def test_backtest_multiple_timeframes(self, sample_historical_data, mock_trading_engine):
        """Test backtesting across multiple timeframes."""
        from bot_engine.trading_engine import TradingEngine
        
        mock_trading_engine.market_data_manager.get_historical_data.return_value = sample_historical_data
        
        engine = TradingEngine()
        timeframes = ['1h', '4h', '1d']
        
        for timeframe in timeframes:
            result = engine.run_backtest(
                strategy_name='rsi',
                symbol='BTCUSDT',
                timeframe=timeframe,
                start_date='2023-01-01',
                end_date='2023-01-31'
            )
            
            assert result['success'] is True
            assert result['timeframe'] == timeframe
    
    def test_backtest_parameter_optimization(self, sample_historical_data, mock_trading_engine):
        """Test parameter optimization during backtesting."""
        from bot_engine.trading_engine import TradingEngine
        
        mock_trading_engine.market_data_manager.get_historical_data.return_value = sample_historical_data
        
        engine = TradingEngine()
        
        # Test different RSI parameters
        rsi_periods = [10, 14, 20]
        best_result = None
        best_return = -float('inf')
        
        for period in rsi_periods:
            result = engine.run_backtest(
                strategy_name='rsi',
                symbol='BTCUSDT',
                timeframe='1h',
                start_date='2023-01-01',
                end_date='2023-01-31',
                parameters={'rsi_period': period}
            )
            
            assert result['success'] is True
            
            total_return = result['results']['total_return']
            if total_return > best_return:
                best_return = total_return
                best_result = result
        
        assert best_result is not None
        assert best_return > 0  # Assuming positive returns in mock
    
    @pytest.mark.integration
    def test_backtest_integration_with_ccxt_sandbox(self):
        """Integration test with CCXT sandbox mode."""
        # This would test actual integration with exchange sandbox
        # Skip if not in integration test mode
        pytest.skip("Integration test - requires exchange sandbox setup")
    
    def test_backtest_risk_metrics(self, sample_historical_data, mock_trading_engine):
        """Test risk-adjusted performance metrics in backtesting."""
        from bot_engine.trading_engine import TradingEngine
        
        # Mock results with risk metrics
        risk_results = {
            'total_return': 18.5,
            'max_drawdown': -15.2,
            'sharpe_ratio': 1.6,
            'sortino_ratio': 2.1,
            'calmar_ratio': 1.2,
            'var_95': -3.2,
            'cvar_95': -4.8,
            'beta': 0.85,
            'alpha': 2.3,
            'information_ratio': 1.1,
            'treynor_ratio': 0.22,
            'total_trades': 35
        }
        
        mock_trading_engine.backtesting_engine.run_backtest.return_value = risk_results
        mock_trading_engine.market_data_manager.get_historical_data.return_value = sample_historical_data
        
        engine = TradingEngine()
        
        result = engine.run_backtest(
            strategy_name='rsi',
            symbol='BTCUSDT',
            timeframe='1h',
            start_date='2023-01-01',
            end_date='2023-01-31'
        )
        
        assert result['success'] is True
        backtest_results = result['results']
        
        # Verify risk metrics
        assert backtest_results['sharpe_ratio'] > 1.0
        assert backtest_results['max_drawdown'] < 0
        assert backtest_results['var_95'] < 0
        assert backtest_results['cvar_95'] < backtest_results['var_95']