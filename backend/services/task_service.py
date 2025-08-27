"""Service for managing and executing Celery tasks."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from celery.result import AsyncResult

from celery_app import celery_app
from utils.logging_config import get_api_logger

logger = get_api_logger('task_service')

class TaskService:
    """Service for managing Celery tasks and async operations."""
    
    def __init__(self):
        self.celery = celery_app
    
    # Trading Tasks
    def execute_trade_async(self, trade_data: Dict[str, Any], priority: int = 5) -> str:
        """Execute a trade asynchronously.
        
        Args:
            trade_data: Trade execution data
            priority: Task priority (1-10, higher is more important)
            
        Returns:
            Task ID
        """
        try:
            from tasks.trading import execute_trade_async
            
            result = execute_trade_async.apply_async(
                args=[trade_data],
                priority=priority,
                queue='trading'
            )
            
            logger.info(f"Trade execution task queued: {result.id}")
            return result.id
            
        except Exception as e:
            logger.error(f"Failed to queue trade execution: {e}")
            raise
    
    def update_market_data_async(self, symbols: List[str] = None) -> str:
        """Update market data asynchronously.
        
        Args:
            symbols: List of symbols to update (None for all)
            
        Returns:
            Task ID
        """
        try:
            from tasks.trading import update_market_data
            
            result = update_market_data.apply_async(
                args=[symbols],
                queue='trading'
            )
            
            logger.info(f"Market data update task queued: {result.id}")
            return result.id
            
        except Exception as e:
            logger.error(f"Failed to queue market data update: {e}")
            raise
    
    def sync_portfolios_async(self, user_ids: List[int] = None) -> str:
        """Sync user portfolios asynchronously.
        
        Args:
            user_ids: List of user IDs to sync (None for all)
            
        Returns:
            Task ID
        """
        try:
            from tasks.trading import sync_portfolios
            
            result = sync_portfolios.apply_async(
                args=[user_ids],
                queue='trading'
            )
            
            logger.info(f"Portfolio sync task queued: {result.id}")
            return result.id
            
        except Exception as e:
            logger.error(f"Failed to queue portfolio sync: {e}")
            raise
    
    # Notification Tasks
    def send_trade_notification_async(self, notification_data: Dict[str, Any]) -> str:
        """Send trade notification asynchronously.
        
        Args:
            notification_data: Notification data
            
        Returns:
            Task ID
        """
        try:
            from tasks.notifications import send_trade_notification
            
            result = send_trade_notification.apply_async(
                args=[notification_data],
                queue='notifications',
                priority=7  # High priority for trade notifications
            )
            
            logger.info(f"Trade notification task queued: {result.id}")
            return result.id
            
        except Exception as e:
            logger.error(f"Failed to queue trade notification: {e}")
            raise
    
    def send_alert_notification_async(self, alert_data: Dict[str, Any]) -> str:
        """Send alert notification asynchronously.
        
        Args:
            alert_data: Alert data
            
        Returns:
            Task ID
        """
        try:
            from tasks.notifications import send_alert_notification
            
            result = send_alert_notification.apply_async(
                args=[alert_data],
                queue='notifications',
                priority=8  # High priority for alerts
            )
            
            logger.info(f"Alert notification task queued: {result.id}")
            return result.id
            
        except Exception as e:
            logger.error(f"Failed to queue alert notification: {e}")
            raise
    
    def send_bulk_notifications_async(self, notification_list: List[Dict[str, Any]]) -> str:
        """Send multiple notifications asynchronously.
        
        Args:
            notification_list: List of notifications
            
        Returns:
            Task ID
        """
        try:
            from tasks.notifications import send_bulk_notifications
            
            result = send_bulk_notifications.apply_async(
                args=[notification_list],
                queue='notifications'
            )
            
            logger.info(f"Bulk notifications task queued: {result.id}")
            return result.id
            
        except Exception as e:
            logger.error(f"Failed to queue bulk notifications: {e}")
            raise
    
    # Analytics Tasks
    def calculate_portfolio_performance_async(self, user_id: int, period_days: int = 30) -> str:
        """Calculate portfolio performance asynchronously.
        
        Args:
            user_id: User ID
            period_days: Analysis period in days
            
        Returns:
            Task ID
        """
        try:
            from tasks.analytics import calculate_portfolio_performance
            
            result = calculate_portfolio_performance.apply_async(
                args=[user_id, period_days],
                queue='analytics'
            )
            
            logger.info(f"Portfolio performance calculation task queued: {result.id}")
            return result.id
            
        except Exception as e:
            logger.error(f"Failed to queue portfolio performance calculation: {e}")
            raise
    
    def generate_trading_report_async(self, user_id: int, report_type: str = 'monthly') -> str:
        """Generate trading report asynchronously.
        
        Args:
            user_id: User ID
            report_type: Report type ('daily', 'weekly', 'monthly', 'yearly')
            
        Returns:
            Task ID
        """
        try:
            from tasks.analytics import generate_trading_report
            
            result = generate_trading_report.apply_async(
                args=[user_id, report_type],
                queue='analytics'
            )
            
            logger.info(f"Trading report generation task queued: {result.id}")
            return result.id
            
        except Exception as e:
            logger.error(f"Failed to queue trading report generation: {e}")
            raise
    
    def calculate_risk_metrics_async(self, user_id: int, lookback_days: int = 90) -> str:
        """Calculate risk metrics asynchronously.
        
        Args:
            user_id: User ID
            lookback_days: Lookback period in days
            
        Returns:
            Task ID
        """
        try:
            from tasks.analytics import calculate_risk_metrics
            
            result = calculate_risk_metrics.apply_async(
                args=[user_id, lookback_days],
                queue='analytics'
            )
            
            logger.info(f"Risk metrics calculation task queued: {result.id}")
            return result.id
            
        except Exception as e:
            logger.error(f"Failed to queue risk metrics calculation: {e}")
            raise
    
    # Maintenance Tasks
    def system_health_check_async(self) -> str:
        """Perform system health check asynchronously.
        
        Returns:
            Task ID
        """
        try:
            from tasks.maintenance import system_health_check
            
            result = system_health_check.apply_async(
                queue='maintenance',
                priority=8
            )
            
            logger.info(f"System health check task queued: {result.id}")
            return result.id
            
        except Exception as e:
            logger.error(f"Failed to queue system health check: {e}")
            raise
    
    def cleanup_old_trades_async(self, days_to_keep: int = 365) -> str:
        """Clean up old trades asynchronously.
        
        Args:
            days_to_keep: Number of days to keep
            
        Returns:
            Task ID
        """
        try:
            from tasks.maintenance import cleanup_old_trades
            
            result = cleanup_old_trades.apply_async(
                args=[days_to_keep],
                queue='maintenance'
            )
            
            logger.info(f"Trade cleanup task queued: {result.id}")
            return result.id
            
        except Exception as e:
            logger.error(f"Failed to queue trade cleanup: {e}")
            raise
    
    # Task Management
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get the status of a Celery task.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task status information
        """
        try:
            result = AsyncResult(task_id, app=self.celery)
            
            return {
                'task_id': task_id,
                'status': result.status,
                'result': result.result if result.ready() else None,
                'successful': result.successful(),
                'failed': result.failed(),
                'ready': result.ready(),
                'date_done': result.date_done.isoformat() if result.date_done else None,
                'traceback': result.traceback if result.failed() else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get task status for {task_id}: {e}")
            return {
                'task_id': task_id,
                'status': 'ERROR',
                'error': str(e)
            }
    
    def revoke_task(self, task_id: str, terminate: bool = False) -> Dict[str, Any]:
        """Revoke a Celery task.
        
        Args:
            task_id: Task ID
            terminate: Whether to terminate the task if it's running
            
        Returns:
            Revocation result
        """
        try:
            self.celery.control.revoke(task_id, terminate=terminate)
            
            logger.info(f"Task {task_id} revoked (terminate={terminate})")
            
            return {
                'success': True,
                'message': f'Task {task_id} revoked',
                'terminated': terminate
            }
            
        except Exception as e:
            logger.error(f"Failed to revoke task {task_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_active_tasks(self) -> Dict[str, Any]:
        """Get list of active tasks.
        
        Returns:
            Active tasks information
        """
        try:
            inspect = self.celery.control.inspect()
            active_tasks = inspect.active()
            
            return {
                'success': True,
                'active_tasks': active_tasks,
                'worker_count': len(active_tasks) if active_tasks else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get active tasks: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_worker_stats(self) -> Dict[str, Any]:
        """Get Celery worker statistics.
        
        Returns:
            Worker statistics
        """
        try:
            inspect = self.celery.control.inspect()
            stats = inspect.stats()
            
            return {
                'success': True,
                'worker_stats': stats,
                'worker_count': len(stats) if stats else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get worker stats: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_queue_lengths(self) -> Dict[str, Any]:
        """Get queue lengths for monitoring.
        
        Returns:
            Queue length information
        """
        try:
            inspect = self.celery.control.inspect()
            
            # Get reserved tasks (queued but not yet started)
            reserved = inspect.reserved()
            
            # Get active tasks (currently running)
            active = inspect.active()
            
            queue_info = {}
            
            if reserved:
                for worker, tasks in reserved.items():
                    for task in tasks:
                        queue = task.get('delivery_info', {}).get('routing_key', 'default')
                        if queue not in queue_info:
                            queue_info[queue] = {'reserved': 0, 'active': 0}
                        queue_info[queue]['reserved'] += 1
            
            if active:
                for worker, tasks in active.items():
                    for task in tasks:
                        queue = task.get('delivery_info', {}).get('routing_key', 'default')
                        if queue not in queue_info:
                            queue_info[queue] = {'reserved': 0, 'active': 0}
                        queue_info[queue]['active'] += 1
            
            return {
                'success': True,
                'queue_info': queue_info,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get queue lengths: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def schedule_maintenance_tasks(self) -> Dict[str, Any]:
        """Schedule all maintenance tasks.
        
        Returns:
            Scheduling result
        """
        try:
            from tasks.maintenance import schedule_maintenance_tasks
            
            result = schedule_maintenance_tasks.apply_async(
                queue='maintenance'
            )
            
            logger.info(f"Maintenance tasks scheduling queued: {result.id}")
            
            return {
                'success': True,
                'task_id': result.id,
                'message': 'Maintenance tasks scheduled'
            }
            
        except Exception as e:
            logger.error(f"Failed to schedule maintenance tasks: {e}")
            return {
                'success': False,
                'error': str(e)
            }

# Global task service instance
task_service = TaskService()