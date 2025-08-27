"""Celery worker startup script."""

import os
import sys
from celery import Celery
from celery.signals import worker_ready, worker_shutdown

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the configured Celery app
from celery_app import celery_app
from utils.logging_config import setup_logging, get_api_logger

# Setup logging for worker
setup_logging(enable_monitoring=True)
logger = get_api_logger('worker')

@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    """Handle worker ready signal."""
    logger.info(f"Celery worker {sender.hostname} is ready and waiting for tasks")
    
    # Send notification that worker is ready
    try:
        from tasks.notifications import send_alert_notification
        
        alert_data = {
            'title': 'Celery Worker Started',
            'message': f'Celery worker {sender.hostname} has started successfully and is ready to process tasks',
            'severity': 'low',
            'admin_only': True
        }
        
        # Use apply_async to avoid circular import issues
        send_alert_notification.apply_async(args=[alert_data], countdown=5)
        
    except Exception as e:
        logger.error(f"Failed to send worker ready notification: {e}")

@worker_shutdown.connect
def worker_shutdown_handler(sender=None, **kwargs):
    """Handle worker shutdown signal."""
    logger.info(f"Celery worker {sender.hostname} is shutting down")
    
    try:
        from tasks.notifications import send_alert_notification
        
        alert_data = {
            'title': 'Celery Worker Shutdown',
            'message': f'Celery worker {sender.hostname} is shutting down',
            'severity': 'medium',
            'admin_only': True
        }
        
        send_alert_notification.apply_async(args=[alert_data])
        
    except Exception as e:
        logger.error(f"Failed to send worker shutdown notification: {e}")

if __name__ == '__main__':
    # Start the worker
    logger.info("Starting Celery worker...")
    
    # Configure worker arguments
    worker_args = [
        'worker',
        '--loglevel=info',
        '--concurrency=4',
        '--queues=default,trading,notifications,analytics,maintenance',
        '--hostname=worker@%h',
        '--max-tasks-per-child=1000',
        '--max-memory-per-child=200000',  # 200MB
        '--time-limit=1800',  # 30 minutes
        '--soft-time-limit=1500',  # 25 minutes
    ]
    
    # Add optimization flags
    if os.getenv('CELERY_OPTIMIZATION', 'True').lower() == 'true':
        worker_args.extend([
            '--optimization=fair',
            '--prefetch-multiplier=1',
        ])
    
    # Start worker with arguments
    celery_app.worker_main(worker_args)