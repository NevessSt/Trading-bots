"""Celery application configuration for async task processing."""

import os
from celery import Celery
from config.config import Config

# Create Celery instance
celery_app = Celery('trading_bot')

# Configure Celery
celery_app.conf.update(
    broker_url=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    result_backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=False,
    task_compression='gzip',
    result_compression='gzip',
    task_routes={
        'tasks.trading.*': {'queue': 'trading'},
        'tasks.notifications.*': {'queue': 'notifications'},
        'tasks.analytics.*': {'queue': 'analytics'},
        'tasks.maintenance.*': {'queue': 'maintenance'},
    },
    task_default_queue='default',
    task_create_missing_queues=True,
    worker_send_task_events=True,
    task_send_sent_event=True,
    result_expires=3600,  # 1 hour
    task_reject_on_worker_lost=True,
    task_ignore_result=False,
    worker_max_tasks_per_child=1000,
    worker_max_memory_per_child=200000,  # 200MB
    beat_schedule={
        'cleanup-stale-orders': {
            'task': 'tasks.maintenance.cleanup_stale_orders',
            'schedule': 300.0,  # Every 5 minutes
        },
        'update-market-data': {
            'task': 'tasks.trading.update_market_data',
            'schedule': 60.0,  # Every minute
        },
        'portfolio-sync': {
            'task': 'tasks.trading.sync_portfolios',
            'schedule': 180.0,  # Every 3 minutes
        },
        'system-health-check': {
            'task': 'tasks.maintenance.system_health_check',
            'schedule': 600.0,  # Every 10 minutes
        },
        'demo-user-maintenance': {
            'task': 'tasks.demo_user_tasks.demo_user_maintenance',
            'schedule': 3600.0,  # Every hour
        },
        'demo-expiration-warnings': {
            'task': 'tasks.demo_user_tasks.send_demo_expiration_warnings',
            'schedule': 86400.0,  # Daily
        },
    },
)

# Auto-discover tasks
celery_app.autodiscover_tasks([
    'tasks.trading',
    'tasks.notifications', 
    'tasks.analytics',
    'tasks.maintenance',
    'tasks.demo_user_tasks'
])

# Configure for testing
if os.getenv('TESTING') == 'True':
    celery_app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
    )

@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup."""
    print(f'Request: {self.request!r}')
    return 'Debug task completed'

if __name__ == '__main__':
    celery_app.start()