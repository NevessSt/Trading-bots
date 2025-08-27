from datetime import datetime
from database import db
import json

class NotificationPreference(db.Model):
    __tablename__ = 'notification_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)  # email, telegram, push
    event_type = db.Column(db.String(50), nullable=False)  # trade_executed, trade_failed, bot_started, etc.
    enabled = db.Column(db.Boolean, default=True)
    settings = db.Column(db.Text)  # JSON string for additional settings
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref='notification_preferences')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'notification_type': self.notification_type,
            'event_type': self.event_type,
            'enabled': self.enabled,
            'settings': json.loads(self.settings) if self.settings else {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def create_default_preferences(user_id):
        """Create default notification preferences for a new user"""
        default_events = [
            'trade_executed', 'trade_failed', 'bot_started', 
            'bot_stopped', 'system_error', 'profit_alert', 'loss_alert'
        ]
        
        preferences = []
        for event_type in default_events:
            # Email preference (enabled by default for critical events)
            email_enabled = event_type in ['trade_failed', 'system_error', 'loss_alert']
            email_pref = NotificationPreference(
                user_id=user_id,
                notification_type='email',
                event_type=event_type,
                enabled=email_enabled
            )
            preferences.append(email_pref)
            
            # Telegram preference (disabled by default)
            telegram_pref = NotificationPreference(
                user_id=user_id,
                notification_type='telegram',
                event_type=event_type,
                enabled=False
            )
            preferences.append(telegram_pref)
            
            # Push preference (disabled by default)
            push_pref = NotificationPreference(
                user_id=user_id,
                notification_type='push',
                event_type=event_type,
                enabled=False
            )
            preferences.append(push_pref)
        
        return preferences

class NotificationLog(db.Model):
    __tablename__ = 'notification_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)
    recipient = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(255))
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, sent, failed
    error_message = db.Column(db.Text)
    sent_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='notification_logs')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'notification_type': self.notification_type,
            'event_type': self.event_type,
            'recipient': self.recipient,
            'subject': self.subject,
            'message': self.message,
            'status': self.status,
            'error_message': self.error_message,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class NotificationTemplate(db.Model):
    __tablename__ = 'notification_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(50), nullable=False, unique=True)
    email_subject = db.Column(db.String(255))
    email_body = db.Column(db.Text)
    telegram_template = db.Column(db.Text)
    push_title = db.Column(db.String(255))
    push_body = db.Column(db.Text)
    variables = db.Column(db.Text)  # JSON array of available variables
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'event_type': self.event_type,
            'email_subject': self.email_subject,
            'email_body': self.email_body,
            'telegram_template': self.telegram_template,
            'push_title': self.push_title,
            'push_body': self.push_body,
            'variables': json.loads(self.variables) if self.variables else [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def create_default_templates():
        """Create default notification templates"""
        templates = [
            {
                'event_type': 'trade_executed',
                'email_subject': 'Trade Executed Successfully - {symbol}',
                'email_body': '''<html><body>
<h2>🎉 Trade Executed Successfully</h2>
<p>Hello {username},</p>
<p>Your trade has been executed successfully:</p>
<ul>
    <li><strong>Symbol:</strong> {symbol}</li>
    <li><strong>Side:</strong> {side}</li>
    <li><strong>Quantity:</strong> {quantity}</li>
    <li><strong>Price:</strong> ${price}</li>
    <li><strong>Bot:</strong> {bot_name}</li>
    <li><strong>P&L:</strong> ${pnl}</li>
    <li><strong>Time:</strong> {timestamp}</li>
</ul>
<p>Best regards,<br>Trading Bot Platform</p>
</body></html>''',
                'telegram_template': '''🎉 <b>Trade Executed Successfully</b>\n\n📊 <b>Symbol:</b> {symbol}\n📈 <b>Side:</b> {side}\n💰 <b>Quantity:</b> {quantity}\n💵 <b>Price:</b> ${price}\n🤖 <b>Bot:</b> {bot_name}\n📊 <b>P&L:</b> ${pnl}\n⏰ <b>Time:</b> {timestamp}''',
                'push_title': 'Trade Executed',
                'push_body': '{side} {quantity} {symbol} at ${price}',
                'variables': json.dumps(['username', 'symbol', 'side', 'quantity', 'price', 'bot_name', 'pnl', 'timestamp'])
            },
            {
                'event_type': 'trade_failed',
                'email_subject': 'Trade Failed - {symbol}',
                'email_body': '''<html><body>
<h2>❌ Trade Failed</h2>
<p>Hello {username},</p>
<p>Unfortunately, your trade failed to execute:</p>
<ul>
    <li><strong>Symbol:</strong> {symbol}</li>
    <li><strong>Side:</strong> {side}</li>
    <li><strong>Quantity:</strong> {quantity}</li>
    <li><strong>Bot:</strong> {bot_name}</li>
    <li><strong>Error:</strong> {error_message}</li>
    <li><strong>Time:</strong> {timestamp}</li>
</ul>
<p>Please check your bot configuration and try again.</p>
<p>Best regards,<br>Trading Bot Platform</p>
</body></html>''',
                'telegram_template': '''❌ <b>Trade Failed</b>\n\n📊 <b>Symbol:</b> {symbol}\n📈 <b>Side:</b> {side}\n💰 <b>Quantity:</b> {quantity}\n🤖 <b>Bot:</b> {bot_name}\n⚠️ <b>Error:</b> {error_message}\n⏰ <b>Time:</b> {timestamp}''',
                'push_title': 'Trade Failed',
                'push_body': '{side} {quantity} {symbol} failed: {error_message}',
                'variables': json.dumps(['username', 'symbol', 'side', 'quantity', 'bot_name', 'error_message', 'timestamp'])
            },
            {
                'event_type': 'bot_started',
                'email_subject': 'Bot Started - {bot_name}',
                'email_body': '''<html><body>
<h2>🚀 Bot Started</h2>
<p>Hello {username},</p>
<p>Your trading bot has been started successfully:</p>
<ul>
    <li><strong>Bot Name:</strong> {bot_name}</li>
    <li><strong>Strategy:</strong> {strategy}</li>
    <li><strong>Symbol:</strong> {symbol}</li>
    <li><strong>Time:</strong> {timestamp}</li>
</ul>
<p>Best regards,<br>Trading Bot Platform</p>
</body></html>''',
                'telegram_template': '''🚀 <b>Bot Started</b>\n\n🤖 <b>Bot:</b> {bot_name}\n📋 <b>Strategy:</b> {strategy}\n📊 <b>Symbol:</b> {symbol}\n⏰ <b>Time:</b> {timestamp}''',
                'push_title': 'Bot Started',
                'push_body': '{bot_name} started trading {symbol}',
                'variables': json.dumps(['username', 'bot_name', 'strategy', 'symbol', 'timestamp'])
            },
            {
                'event_type': 'bot_stopped',
                'email_subject': 'Bot Stopped - {bot_name}',
                'email_body': '''<html><body>
<h2>⏹️ Bot Stopped</h2>
<p>Hello {username},</p>
<p>Your trading bot has been stopped:</p>
<ul>
    <li><strong>Bot Name:</strong> {bot_name}</li>
    <li><strong>Reason:</strong> {reason}</li>
    <li><strong>Time:</strong> {timestamp}</li>
</ul>
<p>Best regards,<br>Trading Bot Platform</p>
</body></html>''',
                'telegram_template': '''⏹️ <b>Bot Stopped</b>\n\n🤖 <b>Bot:</b> {bot_name}\n📝 <b>Reason:</b> {reason}\n⏰ <b>Time:</b> {timestamp}''',
                'push_title': 'Bot Stopped',
                'push_body': '{bot_name} stopped: {reason}',
                'variables': json.dumps(['username', 'bot_name', 'reason', 'timestamp'])
            },
            {
                'event_type': 'system_error',
                'email_subject': 'System Error Alert',
                'email_body': '''<html><body>
<h2>🚨 System Error Alert</h2>
<p>Hello {username},</p>
<p>A system error has occurred that may affect your trading:</p>
<ul>
    <li><strong>Error Type:</strong> {error_type}</li>
    <li><strong>Message:</strong> {error_message}</li>
    <li><strong>Time:</strong> {timestamp}</li>
</ul>
<p>Our team has been notified and is working to resolve this issue.</p>
<p>Best regards,<br>Trading Bot Platform</p>
</body></html>''',
                'telegram_template': '''🚨 <b>System Error Alert</b>\n\n⚠️ <b>Type:</b> {error_type}\n📝 <b>Message:</b> {error_message}\n⏰ <b>Time:</b> {timestamp}''',
                'push_title': 'System Error',
                'push_body': '{error_type}: {error_message}',
                'variables': json.dumps(['username', 'error_type', 'error_message', 'timestamp'])
            }
        ]
        
        return [NotificationTemplate(**template) for template in templates]