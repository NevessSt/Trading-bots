"""API routes for managing async tasks."""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import logging

from services.task_service import task_service
from utils.logging_config import get_api_logger
from models.user import User
from models.bot import Bot
from database import db

logger = get_api_logger('async_tasks')

async_tasks_bp = Blueprint('async_tasks', __name__, url_prefix='/api/async')

@async_tasks_bp.route('/trade/execute', methods=['POST'])
@jwt_required()
def execute_trade_async():
    """Execute a trade asynchronously."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['bot_id', 'symbol', 'side', 'quantity']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Validate bot ownership
        bot = Bot.query.filter_by(id=data['bot_id'], user_id=user_id).first()
        if not bot:
            return jsonify({
                'success': False,
                'error': 'Bot not found or access denied'
            }), 404
        
        # Validate bot is active
        if not bot.is_active:
            return jsonify({
                'success': False,
                'error': 'Bot is not active'
            }), 400
        
        # Prepare trade data
        trade_data = {
            'user_id': user_id,
            'bot_id': data['bot_id'],
            'symbol': data['symbol'],
            'side': data['side'],
            'quantity': float(data['quantity']),
            'order_type': data.get('order_type', 'market'),
            'price': float(data['price']) if data.get('price') else None,
            'take_profit': float(data['take_profit']) if data.get('take_profit') else None,
            'stop_loss': float(data['stop_loss']) if data.get('stop_loss') else None
        }
        
        # Queue the trade execution
        priority = data.get('priority', 5)
        task_id = task_service.execute_trade_async(trade_data, priority)
        
        logger.info(f"Trade execution queued for user {user_id}: {task_id}")
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': 'Trade execution queued successfully',
            'estimated_completion': '1-5 seconds'
        })
        
    except ValueError as e:
        logger.error(f"Validation error in async trade execution: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Error queuing async trade execution: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to queue trade execution'
        }), 500

@async_tasks_bp.route('/market-data/update', methods=['POST'])
@jwt_required()
def update_market_data_async():
    """Update market data asynchronously."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}
        
        # Get symbols to update (optional)
        symbols = data.get('symbols')
        
        # Queue the market data update
        task_id = task_service.update_market_data_async(symbols)
        
        logger.info(f"Market data update queued by user {user_id}: {task_id}")
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': 'Market data update queued successfully',
            'symbols': symbols or 'all',
            'estimated_completion': '10-30 seconds'
        })
        
    except Exception as e:
        logger.error(f"Error queuing market data update: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to queue market data update'
        }), 500

@async_tasks_bp.route('/portfolio/sync', methods=['POST'])
@jwt_required()
def sync_portfolios_async():
    """Sync user portfolios asynchronously."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}
        
        # Get user IDs to sync (admin only for multiple users)
        user_ids = data.get('user_ids')
        if user_ids and len(user_ids) > 1:
            # Check if user is admin
            user = User.query.get(user_id)
            if not user or not user.is_admin:
                user_ids = [user_id]  # Restrict to current user only
        elif not user_ids:
            user_ids = [user_id]  # Default to current user
        
        # Queue the portfolio sync
        task_id = task_service.sync_portfolios_async(user_ids)
        
        logger.info(f"Portfolio sync queued by user {user_id}: {task_id}")
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': 'Portfolio sync queued successfully',
            'user_count': len(user_ids),
            'estimated_completion': '5-15 seconds'
        })
        
    except Exception as e:
        logger.error(f"Error queuing portfolio sync: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to queue portfolio sync'
        }), 500

@async_tasks_bp.route('/notifications/send', methods=['POST'])
@jwt_required()
def send_notification_async():
    """Send notification asynchronously."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['type', 'message']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        notification_data = {
            'user_id': user_id,
            'type': data['type'],
            'message': data['message'],
            'title': data.get('title', 'Trading Bot Notification'),
            'priority': data.get('priority', 'normal'),
            'channels': data.get('channels', ['email']),
            'metadata': data.get('metadata', {})
        }
        
        # Queue the notification
        if data['type'] == 'trade':
            task_id = task_service.send_trade_notification_async(notification_data)
        else:
            task_id = task_service.send_alert_notification_async(notification_data)
        
        logger.info(f"Notification queued by user {user_id}: {task_id}")
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': 'Notification queued successfully',
            'estimated_completion': '1-3 seconds'
        })
        
    except Exception as e:
        logger.error(f"Error queuing notification: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to queue notification'
        }), 500

