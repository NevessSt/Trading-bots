from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from utils.monitoring import get_metrics_collector
from utils.logger import get_logger
from functools import wraps
import json

monitoring_bp = Blueprint('monitoring', __name__, url_prefix='/api/monitoring')
logger = get_logger('monitoring_api')

def admin_required(f):
    """Decorator to require admin access for monitoring endpoints"""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        # In a real implementation, check if user is admin
        # For now, allow all authenticated users
        return f(*args, **kwargs)
    return decorated_function

@monitoring_bp.route('/health', methods=['GET'])
@admin_required
def get_system_health():
    """Get current system health status"""
    try:
        collector = get_metrics_collector()
        health_data = collector.get_system_health()
        
        return jsonify({
            'success': True,
            'data': health_data
        })
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get system health'
        }), 500

@monitoring_bp.route('/dashboard', methods=['GET'])
@admin_required
def get_dashboard_data():
    """Get comprehensive dashboard data"""
    try:
        collector = get_metrics_collector()
        dashboard_data = collector.get_dashboard_data()
        
        return jsonify({
            'success': True,
            'data': dashboard_data
        })
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get dashboard data'
        }), 500

@monitoring_bp.route('/metrics/<metric_name>', methods=['GET'])
@admin_required
def get_metrics(metric_name):
    """Get specific metrics with optional time range"""
    try:
        collector = get_metrics_collector()
        
        # Parse time range parameters
        start_time = None
        end_time = None
        
        if 'start_time' in request.args:
            start_time = datetime.fromisoformat(request.args['start_time'])
        
        if 'end_time' in request.args:
            end_time = datetime.fromisoformat(request.args['end_time'])
        
        # Default to last hour if no time range specified
        if not start_time and not end_time:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=1)
        
        metrics_data = collector.get_metrics(metric_name, start_time, end_time)
        
        return jsonify({
            'success': True,
            'data': {
                'metric_name': metric_name,
                'start_time': start_time.isoformat() if start_time else None,
                'end_time': end_time.isoformat() if end_time else None,
                'points': metrics_data
            }
        })
    except Exception as e:
        logger.error(f"Error getting metrics {metric_name}: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get metrics for {metric_name}'
        }), 500

@monitoring_bp.route('/api-stats', methods=['GET'])
@admin_required
def get_api_stats():
    """Get API performance statistics"""
    try:
        collector = get_metrics_collector()
        
        # Get recent API metrics
        recent_apis = list(collector.api_metrics)[-100:]  # Last 100 API calls
        
        # Calculate statistics
        if recent_apis:
            response_times = [api['response_time'] for api in recent_apis]
            status_codes = [api['status_code'] for api in recent_apis]
            endpoints = [api['endpoint'] for api in recent_apis]
            
            stats = {
                'total_calls': len(recent_apis),
                'avg_response_time': sum(response_times) / len(response_times),
                'min_response_time': min(response_times),
                'max_response_time': max(response_times),
                'error_rate': len([s for s in status_codes if s >= 400]) / len(status_codes) * 100,
                'top_endpoints': {}
            }
            
            # Count endpoint usage
            endpoint_counts = {}
            for endpoint in endpoints:
                endpoint_counts[endpoint] = endpoint_counts.get(endpoint, 0) + 1
            
            # Get top 10 endpoints
            stats['top_endpoints'] = dict(sorted(endpoint_counts.items(), 
                                               key=lambda x: x[1], reverse=True)[:10])
        else:
            stats = {
                'total_calls': 0,
                'avg_response_time': 0,
                'min_response_time': 0,
                'max_response_time': 0,
                'error_rate': 0,
                'top_endpoints': {}
            }
        
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        logger.error(f"Error getting API stats: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get API statistics'
        }), 500

