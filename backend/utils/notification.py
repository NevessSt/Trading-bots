import os
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from flask import current_app
from models.user import User
from .logger import logger
import uuid
from typing import Dict, List, Optional

class NotificationManager:
    """Manages notifications for users"""
    
    def __init__(self):
        """Initialize the notification manager"""
        self.telegram_bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        
        # Email configuration
        self.email_enabled = os.getenv('EMAIL_NOTIFICATIONS_ENABLED', 'false').lower() == 'true'
        self.smtp_server = os.getenv('SMTP_SERVER')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.from_email = os.getenv('FROM_EMAIL')
        
        # In-memory storage for notifications (in production, use Redis or database)
        self.notifications = {}
    
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
        email = user.get('email')
        if not email:
            return False
        
        if not self.email_enabled or not all([self.smtp_server, self.smtp_username, self.smtp_password, self.from_email]):
            logger.warning("Email configuration incomplete, logging email notification")
            print(f"[EMAIL] To: {email}, Type: {notification_type}, Message: {message}")
            return True
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = email
            msg['Subject'] = f"Trading Bot Alert: {notification_type.upper()}"
            
            body = f"""
            Trading Bot Notification
            
            Type: {notification_type.upper()}
            Message: {message}
            Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
            
            ---
            This is an automated message from your Trading Bot.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            text = msg.as_string()
            server.sendmail(self.from_email, email, text)
            server.quit()
            
            logger.info(f"Email notification sent to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email notification: {str(e)}")
            print(f"[EMAIL ERROR] To: {email}, Type: {notification_type}, Message: {message}")
            return False
    
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
            user_id = str(user['_id'])
            
            notification = {
                'id': str(uuid.uuid4()),
                'user_id': user_id,
                'type': notification_type,
                'title': self._get_notification_title(notification_type),
                'message': message,
                'timestamp': datetime.utcnow().isoformat(),
                'read': False
            }
            
            # Store notification in memory
            if user_id not in self.notifications:
                self.notifications[user_id] = []
            
            self.notifications[user_id].append(notification)
            
            # Keep only last 100 notifications per user
            if len(self.notifications[user_id]) > 100:
                self.notifications[user_id] = self.notifications[user_id][-100:]
            
            logger.info(f"In-app notification created for user {user_id}: {notification_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating in-app notification: {str(e)}")
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
    
    def get_user_notifications(self, user_id, limit=10, offset=0, unread_only=False):
        """Get notifications for a user
        
        Args:
            user_id (str): User ID
            limit (int): Maximum number of notifications to return
            offset (int): Offset for pagination
            unread_only (bool): Return only unread notifications
            
        Returns:
            list: List of notifications
        """
        try:
            user_notifications = self.notifications.get(user_id, [])
            
            if unread_only:
                user_notifications = [n for n in user_notifications if not n['read']]
            
            # Sort by timestamp (newest first)
            user_notifications.sort(key=lambda x: x['timestamp'], reverse=True)
            
            # Apply pagination
            start = offset
            end = offset + limit
            
            return user_notifications[start:end]
            
        except Exception as e:
            logger.error(f"Error getting notifications for user {user_id}: {str(e)}")
            return []
    
    def mark_notification_as_read(self, user_id, notification_id):
        """Mark a notification as read
        
        Args:
            user_id (str): User ID
            notification_id (str): Notification ID
            
        Returns:
            bool: True if notification was marked as read, False otherwise
        """
        try:
            user_notifications = self.notifications.get(user_id, [])
            
            for notification in user_notifications:
                if notification['id'] == notification_id:
                    notification['read'] = True
                    logger.info(f"Notification {notification_id} marked as read for user {user_id}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error marking notification as read: {str(e)}")
            return False
    
    def update_notification_settings(self, user_id, notification_settings):
        """Update notification settings for a user
        
        Args:
            user_id (str): User ID
            notification_settings (dict): Notification settings
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        return User.update(user_id, {'settings.notifications': notification_settings})
    
    def get_unread_count(self, user_id):
        """Get count of unread notifications for a user
        
        Args:
            user_id (str): User ID
            
        Returns:
            int: Number of unread notifications
        """
        try:
            user_notifications = self.notifications.get(user_id, [])
            return len([n for n in user_notifications if not n['read']])
            
        except Exception as e:
            logger.error(f"Error getting unread count for user {user_id}: {str(e)}")
            return 0
    
    def mark_all_read(self, user_id):
        """Mark all notifications as read for a user
        
        Args:
            user_id (str): User ID
            
        Returns:
            bool: True if all notifications were marked as read, False otherwise
        """
        try:
            user_notifications = self.notifications.get(user_id, [])
            
            for notification in user_notifications:
                notification['read'] = True
            
            logger.info(f"All notifications marked as read for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error marking all notifications as read: {str(e)}")
            return False
    
    def send_trade_notification(self, user_id, trade_data):
        """Send trade-specific notification
        
        Args:
            user_id (str): User ID
            trade_data (dict): Trade information
        """
        symbol = trade_data.get('symbol', 'Unknown')
        side = trade_data.get('side', 'Unknown')
        quantity = trade_data.get('quantity', 0)
        price = trade_data.get('price', 0)
        
        message = f"Trade executed: {side.upper()} {quantity} {symbol} at ${price}"
        
        self.send_notification(
            user_id=user_id,
            message=message,
            notification_type='trade'
        )
    
    def send_position_closed_notification(self, user_id, position_data):
        """Send position closed notification
        
        Args:
            user_id (str): User ID
            position_data (dict): Position information
        """
        symbol = position_data.get('symbol', 'Unknown')
        pnl = position_data.get('pnl', 0)
        reason = position_data.get('reason', 'Manual')
        
        pnl_text = f"${pnl:.2f}" if pnl >= 0 else f"-${abs(pnl):.2f}"
        message = f"Position closed: {symbol} - PnL: {pnl_text} ({reason})"
        
        notification_type = 'profit' if pnl >= 0 else 'loss'
        
        self.send_notification(
            user_id=user_id,
            message=message,
            notification_type=notification_type
        )
    
    def send_risk_alert(self, user_id, alert_type, details=None):
        """Send risk management alert
        
        Args:
            user_id (str): User ID
            alert_type (str): Type of risk alert
            details (dict): Additional details
        """
        alert_messages = {
            'daily_loss_limit': 'Daily loss limit exceeded',
            'position_exposure': 'Position exposure limit exceeded',
            'max_positions': 'Maximum open positions limit reached',
            'insufficient_funds': 'Insufficient funds for trade'
        }
        
        message = alert_messages.get(alert_type, f"Risk alert: {alert_type}")
        
        self.send_notification(
            user_id=user_id,
            message=message,
            notification_type='warning'
        )
    
    def send_system_notification(self, user_id, message, severity='info'):
        """Send system notification
        
        Args:
            user_id (str): User ID
            message (str): Notification message
            severity (str): Notification severity
        """
        self.send_notification(
            user_id=user_id,
            message=message,
            notification_type=severity
        )
    
    def _get_notification_title(self, notification_type):
        """Get default title for notification type
        
        Args:
            notification_type (str): Type of notification
            
        Returns:
            str: Default title
        """
        titles = {
            'trade': 'Trade Alert',
            'profit': 'Profit Alert',
            'loss': 'Loss Alert',
            'warning': 'Warning',
            'error': 'Error',
            'info': 'Information',
            'system': 'System Alert'
        }
        return titles.get(notification_type, 'Notification')

# Global notification manager instance
notification_manager = NotificationManager()