@async_tasks_bp.route('/analytics/calculate', methods=['POST'])
@jwt_required()
def calculate_analytics_async():
    """Calculate analytics asynchronously."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}
        
        analytics_type = data.get('type', 'portfolio_performance')
        
        if analytics_type == 'portfolio_performance':
            period_days = data.get('period_days', 30)
            task_id = task_service.calculate_portfolio_performance_async(user_id, period_days)
        elif analytics_type == 'trading_report':
            report_type = data.get('report_type', 'monthly')
            task_id = task_service.generate_trading_report_async(user_id, report_type)
        elif analytics_type == 'risk_metrics':
            lookback_days = data.get('lookback_days', 90)
            task_id = task_service.calculate_risk_metrics_async(user_id, lookback_days)
        else:
            return jsonify({
                'success': False,
                'error': f'Unknown analytics type: {analytics_type}'
            }), 400
        
        logger.info(f"Analytics calculation queued by user {user_id}: {task_id}")
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'analytics_type': analytics_type,
            'message': 'Analytics calculation queued successfully',
            'estimated_completion': '30-60 seconds'
        })
        
    except Exception as e:
        logger.error(f"Error queuing analytics calculation: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to queue analytics calculation'
        }), 500

@async_tasks_bp.route('/task/<task_id>/status', methods=['GET'])
@jwt_required()
def get_task_status(task_id):
    """Get the status of an async task."""
    try:
        user_id = get_jwt_identity()
        
        # Get task status
        status = task_service.get_task_status(task_id)
        
        logger.debug(f"Task status requested by user {user_id}: {task_id}")
        
        return jsonify({
            'success': True,
            'task_status': status
        })
        
    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get task status'
        }), 500

@async_tasks_bp.route('/task/<task_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_task(task_id):
    """Cancel an async task."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}
        
        # Cancel the task
        terminate = data.get('terminate', False)
        result = task_service.revoke_task(task_id, terminate)
        
        logger.info(f"Task cancellation requested by user {user_id}: {task_id}")
        
        return jsonify({
            'success': result['success'],
            'message': result.get('message', result.get('error')),
            'terminated': result.get('terminated', False)
        })
        
    except Exception as e:
        logger.error(f"Error cancelling task: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to cancel task'
        }), 500

@async_tasks_bp.route('/tasks/active', methods=['GET'])
@jwt_required()
def get_active_tasks():
    """Get list of active tasks."""
    try:
        user_id = get_jwt_identity()
        
        # Check if user is admin
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            return jsonify({
                'success': False,
                'error': 'Admin access required'
            }), 403
        
        # Get active tasks
        result = task_service.get_active_tasks()
        
        logger.info(f"Active tasks requested by admin user {user_id}")
        
        return jsonify({
            'success': result['success'],
            'active_tasks': result.get('active_tasks', {}),
            'worker_count': result.get('worker_count', 0)
        })
        
    except Exception as e:
        logger.error(f"Error getting active tasks: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get active tasks'
        }), 500

@async_tasks_bp.route('/workers/stats', methods=['GET'])
@jwt_required()
def get_worker_stats():
    """Get Celery worker statistics."""
    try:
        user_id = get_jwt_identity()
        
        # Check if user is admin
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            return jsonify({
                'success': False,
                'error': 'Admin access required'
            }), 403
        
        # Get worker stats
        result = task_service.get_worker_stats()
        
        logger.info(f"Worker stats requested by admin user {user_id}")
        
        return jsonify({
            'success': result['success'],
            'worker_stats': result.get('worker_stats', {}),
            'worker_count': result.get('worker_count', 0)
        })
        
    except Exception as e:
        logger.error(f"Error getting worker stats: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get worker stats'
        }), 500

@async_tasks_bp.route('/queues/status', methods=['GET'])
@jwt_required()
def get_queue_status():
    """Get queue status and lengths."""
    try:
        user_id = get_jwt_identity()
        
        # Check if user is admin
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            return jsonify({
                'success': False,
                'error': 'Admin access required'
            }), 403
        
        # Get queue lengths
        result = task_service.get_queue_lengths()
        
        logger.info(f"Queue status requested by admin user {user_id}")
        
        return jsonify({
            'success': result['success'],
            'queue_info': result.get('queue_info', {}),
            'timestamp': result.get('timestamp')
        })
        
    except Exception as e:
        logger.error(f"Error getting queue status: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get queue status'
        }), 500

@async_tasks_bp.route('/maintenance/schedule', methods=['POST'])
@jwt_required()
def schedule_maintenance():
    """Schedule maintenance tasks."""
    try:
        user_id = get_jwt_identity()
        
        # Check if user is admin
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            return jsonify({
                'success': False,
                'error': 'Admin access required'
            }), 403
        
        # Schedule maintenance tasks
        result = task_service.schedule_maintenance_tasks()
        
        logger.info(f"Maintenance tasks scheduled by admin user {user_id}")
        
        return jsonify({
            'success': result['success'],
            'task_id': result.get('task_id'),
            'message': result.get('message', result.get('error'))
        })
        
    except Exception as e:
        logger.error(f"Error scheduling maintenance: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to schedule maintenance tasks'
        }), 500

@async_tasks_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for async task system."""
    try:
        # Basic health check
        result = task_service.get_worker_stats()
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'workers_available': result.get('worker_count', 0) > 0,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500