@monitoring_bp.route('/trade-stats', methods=['GET'])
@admin_required
def get_trade_stats():
    """Get trading performance statistics"""
    try:
        collector = get_metrics_collector()
        
        # Get recent trade metrics
        recent_trades = list(collector.trade_metrics)[-100:]  # Last 100 trades
        
        if recent_trades:
            # Calculate statistics
            successful_trades = [t for t in recent_trades if t['status'] == 'completed']
            failed_trades = [t for t in recent_trades if t['status'] == 'failed']
            
            symbols = [t['symbol'] for t in recent_trades]
            amounts = [t['amount'] for t in recent_trades]
            
            stats = {
                'total_trades': len(recent_trades),
                'successful_trades': len(successful_trades),
                'failed_trades': len(failed_trades),
                'success_rate': len(successful_trades) / len(recent_trades) * 100 if recent_trades else 0,
                'total_volume': sum(amounts),
                'avg_trade_size': sum(amounts) / len(amounts) if amounts else 0,
                'active_symbols': list(set(symbols)),
                'symbol_distribution': {}
            }
            
            # Count trades per symbol
            symbol_counts = {}
            for symbol in symbols:
                symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
            
            stats['symbol_distribution'] = symbol_counts
        else:
            stats = {
                'total_trades': 0,
                'successful_trades': 0,
                'failed_trades': 0,
                'success_rate': 0,
                'total_volume': 0,
                'avg_trade_size': 0,
                'active_symbols': [],
                'symbol_distribution': {}
            }
        
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        logger.error(f"Error getting trade stats: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get trade statistics'
        }), 500

@monitoring_bp.route('/errors', methods=['GET'])
@admin_required
def get_error_logs():
    """Get recent error logs"""
    try:
        collector = get_metrics_collector()
        
        # Get query parameters
        limit = int(request.args.get('limit', 50))
        error_type = request.args.get('type')
        
        # Get recent errors
        recent_errors = list(collector.error_metrics)
        
        # Filter by error type if specified
        if error_type:
            recent_errors = [e for e in recent_errors if e['error_type'] == error_type]
        
        # Limit results
        recent_errors = recent_errors[-limit:]
        
        # Calculate error statistics
        error_types = [e['error_type'] for e in recent_errors]
        error_type_counts = {}
        for et in error_types:
            error_type_counts[et] = error_type_counts.get(et, 0) + 1
        
        return jsonify({
            'success': True,
            'data': {
                'errors': recent_errors,
                'total_count': len(recent_errors),
                'error_type_distribution': error_type_counts
            }
        })
    except Exception as e:
        logger.error(f"Error getting error logs: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get error logs'
        }), 500

@monitoring_bp.route('/alerts', methods=['GET'])
@admin_required
def get_active_alerts():
    """Get active system alerts"""
    try:
        collector = get_metrics_collector()
        health = collector.get_system_health()
        
        alerts = []
        
        # Check for system alerts
        if health.get('status') == 'critical':
            if health.get('cpu_usage', 0) > 90:
                alerts.append({
                    'type': 'system',
                    'severity': 'critical',
                    'message': f"High CPU usage: {health['cpu_usage']:.1f}%",
                    'timestamp': health.get('timestamp')
                })
            
            if health.get('memory_usage', 0) > 90:
                alerts.append({
                    'type': 'system',
                    'severity': 'critical',
                    'message': f"High memory usage: {health['memory_usage']:.1f}%",
                    'timestamp': health.get('timestamp')
                })
            
            if health.get('error_rate', 0) > 10:
                alerts.append({
                    'type': 'api',
                    'severity': 'critical',
                    'message': f"High error rate: {health['error_rate']:.1f}%",
                    'timestamp': health.get('timestamp')
                })
        
        elif health.get('status') == 'warning':
            if health.get('cpu_usage', 0) > 70:
                alerts.append({
                    'type': 'system',
                    'severity': 'warning',
                    'message': f"Elevated CPU usage: {health['cpu_usage']:.1f}%",
                    'timestamp': health.get('timestamp')
                })
            
            if health.get('memory_usage', 0) > 70:
                alerts.append({
                    'type': 'system',
                    'severity': 'warning',
                    'message': f"Elevated memory usage: {health['memory_usage']:.1f}%",
                    'timestamp': health.get('timestamp')
                })
        
        return jsonify({
            'success': True,
            'data': {
                'alerts': alerts,
                'total_count': len(alerts)
            }
        })
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get alerts'
        }), 500

@monitoring_bp.route('/cleanup', methods=['POST'])
@admin_required
def cleanup_old_metrics():
    """Manually trigger cleanup of old metrics"""
    try:
        collector = get_metrics_collector()
        collector.cleanup_old_metrics()
        
        return jsonify({
            'success': True,
            'message': 'Old metrics cleaned up successfully'
        })
    except Exception as e:
        logger.error(f"Error cleaning up metrics: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to cleanup metrics'
        }), 500