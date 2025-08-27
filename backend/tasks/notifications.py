"""Notification-related Celery tasks for async processing."""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from celery import Task

from celery_app import celery_app
from models.user import User
from models.trade import Trade
from services.notification_service import NotificationService
from utils.logging_config import get_api_logger
from database import db

logger = get_api_logger('notifications_tasks')

class NotificationTask(Task):
    """Base class for notification tasks with error handling."""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        logger.error(f"Notification task {task_id} failed: {exc}")

@celery_app.task(bind=True, base=NotificationTask, max_retries=3)
def send_trade_notification(self, notification_data: Dict[str, Any]):
    """Send trade execution notification to user.
    
    Args:
        notification_data: Dictionary containing notification details
            - trade_id: Trade ID
            - user_id: User ID
            - success: Whether trade was successful
            - symbol: Trading pair
            - side: 'buy' or 'sell'
            - quantity: Trade quantity
            - price: Execution price
    """
    try:
        logger.info(f"Sending trade notification: {notification_data}")
        
        user = User.query.get(notification_data['user_id'])
        if not user:
            logger.error(f"User not found: {notification_data['user_id']}")
            return {'success': False, 'error': 'User not found'}
        
        trade = Trade.query.get(notification_data['trade_id']) if notification_data.get('trade_id') else None
        
        notification_service = NotificationService()
        
        # Prepare notification content
        if notification_data['success']:
            title = f"Trade Executed Successfully"
            message = (
                f"Your {notification_data['side'].upper()} order for "
                f"{notification_data['quantity']} {notification_data['symbol']} "
                f"has been executed at ${notification_data.get('price', 'Market Price')}"
            )
            notification_type = 'trade_success'
        else:
            title = f"Trade Execution Failed"
            message = (
                f"Your {notification_data['side'].upper()} order for "
                f"{notification_data['quantity']} {notification_data['symbol']} "
                f"failed to execute. Please check your account."
            )
            notification_type = 'trade_failure'
        
        # Send notifications based on user preferences
        results = {}
        
        # Email notification
        if user.email_notifications:
            try:
                email_result = notification_service.send_email_notification(
                    user_id=user.id,
                    subject=title,
                    message=message,
                    notification_type=notification_type,
                    trade_data=notification_data
                )
                results['email'] = email_result
            except Exception as e:
                logger.error(f"Failed to send email notification: {e}")
                results['email'] = {'success': False, 'error': str(e)}
        
        # Push notification
        if user.push_notifications:
            try:
                push_result = notification_service.send_push_notification(
                    user_id=user.id,
                    title=title,
                    message=message,
                    data=notification_data
                )
                results['push'] = push_result
            except Exception as e:
                logger.error(f"Failed to send push notification: {e}")
                results['push'] = {'success': False, 'error': str(e)}
        
        # Telegram notification
        if user.telegram_notifications and user.telegram_chat_id:
            try:
                telegram_result = send_telegram_notification.delay({
                    'chat_id': user.telegram_chat_id,
                    'message': f"{title}\n\n{message}",
                    'parse_mode': 'HTML'
                })
                results['telegram'] = {'success': True, 'task_id': telegram_result.id}
            except Exception as e:
                logger.error(f"Failed to queue Telegram notification: {e}")
                results['telegram'] = {'success': False, 'error': str(e)}
        
        logger.info(f"Trade notification sent successfully: {results}")
        
        return {
            'success': True,
            'results': results,
            'notification_type': notification_type
        }
        
    except Exception as exc:
        logger.error(f"Trade notification failed: {exc}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=30 * (2 ** self.request.retries))
        
        return {'success': False, 'error': str(exc)}

@celery_app.task(bind=True, base=NotificationTask, max_retries=3)
def send_alert_notification(self, alert_data: Dict[str, Any]):
    """Send system alert notification.
    
    Args:
        alert_data: Dictionary containing alert details
            - title: Alert title
            - message: Alert message
            - severity: 'low', 'medium', 'high', 'critical'
            - user_ids: List of user IDs to notify (optional)
            - admin_only: Whether to send only to admins
    """
    try:
        logger.info(f"Sending alert notification: {alert_data}")
        
        notification_service = NotificationService()
        
        # Determine recipients
        if alert_data.get('admin_only', False):
            users = User.query.filter_by(is_admin=True).all()
        elif alert_data.get('user_ids'):
            users = User.query.filter(User.id.in_(alert_data['user_ids'])).all()
        else:
            # Send to all users with alert notifications enabled
            users = User.query.filter_by(alert_notifications=True).all()
        
        if not users:
            logger.warning("No users to send alert notification to")
            return {'success': True, 'recipients': 0}
        
        results = []
        
        for user in users:
            try:
                user_result = {
                    'user_id': user.id,
                    'email': None,
                    'push': None,
                    'telegram': None
                }
                
                # Email notification
                if user.email_notifications:
                    email_result = notification_service.send_email_notification(
                        user_id=user.id,
                        subject=f"[{alert_data['severity'].upper()}] {alert_data['title']}",
                        message=alert_data['message'],
                        notification_type='system_alert',
                        alert_data=alert_data
                    )
                    user_result['email'] = email_result
                
                # Push notification
                if user.push_notifications:
                    push_result = notification_service.send_push_notification(
                        user_id=user.id,
                        title=f"[{alert_data['severity'].upper()}] {alert_data['title']}",
                        message=alert_data['message'],
                        data=alert_data
                    )
                    user_result['push'] = push_result
                
                # Telegram notification for critical alerts
                if (user.telegram_notifications and user.telegram_chat_id and 
                    alert_data['severity'] in ['high', 'critical']):
                    telegram_result = send_telegram_notification.delay({
                        'chat_id': user.telegram_chat_id,
                        'message': f"🚨 <b>{alert_data['title']}</b>\n\n{alert_data['message']}",
                        'parse_mode': 'HTML'
                    })
                    user_result['telegram'] = {'success': True, 'task_id': telegram_result.id}
                
                results.append(user_result)
                
            except Exception as e:
                logger.error(f"Failed to send alert to user {user.id}: {e}")
                results.append({
                    'user_id': user.id,
                    'error': str(e)
                })
        
        logger.info(f"Alert notification sent to {len(results)} users")
        
        return {
            'success': True,
            'recipients': len(results),
            'results': results
        }
        
    except Exception as exc:
        logger.error(f"Alert notification failed: {exc}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60)
        
        return {'success': False, 'error': str(exc)}

@celery_app.task(bind=True, base=NotificationTask, max_retries=3)
def send_email_notification(self, email_data: Dict[str, Any]):
    """Send email notification.
    
    Args:
        email_data: Dictionary containing email details
            - to: Recipient email address
            - subject: Email subject
            - message: Email message
            - html_content: HTML content (optional)
            - template: Email template name (optional)
            - template_data: Data for template rendering (optional)
    """
    try:
        logger.info(f"Sending email notification to: {email_data.get('to')}")
        
        notification_service = NotificationService()
        
        result = notification_service.send_email(
            to=email_data['to'],
            subject=email_data['subject'],
            message=email_data['message'],
            html_content=email_data.get('html_content'),
            template=email_data.get('template'),
            template_data=email_data.get('template_data', {})
        )
        
        if result['success']:
            logger.info(f"Email sent successfully to: {email_data['to']}")
        else:
            logger.error(f"Email sending failed: {result.get('error')}")
        
        return result
        
    except Exception as exc:
        logger.error(f"Email notification failed: {exc}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=30 * (2 ** self.request.retries))
        
        return {'success': False, 'error': str(exc)}

@celery_app.task(bind=True, base=NotificationTask, max_retries=3)
def send_telegram_notification(self, telegram_data: Dict[str, Any]):
    """Send Telegram notification.
    
    Args:
        telegram_data: Dictionary containing Telegram details
            - chat_id: Telegram chat ID
            - message: Message text
            - parse_mode: 'HTML' or 'Markdown' (optional)
            - disable_notification: Boolean (optional)
    """
    try:
        logger.info(f"Sending Telegram notification to: {telegram_data.get('chat_id')}")
        
        notification_service = NotificationService()
        
        result = notification_service.send_telegram_message(
            chat_id=telegram_data['chat_id'],
            message=telegram_data['message'],
            parse_mode=telegram_data.get('parse_mode', 'HTML'),
            disable_notification=telegram_data.get('disable_notification', False)
        )
        
        if result['success']:
            logger.info(f"Telegram message sent successfully to: {telegram_data['chat_id']}")
        else:
            logger.error(f"Telegram sending failed: {result.get('error')}")
        
        return result
        
    except Exception as exc:
        logger.error(f"Telegram notification failed: {exc}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=30 * (2 ** self.request.retries))
        
        return {'success': False, 'error': str(exc)}

@celery_app.task
def send_bulk_notifications(notification_list: List[Dict[str, Any]]):
    """Send multiple notifications in bulk.
    
    Args:
        notification_list: List of notification dictionaries
    """
    try:
        logger.info(f"Sending {len(notification_list)} bulk notifications")
        
        results = []
        
        for notification in notification_list:
            try:
                notification_type = notification.get('type', 'email')
                
                if notification_type == 'email':
                    result = send_email_notification.delay(notification)
                elif notification_type == 'telegram':
                    result = send_telegram_notification.delay(notification)
                elif notification_type == 'trade':
                    result = send_trade_notification.delay(notification)
                elif notification_type == 'alert':
                    result = send_alert_notification.delay(notification)
                else:
                    logger.warning(f"Unknown notification type: {notification_type}")
                    continue
                
                results.append({
                    'type': notification_type,
                    'task_id': result.id,
                    'success': True
                })
                
            except Exception as e:
                logger.error(f"Failed to queue notification: {e}")
                results.append({
                    'type': notification.get('type', 'unknown'),
                    'success': False,
                    'error': str(e)
                })
        
        logger.info(f"Bulk notifications queued: {len(results)} tasks")
        
        return {
            'success': True,
            'total_notifications': len(notification_list),
            'queued_tasks': len([r for r in results if r['success']]),
            'failed_tasks': len([r for r in results if not r['success']]),
            'results': results
        }
        
    except Exception as exc:
        logger.error(f"Bulk notifications failed: {exc}")
        return {'success': False, 'error': str(exc)}