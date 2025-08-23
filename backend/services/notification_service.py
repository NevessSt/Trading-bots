import smtplib
import requests
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List, Optional
from flask import current_app

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        self.smtp_server = None
        self.smtp_port = None
        self.smtp_username = None
        self.smtp_password = None
        self.from_email = None
        
    def initialize_smtp(self, smtp_server: str, smtp_port: int, username: str, password: str, from_email: str):
        """Initialize SMTP configuration"""
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_username = username
        self.smtp_password = password
        self.from_email = from_email
        
    def send_email(self, to_email: str, subject: str, body: str, html_body: str = None) -> bool:
        """Send email notification"""
        try:
            if not all([self.smtp_server, self.smtp_port, self.smtp_username, self.smtp_password]):
                logger.error("SMTP configuration not initialized")
                return False
                
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # Add plain text part
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            # Add HTML part if provided
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
                
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def send_telegram_message(self, bot_token: str, chat_id: str, message: str, parse_mode: str = 'HTML') -> bool:
        """Send Telegram notification"""
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': parse_mode
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.info(f"Telegram message sent successfully to chat {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Telegram message to {chat_id}: {str(e)}")
            return False
    
    def send_trade_notification(self, user_id: int, trade_data: Dict) -> None:
        """Send trade execution notification"""
        try:
            # Lazy import to avoid circular imports
            from models.user import User
            
            # Get user from database
            user = User.query.get(user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return
                
            # Get user notification settings
            settings = getattr(user, 'notification_settings', None)
            if settings and isinstance(settings, str):
                import json
                settings = json.loads(settings)
            else:
                settings = {}
            
            if not settings.get('trade_notifications', True):
                return
            
            # Prepare notification content
            symbol = trade_data.get('symbol', 'Unknown')
            side = trade_data.get('side', 'Unknown')
            quantity = trade_data.get('quantity', 0)
            price = trade_data.get('price', 0)
            pnl = trade_data.get('pnl', 0)
            
            subject = f"Trade Executed: {symbol}"
            
            # Plain text message
            message = f"""
Trade Notification

Symbol: {symbol}
Side: {side.upper()}
Quantity: {quantity}
Price: ${price:.4f}
P&L: ${pnl:.2f}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This is an automated notification from your trading bot.
"""
            
            # HTML message
            html_message = f"""
<html>
<body>
    <h2>🚀 Trade Notification</h2>
    <table style="border-collapse: collapse; width: 100%;">
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px; font-weight: bold;">Symbol:</td>
            <td style="border: 1px solid #ddd; padding: 8px;">{symbol}</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px; font-weight: bold;">Side:</td>
            <td style="border: 1px solid #ddd; padding: 8px;">{side.upper()}</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px; font-weight: bold;">Quantity:</td>
            <td style="border: 1px solid #ddd; padding: 8px;">{quantity}</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px; font-weight: bold;">Price:</td>
            <td style="border: 1px solid #ddd; padding: 8px;">${price:.4f}</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px; font-weight: bold;">P&L:</td>
            <td style="border: 1px solid #ddd; padding: 8px; color: {'green' if pnl >= 0 else 'red'};">{'$' + str(pnl) if pnl >= 0 else '-$' + str(abs(pnl))}</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px; font-weight: bold;">Time:</td>
            <td style="border: 1px solid #ddd; padding: 8px;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
        </tr>
    </table>
    <p><em>This is an automated notification from your trading bot.</em></p>
</body>
</html>
"""
            
            # Send email notification
            if settings.get('email_notifications', True) and user.email:
                self.send_email(user.email, subject, message, html_message)
            
            # Send Telegram notification
            if settings.get('telegram_notifications', False):
                bot_token = settings.get('telegram_bot_token')
                chat_id = settings.get('telegram_chat_id')
                
                if bot_token and chat_id:
                    telegram_message = f"""
🚀 <b>Trade Executed</b>

📊 <b>Symbol:</b> {symbol}
📈 <b>Side:</b> {side.upper()}
💰 <b>Quantity:</b> {quantity}
💵 <b>Price:</b> ${price:.4f}
📊 <b>P&L:</b> {'$' + str(pnl) if pnl >= 0 else '-$' + str(abs(pnl))}
🕐 <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<em>Automated notification from your trading bot</em>
"""
                    self.send_telegram_message(bot_token, chat_id, telegram_message)
                    
        except Exception as e:
            logger.error(f"Failed to send trade notification: {str(e)}")
    
    def send_profit_loss_alert(self, user_id: int, pnl: float, threshold: float, alert_type: str) -> None:
        """Send profit/loss threshold alert"""
        try:
            # Lazy import to avoid circular imports
            from models.user import User
            
            # Get user from database
            user = User.query.get(user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return
                
            # Get user notification settings
            settings = getattr(user, 'notification_settings', None)
            if settings and isinstance(settings, str):
                import json
                settings = json.loads(settings)
            else:
                settings = {}
            
            if not settings.get('profit_loss_alerts', True):
                return
            
            emoji = "🎉" if alert_type == "profit" else "⚠️"
            color = "green" if alert_type == "profit" else "red"
            
            subject = f"{emoji} {alert_type.title()} Alert: ${abs(pnl):.2f}"
            
            message = f"""
{alert_type.title()} Alert

Your trading bot has {'reached a profit' if alert_type == 'profit' else 'exceeded the loss'} threshold.

Current P&L: ${pnl:.2f}
Threshold: ${threshold:.2f}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Please review your trading strategy and consider taking action if necessary.
"""
            
            html_message = f"""
<html>
<body>
    <h2 style="color: {color};">{emoji} {alert_type.title()} Alert</h2>
    <p>Your trading bot has {'<strong>reached a profit</strong>' if alert_type == 'profit' else '<strong>exceeded the loss</strong>'} threshold.</p>
    
    <table style="border-collapse: collapse; margin: 20px 0;">
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px; font-weight: bold;">Current P&L:</td>
            <td style="border: 1px solid #ddd; padding: 8px; color: {color};">${pnl:.2f}</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px; font-weight: bold;">Threshold:</td>
            <td style="border: 1px solid #ddd; padding: 8px;">${threshold:.2f}</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px; font-weight: bold;">Time:</td>
            <td style="border: 1px solid #ddd; padding: 8px;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
        </tr>
    </table>
    
    <p><em>Please review your trading strategy and consider taking action if necessary.</em></p>
</body>
</html>
"""
            
            # Send email notification
            if settings.get('email_notifications', True) and user.email:
                self.send_email(user.email, subject, message, html_message)
            
            # Send Telegram notification
            if settings.get('telegram_notifications', False):
                bot_token = settings.get('telegram_bot_token')
                chat_id = settings.get('telegram_chat_id')
                
                if bot_token and chat_id:
                    telegram_message = f"""
{emoji} <b>{alert_type.title()} Alert</b>

Your trading bot has {'<b>reached a profit</b>' if alert_type == 'profit' else '<b>exceeded the loss</b>'} threshold.

💰 <b>Current P&L:</b> ${pnl:.2f}
🎯 <b>Threshold:</b> ${threshold:.2f}
🕐 <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<em>Please review your trading strategy and consider taking action if necessary.</em>
"""
                    self.send_telegram_message(bot_token, chat_id, telegram_message)
                    
        except Exception as e:
            logger.error(f"Failed to send profit/loss alert: {str(e)}")
    
    def send_bot_status_alert(self, user_id: int, bot_name: str, status: str, message: str = None) -> None:
        """Send bot status change alert"""
        try:
            # Lazy import to avoid circular imports
            from models.user import User
            
            # Get user from database
            user = User.query.get(user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return
                
            # Get user notification settings
            settings = getattr(user, 'notification_settings', None)
            if settings and isinstance(settings, str):
                import json
                settings = json.loads(settings)
            else:
                settings = {}
            
            if not settings.get('system_alerts', True):
                return
            
            status_emoji = {
                'started': '🟢',
                'stopped': '🔴',
                'error': '❌',
                'warning': '⚠️',
                'paused': '⏸️'
            }.get(status.lower(), '🔵')
            
            subject = f"{status_emoji} Bot Status: {bot_name} - {status.title()}"
            
            email_message = f"""
Bot Status Alert

Bot Name: {bot_name}
Status: {status.title()}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{message or 'No additional details provided.'}

This is an automated notification from your trading system.
"""
            
            html_message = f"""
<html>
<body>
    <h2>{status_emoji} Bot Status Alert</h2>
    <table style="border-collapse: collapse; margin: 20px 0;">
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px; font-weight: bold;">Bot Name:</td>
            <td style="border: 1px solid #ddd; padding: 8px;">{bot_name}</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px; font-weight: bold;">Status:</td>
            <td style="border: 1px solid #ddd; padding: 8px;">{status.title()}</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px; font-weight: bold;">Time:</td>
            <td style="border: 1px solid #ddd; padding: 8px;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
        </tr>
    </table>
    
    {f'<p><strong>Details:</strong> {message}</p>' if message else ''}
    
    <p><em>This is an automated notification from your trading system.</em></p>
</body>
</html>
"""
            
            # Send email notification
            if settings.get('email_notifications', True) and user.email:
                self.send_email(user.email, subject, email_message, html_message)
            
            # Send Telegram notification
            if settings.get('telegram_notifications', False):
                bot_token = settings.get('telegram_bot_token')
                chat_id = settings.get('telegram_chat_id')
                
                if bot_token and chat_id:
                    telegram_message = f"""
{status_emoji} <b>Bot Status Alert</b>

🤖 <b>Bot Name:</b> {bot_name}
📊 <b>Status:</b> {status.title()}
🕐 <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{f'<b>Details:</b> {message}' if message else ''}

<em>Automated notification from your trading system</em>
"""
                    self.send_telegram_message(bot_token, chat_id, telegram_message)
                    
        except Exception as e:
            logger.error(f"Failed to send bot status alert: {str(e)}")
    
    def send_daily_summary(self, user_id: int, summary_data: Dict) -> None:
        """Send daily trading summary"""
        try:
            # Lazy import to avoid circular imports
            from models.user import User
            
            # Get user from database
            user = User.query.get(user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return
                
            # Get user notification settings
            settings = getattr(user, 'notification_settings', None)
            if settings and isinstance(settings, str):
                import json
                settings = json.loads(settings)
            else:
                settings = {}
            
            if not settings.get('daily_summary', True):
                return
            
            total_pnl = summary_data.get('total_pnl', 0)
            total_trades = summary_data.get('total_trades', 0)
            winning_trades = summary_data.get('winning_trades', 0)
            losing_trades = summary_data.get('losing_trades', 0)
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            subject = f"📊 Daily Trading Summary - {datetime.now().strftime('%Y-%m-%d')}"
            
            message = f"""
Daily Trading Summary - {datetime.now().strftime('%Y-%m-%d')}

Total P&L: ${total_pnl:.2f}
Total Trades: {total_trades}
Winning Trades: {winning_trades}
Losing Trades: {losing_trades}
Win Rate: {win_rate:.1f}%

Thank you for using our trading platform!
"""
            
            html_message = f"""
<html>
<body>
    <h2>📊 Daily Trading Summary</h2>
    <h3>{datetime.now().strftime('%Y-%m-%d')}</h3>
    
    <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
        <tr>
            <td style="border: 1px solid #ddd; padding: 12px; font-weight: bold; background-color: #f2f2f2;">Total P&L:</td>
            <td style="border: 1px solid #ddd; padding: 12px; color: {'green' if total_pnl >= 0 else 'red'}; font-weight: bold;">${total_pnl:.2f}</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 12px; font-weight: bold; background-color: #f2f2f2;">Total Trades:</td>
            <td style="border: 1px solid #ddd; padding: 12px;">{total_trades}</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 12px; font-weight: bold; background-color: #f2f2f2;">Winning Trades:</td>
            <td style="border: 1px solid #ddd; padding: 12px; color: green;">{winning_trades}</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 12px; font-weight: bold; background-color: #f2f2f2;">Losing Trades:</td>
            <td style="border: 1px solid #ddd; padding: 12px; color: red;">{losing_trades}</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 12px; font-weight: bold; background-color: #f2f2f2;">Win Rate:</td>
            <td style="border: 1px solid #ddd; padding: 12px; font-weight: bold;">{win_rate:.1f}%</td>
        </tr>
    </table>
    
    <p><em>Thank you for using our trading platform!</em></p>
</body>
</html>
"""
            
            # Send email notification
            if settings.get('email_notifications', True) and user.email:
                self.send_email(user.email, subject, message, html_message)
            
            # Send Telegram notification
            if settings.get('telegram_notifications', False):
                bot_token = settings.get('telegram_bot_token')
                chat_id = settings.get('telegram_chat_id')
                
                if bot_token and chat_id:
                    telegram_message = f"""
📊 <b>Daily Trading Summary</b>
📅 <b>{datetime.now().strftime('%Y-%m-%d')}</b>

💰 <b>Total P&L:</b> ${total_pnl:.2f}
📈 <b>Total Trades:</b> {total_trades}
✅ <b>Winning Trades:</b> {winning_trades}
❌ <b>Losing Trades:</b> {losing_trades}
🎯 <b>Win Rate:</b> {win_rate:.1f}%

<em>Thank you for using our trading platform!</em>
"""
                    self.send_telegram_message(bot_token, chat_id, telegram_message)
                    
        except Exception as e:
            logger.error(f"Failed to send daily summary: {str(e)}")
    
    def send_market_alert(self, user_ids: List[int], alert_data: Dict) -> None:
        """Send market alert to multiple users"""
        try:
            # Lazy import to avoid circular imports
            from models.user import User
            
            alert_type = alert_data.get('type', 'general')
            message = alert_data.get('message', 'Market alert')
            symbol = alert_data.get('symbol', '')
            
            subject = f"🚨 Market Alert: {symbol}" if symbol else "🚨 Market Alert"
            
            email_message = f"""
Market Alert

{message}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This is an automated market alert from your trading system.
"""
            
            html_message = f"""
<html>
<body>
    <h2>🚨 Market Alert</h2>
    {f'<h3>{symbol}</h3>' if symbol else ''}
    
    <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0;">
        <p style="margin: 0; font-size: 16px;">{message}</p>
    </div>
    
    <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <p><em>This is an automated market alert from your trading system.</em></p>
</body>
</html>
"""
            
            for user_id in user_ids:
                try:
                    # Get user from database
                    user = User.query.get(user_id)
                    if not user:
                        logger.error(f"User {user_id} not found")
                        continue
                        
                    # Get user notification settings
                    settings = getattr(user, 'notification_settings', None)
                    if settings and isinstance(settings, str):
                        import json
                        settings = json.loads(settings)
                    else:
                        settings = {}
                    
                    # Send email notification
                    if settings.get('email_notifications', True) and user.email:
                        self.send_email(user.email, subject, email_message, html_message)
                    
                    # Send Telegram notification
                    if settings.get('telegram_notifications', False):
                        bot_token = settings.get('telegram_bot_token')
                        chat_id = settings.get('telegram_chat_id')
                        
                        if bot_token and chat_id:
                            telegram_message = f"""
🚨 <b>Market Alert</b>
{f'📊 <b>{symbol}</b>' if symbol else ''}

{message}

🕐 <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<em>Automated market alert from your trading system</em>
"""
                            self.send_telegram_message(bot_token, chat_id, telegram_message)
                            
                except Exception as e:
                    logger.error(f"Failed to send market alert to user {user_id}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Failed to send market alerts: {str(e)}")

# Global notification service instance
notification_service = NotificationService()