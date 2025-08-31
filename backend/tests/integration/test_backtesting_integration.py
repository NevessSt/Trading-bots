"""Integration tests for backtesting system."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import asyncio
from typing import Dict, List, Any


@pytest.mark.integration
@pytest.mark.backtest
class TestBacktestingIntegration:
    """Integration tests for the complete backtesting system."""
    
    def test_end_to_end_backtest_workflow(self, sample_historical_data, mock_binance_client):
        """Test complete backtesting workflow from data to results."""
        # Mock the trading engine and strategy components
        with patch('bot_engine.trading_engine.TradingEngine') as mock_engine_class:
            mock_engine = Mock()
            mock_engine_class.return_value = mock_engine
            
            # Setup backtest result
            expected_result = {
                'success': True,
                'strategy': 'RSI_MACD_Combined',
                'symbol': 'BTCUSDT',
                'timeframe': '1h',
                'start_date': '2023-01-01',
                'end_date': '2023-12-31',
                'initial_capital': 10000,
                'final_capital': 12500,
                'total_return': 0.25,
                'max_drawdown': 0.12,
                'sharpe_ratio': 1.8,
                'win_rate': 0.65,
                'total_trades': 200,
                'winning_trades': 130,
                'losing_trades': 70,
                'avg_trade_duration': '4.5h',
                'profit_factor': 1.7,
                'trades': [
                    {
                        'timestamp': '2023-01-15T10:00:00',
                        'action': 'BUY',
                        'price': 21500.0,
                        'quantity': 0.465,
                        'pnl': 0,
                        'portfolio_value': 10000
                    },
                    {
                        'timestamp': '2023-01-16T14:30:00',
                        'action': 'SELL',
                        'price': 22100.0,
                        'quantity': 0.465,
                        'pnl': 279.0,
                        'portfolio_value': 10279
                    }
                ]
            }
            
            mock_engine.run_backtest.return_value = expected_result
            
            # Execute backtest
            strategy_config = {
                'name': 'RSI_MACD_Combined',
                'parameters': {
                    'rsi_period': 14,
                    'rsi_oversold': 30,
                    'rsi_overbought': 70,
                    'macd_fast': 12,
                    'macd_slow': 26,
                    'macd_signal': 9
                }
            }
            
            result = mock_engine.run_backtest(
                strategy=strategy_config,
                symbol='BTCUSDT',
                timeframe='1h',
                start_date='2023-01-01',
                end_date='2023-12-31',
                initial_capital=10000,
                data=sample_historical_data
            )
            
            # Verify results
            assert result['success'] is True
            assert result['strategy'] == 'RSI_MACD_Combined'
            assert result['total_return'] == 0.25
            assert result['sharpe_ratio'] == 1.8
            assert result['win_rate'] == 0.65
            assert len(result['trades']) == 2
            
            # Verify engine was called with correct parameters
            mock_engine.run_backtest.assert_called_once()
            call_args = mock_engine.run_backtest.call_args
            assert call_args[1]['strategy'] == strategy_config
            assert call_args[1]['symbol'] == 'BTCUSDT'
            assert call_args[1]['initial_capital'] == 10000
    
    def test_multiple_strategy_comparison(self, sample_historical_data):
        """Test running multiple strategies and comparing results."""
        with patch('bot_engine.trading_engine.TradingEngine') as mock_engine_class:
            mock_engine = Mock()
            mock_engine_class.return_value = mock_engine
            
            # Define multiple strategies
            strategies = [
                {
                    'name': 'RSI_Strategy',
                    'parameters': {'period': 14, 'oversold': 30, 'overbought': 70}
                },
                {
                    'name': 'MACD_Strategy', 
                    'parameters': {'fast': 12, 'slow': 26, 'signal': 9}
                },
                {
                    'name': 'EMA_Crossover',
                    'parameters': {'fast_period': 10, 'slow_period': 20}
                }
            ]
            
            # Mock results for each strategy
            strategy_results = {
                'RSI_Strategy': {
                    'success': True,
                    'total_return': 0.18,
                    'sharpe_ratio': 1.5,
                    'max_drawdown': 0.10,
                    'win_rate': 0.62
                },
                'MACD_Strategy': {
                    'success': True,
                    'total_return': 0.22,
                    'sharpe_ratio': 1.7,
                    'max_drawdown': 0.08,
                    'win_rate': 0.68
                },
                'EMA_Crossover': {
                    'success': True,
                    'total_return': 0.15,
                    'sharpe_ratio': 1.3,
                    'max_drawdown': 0.12,
                    'win_rate': 0.58
                }
            }
            
            def mock_backtest_side_effect(*args, **kwargs):
                strategy_name = kwargs['strategy']['name']
                return strategy_results[strategy_name]
            
            mock_engine.run_backtest.side_effect = mock_backtest_side_effect
            
            # Run backtests for all strategies
            results = []
            for strategy in strategies:
                result = mock_engine.run_backtest(
                    strategy=strategy,
                    symbol='BTCUSDT',
                    timeframe='1h',
                    start_date='2023-01-01',
                    end_date='2023-12-31',
                    initial_capital=10000,
                    data=sample_historical_data
                )
                results.append(result)
            
            # Verify all strategies ran successfully
            assert len(results) == 3
            assert all(result['success'] for result in results)
            
            # Find best performing strategy by Sharpe ratio
            best_strategy = max(results, key=lambda x: x['sharpe_ratio'])
            assert best_strategy['sharpe_ratio'] == 1.7  # MACD should be best
            
            # Verify engine was called for each strategy
            assert mock_engine.run_backtest.call_count == 3
    
    def test_backtest_with_risk_management(self, sample_historical_data):
        """Test backtesting with risk management parameters."""
        with patch('bot_engine.trading_engine.TradingEngine') as mock_engine_class:
            mock_engine = Mock()
            mock_engine_class.return_value = mock_engine
            
            # Setup backtest with risk management
            risk_config = {
                'max_position_size': 0.1,  # 10% of portfolio
                'stop_loss': 0.05,         # 5% stop loss
                'take_profit': 0.15,       # 15% take profit
                'max_drawdown': 0.20,      # 20% max drawdown
                'risk_per_trade': 0.02     # 2% risk per trade
            }
            
            expected_result = {
                'success': True,
                'strategy': 'RSI_with_Risk_Management',
                'risk_metrics': {
                    'max_position_size_used': 0.08,
                    'stop_losses_triggered': 15,
                    'take_profits_triggered': 25,
                    'max_drawdown_reached': 0.18,
                    'avg_risk_per_trade': 0.019,
                    'risk_adjusted_return': 0.16,
                    'calmar_ratio': 0.89
                },
                'total_return': 0.16,
                'max_drawdown': 0.18,
                'sharpe_ratio': 1.4,
                'total_trades': 180,
                'winning_trades': 108,
                'losing_trades': 72
            }
            
            mock_engine.run_backtest.return_value = expected_result
            
            # Execute backtest with risk management
            result = mock_engine.run_backtest(
                strategy={'name': 'RSI_with_Risk_Management', 'parameters': {'period': 14}},
                symbol='BTCUSDT',
                timeframe='1h',
                start_date='2023-01-01',
                end_date='2023-12-31',
                initial_capital=10000,
                risk_management=risk_config,
                data=sample_historical_data
            )
            
            # Verify risk management was applied
            assert result['success'] is True
            assert 'risk_metrics' in result
            assert result['risk_metrics']['max_position_size_used'] <= risk_config['max_position_size']
            assert result['risk_metrics']['max_drawdown_reached'] <= risk_config['max_drawdown']
            assert result['risk_metrics']['stop_losses_triggered'] > 0
            assert result['risk_metrics']['take_profits_triggered'] > 0
    
    def test_backtest_data_validation(self, mock_binance_client):
        """Test backtesting with invalid or insufficient data."""
        with patch('bot_engine.trading_engine.TradingEngine') as mock_engine_class:
            mock_engine = Mock()
            mock_engine_class.return_value = mock_engine
            
            # Test with empty data
            empty_data = pd.DataFrame()
            mock_engine.run_backtest.return_value = {
                'success': False,
                'error': 'Insufficient historical data for backtesting',
                'min_required_periods': 100,
                'provided_periods': 0
            }
            
            result = mock_engine.run_backtest(
                strategy={'name': 'RSI_Strategy', 'parameters': {'period': 14}},
                symbol='BTCUSDT',
                timeframe='1h',
                start_date='2023-01-01',
                end_date='2023-12-31',
                initial_capital=10000,
                data=empty_data
            )
            
            assert result['success'] is False
            assert 'error' in result
            assert 'Insufficient historical data' in result['error']
            
            # Test with insufficient data (less than required periods)
            insufficient_data = pd.DataFrame({
                'timestamp': pd.date_range('2023-01-01', periods=10, freq='1H'),
                'open': [50000] * 10,
                'high': [50100] * 10,
                'low': [49900] * 10,
                'close': [50050] * 10,
                'volume': [100] * 10
            })
            
            mock_engine.run_backtest.return_value = {
                'success': False,
                'error': 'Insufficient historical data for backtesting',
                'min_required_periods': 100,
                'provided_periods': 10
            }
            
            result = mock_engine.run_backtest(
                strategy={'name': 'RSI_Strategy', 'parameters': {'period': 14}},
                symbol='BTCUSDT',
                timeframe='1h',
                start_date='2023-01-01',
                end_date='2023-01-10',
                initial_capital=10000,
                data=insufficient_data
            )
            
            assert result['success'] is False
            assert result['provided_periods'] == 10
            assert result['min_required_periods'] == 100
    
    def test_backtest_performance_metrics_calculation(self, sample_historical_data):
        """Test calculation of various performance metrics."""
        with patch('bot_engine.trading_engine.TradingEngine') as mock_engine_class:
            mock_engine = Mock()
            mock_engine_class.return_value = mock_engine
            
            # Detailed performance metrics
            expected_result = {
                'success': True,
                'strategy': 'Comprehensive_Strategy',
                'performance_metrics': {
                    'total_return': 0.25,
                    'annualized_return': 0.28,
                    'volatility': 0.15,
                    'sharpe_ratio': 1.87,
                    'sortino_ratio': 2.34,
                    'calmar_ratio': 2.33,
                    'max_drawdown': 0.12,
                    'max_drawdown_duration': '45 days',
                    'win_rate': 0.68,
                    'profit_factor': 1.85,
                    'expectancy': 0.0045,
                    'kelly_criterion': 0.15,
                    'var_95': 0.032,
                    'cvar_95': 0.048,
                    'beta': 0.85,
                    'alpha': 0.12,
                    'information_ratio': 0.95,
                    'treynor_ratio': 0.33
                },
                'trade_analysis': {
                    'total_trades': 250,
                    'winning_trades': 170,
                    'losing_trades': 80,
                    'avg_win': 0.025,
                    'avg_loss': -0.015,
                    'largest_win': 0.085,
                    'largest_loss': -0.045,
                    'avg_trade_duration': '3.2 hours',
                    'longest_winning_streak': 12,
                    'longest_losing_streak': 5
                },
                'monthly_returns': {
                    '2023-01': 0.02,
                    '2023-02': 0.015,
                    '2023-03': 0.03,
                    '2023-04': -0.01,
                    '2023-05': 0.025,
                    '2023-06': 0.02,
                    '2023-07': 0.018,
                    '2023-08': 0.022,
                    '2023-09': -0.005,
                    '2023-10': 0.028,
                    '2023-11': 0.015,
                    '2023-12': 0.02
                }
            }
            
            mock_engine.run_backtest.return_value = expected_result
            
            result = mock_engine.run_backtest(
                strategy={'name': 'Comprehensive_Strategy', 'parameters': {}},
                symbol='BTCUSDT',
                timeframe='1h',
                start_date='2023-01-01',
                end_date='2023-12-31',
                initial_capital=10000,
                calculate_detailed_metrics=True,
                data=sample_historical_data
            )
            
            # Verify comprehensive metrics are present
            assert result['success'] is True
            assert 'performance_metrics' in result
            assert 'trade_analysis' in result
            assert 'monthly_returns' in result
            
            # Verify key performance metrics
            metrics = result['performance_metrics']
            assert metrics['sharpe_ratio'] > 1.5  # Good Sharpe ratio
            assert metrics['win_rate'] > 0.6      # Good win rate
            assert metrics['max_drawdown'] < 0.2  # Acceptable drawdown
            assert metrics['profit_factor'] > 1.5 # Profitable strategy
            
            # Verify trade analysis
            trade_analysis = result['trade_analysis']
            assert trade_analysis['total_trades'] > 0
            assert trade_analysis['winning_trades'] > trade_analysis['losing_trades']
            assert trade_analysis['avg_win'] > abs(trade_analysis['avg_loss'])
            
            # Verify monthly returns
            monthly_returns = result['monthly_returns']
            assert len(monthly_returns) == 12
            total_monthly_return = sum(monthly_returns.values())
            assert abs(total_monthly_return - 0.25) < 0.01  # Should match total return
    
    @pytest.mark.slow
    def test_backtest_with_real_time_simulation(self, sample_historical_data):
        """Test backtesting with real-time simulation features."""
        with patch('bot_engine.trading_engine.TradingEngine') as mock_engine_class:
            mock_engine = Mock()
            mock_engine_class.return_value = mock_engine
            
            # Mock real-time simulation result
            expected_result = {
                'success': True,
                'strategy': 'Real_Time_RSI',
                'simulation_mode': 'real_time',
                'execution_details': {
                    'slippage_applied': True,
                    'commission_applied': True,
                    'latency_simulation': True,
                    'market_impact': True,
                    'avg_slippage': 0.0015,
                    'total_commission': 125.50,
                    'avg_latency_ms': 45,
                    'market_impact_cost': 0.008
                },
                'realistic_performance': {
                    'gross_return': 0.28,
                    'net_return': 0.22,  # After costs
                    'transaction_costs': 0.06,
                    'sharpe_ratio_gross': 1.9,
                    'sharpe_ratio_net': 1.6
                }
            }
            
            mock_engine.run_backtest.return_value = expected_result
            
            # Configure real-time simulation
            simulation_config = {
                'apply_slippage': True,
                'slippage_model': 'linear',
                'commission_rate': 0.001,
                'simulate_latency': True,
                'latency_range': (20, 80),  # ms
                'market_impact': True,
                'liquidity_model': 'depth_based'
            }
            
            result = mock_engine.run_backtest(
                strategy={'name': 'Real_Time_RSI', 'parameters': {'period': 14}},
                symbol='BTCUSDT',
                timeframe='1h',
                start_date='2023-01-01',
                end_date='2023-12-31',
                initial_capital=10000,
                simulation_config=simulation_config,
                data=sample_historical_data
            )
            
            # Verify real-time simulation was applied
            assert result['success'] is True
            assert result['simulation_mode'] == 'real_time'
            assert 'execution_details' in result
            assert 'realistic_performance' in result
            
            # Verify costs were applied
            execution = result['execution_details']
            assert execution['slippage_applied'] is True
            assert execution['commission_applied'] is True
            assert execution['total_commission'] > 0
            
            # Verify net performance is lower than gross
            performance = result['realistic_performance']
            assert performance['net_return'] < performance['gross_return']
            assert performance['sharpe_ratio_net'] < performance['sharpe_ratio_gross']
            assert performance['transaction_costs'] > 0