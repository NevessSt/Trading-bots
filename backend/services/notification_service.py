import smtplib
import requests
import logging
import json
import asyncio
import aiohttp
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from flask import current_app
from database import db
from models.notification import NotificationPreference, NotificationLog, NotificationTemplate
from models.user import User
from services.logging_service import get_logger, LogCategory
from services.retry_service import get_retry_service, RetryConfig, async_retry, API_RETRY_CONFIG

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self, websocket_service=None):
        self.websocket_service = websocket_service
        self.email_config = {
            'smtp_server': current_app.config.get('SMTP_SERVER', 'smtp.gmail.com') if current_app else 'smtp.gmail.com',
            'smtp_port': current_app.config.get('SMTP_PORT', 587) if current_app else 587,
            'smtp_username': current_app.config.get('SMTP_USERNAME') if current_app else None,
            'smtp_password': current_app.config.get('SMTP_PASSWORD') if current_app else None,
            'from_email': current_app.config.get('FROM_EMAIL') if current_app else None
        }
        
        self.telegram_config = {
            'bot_token': current_app.config.get('TELEGRAM_BOT_TOKEN') if current_app else None,
            'api_url': 'https://api.telegram.org/bot{}/sendMessage'
        }
        
        self.push_config = {
            'firebase_key': current_app.config.get('FIREBASE_SERVER_KEY') if current_app else None,
            'fcm_url': 'https://fcm.googleapis.com/fcm/send'
        }
        
    def send_notification(self, user_id: int, event_type: str, data: Dict[str, Any]) -> Dict[str, bool]:
        """Send notifications based on user preferences"""
        results = {'email': False, 'telegram': False, 'push': False}
        
        try:
            user = User.query.get(user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return results
            
            # Get user notification preferences
            preferences = NotificationPreference.query.filter_by(
                user_id=user_id,
                event_type=event_type,
                enabled=True
            ).all()
            
            # If no preferences exist, create default ones
            if not preferences:
                self.create_default_preferences(user_id)
                preferences = NotificationPreference.query.filter_by(
                    user_id=user_id,
                    event_type=event_type,
                    enabled=True
                ).all()
            
            for pref in preferences:
                try:
                    if pref.notification_type == 'email' and user.email:
                        results['email'] = self._send_email(user, event_type, data, pref)
                    elif pref.notification_type == 'telegram':
                        results['telegram'] = self._send_telegram(user, event_type, data, pref)
                    elif pref.notification_type == 'push':
                        results['push'] = self._send_push(user, event_type, data, pref)
                except Exception as e:
                    self._log_notification(user_id, pref.notification_type, event_type, 
                                         '', '', str(data), 'failed', str(e))
            
            # Send real-time notification via WebSocket if available
            if any(results.values()) and self.websocket_service:
                try:
                    websocket_data = {
                        'event_type': event_type,
                        'data': data,
                        'results': results,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    self.websocket_service.send_notification_to_user(user_id, websocket_data)
                except Exception as e:
                    logger.error(f'Error sending WebSocket notification: {e}')
            
            return results
            
        except Exception as e:
            logger.error(f"Notification service error: {str(e)}")
            return results
        
    def _send_email(self, user: User, event_type: str, data: Dict[str, Any], 
                   preference: NotificationPreference) -> bool:
        """Send email notification"""
        try:
            if not all([self.email_config['smtp_username'], 
                       self.email_config['smtp_password'],
                       self.email_config['from_email']]):
                logger.error("SMTP configuration not complete")
                return False
            
            subject, body = self._generate_email_content(event_type, data, user)
            
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_config['from_email']
            msg['To'] = user.email
            msg['Subject'] = subject
            
            # Add HTML content
            html_part = MIMEText(body, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.email_config['smtp_server'], 
                            self.email_config['smtp_port']) as server:
                server.starttls()
                server.login(self.email_config['smtp_username'], 
                           self.email_config['smtp_password'])
                server.send_message(msg)
            
            self._log_notification(user.id, 'email', event_type, user.email, 
                                 subject, body, 'sent')
            logger.info(f"Email sent successfully to {user.email}")
            return True
            
        except Exception as e:
            self._log_notification(user.id, 'email', event_type, user.email, 
                                 subject if 'subject' in locals() else '', 
                                 body if 'body' in locals() else '', 'failed', str(e))
            logger.error(f"Failed to send email to {user.email}: {str(e)}")
            return False
    
    def _send_telegram(self, user: User, event_type: str, data: Dict[str, Any], 
                      preference: NotificationPreference) -> bool:
        """Send Telegram notification"""
        try:
            if not self.telegram_config['bot_token']:
                logger.error("Telegram bot token not configured")
                return False
            
            # Get user's Telegram chat ID from preference settings
            settings = json.loads(preference.settings or '{}')
            chat_id = settings.get('telegram_chat_id')
            
            if not chat_id:
                logger.error(f"Telegram chat ID not configured for user {user.id}")
                return False
            
            message = self._generate_telegram_content(event_type, data, user)
            
            url = self.telegram_config['api_url'].format(self.telegram_config['bot_token'])
            payload = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                self._log_notification(user.id, 'telegram', event_type, chat_id, 
                                     '', message, 'sent')
                logger.info(f"Telegram message sent successfully to chat {chat_id}")
                return True
            else:
                self._log_notification(user.id, 'telegram', event_type, chat_id, 
                                     '', message, 'failed', response.text)
                logger.error(f"Failed to send Telegram message: {response.text}")
                return False
                
        except Exception as e:
            self._log_notification(user.id, 'telegram', event_type, 
                                 chat_id if 'chat_id' in locals() else '', 
                                 '', message if 'message' in locals() else '', 
                                 'failed', str(e))
            logger.error(f"Failed to send Telegram message: {str(e)}")
            return False
    
    def _send_push(self, user: User, event_type: str, data: Dict[str, Any], 
                  preference: NotificationPreference) -> bool:
        """Send push notification via Firebase FCM"""
        try:
            if not self.push_config['firebase_key']:
                logger.error("Firebase server key not configured")
                return False
            
            # Get user's FCM token from preference settings
            settings = json.loads(preference.settings or '{}')
            fcm_token = settings.get('fcm_token')
            
            if not fcm_token:
                logger.error(f"FCM token not configured for user {user.id}")
                return False
            
            title, body = self._generate_push_content(event_type, data, user)
            
            headers = {
                'Authorization': f'key={self.push_config["firebase_key"]}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'to': fcm_token,
                'notification': {
                    'title': title,
                    'body': body,
                    'icon': 'trading_bot_icon',
                    'click_action': 'FLUTTER_NOTIFICATION_CLICK'
                },
                'data': {
                    'event_type': event_type,
                    'timestamp': datetime.utcnow().isoformat(),
                    **data
                }
            }
            
            response = requests.post(self.push_config['fcm_url'], 
                                   headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                self._log_notification(user.id, 'push', event_type, fcm_token, 
                                     title, body, 'sent')
                logger.info(f"Push notification sent successfully to {fcm_token[:10]}...")
                return True
            else:
                self._log_notification(user.id, 'push', event_type, fcm_token, 
                                     title, body, 'failed', response.text)
                logger.error(f"Failed to send push notification: {response.text}")
                return False
                
        except Exception as e:
            self._log_notification(user.id, 'push', event_type, 
                                 fcm_token if 'fcm_token' in locals() else '', 
                                 title if 'title' in locals() else '', 
                                 body if 'body' in locals() else '', 
                                 'failed', str(e))
            logger.error(f"Failed to send push notification: {str(e)}")
            return False
    
    def _generate_email_content(self, event_type: str, data: Dict[str, Any], user: User) -> Tuple[str, str]:
        """Generate email subject and body content"""
        try:
            template = NotificationTemplate.query.filter_by(
                event_type=event_type, 
                notification_type='email'
            ).first()
            
            if template:
                subject = template.subject_template.format(**data, user=user)
                body = template.body_template.format(**data, user=user)
            else:
                # Default templates
                if event_type == 'trade_executed':
                    subject = f"Trade Executed - {data.get('symbol', 'Unknown')}"
                    body = f"""Dear {user.username},
                    
Your trade has been executed:
                    Symbol: {data.get('symbol', 'N/A')}
                    Side: {data.get('side', 'N/A')}
                    Quantity: {data.get('quantity', 'N/A')}
                    Price: {data.get('price', 'N/A')}
                    
                    Best regards,
                    Trading Bot System"""
                elif event_type == 'trade_failed':
                    subject = f"Trade Failed - {data.get('symbol', 'Unknown')}"
                    body = f"""Dear {user.username},
                    
                    Your trade failed to execute:
                    Symbol: {data.get('symbol', 'N/A')}
                    Error: {data.get('error', 'Unknown error')}
                    
                    Please check your bot configuration.
                    
                    Best regards,
                    Trading Bot System"""
                else:
                    subject = f"Trading Bot Notification - {event_type}"
                    body = f"Dear {user.username},\n\nEvent: {event_type}\nData: {data}\n\nBest regards,\nTrading Bot System"
            
            return subject, body
            
        except Exception as e:
            logger.error(f"Failed to generate email content: {str(e)}")
            return f"Trading Bot Notification - {event_type}", f"Event: {event_type}\nData: {data}"
    
    def _generate_telegram_content(self, event_type: str, data: Dict[str, Any], user: User) -> str:
        """Generate Telegram message content"""
        try:
            template = NotificationTemplate.query.filter_by(
                event_type=event_type, 
                notification_type='telegram'
            ).first()
            
            if template:
                message = template.body_template.format(**data, user=user)
            else:
                # Default templates
                if event_type == 'trade_executed':
                    message = f"""🎯 <b>Trade Executed</b>
                    
📊 Symbol: {data.get('symbol', 'N/A')}
📈 Side: {data.get('side', 'N/A')}
💰 Quantity: {data.get('quantity', 'N/A')}
💵 Price: {data.get('price', 'N/A')}
⏰ Time: {data.get('timestamp', 'N/A')}"""
                elif event_type == 'trade_failed':
                    message = f"""❌ <b>Trade Failed</b>
                    
📊 Symbol: {data.get('symbol', 'N/A')}
❗ Error: {data.get('error', 'Unknown error')}
⏰ Time: {data.get('timestamp', 'N/A')}"""
                elif event_type == 'bot_started':
                    message = f"""🚀 <b>Bot Started</b>
                    
🤖 Bot: {data.get('bot_name', 'N/A')}
📊 Strategy: {data.get('strategy', 'N/A')}
⏰ Time: {data.get('timestamp', 'N/A')}"""
                else:
                    message = f"<b>{event_type.replace('_', ' ').title()}</b>\n\n{data}"
            
            return message
            
        except Exception as e:
            logger.error(f"Failed to generate Telegram content: {str(e)}")
            return f"Event: {event_type}\nData: {data}"
    
    def _generate_push_content(self, event_type: str, data: Dict[str, Any], user: User) -> Tuple[str, str]:
        """Generate push notification title and body"""
        try:
            template = NotificationTemplate.query.filter_by(
                event_type=event_type, 
                notification_type='push'
            ).first()
            
            if template:
                title = template.subject_template.format(**data, user=user)
                body = template.body_template.format(**data, user=user)
            else:
                # Default templates
                if event_type == 'trade_executed':
                    title = "Trade Executed"
                    body = f"{data.get('side', 'N/A')} {data.get('quantity', 'N/A')} {data.get('symbol', 'N/A')} at {data.get('price', 'N/A')}"
                elif event_type == 'trade_failed':
                    title = "Trade Failed"
                    body = f"Failed to execute {data.get('symbol', 'N/A')} trade: {data.get('error', 'Unknown error')}"
                elif event_type == 'bot_started':
                    title = "Bot Started"
                    body = f"{data.get('bot_name', 'N/A')} is now running"
                else:
                    title = event_type.replace('_', ' ').title()
                    body = str(data)
            
            return title, body
            
        except Exception as e:
            logger.error(f"Failed to generate push content: {str(e)}")
            return event_type.replace('_', ' ').title(), str(data)
    
    def _log_notification(self, user_id: int, notification_type: str, event_type: str, 
                         recipient: str, subject: str, content: str, status: str, 
                         error_message: str = None) -> None:
        """Log notification to database"""
        try:
            log_entry = NotificationLog(
                user_id=user_id,
                notification_type=notification_type,
                event_type=event_type,
                recipient=recipient,
                subject=subject,
                content=content,
                status=status,
                error_message=error_message,
                sent_at=datetime.utcnow()
            )
            
            db.session.add(log_entry)
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Failed to log notification: {str(e)}")
            db.session.rollback()
    
    def send_trade_notification(self, user_id: int, trade_data: Dict) -> None:
        """Send trade execution notification"""
        try:
            self.send_notification(user_id, 'trade_executed', trade_data)
        except Exception as e:
            logger.error(f"Failed to send trade notification: {str(e)}")
    
    def send_profit_loss_alert(self, user_id: int, pnl: float, threshold: float, alert_type: str) -> None:
        """Send profit/loss threshold alert"""
        try:
            pnl_data = {
                'pnl': pnl,
                'threshold': threshold,
                'type': alert_type,
                'timestamp': datetime.utcnow().isoformat()
            }
            event_type = 'profit_alert' if alert_type == 'profit' else 'loss_alert'
            self.send_notification(user_id, event_type, pnl_data)
        except Exception as e:
            logger.error(f"Failed to send P&L alert: {str(e)}")
    
    def send_bot_status_alert(self, user_id: int, bot_name: str, status: str, message: str = None) -> None:
        """Send bot status change alert"""
        try:
            bot_data = {
                'bot_name': bot_name,
                'status': status,
                'message': message,
                'timestamp': datetime.utcnow().isoformat()
            }
            event_type = f"bot_{status}"
            self.send_notification(user_id, event_type, bot_data)
        except Exception as e:
            logger.error(f"Failed to send bot status alert: {str(e)}")
    
    def send_daily_summary(self, user_id: int, summary_data: Dict) -> None:
        """Send daily trading summary"""
        try:
            summary_data['timestamp'] = datetime.utcnow().isoformat()
            self.send_notification(user_id, 'daily_summary', summary_data)
        except Exception as e:
            logger.error(f"Failed to send daily summary: {str(e)}")
    
    def send_market_alert(self, user_ids: List[int], alert_data: Dict) -> None:
        """Send market alert to multiple users"""
        try:
            alert_data['timestamp'] = datetime.utcnow().isoformat()
            for user_id in user_ids:
                try:
                    self.send_notification(user_id, 'market_alert', alert_data)
                except Exception as e:
                    logger.error(f"Failed to send market alert to user {user_id}: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to send market alerts: {str(e)}")

    def create_default_preferences(self, user_id: int) -> None:
        """Create default notification preferences for a user"""
        try:
            default_events = [
                'trade_executed', 'trade_failed', 'bot_started', 'bot_stopped', 
                'bot_error', 'profit_alert', 'loss_alert', 'daily_summary', 
                'market_alert', 'system_alert'
            ]
            
            default_types = ['email', 'telegram', 'push']
            
            for event_type in default_events:
                for notification_type in default_types:
                    # Check if preference already exists
                    existing = NotificationPreference.query.filter_by(
                        user_id=user_id,
                        event_type=event_type,
                        notification_type=notification_type
                    ).first()
                    
                    if not existing:
                        preference = NotificationPreference(
                            user_id=user_id,
                            event_type=event_type,
                            notification_type=notification_type,
                            enabled=True if notification_type == 'email' else False,
                            settings='{}'
                        )
                        db.session.add(preference)
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Failed to create default preferences: {str(e)}")
            db.session.rollback()
    
    def send_test_notification(self, user_id: int, notification_type: str) -> bool:
        """Send test notification for configuration testing"""
        try:
            test_data = {
                'message': 'This is a test notification',
                'timestamp': datetime.utcnow().isoformat(),
                'test': True
            }
            
            user = User.query.get(user_id)
            if not user:
                return False
            
            # Get or create preference for the user
            preference = NotificationPreference.query.filter_by(
                user_id=user_id, 
                notification_type=notification_type
            ).first()
            
            if not preference:
                return False
            
            if notification_type == 'email':
                return self._send_email(user, 'test_notification', test_data, preference)
            elif notification_type == 'telegram':
                return self._send_telegram(user, 'test_notification', test_data, preference)
            elif notification_type == 'push':
                return self._send_push(user, 'test_notification', test_data, preference)
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to send test notification: {str(e)}")
            return False
    
    # Enhanced error handling and system notification methods
    def send_system_error(self, error_message: str, error_type: str = 'system_error', 
                         metadata: Dict[str, Any] = None) -> None:
        """Send system error notification to all admin users"""
        try:
            # Get all admin users
            admin_users = User.query.filter_by(role='admin').all()
            
            error_data = {
                'error_message': error_message,
                'error_type': error_type,
                'timestamp': datetime.utcnow().isoformat(),
                'metadata': metadata or {}
            }
            
            for admin in admin_users:
                self.send_notification(admin.id, 'system_error', error_data)
                
        except Exception as e:
            logger.error(f"Failed to send system error notification: {str(e)}")
    
    def send_critical_alert(self, title: str, message: str, metadata: Dict[str, Any] = None) -> None:
        """Send critical alert to all admin users immediately"""
        try:
            admin_users = User.query.filter_by(role='admin').all()
            
            alert_data = {
                'title': title,
                'message': message,
                'severity': 'critical',
                'timestamp': datetime.utcnow().isoformat(),
                'metadata': metadata or {}
            }
            
            for admin in admin_users:
                self.send_notification(admin.id, 'critical_alert', alert_data)
                
        except Exception as e:
            logger.error(f"Failed to send critical alert: {str(e)}")
    
    def send_api_error_alert(self, api_name: str, error_message: str, 
                           retry_count: int = 0, metadata: Dict[str, Any] = None) -> None:
        """Send API error notification"""
        try:
            admin_users = User.query.filter_by(role='admin').all()
            
            api_error_data = {
                'api_name': api_name,
                'error_message': error_message,
                'retry_count': retry_count,
                'timestamp': datetime.utcnow().isoformat(),
                'metadata': metadata or {}
            }
            
            for admin in admin_users:
                self.send_notification(admin.id, 'api_error', api_error_data)
                
        except Exception as e:
            logger.error(f"Failed to send API error alert: {str(e)}")
    
    def send_trading_engine_alert(self, engine_status: str, message: str, 
                                metadata: Dict[str, Any] = None) -> None:
        """Send trading engine status alert"""
        try:
            # Send to all users who have trading bots
            users_with_bots = User.query.filter(User.trading_bots.any()).all()
            
            engine_data = {
                'engine_status': engine_status,
                'message': message,
                'timestamp': datetime.utcnow().isoformat(),
                'metadata': metadata or {}
            }
            
            for user in users_with_bots:
                self.send_notification(user.id, 'trading_engine_alert', engine_data)
                
        except Exception as e:
            logger.error(f"Failed to send trading engine alert: {str(e)}")
    
    def send_security_alert(self, security_event: str, details: str, 
                          user_id: Optional[int] = None, metadata: Dict[str, Any] = None) -> None:
        """Send security alert"""
        try:
            security_data = {
                'security_event': security_event,
                'details': details,
                'timestamp': datetime.utcnow().isoformat(),
                'metadata': metadata or {}
            }
            
            if user_id:
                # Send to specific user
                self.send_notification(user_id, 'security_alert', security_data)
            else:
                # Send to all admin users
                admin_users = User.query.filter_by(role='admin').all()
                for admin in admin_users:
                    self.send_notification(admin.id, 'security_alert', security_data)
                    
        except Exception as e:
            logger.error(f"Failed to send security alert: {str(e)}")
    
    @async_retry(config=API_RETRY_CONFIG, circuit_breaker="telegram_async")
    async def send_telegram_async(self, chat_id: str, message: str) -> bool:
        """Send Telegram message asynchronously with retry logic"""
        if not self.telegram_config['bot_token']:
            logger.warning("Telegram bot token not configured")
            return False
            
        try:
            url = self.telegram_config['api_url'].format(self.telegram_config['bot_token'])
            payload = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        logger.info(f"Telegram message sent successfully to {chat_id}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Telegram API error {response.status}: {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {str(e)}")
            raise
    
    def send_immediate_alert(self, message: str, alert_type: str = 'urgent') -> None:
        """Send immediate alert via all available channels"""
        try:
            # Get emergency contact settings
            emergency_telegram_chat = current_app.config.get('EMERGENCY_TELEGRAM_CHAT') if current_app else None
            emergency_email = current_app.config.get('EMERGENCY_EMAIL') if current_app else None
            
            alert_data = {
                'message': message,
                'alert_type': alert_type,
                'timestamp': datetime.utcnow().isoformat(),
                'severity': 'immediate'
            }
            
            # Send to emergency Telegram if configured
            if emergency_telegram_chat and self.telegram_config['bot_token']:
                asyncio.create_task(self.send_telegram_async(emergency_telegram_chat, 
                    f"🚨 URGENT ALERT 🚨\n\n{message}\n\nTime: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"))
            
            # Send to all admin users
            admin_users = User.query.filter_by(role='admin').all()
            for admin in admin_users:
                self.send_notification(admin.id, 'immediate_alert', alert_data)
                
        except Exception as e:
            logger.error(f"Failed to send immediate alert: {str(e)}")

# Global notification service instance
notification_service = NotificationService()