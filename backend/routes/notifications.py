from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import db
from models.notification import NotificationPreference, NotificationLog, NotificationTemplate
from models.user import User
from services.notification_service import notification_service
import json
from datetime import datetime, timedelta
from sqlalchemy import desc

notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')

@notifications_bp.route('/preferences', methods=['GET'])
@jwt_required()
def get_preferences():
    """Get user notification preferences"""
    try:
        user_id = get_jwt_identity()
        
        preferences = NotificationPreference.query.filter_by(user_id=user_id).all()
        
        # If no preferences exist, create default ones
        if not preferences:
            default_prefs = NotificationPreference.create_default_preferences(user_id)
            for pref in default_prefs:
                db.session.add(pref)
            db.session.commit()
            preferences = default_prefs
        
        # Group preferences by event type
        grouped_preferences = {}
        for pref in preferences:
            event_type = pref.event_type
            if event_type not in grouped_preferences:
                grouped_preferences[event_type] = {}
            
            grouped_preferences[event_type][pref.notification_type] = {
                'id': pref.id,
                'enabled': pref.enabled,
                'settings': json.loads(pref.settings) if pref.settings else {}
            }
        
        return jsonify({
            'success': True,
            'preferences': grouped_preferences
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting preferences: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to get preferences'
        }), 500

@notifications_bp.route('/preferences', methods=['POST'])
@jwt_required()
def update_preferences():
    """Update user notification preferences"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        preference_id = data.get('preference_id')
        enabled = data.get('enabled')
        settings = data.get('settings', {})
        
        if preference_id is None:
            return jsonify({
                'success': False,
                'message': 'Preference ID is required'
            }), 400
        
        preference = NotificationPreference.query.filter_by(
            id=preference_id,
            user_id=user_id
        ).first()
        
        if not preference:
            return jsonify({
                'success': False,
                'message': 'Preference not found'
            }), 404
        
        if enabled is not None:
            preference.enabled = enabled
        
        if settings:
            preference.settings = json.dumps(settings)
        
        preference.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Preference updated successfully'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error updating preferences: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Failed to update preference'
        }), 500

@notifications_bp.route('/preferences/bulk', methods=['POST'])
@jwt_required()
def bulk_update_preferences():
    """Bulk update notification preferences"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        updates = data.get('updates', [])
        
        if not updates:
            return jsonify({
                'success': False,
                'message': 'No updates provided'
            }), 400
        
        updated_count = 0
        for update in updates:
            preference_id = update.get('preference_id')
            enabled = update.get('enabled')
            settings = update.get('settings')
            
            if preference_id is None:
                continue
            
            preference = NotificationPreference.query.filter_by(
                id=preference_id,
                user_id=user_id
            ).first()
            
            if not preference:
                continue
            
            if enabled is not None:
                preference.enabled = enabled
            
            if settings is not None:
                preference.settings = json.dumps(settings)
            
            preference.updated_at = datetime.utcnow()
            updated_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Updated {updated_count} preferences successfully'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error bulk updating preferences: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Failed to update preferences'
        }), 500

