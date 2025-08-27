from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from auth.decorators import admin_required
import logging
from typing import Dict, Any

# Create blueprint
strategy_management_bp = Blueprint('strategy_management', __name__, url_prefix='/api/strategies')
logger = logging.getLogger(__name__)

@strategy_management_bp.route('/available', methods=['GET'])
@jwt_required()
def get_available_strategies():
    """Get list of available strategies"""
    try:
        from bot_engine.trading_engine import TradingEngine
        
        # Get trading engine instance
        trading_engine = current_app.trading_engine if hasattr(current_app, 'trading_engine') else TradingEngine()
        
        # Get available strategies
        strategies = trading_engine.strategy_factory.get_available_strategies()
        
        return jsonify({
            'success': True,
            'strategies': strategies,
            'count': len(strategies)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting available strategies: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get available strategies',
            'details': str(e)
        }), 500

@strategy_management_bp.route('/stats', methods=['GET'])
@jwt_required()
@admin_required
def get_strategy_stats():
    """Get strategy statistics (admin only)"""
    try:
        from bot_engine.trading_engine import TradingEngine
        
        # Get trading engine instance
        trading_engine = current_app.trading_engine if hasattr(current_app, 'trading_engine') else TradingEngine()
        
        # Get strategy statistics
        stats = trading_engine.strategy_factory.get_strategy_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting strategy stats: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get strategy statistics',
            'details': str(e)
        }), 500

@strategy_management_bp.route('/reload', methods=['POST'])
@jwt_required()
@admin_required
def reload_strategies():
    """Reload all strategies (admin only)"""
    try:
        from bot_engine.trading_engine import TradingEngine
        
        # Get trading engine instance
        trading_engine = current_app.trading_engine if hasattr(current_app, 'trading_engine') else TradingEngine()
        
        # Reload strategies
        count = trading_engine.strategy_factory.reload_strategies()
        
        return jsonify({
            'success': True,
            'message': f'Successfully reloaded {count} strategies',
            'reloaded_count': count
        }), 200
        
    except Exception as e:
        logger.error(f"Error reloading strategies: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to reload strategies',
            'details': str(e)
        }), 500

@strategy_management_bp.route('/add', methods=['POST'])
@jwt_required()
@admin_required
def add_strategy():
    """Add a new strategy from code (admin only)"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        strategy_code = data.get('code')
        strategy_name = data.get('name')
        
        if not strategy_code or not strategy_name:
            return jsonify({
                'success': False,
                'error': 'Both code and name are required'
            }), 400
        
        # Validate strategy name
        if not strategy_name.replace('_', '').isalnum():
            return jsonify({
                'success': False,
                'error': 'Strategy name must contain only letters, numbers, and underscores'
            }), 400
        
        from bot_engine.trading_engine import TradingEngine
        
        # Get trading engine instance
        trading_engine = current_app.trading_engine if hasattr(current_app, 'trading_engine') else TradingEngine()
        
        # Add strategy
        strategy_id = trading_engine.strategy_factory.add_strategy_from_code(strategy_code, strategy_name)
        
        if strategy_id:
            return jsonify({
                'success': True,
                'message': f'Strategy added successfully',
                'strategy_id': strategy_id
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to add strategy'
            }), 500
        
    except Exception as e:
        logger.error(f"Error adding strategy: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to add strategy',
            'details': str(e)
        }), 500

@strategy_management_bp.route('/test', methods=['POST'])
@jwt_required()
def test_strategy():
    """Test a strategy with sample data"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        strategy_name = data.get('strategy_name')
        parameters = data.get('parameters', {})
        
        if not strategy_name:
            return jsonify({
                'success': False,
                'error': 'Strategy name is required'
            }), 400
        
        from bot_engine.trading_engine import TradingEngine
        import pandas as pd
        import numpy as np
        
        # Get trading engine instance
        trading_engine = current_app.trading_engine if hasattr(current_app, 'trading_engine') else TradingEngine()
        
        # Create strategy instance
        strategy = trading_engine.strategy_factory.get_strategy(strategy_name, parameters)
        
        if not strategy:
            return jsonify({
                'success': False,
                'error': f'Strategy not found: {strategy_name}'
            }), 404
        
        # Generate sample OHLCV data for testing
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='1H')
        np.random.seed(42)  # For reproducible results
        
        # Generate realistic price data
        base_price = 100.0
        price_changes = np.random.normal(0, 0.02, len(dates))
        prices = [base_price]
        
        for change in price_changes[1:]:
            new_price = prices[-1] * (1 + change)
            prices.append(max(new_price, 1.0))  # Ensure price doesn't go negative
        
        # Create OHLCV data
        sample_data = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
            'close': prices,
            'volume': np.random.randint(1000, 10000, len(dates))
        })
        
        # Test strategy
        try:
            signals = strategy.generate_signals(sample_data)
            
            # Calculate basic metrics
            buy_signals = len(signals[signals.get('signal', 0) == 1]) if 'signal' in signals.columns else 0
            sell_signals = len(signals[signals.get('signal', 0) == -1]) if 'signal' in signals.columns else 0
            
            # Run backtest if available
            backtest_results = None
            if hasattr(strategy, 'backtest'):
                try:
                    backtest_results = strategy.backtest(sample_data)
                except Exception as backtest_error:
                    logger.warning(f"Backtest failed: {backtest_error}")
            
            return jsonify({
                'success': True,
                'strategy_name': strategy_name,
                'parameters': parameters,
                'test_results': {
                    'data_points': len(sample_data),
                    'buy_signals': buy_signals,
                    'sell_signals': sell_signals,
                    'total_signals': buy_signals + sell_signals,
                    'signal_frequency': (buy_signals + sell_signals) / len(sample_data) * 100
                },
                'backtest_results': backtest_results,
                'message': 'Strategy tested successfully'
            }), 200
            
        except Exception as strategy_error:
            return jsonify({
                'success': False,
                'error': f'Strategy execution failed: {str(strategy_error)}'
            }), 500
        
    except Exception as e:
        logger.error(f"Error testing strategy: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to test strategy',
            'details': str(e)
        }), 500

