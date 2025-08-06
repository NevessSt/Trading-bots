import os
import requests
from datetime import datetime
from flask import current_app
from models.user import User

class NotificationManager:
    """Manages notifications for users"""
    
    def __init__(self):
        """Initialize the notification manager"""
        self.telegram_bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    
    def send_notification(self, user_id, message, notification_type='trade'):
        """Send a notification to a user
        
        Args:
            user_id (str): User ID
            message (str): Notification message
            notification_type (str): Type of notification ('trade', 'system', 'alert')
            
        Returns:
            bool: True if notification was sent successfully, False otherwise
        """
        # Get user notification preferences
        user = User.find_by_id(user_id)
        if not user:
            return False
        
        notification_settings = user.get('settings', {}).get('notifications', {})
        
        # Check if user has enabled this notification type
        if not notification_settings.get(notification_type, True):
            return False
        
        # Determine notification methods
        methods = notification_settings.get('methods', ['email'])
        
        success = False
        
        # Send notifications via enabled methods
        for method in methods:
            if method == 'email':
                success = self._send_email_notification(user, message, notification_type) or success
            elif method == 'telegram':
                success = self._send_telegram_notification(user, message, notification_type) or success
            elif method == 'in_app':
                success = self._send_in_app_notification(user, message, notification_type) or success
        
        # Log notification
        self._log_notification(user_id, message, notification_type, success)
        
        return success
    
    def _send_email_notification(self, user, message, notification_type):
        """Send an email notification
        
        Args:
            user (dict): User document
            message (str): Notification message
            notification_type (str): Type of notification
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        # In a production environment, this would use a proper email service like SendGrid or SMTP
        # For now, we'll just log the email
        email = user.get('email')
        if not email:
            return False
        
        print(f"[EMAIL] To: {email}, Type: {notification_type}, Message: {message}")
        
        # TODO: Implement actual email sending
        return True
    
    def _send_telegram_notification(self, user, message, notification_type):
        """Send a Telegram notification
        
        Args:
            user (dict): User document
            message (str): Notification message
            notification_type (str): Type of notification
            
        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        telegram_chat_id = user.get('settings', {}).get('notifications', {}).get('telegram_chat_id')
        if not telegram_chat_id or not self.telegram_bot_token:
            return False
        
        try:
            # Format message
            formatted_message = f"[{notification_type.upper()}] {message}"
            
            # Send message via Telegram API
            response = requests.post(
                f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage",
                json={
                    'chat_id': telegram_chat_id,
                    'text': formatted_message,
                    'parse_mode': 'Markdown'
                }
            )
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"Error sending Telegram notification: {str(e)}")
            return False
    
    def _send_in_app_notification(self, user, message, notification_type):
        """Send an in-app notification
        
        Args:
            user (dict): User document
            message (str): Notification message
            notification_type (str): Type of notification
            
        Returns:
            bool: True if notification was created successfully, False otherwise
        """
        try:
            # In a real implementation, this would store the notification in the database
            # For now, we'll just log it
            print(f"[IN-APP] User: {user['_id']}, Type: {notification_type}, Message: {message}")
            
            # TODO: Implement actual in-app notification storage
            return True
            
        except Exception as e:
            print(f"Error creating in-app notification: {str(e)}")
            return False
    
    def _log_notification(self, user_id, message, notification_type, success):
        """Log a notification
        
        Args:
            user_id (str): User ID
            message (str): Notification message
            notification_type (str): Type of notification
            success (bool): Whether the notification was sent successfully
        """
        # In a real implementation, this would store the notification log in the database
        # For now, we'll just print it
        timestamp = datetime.utcnow().isoformat()
        status = "SUCCESS" if success else "FAILED"
        print(f"[NOTIFICATION LOG] {timestamp} - User: {user_id}, Type: {notification_type}, Status: {status}, Message: {message}")
    
    def get_user_notifications(self, user_id, limit=10, offset=0):
        """Get notifications for a user
        
        Args:
            user_id (str): User ID
            limit (int): Maximum number of notifications to return
            offset (int): Offset for pagination
            
        Returns:
            list: List of notifications
        """
        # In a real implementation, this would query the database for notifications
        # For now, we'll return a placeholder
        return []
    
    def mark_notification_as_read(self, user_id, notification_id):
        """Mark a notification as read
        
        Args:
            user_id (str): User ID
            notification_id (str): Notification ID
            
        Returns:
            bool: True if notification was marked as read, False otherwise
        """
        # In a real implementation, this would update the notification in the database
        # For now, we'll return a placeholder
        return True
    
    def update_notification_settings(self, user_id, notification_settings):
        """Update notification settings for a user
        
        Args:
            user_id (str): User ID
            notification_settings (dict): Notification settings
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        return User.update(user_id, {'settings.notifications': notification_settings})