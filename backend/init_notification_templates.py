#!/usr/bin/env python3
"""
Initialize notification templates in the database.
This script creates default notification templates for various trading events.
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import only what we need
from config import Config
from database import db
from models.notification import NotificationTemplate

def create_notification_templates(session):
    """Create default notification templates."""
    
    templates = [
        # Trade Executed Templates
        {
            'event_type': 'trade_executed',
            'notification_type': 'email',
            'subject_template': 'Trade Executed - {symbol}',
            'body_template': '''Dear {user.username},

Your trade has been successfully executed:

• Symbol: {symbol}
• Side: {side}
• Quantity: {quantity}
• Price: ${price}
• Total Value: ${total_value}
• Timestamp: {timestamp}
• P&L: ${pnl}

Your current portfolio balance has been updated accordingly.

Best regards,
Trading Bot System'''
        },
        {
            'event_type': 'trade_executed',
            'notification_type': 'telegram',
            'subject_template': '',
            'body_template': '''🎯 <b>Trade Executed</b>

📊 <b>Symbol:</b> {symbol}
📈 <b>Side:</b> {side}
💰 <b>Quantity:</b> {quantity}
💵 <b>Price:</b> ${price}
💎 <b>Total Value:</b> ${total_value}
📊 <b>P&L:</b> ${pnl}
⏰ <b>Time:</b> {timestamp}

<em>Your portfolio has been updated</em>'''
        },
        {
            'event_type': 'trade_executed',
            'notification_type': 'push',
            'subject_template': 'Trade Executed',
            'body_template': '{side} {quantity} {symbol} at ${price} - P&L: ${pnl}'
        },
        
        # Trade Failed Templates
        {
            'event_type': 'trade_failed',
            'notification_type': 'email',
            'subject_template': 'Trade Failed - {symbol}',
            'body_template': '''Dear {user.username},

Your trade failed to execute:

• Symbol: {symbol}
• Side: {side}
• Quantity: {quantity}
• Attempted Price: ${price}
• Error: {error}
• Timestamp: {timestamp}

Please check your bot configuration and account balance.

Best regards,
Trading Bot System'''
        },
        {
            'event_type': 'trade_failed',
            'notification_type': 'telegram',
            'subject_template': '',
            'body_template': '''❌ <b>Trade Failed</b>

📊 <b>Symbol:</b> {symbol}
📈 <b>Side:</b> {side}
💰 <b>Quantity:</b> {quantity}
💵 <b>Price:</b> ${price}
❗ <b>Error:</b> {error}
⏰ <b>Time:</b> {timestamp}

<em>Please check your bot configuration</em>'''
        },
        {
            'event_type': 'trade_failed',
            'notification_type': 'push',
            'subject_template': 'Trade Failed',
            'body_template': 'Failed to execute {symbol} trade: {error}'
        },
        
        # Bot Started Templates
        {
            'event_type': 'bot_started',
            'notification_type': 'email',
            'subject_template': 'Trading Bot Started - {bot_name}',
            'body_template': '''Dear {user.username},

Your trading bot has been started:

• Bot Name: {bot_name}
• Strategy: {strategy}
• Exchange: {exchange}
• Trading Pairs: {trading_pairs}
• Timestamp: {timestamp}

The bot is now actively monitoring the market.

Best regards,
Trading Bot System'''
        },
        {
            'event_type': 'bot_started',
            'notification_type': 'telegram',
            'subject_template': '',
            'body_template': '''🚀 <b>Bot Started</b>

🤖 <b>Bot:</b> {bot_name}
📊 <b>Strategy:</b> {strategy}
🏦 <b>Exchange:</b> {exchange}
💱 <b>Pairs:</b> {trading_pairs}
⏰ <b>Time:</b> {timestamp}

<em>Bot is now active and monitoring</em>'''
        },
        {
            'event_type': 'bot_started',
            'notification_type': 'push',
            'subject_template': 'Bot Started',
            'body_template': '{bot_name} is now running with {strategy} strategy'
        },
        
        # Bot Stopped Templates
        {
            'event_type': 'bot_stopped',
            'notification_type': 'email',
            'subject_template': 'Trading Bot Stopped - {bot_name}',
            'body_template': '''Dear {user.username},

Your trading bot has been stopped:

• Bot Name: {bot_name}
• Reason: {reason}
• Runtime: {runtime}
• Total Trades: {total_trades}
• Final P&L: ${final_pnl}
• Timestamp: {timestamp}

The bot has ceased all trading activities.

Best regards,
Trading Bot System'''
        },
        {
            'event_type': 'bot_stopped',
            'notification_type': 'telegram',
            'subject_template': '',
            'body_template': '''🔴 <b>Bot Stopped</b>

🤖 <b>Bot:</b> {bot_name}
❓ <b>Reason:</b> {reason}
⏱️ <b>Runtime:</b> {runtime}
📊 <b>Trades:</b> {total_trades}
💰 <b>Final P&L:</b> ${final_pnl}
⏰ <b>Time:</b> {timestamp}

<em>Bot has ceased trading activities</em>'''
        },
        {
            'event_type': 'bot_stopped',
            'notification_type': 'push',
            'subject_template': 'Bot Stopped',
            'body_template': '{bot_name} stopped - Final P&L: ${final_pnl}'
        },
        
        # Bot Error Templates
        {
            'event_type': 'bot_error',
            'notification_type': 'email',
            'subject_template': 'Trading Bot Error - {bot_name}',
            'body_template': '''Dear {user.username},

Your trading bot encountered an error:

• Bot Name: {bot_name}
• Error Type: {error_type}
• Error Message: {error_message}
• Timestamp: {timestamp}
• Bot Status: {bot_status}

Please check your bot configuration.

Best regards,
Trading Bot System'''
        },
        {
            'event_type': 'bot_error',
            'notification_type': 'telegram',
            'subject_template': '',
            'body_template': '''❌ <b>Bot Error</b>

🤖 <b>Bot:</b> {bot_name}
⚠️ <b>Error:</b> {error_type}
📝 <b>Message:</b> {error_message}
📊 <b>Status:</b> {bot_status}
⏰ <b>Time:</b> {timestamp}

<em>Please check your bot configuration</em>'''
        },
        {
            'event_type': 'bot_error',
            'notification_type': 'push',
            'subject_template': 'Bot Error',
            'body_template': '{bot_name} error: {error_type}'
        },
        
        # Profit Alert Templates
        {
            'event_type': 'profit_alert',
            'notification_type': 'email',
            'subject_template': '🎉 Profit Target Reached - ${pnl}',
            'body_template': '''Dear {user.username},

Congratulations! Your trading bot has reached a profit milestone:

• Current P&L: ${pnl}
• Profit Threshold: ${threshold}
• Achievement Time: {timestamp}

Your successful trading strategy is paying off!

Best regards,
Trading Bot System'''
        },
        {
            'event_type': 'profit_alert',
            'notification_type': 'telegram',
            'subject_template': '',
            'body_template': '''🎉 <b>Profit Target Reached!</b>

💰 <b>Current P&L:</b> ${pnl}
🎯 <b>Threshold:</b> ${threshold}
⏰ <b>Time:</b> {timestamp}

<em>Congratulations on your successful trading!</em>'''
        },
        {
            'event_type': 'profit_alert',
            'notification_type': 'push',
            'subject_template': 'Profit Target Reached!',
            'body_template': 'Profit of ${pnl} achieved - Target: ${threshold}'
        },
        
        # Loss Alert Templates
        {
            'event_type': 'loss_alert',
            'notification_type': 'email',
            'subject_template': '⚠️ Loss Threshold Exceeded - ${pnl}',
            'body_template': '''Dear {user.username},

Your trading bot has exceeded the loss threshold:

• Current P&L: ${pnl}
• Loss Threshold: ${threshold}
• Alert Time: {timestamp}

Please review your trading strategy.

Best regards,
Trading Bot System'''
        },
        {
            'event_type': 'loss_alert',
            'notification_type': 'telegram',
            'subject_template': '',
            'body_template': '''⚠️ <b>Loss Threshold Exceeded</b>

💸 <b>Current P&L:</b> ${pnl}
🎯 <b>Threshold:</b> ${threshold}
⏰ <b>Time:</b> {timestamp}

<em>Please review your trading strategy</em>'''
        },
        {
            'event_type': 'loss_alert',
            'notification_type': 'push',
            'subject_template': 'Loss Alert',
            'body_template': 'Loss of ${pnl} exceeded threshold ${threshold}'
        },
        
        # Daily Summary Templates
        {
            'event_type': 'daily_summary',
            'notification_type': 'email',
            'subject_template': '📊 Daily Trading Summary - {date}',
            'body_template': '''Dear {user.username},

Here's your daily trading summary for {date}:

• Total P&L: ${total_pnl}
• Total Trades: {total_trades}
• Winning Trades: {winning_trades}
• Win Rate: {win_rate}%
• Starting Balance: ${starting_balance}
• Ending Balance: ${ending_balance}

Keep up the great work!

Best regards,
Trading Bot System'''
        },
        {
            'event_type': 'daily_summary',
            'notification_type': 'telegram',
            'subject_template': '',
            'body_template': '''📊 <b>Daily Summary - {date}</b>

💰 <b>Total P&L:</b> ${total_pnl}
📈 <b>Trades:</b> {total_trades} ({win_rate}% win rate)
✅ <b>Winners:</b> {winning_trades}
💼 <b>Balance:</b> ${starting_balance} → ${ending_balance}

<em>Keep trading smart!</em>'''
        },
        {
            'event_type': 'daily_summary',
            'notification_type': 'push',
            'subject_template': 'Daily Summary',
            'body_template': 'P&L: ${total_pnl} | Trades: {total_trades} | Win Rate: {win_rate}%'
        },
        
        # Test Notification Template
        {
            'event_type': 'test_notification',
            'notification_type': 'email',
            'subject_template': 'Test Notification - Trading Bot System',
            'body_template': '''Dear {user.username},

This is a test notification to verify your email settings.

• Test Time: {timestamp}
• Status: Working correctly!

Best regards,
Trading Bot System'''
        },
        {
            'event_type': 'test_notification',
            'notification_type': 'telegram',
            'subject_template': '',
            'body_template': '''🧪 <b>Test Notification</b>

✅ <b>Status:</b> Working correctly!
⏰ <b>Time:</b> {timestamp}

<em>Your Telegram notifications are working!</em>'''
        },
        {
            'event_type': 'test_notification',
            'notification_type': 'push',
            'subject_template': 'Test Notification',
            'body_template': 'Push notifications are working correctly!'
        }
    ]
    
    # Group templates by event_type
    templates_by_event = {}
    for template_data in templates:
        event_type = template_data['event_type']
        if event_type not in templates_by_event:
            templates_by_event[event_type] = {}
        templates_by_event[event_type][template_data['notification_type']] = template_data
    
    # Create templates
    created_count = 0
    updated_count = 0
    
    for event_type, notification_templates in templates_by_event.items():
        # Check if template already exists
        existing_template = session.query(NotificationTemplate).filter_by(
            event_type=event_type
        ).first()
        
        if existing_template:
            # Update existing template
            if 'email' in notification_templates:
                existing_template.email_subject = notification_templates['email']['subject_template']
                existing_template.email_body = notification_templates['email']['body_template']
            if 'telegram' in notification_templates:
                existing_template.telegram_template = notification_templates['telegram']['body_template']
            if 'push' in notification_templates:
                existing_template.push_title = notification_templates['push']['subject_template']
                existing_template.push_body = notification_templates['push']['body_template']
            existing_template.updated_at = datetime.utcnow()
            updated_count += 1
        else:
            # Create new template
            template = NotificationTemplate(event_type=event_type)
            if 'email' in notification_templates:
                template.email_subject = notification_templates['email']['subject_template']
                template.email_body = notification_templates['email']['body_template']
            if 'telegram' in notification_templates:
                template.telegram_template = notification_templates['telegram']['body_template']
            if 'push' in notification_templates:
                template.push_title = notification_templates['push']['subject_template']
                template.push_body = notification_templates['push']['body_template']
            session.add(template)
            created_count += 1
    
    # Commit changes
    try:
        session.commit()
        print(f"✅ Successfully created {created_count} new templates")
        print(f"✅ Successfully updated {updated_count} existing templates")
        print(f"📊 Total templates in database: {session.query(NotificationTemplate).count()}")
        return True
    except Exception as e:
        session.rollback()
        print(f"❌ Error creating templates: {str(e)}")
        return False

def main():
    """Main function to initialize notification templates."""
    print("🚀 Initializing notification templates...")
    
    try:
        # Create database engine
        config = Config()
        engine = create_engine(config.SQLALCHEMY_DATABASE_URI)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Create database tables if they don't exist
        db.metadata.create_all(engine)
        print("✅ Database tables created/verified")
        
        # Create notification templates
        success = create_notification_templates(session)
        
        if success:
            print("\n🎉 Notification templates initialization completed successfully!")
            print("\n📋 Available event types:")
            event_types = session.query(NotificationTemplate.event_type).distinct().all()
            for event_type in event_types:
                print(f"  • {event_type[0]}")
            
            print("\n📱 Available notification types:")
            notification_types = session.query(NotificationTemplate.notification_type).distinct().all()
            for notification_type in notification_types:
                print(f"  • {notification_type[0]}")
        else:
            print("\n❌ Failed to initialize notification templates")
            return False
            
        session.close()
        
    except Exception as e:
        print(f"❌ Error initializing templates: {str(e)}")
        return False
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)