@strategy_management_bp.route('/validate', methods=['POST'])
@jwt_required()
def validate_strategy_code():
    """Validate strategy code without adding it"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        strategy_code = data.get('code')
        
        if not strategy_code:
            return jsonify({
                'success': False,
                'error': 'Strategy code is required'
            }), 400
        
        # Basic syntax validation
        try:
            compile(strategy_code, '<string>', 'exec')
        except SyntaxError as e:
            return jsonify({
                'success': False,
                'error': 'Syntax error in strategy code',
                'details': str(e),
                'line': e.lineno
            }), 400
        
        # Check for required imports and base class
        required_patterns = [
            'BaseStrategy',
            'def generate_signals',
            'def get_parameters',
            'def set_parameters'
        ]
        
        missing_patterns = []
        for pattern in required_patterns:
            if pattern not in strategy_code:
                missing_patterns.append(pattern)
        
        if missing_patterns:
            return jsonify({
                'success': False,
                'error': 'Strategy code is missing required components',
                'missing': missing_patterns,
                'hint': 'Strategy must inherit from BaseStrategy and implement required methods'
            }), 400
        
        # Check for potentially dangerous code
        dangerous_patterns = [
            'import os',
            'import sys',
            'import subprocess',
            'exec(',
            'eval(',
            'open(',
            '__import__',
            'globals(',
            'locals('
        ]
        
        found_dangerous = []
        for pattern in dangerous_patterns:
            if pattern in strategy_code:
                found_dangerous.append(pattern)
        
        warnings = []
        if found_dangerous:
            warnings.append(f"Potentially dangerous code detected: {', '.join(found_dangerous)}")
        
        return jsonify({
            'success': True,
            'message': 'Strategy code validation passed',
            'warnings': warnings
        }), 200
        
    except Exception as e:
        logger.error(f"Error validating strategy code: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to validate strategy code',
            'details': str(e)
        }), 500

@strategy_management_bp.route('/metadata/<strategy_id>', methods=['GET'])
@jwt_required()
def get_strategy_metadata(strategy_id):
    """Get metadata for a specific strategy"""
    try:
        from bot_engine.trading_engine import TradingEngine
        
        # Get trading engine instance
        trading_engine = current_app.trading_engine if hasattr(current_app, 'trading_engine') else TradingEngine()
        
        # Check if dynamic manager is available
        if (hasattr(trading_engine.strategy_factory, 'dynamic_manager') and 
            trading_engine.strategy_factory.dynamic_manager):
            
            metadata = trading_engine.strategy_factory.dynamic_manager.get_strategy_metadata(strategy_id)
            
            if metadata:
                return jsonify({
                    'success': True,
                    'metadata': {
                        'id': metadata.id,
                        'name': metadata.name,
                        'description': metadata.description,
                        'version': metadata.version,
                        'author': metadata.author,
                        'created_at': metadata.created_at.isoformat(),
                        'updated_at': metadata.updated_at.isoformat(),
                        'parameters': metadata.parameters,
                        'tags': metadata.tags,
                        'risk_level': metadata.risk_level,
                        'min_capital': metadata.min_capital,
                        'supported_timeframes': metadata.supported_timeframes,
                        'is_active': metadata.is_active
                    }
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': f'Strategy metadata not found: {strategy_id}'
                }), 404
        else:
            # Fallback for legacy strategies
            strategies = trading_engine.strategy_factory.get_available_strategies()
            strategy_info = next((s for s in strategies if s['id'] == strategy_id), None)
            
            if strategy_info:
                return jsonify({
                    'success': True,
                    'metadata': strategy_info
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': f'Strategy not found: {strategy_id}'
                }), 404
        
    except Exception as e:
        logger.error(f"Error getting strategy metadata: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get strategy metadata',
            'details': str(e)
        }), 500

@strategy_management_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for strategy management"""
    try:
        from bot_engine.trading_engine import TradingEngine
        
        # Get trading engine instance
        trading_engine = TradingEngine()
        
        # Check if dynamic loading is enabled
        dynamic_enabled = (hasattr(trading_engine.strategy_factory, 'enable_dynamic_loading') and 
                          trading_engine.strategy_factory.enable_dynamic_loading)
        
        # Get basic stats
        strategies = trading_engine.strategy_factory.get_available_strategies()
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'dynamic_loading_enabled': dynamic_enabled,
            'available_strategies': len(strategies),
            'timestamp': pd.Timestamp.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Strategy management health check failed: {e}")
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500