@notifications_bp.route('/test', methods=['POST'])
@jwt_required()
def test_notification():
    """Send test notification"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        notification_type = data.get('notification_type')  # email, telegram, push
        
        if not notification_type:
            return jsonify({
                'success': False,
                'message': 'Notification type is required'
            }), 400
        
        if notification_type not in ['email', 'telegram', 'push']:
            return jsonify({
                'success': False,
                'message': 'Invalid notification type'
            }), 400
        
        # Get user
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Test data
        test_data = {
            'symbol': 'BTC/USDT',
            'side': 'BUY',
            'quantity': '0.001',
            'price': '45000.00',
            'bot_name': 'Test Bot',
            'strategy': 'Test Strategy',
            'pnl': '50.00',
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        }
        
        # Create a temporary preference for testing
        temp_preference = NotificationPreference(
            user_id=user_id,
            notification_type=notification_type,
            event_type='trade_executed',
            enabled=True,
            settings=data.get('settings', '{}')
        )
        
        success = False
        error_message = None
        
        try:
            if notification_type == 'email':
                if not user.email:
                    return jsonify({
                        'success': False,
                        'message': 'User email not configured'
                    }), 400
                success = notification_service._send_email(user, 'trade_executed', test_data, temp_preference)
            
            elif notification_type == 'telegram':
                settings = json.loads(data.get('settings', '{}'))
                if not settings.get('telegram_chat_id'):
                    return jsonify({
                        'success': False,
                        'message': 'Telegram chat ID not configured'
                    }), 400
                success = notification_service._send_telegram(user, 'trade_executed', test_data, temp_preference)
            
            elif notification_type == 'push':
                settings = json.loads(data.get('settings', '{}'))
                if not settings.get('fcm_token'):
                    return jsonify({
                        'success': False,
                        'message': 'FCM token not configured'
                    }), 400
                success = notification_service._send_push(user, 'trade_executed', test_data, temp_preference)
        
        except Exception as e:
            error_message = str(e)
            success = False
        
        return jsonify({
            'success': success,
            'message': f'Test {notification_type} notification sent successfully' if success else f'Failed to send test {notification_type} notification',
            'error': error_message if error_message else None
        })
        
    except Exception as e:
        current_app.logger.error(f"Error sending test notification: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to send test notification'
        }), 500

@notifications_bp.route('/logs', methods=['GET'])
@jwt_required()
def get_notification_logs():
    """Get user notification logs"""
    try:
        user_id = get_jwt_identity()
        
        # Query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        notification_type = request.args.get('notification_type')
        event_type = request.args.get('event_type')
        status = request.args.get('status')
        days = request.args.get('days', 30, type=int)
        
        # Build query
        query = NotificationLog.query.filter_by(user_id=user_id)
        
        # Apply filters
        if notification_type:
            query = query.filter(NotificationLog.notification_type == notification_type)
        
        if event_type:
            query = query.filter(NotificationLog.event_type == event_type)
        
        if status:
            query = query.filter(NotificationLog.status == status)
        
        # Filter by date range
        if days > 0:
            start_date = datetime.utcnow() - timedelta(days=days)
            query = query.filter(NotificationLog.created_at >= start_date)
        
        # Order by creation date (newest first)
        query = query.order_by(desc(NotificationLog.created_at))
        
        # Paginate
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        logs = [log.to_dict() for log in pagination.items]
        
        return jsonify({
            'success': True,
            'logs': logs,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting notification logs: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to get notification logs'
        }), 500

@notifications_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_notification_stats():
    """Get notification statistics"""
    try:
        user_id = get_jwt_identity()
        
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Total notifications sent
        total_sent = NotificationLog.query.filter(
            NotificationLog.user_id == user_id,
            NotificationLog.status == 'sent',
            NotificationLog.created_at >= start_date
        ).count()
        
        # Total notifications failed
        total_failed = NotificationLog.query.filter(
            NotificationLog.user_id == user_id,
            NotificationLog.status == 'failed',
            NotificationLog.created_at >= start_date
        ).count()
        
        # Notifications by type
        notifications_by_type = db.session.query(
            NotificationLog.notification_type,
            db.func.count(NotificationLog.id).label('count')
        ).filter(
            NotificationLog.user_id == user_id,
            NotificationLog.created_at >= start_date
        ).group_by(NotificationLog.notification_type).all()
        
        # Notifications by event type
        notifications_by_event = db.session.query(
            NotificationLog.event_type,
            db.func.count(NotificationLog.id).label('count')
        ).filter(
            NotificationLog.user_id == user_id,
            NotificationLog.created_at >= start_date
        ).group_by(NotificationLog.event_type).all()
        
        # Success rate by type
        success_rates = {}
        for notification_type in ['email', 'telegram', 'push']:
            sent_count = NotificationLog.query.filter(
                NotificationLog.user_id == user_id,
                NotificationLog.notification_type == notification_type,
                NotificationLog.status == 'sent',
                NotificationLog.created_at >= start_date
            ).count()
            
            total_count = NotificationLog.query.filter(
                NotificationLog.user_id == user_id,
                NotificationLog.notification_type == notification_type,
                NotificationLog.created_at >= start_date
            ).count()
            
            success_rates[notification_type] = {
                'sent': sent_count,
                'total': total_count,
                'rate': (sent_count / total_count * 100) if total_count > 0 else 0
            }
        
        return jsonify({
            'success': True,
            'stats': {
                'total_sent': total_sent,
                'total_failed': total_failed,
                'success_rate': (total_sent / (total_sent + total_failed) * 100) if (total_sent + total_failed) > 0 else 0,
                'by_type': {item[0]: item[1] for item in notifications_by_type},
                'by_event': {item[0]: item[1] for item in notifications_by_event},
                'success_rates': success_rates,
                'period_days': days
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting notification stats: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to get notification statistics'
        }), 500

@notifications_bp.route('/templates', methods=['GET'])
@jwt_required()
def get_notification_templates():
    """Get notification templates"""
    try:
        templates = NotificationTemplate.query.all()
        
        # If no templates exist, create default ones
        if not templates:
            default_templates = NotificationTemplate.create_default_templates()
            for template in default_templates:
                db.session.add(template)
            db.session.commit()
            templates = default_templates
        
        return jsonify({
            'success': True,
            'templates': [template.to_dict() for template in templates]
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting templates: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to get notification templates'
        }), 500

@notifications_bp.route('/config', methods=['GET'])
@jwt_required()
def get_notification_config():
    """Get notification configuration status"""
    try:
        # Check SMTP configuration
        smtp_configured = all([
            current_app.config.get('SMTP_SERVER'),
            current_app.config.get('SMTP_USERNAME'),
            current_app.config.get('SMTP_PASSWORD'),
            current_app.config.get('FROM_EMAIL')
        ])
        
        # Check Telegram configuration
        telegram_configured = bool(current_app.config.get('TELEGRAM_BOT_TOKEN'))
        
        # Check Push notification configuration
        push_configured = bool(current_app.config.get('FIREBASE_SERVER_KEY'))
        
        return jsonify({
            'success': True,
            'config': {
                'email_configured': smtp_configured,
                'telegram_configured': telegram_configured,
                'push_configured': push_configured,
                'available_types': {
                    'email': smtp_configured,
                    'telegram': telegram_configured,
                    'push': push_configured
                },
                'event_types': [
                    'trade_executed',
                    'trade_failed',
                    'bot_started',
                    'bot_stopped',
                    'system_error',
                    'profit_alert',
                    'loss_alert'
                ]
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting notification config: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to get notification configuration'
        }), 500

@notifications_bp.route('/send', methods=['POST'])
@jwt_required()
def send_notification():
    """Manually send a notification (admin only)"""
    try:
        user_id = get_jwt_identity()
        
        # Check if user is admin (you may need to implement this check)
        user = User.query.get(user_id)
        if not user or not getattr(user, 'is_admin', False):
            return jsonify({
                'success': False,
                'message': 'Admin access required'
            }), 403
        
        data = request.get_json()
        
        target_user_id = data.get('user_id')
        event_type = data.get('event_type')
        notification_data = data.get('data', {})
        
        if not all([target_user_id, event_type]):
            return jsonify({
                'success': False,
                'message': 'User ID and event type are required'
            }), 400
        
        # Send notification
        results = notification_service.send_notification(target_user_id, event_type, notification_data)
        
        return jsonify({
            'success': True,
            'message': 'Notification sent',
            'results': results
        })
        
    except Exception as e:
        current_app.logger.error(f"Error sending notification: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to send notification'
        }), 500