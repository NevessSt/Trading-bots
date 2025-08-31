import logging
import json
import asyncio
import smtplib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from email.mime.base import MimeBase
from email import encoders
import threading
import queue
import time
from collections import defaultdict, deque

# Configure logging
logging.basicConfig(level=logging.INFO)
notification_logger = logging.getLogger('notifications')

class NotificationType(Enum):
    TRADE_EXECUTED = "trade_executed"
    TRADE_FAILED = "trade_failed"
    BOT_STARTED = "bot_started"
    BOT_STOPPED = "bot_stopped"
    BOT_ERROR = "bot_error"
    BALANCE_LOW = "balance_low"
    PROFIT_TARGET = "profit_target"
    LOSS_LIMIT = "loss_limit"
    SECURITY_ALERT = "security_alert"
    SYSTEM_ERROR = "system_error"
    MARKET_ALERT = "market_alert"
    RISK_WARNING = "risk_warning"
    LICENSE_EXPIRY = "license_expiry"
    API_KEY_ISSUE = "api_key_issue"
    EMERGENCY_STOP = "emergency_stop"

class NotificationPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class NotificationChannel(Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"
    IN_APP = "in_app"
    TELEGRAM = "telegram"
    SLACK = "slack"

@dataclass
class NotificationTemplate:
    """Template for different types of notifications"""
    type: NotificationType
    title: str
    message: str
    priority: NotificationPriority
    channels: List[NotificationChannel]
    variables: List[str] = None
    
    def __post_init__(self):
        if self.variables is None:
            self.variables = []

@dataclass
class NotificationRequest:
    """Notification request with all details"""
    user_id: int
    type: NotificationType
    title: str
    message: str
    priority: NotificationPriority
    channels: List[NotificationChannel]
    data: Dict[str, Any] = None
    scheduled_time: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    
    def __post_init__(self):
        if self.data is None:
            self.data = {}
        if self.scheduled_time is None:
            self.scheduled_time = datetime.utcnow()

@dataclass
class NotificationResult:
    """Result of notification delivery attempt"""
    success: bool
    channel: NotificationChannel
    message: str
    timestamp: datetime
    error: Optional[str] = None

class EnhancedNotificationService:
    """Enhanced notification service with multiple channels and smart delivery"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.templates = self._initialize_templates()
        self.user_preferences = {}  # User notification preferences
        self.delivery_queue = queue.PriorityQueue()
        self.failed_notifications = deque(maxlen=1000)
        self.notification_history = defaultdict(list)
        self.rate_limits = defaultdict(lambda: deque())
        self.channels = self._initialize_channels()
        self.running = False
        self.worker_thread = None
        
        # Statistics
        self.stats = {
            'sent': defaultdict(int),
            'failed': defaultdict(int),
            'rate_limited': defaultdict(int)
        }
        
        self.start_service()
    
    def _initialize_templates(self) -> Dict[NotificationType, NotificationTemplate]:
        """Initialize notification templates"""
        return {
            NotificationType.TRADE_EXECUTED: NotificationTemplate(
                type=NotificationType.TRADE_EXECUTED,
                title="Trade Executed Successfully",
                message="Your {side} order for {amount} {symbol} has been executed at {price}",
                priority=NotificationPriority.MEDIUM,
                channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL],
                variables=['side', 'amount', 'symbol', 'price']
            ),
            NotificationType.TRADE_FAILED: NotificationTemplate(
                type=NotificationType.TRADE_FAILED,
                title="Trade Failed",
                message="Your {side} order for {amount} {symbol} failed: {error}",
                priority=NotificationPriority.HIGH,
                channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL, NotificationChannel.PUSH],
                variables=['side', 'amount', 'symbol', 'error']
            ),
            NotificationType.BOT_STARTED: NotificationTemplate(
                type=NotificationType.BOT_STARTED,
                title="Trading Bot Started",
                message="Your trading bot '{bot_name}' has started successfully",
                priority=NotificationPriority.MEDIUM,
                channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL],
                variables=['bot_name']
            ),
            NotificationType.BOT_STOPPED: NotificationTemplate(
                type=NotificationType.BOT_STOPPED,
                title="Trading Bot Stopped",
                message="Your trading bot '{bot_name}' has been stopped",
                priority=NotificationPriority.MEDIUM,
                channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL],
                variables=['bot_name']
            ),
            NotificationType.BOT_ERROR: NotificationTemplate(
                type=NotificationType.BOT_ERROR,
                title="Trading Bot Error",
                message="Your trading bot '{bot_name}' encountered an error: {error}",
                priority=NotificationPriority.HIGH,
                channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL, NotificationChannel.PUSH],
                variables=['bot_name', 'error']
            ),
            NotificationType.BALANCE_LOW: NotificationTemplate(
                type=NotificationType.BALANCE_LOW,
                title="Low Account Balance Warning",
                message="Your account balance is low: ${balance}. Consider adding funds to continue trading.",
                priority=NotificationPriority.HIGH,
                channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL, NotificationChannel.PUSH],
                variables=['balance']
            ),
            NotificationType.PROFIT_TARGET: NotificationTemplate(
                type=NotificationType.PROFIT_TARGET,
                title="Profit Target Reached! 🎉",
                message="Congratulations! Your bot '{bot_name}' has reached the profit target of ${target}",
                priority=NotificationPriority.MEDIUM,
                channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL, NotificationChannel.PUSH],
                variables=['bot_name', 'target']
            ),
            NotificationType.LOSS_LIMIT: NotificationTemplate(
                type=NotificationType.LOSS_LIMIT,
                title="Loss Limit Reached ⚠️",
                message="Your bot '{bot_name}' has reached the loss limit of ${limit}. Trading has been paused.",
                priority=NotificationPriority.HIGH,
                channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL, NotificationChannel.PUSH, NotificationChannel.SMS],
                variables=['bot_name', 'limit']
            ),
            NotificationType.SECURITY_ALERT: NotificationTemplate(
                type=NotificationType.SECURITY_ALERT,
                title="Security Alert 🔒",
                message="Suspicious activity detected on your account: {details}",
                priority=NotificationPriority.CRITICAL,
                channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL, NotificationChannel.PUSH, NotificationChannel.SMS],
                variables=['details']
            ),
            NotificationType.SYSTEM_ERROR: NotificationTemplate(
                type=NotificationType.SYSTEM_ERROR,
                title="System Error",
                message="A system error occurred: {error}. Our team has been notified.",
                priority=NotificationPriority.HIGH,
                channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL],
                variables=['error']
            ),
            NotificationType.EMERGENCY_STOP: NotificationTemplate(
                type=NotificationType.EMERGENCY_STOP,
                title="🚨 EMERGENCY STOP ACTIVATED",
                message="Emergency stop has been activated: {reason}. All trading has been halted.",
                priority=NotificationPriority.CRITICAL,
                channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL, NotificationChannel.PUSH, NotificationChannel.SMS],
                variables=['reason']
            )
        }
    
    def _initialize_channels(self) -> Dict[NotificationChannel, Callable]:
        """Initialize notification delivery channels"""
        return {
            NotificationChannel.EMAIL: self._send_email,
            NotificationChannel.SMS: self._send_sms,
            NotificationChannel.PUSH: self._send_push,
            NotificationChannel.IN_APP: self._send_in_app,
            NotificationChannel.TELEGRAM: self._send_telegram,
            NotificationChannel.WEBHOOK: self._send_webhook
        }
    
    def start_service(self):
        """Start the notification service worker"""
        if not self.running:
            self.running = True
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()
            notification_logger.info("Enhanced notification service started")
    
    def stop_service(self):
        """Stop the notification service"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        notification_logger.info("Enhanced notification service stopped")
    
    def send_notification(self, user_id: int, notification_type: NotificationType, 
                         data: Dict[str, Any] = None, custom_channels: List[NotificationChannel] = None,
                         custom_message: str = None, custom_title: str = None) -> bool:
        """Send notification to user"""
        try:
            template = self.templates.get(notification_type)
            if not template:
                notification_logger.error(f"No template found for notification type: {notification_type}")
                return False
            
            # Get user preferences
            user_prefs = self.user_preferences.get(user_id, {})
            
            # Determine channels to use
            channels = custom_channels or template.channels
            if user_prefs.get('disabled_channels'):
                channels = [ch for ch in channels if ch not in user_prefs['disabled_channels']]
            
            # Format message
            message = custom_message or template.message
            title = custom_title or template.title
            
            if data and template.variables:
                try:
                    message = message.format(**data)
                    title = title.format(**data)
                except KeyError as e:
                    notification_logger.warning(f"Missing variable {e} for notification template")
            
            # Create notification request
            notification = NotificationRequest(
                user_id=user_id,
                type=notification_type,
                title=title,
                message=message,
                priority=template.priority,
                channels=channels,
                data=data or {}
            )
            
            # Add to queue with priority
            priority_value = (4 - template.priority.value, time.time())  # Higher priority = lower number
            self.delivery_queue.put((priority_value, notification))
            
            notification_logger.info(f"Notification queued for user {user_id}: {notification_type.value}")
            return True
            
        except Exception as e:
            notification_logger.error(f"Failed to queue notification: {str(e)}")
            return False
    
    def _worker_loop(self):
        """Main worker loop for processing notifications"""
        while self.running:
            try:
                # Get notification from queue (with timeout)
                try:
                    priority, notification = self.delivery_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                # Check if notification has expired
                if notification.expires_at and datetime.utcnow() > notification.expires_at:
                    notification_logger.info(f"Notification expired: {notification.type.value}")
                    continue
                
                # Check rate limits
                if self._is_rate_limited(notification.user_id, notification.type):
                    # Re-queue for later
                    notification.scheduled_time = datetime.utcnow() + timedelta(minutes=5)
                    self.delivery_queue.put((priority, notification))
                    continue
                
                # Process notification
                self._process_notification(notification)
                
            except Exception as e:
                notification_logger.error(f"Error in notification worker loop: {str(e)}")
                time.sleep(1)
    
    def _process_notification(self, notification: NotificationRequest):
        """Process a single notification"""
        results = []
        
        for channel in notification.channels:
            try:
                if channel in self.channels:
                    result = self.channels[channel](notification)
                    results.append(result)
                    
                    if result.success:
                        self.stats['sent'][channel] += 1
                    else:
                        self.stats['failed'][channel] += 1
                        
                else:
                    notification_logger.warning(f"Unknown notification channel: {channel}")
                    
            except Exception as e:
                error_msg = f"Failed to send via {channel.value}: {str(e)}"
                notification_logger.error(error_msg)
                
                results.append(NotificationResult(
                    success=False,
                    channel=channel,
                    message=notification.message,
                    timestamp=datetime.utcnow(),
                    error=error_msg
                ))
                
                self.stats['failed'][channel] += 1
        
        # Store notification history
        self.notification_history[notification.user_id].append({
            'notification': asdict(notification),
            'results': [asdict(r) for r in results],
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Handle failed notifications
        failed_channels = [r.channel for r in results if not r.success]
        if failed_channels and notification.retry_count < notification.max_retries:
            self._retry_notification(notification, failed_channels)
    
    def _retry_notification(self, notification: NotificationRequest, failed_channels: List[NotificationChannel]):
        """Retry failed notification"""
        notification.retry_count += 1
        notification.channels = failed_channels
        notification.scheduled_time = datetime.utcnow() + timedelta(minutes=2 ** notification.retry_count)
        
        priority_value = (4 - notification.priority.value, time.time())
        self.delivery_queue.put((priority_value, notification))
        
        notification_logger.info(f"Retrying notification (attempt {notification.retry_count}) for user {notification.user_id}")
    
    def _is_rate_limited(self, user_id: int, notification_type: NotificationType) -> bool:
        """Check if user is rate limited for this notification type"""
        now = time.time()
        key = f"{user_id}:{notification_type.value}"
        
        # Clean old entries (last hour)
        while self.rate_limits[key] and self.rate_limits[key][0] < now - 3600:
            self.rate_limits[key].popleft()
        
        # Check limits based on notification type
        if notification_type in [NotificationType.TRADE_EXECUTED, NotificationType.TRADE_FAILED]:
            limit = 10  # Max 10 trade notifications per hour
        elif notification_type in [NotificationType.SECURITY_ALERT, NotificationType.EMERGENCY_STOP]:
            limit = 5   # Max 5 security alerts per hour
        else:
            limit = 20  # Default limit
        
        if len(self.rate_limits[key]) >= limit:
            self.stats['rate_limited'][notification_type] += 1
            return True
        
        # Add current notification
        self.rate_limits[key].append(now)
        return False
    
    def _send_email(self, notification: NotificationRequest) -> NotificationResult:
        """Send email notification"""
        try:
            # Get email configuration
            email_config = self.config.get('email', {})
            if not email_config:
                raise Exception("Email configuration not found")
            
            # Get user email (implement based on your user model)
            user_email = self._get_user_email(notification.user_id)
            if not user_email:
                raise Exception("User email not found")
            
            # Create email message
            msg = MimeMultipart()
            msg['From'] = email_config.get('from_email')
            msg['To'] = user_email
            msg['Subject'] = notification.title
            
            # Create HTML body
            html_body = self._create_email_html(notification)
            msg.attach(MimeText(html_body, 'html'))
            
            # Send email
            with smtplib.SMTP(email_config.get('smtp_host'), email_config.get('smtp_port', 587)) as server:
                server.starttls()
                server.login(email_config.get('username'), email_config.get('password'))
                server.send_message(msg)
            
            return NotificationResult(
                success=True,
                channel=NotificationChannel.EMAIL,
                message=notification.message,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            return NotificationResult(
                success=False,
                channel=NotificationChannel.EMAIL,
                message=notification.message,
                timestamp=datetime.utcnow(),
                error=str(e)
            )
    
    def _send_push(self, notification: NotificationRequest) -> NotificationResult:
        """Send push notification"""
        try:
            # Implement push notification logic (Firebase, etc.)
            # This is a placeholder implementation
            
            push_config = self.config.get('push', {})
            if not push_config:
                raise Exception("Push notification configuration not found")
            
            # Get user's push tokens
            push_tokens = self._get_user_push_tokens(notification.user_id)
            if not push_tokens:
                raise Exception("No push tokens found for user")
            
            # Send push notification (implement with your push service)
            # Example: Firebase Cloud Messaging
            
            return NotificationResult(
                success=True,
                channel=NotificationChannel.PUSH,
                message=notification.message,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            return NotificationResult(
                success=False,
                channel=NotificationChannel.PUSH,
                message=notification.message,
                timestamp=datetime.utcnow(),
                error=str(e)
            )
    
    def _send_sms(self, notification: NotificationRequest) -> NotificationResult:
        """Send SMS notification"""
        try:
            # Implement SMS logic (Twilio, etc.)
            sms_config = self.config.get('sms', {})
            if not sms_config:
                raise Exception("SMS configuration not found")
            
            user_phone = self._get_user_phone(notification.user_id)
            if not user_phone:
                raise Exception("User phone number not found")
            
            # Send SMS (implement with your SMS service)
            
            return NotificationResult(
                success=True,
                channel=NotificationChannel.SMS,
                message=notification.message,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            return NotificationResult(
                success=False,
                channel=NotificationChannel.SMS,
                message=notification.message,
                timestamp=datetime.utcnow(),
                error=str(e)
            )
    
    def _send_in_app(self, notification: NotificationRequest) -> NotificationResult:
        """Send in-app notification"""
        try:
            # Store notification in database for in-app display
            # This would typically involve saving to a notifications table
            
            notification_data = {
                'user_id': notification.user_id,
                'type': notification.type.value,
                'title': notification.title,
                'message': notification.message,
                'priority': notification.priority.value,
                'data': notification.data,
                'created_at': datetime.utcnow(),
                'read': False
            }
            
            # Save to database (implement based on your model)
            # Example: InAppNotification.create(**notification_data)
            
            return NotificationResult(
                success=True,
                channel=NotificationChannel.IN_APP,
                message=notification.message,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            return NotificationResult(
                success=False,
                channel=NotificationChannel.IN_APP,
                message=notification.message,
                timestamp=datetime.utcnow(),
                error=str(e)
            )
    
    def _send_telegram(self, notification: NotificationRequest) -> NotificationResult:
        """Send Telegram notification"""
        try:
            telegram_config = self.config.get('telegram', {})
            if not telegram_config:
                raise Exception("Telegram configuration not found")
            
            # Get user's Telegram chat ID
            chat_id = self._get_user_telegram_chat_id(notification.user_id)
            if not chat_id:
                raise Exception("User Telegram chat ID not found")
            
            # Send Telegram message (implement with Telegram Bot API)
            
            return NotificationResult(
                success=True,
                channel=NotificationChannel.TELEGRAM,
                message=notification.message,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            return NotificationResult(
                success=False,
                channel=NotificationChannel.TELEGRAM,
                message=notification.message,
                timestamp=datetime.utcnow(),
                error=str(e)
            )
    
    def _send_webhook(self, notification: NotificationRequest) -> NotificationResult:
        """Send webhook notification"""
        try:
            import requests
            
            webhook_config = self.config.get('webhook', {})
            if not webhook_config:
                raise Exception("Webhook configuration not found")
            
            # Get user's webhook URL
            webhook_url = self._get_user_webhook_url(notification.user_id)
            if not webhook_url:
                raise Exception("User webhook URL not found")
            
            # Prepare webhook payload
            payload = {
                'type': notification.type.value,
                'title': notification.title,
                'message': notification.message,
                'priority': notification.priority.value,
                'data': notification.data,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Send webhook
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            return NotificationResult(
                success=True,
                channel=NotificationChannel.WEBHOOK,
                message=notification.message,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            return NotificationResult(
                success=False,
                channel=NotificationChannel.WEBHOOK,
                message=notification.message,
                timestamp=datetime.utcnow(),
                error=str(e)
            )
    
    def _create_email_html(self, notification: NotificationRequest) -> str:
        """Create HTML email body"""
        priority_colors = {
            NotificationPriority.LOW: '#28a745',
            NotificationPriority.MEDIUM: '#ffc107',
            NotificationPriority.HIGH: '#fd7e14',
            NotificationPriority.CRITICAL: '#dc3545'
        }
        
        color = priority_colors.get(notification.priority, '#6c757d')
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{notification.title}</title>
        </head>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f8f9fa;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <div style="background-color: {color}; color: white; padding: 20px; text-align: center;">
                    <h1 style="margin: 0; font-size: 24px;">{notification.title}</h1>
                </div>
                <div style="padding: 30px;">
                    <p style="font-size: 16px; line-height: 1.6; color: #333; margin-bottom: 20px;">
                        {notification.message}
                    </p>
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 20px;">
                        <p style="margin: 0; font-size: 14px; color: #6c757d;">
                            <strong>Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}<br>
                            <strong>Priority:</strong> {notification.priority.value.title()}<br>
                            <strong>Type:</strong> {notification.type.value.replace('_', ' ').title()}
                        </p>
                    </div>
                </div>
                <div style="background-color: #f8f9fa; padding: 20px; text-align: center; border-top: 1px solid #dee2e6;">
                    <p style="margin: 0; font-size: 12px; color: #6c757d;">
                        This is an automated notification from your Trading Bot System.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    # Helper methods (implement based on your user model)
    def _get_user_email(self, user_id: int) -> Optional[str]:
        """Get user email address"""
        # Implement based on your user model
        return None
    
    def _get_user_phone(self, user_id: int) -> Optional[str]:
        """Get user phone number"""
        # Implement based on your user model
        return None
    
    def _get_user_push_tokens(self, user_id: int) -> List[str]:
        """Get user push notification tokens"""
        # Implement based on your user model
        return []
    
    def _get_user_telegram_chat_id(self, user_id: int) -> Optional[str]:
        """Get user Telegram chat ID"""
        # Implement based on your user model
        return None
    
    def _get_user_webhook_url(self, user_id: int) -> Optional[str]:
        """Get user webhook URL"""
        # Implement based on your user model
        return None
    
    def set_user_preferences(self, user_id: int, preferences: Dict[str, Any]):
        """Set user notification preferences"""
        self.user_preferences[user_id] = preferences
        notification_logger.info(f"Updated notification preferences for user {user_id}")
    
    def get_notification_history(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get notification history for user"""
        history = self.notification_history.get(user_id, [])
        return history[-limit:] if limit else history
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get notification service statistics"""
        return {
            'running': self.running,
            'queue_size': self.delivery_queue.qsize(),
            'stats': dict(self.stats),
            'total_users': len(self.user_preferences),
            'failed_notifications': len(self.failed_notifications)
        }
    
    def clear_user_history(self, user_id: int):
        """Clear notification history for user"""
        if user_id in self.notification_history:
            del self.notification_history[user_id]
        notification_logger.info(f"Cleared notification history for user {user_id}")

# Global notification service instance
enhanced_notification_service = EnhancedNotificationService()