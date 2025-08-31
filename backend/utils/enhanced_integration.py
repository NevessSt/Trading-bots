import logging
from typing import Dict, Any, Optional
from datetime import datetime
from flask import Flask, request, jsonify, g
from functools import wraps

# Import our enhanced components
from middleware.enhanced_security import EnhancedSecurityMiddleware
from utils.error_handler import EnhancedErrorHandler
from utils.trading_safety import TradingSafetySystem
from services.enhanced_notification_service import enhanced_notification_service, NotificationType

# Configure logging
logging.basicConfig(level=logging.INFO)
integration_logger = logging.getLogger('enhanced_integration')

class EnhancedTradingBotIntegration:
    """Main integration class that coordinates all enhanced components"""
    
    def __init__(self, app: Flask = None):
        self.app = app
        self.security_middleware = None
        self.error_handler = None
        self.safety_system = None
        self.notification_service = enhanced_notification_service
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize all enhanced components with Flask app"""
        self.app = app
        
        # Initialize enhanced security
        self.security_middleware = EnhancedSecurityMiddleware()
        self.security_middleware.init_app(app)
        
        # Initialize enhanced error handler
        self.error_handler = EnhancedErrorHandler()
        
        # Initialize trading safety system
        safety_config = app.config.get('TRADING_SAFETY', {})
        self.safety_system = TradingSafetySystem(safety_config)
        
        # Register enhanced error handlers
        self._register_error_handlers(app)
        
        # Register enhanced routes
        self._register_enhanced_routes(app)
        
        integration_logger.info("Enhanced Trading Bot Integration initialized successfully")
    
    def _register_error_handlers(self, app: Flask):
        """Register enhanced error handlers"""
        
        @app.errorhandler(400)
        def handle_bad_request(error):
            return self._handle_error(error, 'Bad Request', 400)
        
        @app.errorhandler(401)
        def handle_unauthorized(error):
            return self._handle_error(error, 'Unauthorized', 401)
        
        @app.errorhandler(403)
        def handle_forbidden(error):
            return self._handle_error(error, 'Forbidden', 403)
        
        @app.errorhandler(404)
        def handle_not_found(error):
            return self._handle_error(error, 'Not Found', 404)
        
        @app.errorhandler(429)
        def handle_rate_limit(error):
            return self._handle_error(error, 'Rate Limit Exceeded', 429)
        
        @app.errorhandler(500)
        def handle_internal_error(error):
            return self._handle_error(error, 'Internal Server Error', 500)
        
        @app.errorhandler(Exception)
        def handle_generic_exception(error):
            return self._handle_error(error, 'Unexpected Error', 500)
    
    def _handle_error(self, error, message: str, status_code: int):
        """Enhanced error handling with logging and notifications"""
        try:
            # Log the error
            error_details = {
                'error': str(error),
                'message': message,
                'status_code': status_code,
                'endpoint': request.endpoint,
                'method': request.method,
                'url': request.url,
                'user_agent': request.headers.get('User-Agent'),
                'ip_address': request.remote_addr,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            integration_logger.error(f"Error {status_code}: {message}", extra=error_details)
            
            # Send notification for critical errors
            if status_code >= 500:
                user_id = getattr(g, 'current_user_id', None)
                if user_id:
                    self.notification_service.send_notification(
                        user_id=user_id,
                        notification_type=NotificationType.SYSTEM_ERROR,
                        data={'error': message, 'status_code': status_code}
                    )
            
            # Return error response
            return jsonify({
                'success': False,
                'error': message,
                'status_code': status_code,
                'timestamp': datetime.utcnow().isoformat()
            }), status_code
            
        except Exception as e:
            integration_logger.critical(f"Error in error handler: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Critical system error',
                'status_code': 500
            }), 500
    
    def _register_enhanced_routes(self, app: Flask):
        """Register enhanced API routes for system management"""
        
        @app.route('/api/system/health', methods=['GET'])
        def system_health():
            """Enhanced system health check"""
            try:
                health_data = {
                    'status': 'healthy',
                    'timestamp': datetime.utcnow().isoformat(),
                    'components': {
                        'security': self.security_middleware.get_security_stats() if self.security_middleware else None,
                        'safety': self.safety_system.get_system_status() if self.safety_system else None,
                        'notifications': self.notification_service.get_service_stats(),
                        'error_handler': self.error_handler.get_stats() if self.error_handler else None
                    }
                }
                
                return jsonify({
                    'success': True,
                    'data': health_data
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'Health check failed: {str(e)}'
                }), 500
        
        @app.route('/api/system/security/stats', methods=['GET'])
        @self.security_middleware.require_secure_endpoint
        def security_stats():
            """Get security statistics"""
            try:
                stats = self.security_middleware.get_security_stats()
                return jsonify({
                    'success': True,
                    'data': stats
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @app.route('/api/system/safety/status', methods=['GET'])
        @self.security_middleware.require_trading_security
        def safety_status():
            """Get trading safety system status"""
            try:
                status = self.safety_system.get_system_status()
                return jsonify({
                    'success': True,
                    'data': status
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @app.route('/api/system/safety/emergency-stop', methods=['POST'])
        @self.security_middleware.require_secure_endpoint
        def emergency_stop():
            """Activate emergency stop"""
            try:
                data = request.get_json() or {}
                reason = data.get('reason', 'Manual emergency stop')
                
                self.safety_system.activate_emergency_stop(reason)
                
                # Send critical notification
                user_id = getattr(g, 'current_user_id', None)
                if user_id:
                    self.notification_service.send_notification(
                        user_id=user_id,
                        notification_type=NotificationType.EMERGENCY_STOP,
                        data={'reason': reason}
                    )
                
                return jsonify({
                    'success': True,
                    'message': 'Emergency stop activated',
                    'reason': reason
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @app.route('/api/system/notifications/preferences', methods=['GET', 'POST'])
        @self.security_middleware.authenticate_request
        def notification_preferences():
            """Get or set user notification preferences"""
            try:
                user_id = getattr(g, 'current_user_id')
                
                if request.method == 'GET':
                    # Get current preferences
                    prefs = self.notification_service.user_preferences.get(user_id, {})
                    return jsonify({
                        'success': True,
                        'data': prefs
                    })
                
                elif request.method == 'POST':
                    # Set preferences
                    data = request.get_json() or {}
                    self.notification_service.set_user_preferences(user_id, data)
                    
                    return jsonify({
                        'success': True,
                        'message': 'Notification preferences updated'
                    })
                    
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @app.route('/api/system/notifications/history', methods=['GET'])
        @self.security_middleware.authenticate_request
        def notification_history():
            """Get user notification history"""
            try:
                user_id = getattr(g, 'current_user_id')
                limit = request.args.get('limit', 50, type=int)
                
                history = self.notification_service.get_notification_history(user_id, limit)
                
                return jsonify({
                    'success': True,
                    'data': history
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
    
    def create_enhanced_trading_decorator(self):
        """Create a decorator for enhanced trading operations"""
        def enhanced_trading_operation(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                try:
                    # Security checks
                    if not self.security_middleware.validate_trading_request():
                        return jsonify({
                            'success': False,
                            'error': 'Security validation failed'
                        }), 403
                    
                    # Safety checks
                    user_id = getattr(g, 'current_user_id')
                    trade_data = request.get_json() or {}
                    
                    safety_result = self.safety_system.assess_trade_risk(user_id, trade_data)
                    if not safety_result.approved:
                        # Send risk warning notification
                        self.notification_service.send_notification(
                            user_id=user_id,
                            notification_type=NotificationType.RISK_WARNING,
                            data={
                                'reason': safety_result.reason,
                                'risk_level': safety_result.risk_level.value
                            }
                        )
                        
                        return jsonify({
                            'success': False,
                            'error': 'Trade rejected by safety system',
                            'reason': safety_result.reason,
                            'risk_level': safety_result.risk_level.value
                        }), 400
                    
                    # Execute the trading operation
                    result = f(*args, **kwargs)
                    
                    # Log successful trade
                    if isinstance(result, tuple) and len(result) == 2:
                        response_data, status_code = result
                        if status_code == 200 and response_data.get('success'):
                            self.safety_system.record_trade(user_id, trade_data, True)
                            
                            # Send success notification
                            self.notification_service.send_notification(
                                user_id=user_id,
                                notification_type=NotificationType.TRADE_EXECUTED,
                                data=trade_data
                            )
                    
                    return result
                    
                except Exception as e:
                    # Handle trading errors
                    user_id = getattr(g, 'current_user_id', None)
                    if user_id:
                        self.safety_system.record_trade(user_id, trade_data, False, str(e))
                        
                        # Send error notification
                        self.notification_service.send_notification(
                            user_id=user_id,
                            notification_type=NotificationType.TRADE_FAILED,
                            data={'error': str(e), **trade_data}
                        )
                    
                    return jsonify({
                        'success': False,
                        'error': f'Trading operation failed: {str(e)}'
                    }), 500
            
            return decorated_function
        return enhanced_trading_operation
    
    def create_enhanced_bot_decorator(self):
        """Create a decorator for enhanced bot operations"""
        def enhanced_bot_operation(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                try:
                    user_id = getattr(g, 'current_user_id')
                    
                    # Execute the bot operation
                    result = f(*args, **kwargs)
                    
                    # Send appropriate notifications based on operation
                    operation = f.__name__
                    bot_data = request.get_json() or {}
                    bot_name = bot_data.get('name', 'Unknown Bot')
                    
                    if operation == 'start_bot':
                        self.notification_service.send_notification(
                            user_id=user_id,
                            notification_type=NotificationType.BOT_STARTED,
                            data={'bot_name': bot_name}
                        )
                    elif operation == 'stop_bot':
                        self.notification_service.send_notification(
                            user_id=user_id,
                            notification_type=NotificationType.BOT_STOPPED,
                            data={'bot_name': bot_name}
                        )
                    
                    return result
                    
                except Exception as e:
                    # Handle bot errors
                    user_id = getattr(g, 'current_user_id', None)
                    if user_id:
                        bot_name = request.get_json().get('name', 'Unknown Bot') if request.get_json() else 'Unknown Bot'
                        self.notification_service.send_notification(
                            user_id=user_id,
                            notification_type=NotificationType.BOT_ERROR,
                            data={'bot_name': bot_name, 'error': str(e)}
                        )
                    
                    return jsonify({
                        'success': False,
                        'error': f'Bot operation failed: {str(e)}'
                    }), 500
            
            return decorated_function
        return enhanced_bot_operation
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'security': {
                'enabled': self.security_middleware is not None,
                'stats': self.security_middleware.get_security_stats() if self.security_middleware else None
            },
            'safety': {
                'enabled': self.safety_system is not None,
                'emergency_stop': self.safety_system.emergency_stop_active if self.safety_system else False,
                'status': self.safety_system.get_system_status() if self.safety_system else None
            },
            'notifications': {
                'enabled': self.notification_service is not None,
                'stats': self.notification_service.get_service_stats() if self.notification_service else None
            },
            'error_handling': {
                'enabled': self.error_handler is not None,
                'stats': self.error_handler.get_stats() if self.error_handler else None
            }
        }

# Global integration instance
enhanced_integration = EnhancedTradingBotIntegration()

# Convenience decorators
enhanced_trading = lambda f: enhanced_integration.create_enhanced_trading_decorator()(f)
enhanced_bot = lambda f: enhanced_integration.create_enhanced_bot_decorator()(f)