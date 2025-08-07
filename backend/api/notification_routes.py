from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.notification import notification_manager
from utils.logger import logger
from utils.security import rate_limit

notification_bp = Blueprint('notification', __name__)

@notification_bp.route('/list', methods=['GET'])
@jwt_required()
@rate_limit(requests_per_minute=60)
def get_notifications():
    """Get notifications for the current user"""
    try:
        user_id = get_jwt_identity()
        
        # Get query parameters
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        
        # Validate parameters
        if limit > 100:
            limit = 100
        if limit < 1:
            limit = 20
        if offset < 0:
            offset = 0
        
        # Get notifications
        notifications = notification_manager.get_user_notifications(
            user_id=user_id,
            limit=limit,
            offset=offset,
            unread_only=unread_only
        )
        
        # Get unread count
        unread_count = notification_manager.get_unread_count(user_id)
        
        logger.info(f"Retrieved {len(notifications)} notifications for user {user_id}")
        
        return jsonify({
            'success': True,
            'notifications': notifications,
            'unread_count': unread_count,
            'total_returned': len(notifications)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting notifications: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve notifications'
        }), 500

@notification_bp.route('/mark-read', methods=['POST'])
@jwt_required()
@rate_limit(requests_per_minute=120)
def mark_notification_read():
    """Mark a notification as read"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'notification_id' not in data:
            return jsonify({
                'success': False,
                'error': 'notification_id is required'
            }), 400
        
        notification_id = data['notification_id']
        
        # Validate notification_id
        if not isinstance(notification_id, str) or not notification_id.strip():
            return jsonify({
                'success': False,
                'error': 'Invalid notification_id'
            }), 400
        
        # Mark notification as read
        success = notification_manager.mark_notification_as_read(user_id, notification_id)
        
        if success:
            logger.info(f"Notification {notification_id} marked as read for user {user_id}")
            return jsonify({
                'success': True,
                'message': 'Notification marked as read'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Notification not found'
            }), 404
        
    except Exception as e:
        logger.error(f"Error marking notification as read: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to mark notification as read'
        }), 500

@notification_bp.route('/mark-all-read', methods=['POST'])
@jwt_required()
@rate_limit(requests_per_minute=30)
def mark_all_notifications_read():
    """Mark all notifications as read for the current user"""
    try:
        user_id = get_jwt_identity()
        
        # Mark all notifications as read
        success = notification_manager.mark_all_read(user_id)
        
        if success:
            logger.info(f"All notifications marked as read for user {user_id}")
            return jsonify({
                'success': True,
                'message': 'All notifications marked as read'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to mark notifications as read'
            }), 500
        
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to mark all notifications as read'
        }), 500

@notification_bp.route('/unread-count', methods=['GET'])
@jwt_required()
@rate_limit(requests_per_minute=120)
def get_unread_count():
    """Get count of unread notifications"""
    try:
        user_id = get_jwt_identity()
        
        unread_count = notification_manager.get_unread_count(user_id)
        
        return jsonify({
            'success': True,
            'unread_count': unread_count
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting unread count: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get unread count'
        }), 500

@notification_bp.route('/settings', methods=['GET'])
@jwt_required()
@rate_limit(requests_per_minute=60)
def get_notification_settings():
    """Get notification settings for the current user"""
    try:
        user_id = get_jwt_identity()
        
        from ..models.user import User
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Get notification settings with defaults
        notification_settings = user.get('settings', {}).get('notifications', {
            'trade': True,
            'profit': True,
            'loss': True,
            'warning': True,
            'error': True,
            'info': True,
            'system': True,
            'methods': ['in_app'],
            'email_notifications': False,
            'telegram_chat_id': None
        })
        
        logger.info(f"Retrieved notification settings for user {user_id}")
        
        return jsonify({
            'success': True,
            'settings': notification_settings
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting notification settings: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve notification settings'
        }), 500

@notification_bp.route('/settings', methods=['PUT'])
@jwt_required()
@rate_limit(requests_per_minute=30)
def update_notification_settings():
    """Update notification settings for the current user"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required'
            }), 400
        
        # Validate notification types
        valid_types = ['trade', 'profit', 'loss', 'warning', 'error', 'info', 'system']
        valid_methods = ['in_app', 'email', 'telegram']
        
        # Validate settings structure
        settings = {}
        
        # Validate notification type preferences
        for notification_type in valid_types:
            if notification_type in data:
                if not isinstance(data[notification_type], bool):
                    return jsonify({
                        'success': False,
                        'error': f'Invalid value for {notification_type}, must be boolean'
                    }), 400
                settings[notification_type] = data[notification_type]
        
        # Validate methods
        if 'methods' in data:
            if not isinstance(data['methods'], list):
                return jsonify({
                    'success': False,
                    'error': 'methods must be an array'
                }), 400
            
            for method in data['methods']:
                if method not in valid_methods:
                    return jsonify({
                        'success': False,
                        'error': f'Invalid notification method: {method}'
                    }), 400
            
            settings['methods'] = data['methods']
        
        # Validate email notifications
        if 'email_notifications' in data:
            if not isinstance(data['email_notifications'], bool):
                return jsonify({
                    'success': False,
                    'error': 'email_notifications must be boolean'
                }), 400
            settings['email_notifications'] = data['email_notifications']
        
        # Validate telegram chat ID
        if 'telegram_chat_id' in data:
            if data['telegram_chat_id'] is not None and not isinstance(data['telegram_chat_id'], str):
                return jsonify({
                    'success': False,
                    'error': 'telegram_chat_id must be string or null'
                }), 400
            settings['telegram_chat_id'] = data['telegram_chat_id']
        
        # Update settings
        success = notification_manager.update_notification_settings(user_id, settings)
        
        if success:
            logger.info(f"Notification settings updated for user {user_id}")
            return jsonify({
                'success': True,
                'message': 'Notification settings updated successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to update notification settings'
            }), 500
        
    except Exception as e:
        logger.error(f"Error updating notification settings: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to update notification settings'
        }), 500

@notification_bp.route('/test', methods=['POST'])
@jwt_required()
@rate_limit(requests_per_minute=10)
def send_test_notification():
    """Send a test notification to verify settings"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        notification_type = data.get('type', 'info') if data else 'info'
        
        # Validate notification type
        valid_types = ['trade', 'profit', 'loss', 'warning', 'error', 'info', 'system']
        if notification_type not in valid_types:
            notification_type = 'info'
        
        # Send test notification
        message = f"This is a test {notification_type} notification from your Trading Bot."
        
        success = notification_manager.send_notification(
            user_id=user_id,
            message=message,
            notification_type=notification_type
        )
        
        if success:
            logger.info(f"Test notification sent to user {user_id}")
            return jsonify({
                'success': True,
                'message': 'Test notification sent successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to send test notification'
            }), 500
        
    except Exception as e:
        logger.error(f"Error sending test notification: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to send test notification'
        }), 500