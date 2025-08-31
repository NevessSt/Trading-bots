"""Celery tasks for demo user management and auto-expiration."""

from celery import Celery
from datetime import datetime, timedelta

from services.demo_user_service import DemoUserService
from services.logging_service import get_logger, LogCategory
from celery_app import celery_app

logger = get_logger(LogCategory.SYSTEM)


@celery_app.task(bind=True, name='demo_user_cleanup')
def cleanup_expired_demo_users(self, batch_size=100):
    """Celery task to clean up expired demo users.
    
    Args:
        batch_size: Number of users to process in each batch
        
    Returns:
        Dictionary with cleanup statistics
    """
    try:
        logger.info("Starting demo user cleanup task")
        
        demo_service = DemoUserService()
        stats = demo_service.cleanup_expired_demo_users(batch_size=batch_size)
        
        logger.info(f"Demo user cleanup completed: {stats}")
        
        return {
            'status': 'success',
            'stats': stats,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Demo user cleanup task failed: {e}")
        
        # Retry the task with exponential backoff
        raise self.retry(
            exc=e,
            countdown=60 * (2 ** self.request.retries),  # Exponential backoff
            max_retries=3
        )


@celery_app.task(bind=True, name='demo_user_expiration_warnings')
def send_demo_expiration_warnings(self, days_before=1):
    """Celery task to send expiration warnings to demo users.
    
    Args:
        days_before: Number of days before expiry to send warning
        
    Returns:
        Dictionary with warning statistics
    """
    try:
        logger.info(f"Starting demo expiration warnings task ({days_before} days before)")
        
        demo_service = DemoUserService()
        stats = demo_service.send_expiration_warnings(days_before=days_before)
        
        logger.info(f"Demo expiration warnings completed: {stats}")
        
        return {
            'status': 'success',
            'stats': stats,
            'days_before': days_before,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Demo expiration warnings task failed: {e}")
        
        # Retry the task with exponential backoff
        raise self.retry(
            exc=e,
            countdown=60 * (2 ** self.request.retries),
            max_retries=3
        )


@celery_app.task(bind=True, name='demo_user_stats_report')
def generate_demo_user_stats_report(self):
    """Celery task to generate demo user statistics report.
    
    Returns:
        Dictionary with demo user statistics
    """
    try:
        logger.info("Generating demo user statistics report")
        
        demo_service = DemoUserService()
        stats = demo_service.get_demo_user_stats()
        
        # Add timestamp and additional metrics
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'stats': stats,
            'health_metrics': {
                'conversion_rate': _calculate_conversion_rate(stats),
                'average_demo_duration': _calculate_average_demo_duration(),
                'expiration_efficiency': _calculate_expiration_efficiency(stats)
            }
        }
        
        logger.info(f"Demo user stats report generated: {report}")
        
        return {
            'status': 'success',
            'report': report
        }
        
    except Exception as e:
        logger.error(f"Demo user stats report task failed: {e}")
        
        # Retry the task
        raise self.retry(
            exc=e,
            countdown=60 * (2 ** self.request.retries),
            max_retries=2
        )


@celery_app.task(bind=True, name='demo_user_maintenance')
def demo_user_maintenance(self):
    """Comprehensive demo user maintenance task.
    
    Performs multiple maintenance operations:
    - Clean up expired users
    - Send expiration warnings
    - Generate statistics
    - Perform health checks
    
    Returns:
        Dictionary with all maintenance results
    """
    try:
        logger.info("Starting comprehensive demo user maintenance")
        
        demo_service = DemoUserService()
        results = {}
        
        # 1. Clean up expired users
        logger.info("Step 1: Cleaning up expired demo users")
        results['cleanup'] = demo_service.cleanup_expired_demo_users()
        
        # 2. Send 1-day warnings
        logger.info("Step 2: Sending 1-day expiration warnings")
        results['warnings_1day'] = demo_service.send_expiration_warnings(days_before=1)
        
        # 3. Send 3-day warnings
        logger.info("Step 3: Sending 3-day expiration warnings")
        results['warnings_3day'] = demo_service.send_expiration_warnings(days_before=3)
        
        # 4. Generate statistics
        logger.info("Step 4: Generating statistics")
        results['stats'] = demo_service.get_demo_user_stats()
        
        # 5. Health check
        logger.info("Step 5: Performing health check")
        results['health_check'] = _perform_demo_user_health_check(results['stats'])
        
        maintenance_result = {
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'results': results,
            'summary': {
                'users_expired': results['cleanup'].get('expired', 0),
                'warnings_sent': (
                    results['warnings_1day'].get('warnings_sent', 0) + 
                    results['warnings_3day'].get('warnings_sent', 0)
                ),
                'total_errors': (
                    results['cleanup'].get('errors', 0) + 
                    results['warnings_1day'].get('errors', 0) + 
                    results['warnings_3day'].get('errors', 0)
                )
            }
        }
        
        logger.info(f"Demo user maintenance completed: {maintenance_result['summary']}")
        
        return maintenance_result
        
    except Exception as e:
        logger.error(f"Demo user maintenance task failed: {e}")
        
        # Retry the task
        raise self.retry(
            exc=e,
            countdown=300,  # 5 minutes
            max_retries=2
        )


def _calculate_conversion_rate(stats):
    """Calculate demo to paid conversion rate."""
    try:
        from models import User
        
        total_demo = stats.get('total_demo_users', 0)
        if total_demo == 0:
            return 0.0
        
        # Count users who started as demo and converted to paid
        converted_users = User.query.filter(
            User.is_demo == False,
            User.was_demo == True  # Assuming we track this
        ).count()
        
        return round((converted_users / total_demo) * 100, 2)
        
    except Exception as e:
        logger.error(f"Failed to calculate conversion rate: {e}")
        return 0.0


def _calculate_average_demo_duration():
    """Calculate average duration of demo accounts."""
    try:
        from models import User
        from sqlalchemy import func
        
        # Get average duration for expired demo users
        result = User.query.filter(
            User.is_demo == True,
            User.expired_at.isnot(None)
        ).with_entities(
            func.avg(
                func.extract('epoch', User.expired_at) - 
                func.extract('epoch', User.created_at)
            ).label('avg_duration_seconds')
        ).first()
        
        if result and result.avg_duration_seconds:
            # Convert seconds to days
            avg_days = result.avg_duration_seconds / (24 * 60 * 60)
            return round(avg_days, 2)
        
        return 0.0
        
    except Exception as e:
        logger.error(f"Failed to calculate average demo duration: {e}")
        return 0.0


def _calculate_expiration_efficiency(stats):
    """Calculate how efficiently expired users are being cleaned up."""
    try:
        overdue = stats.get('overdue_expiration', 0)
        expired = stats.get('expired_demo_users', 0)
        
        if expired == 0:
            return 100.0  # No expired users, perfect efficiency
        
        efficiency = ((expired - overdue) / expired) * 100
        return round(max(0, efficiency), 2)
        
    except Exception as e:
        logger.error(f"Failed to calculate expiration efficiency: {e}")
        return 0.0


def _perform_demo_user_health_check(stats):
    """Perform health check on demo user system."""
    health_check = {
        'status': 'healthy',
        'issues': [],
        'recommendations': []
    }
    
    try:
        # Check for overdue expirations
        overdue = stats.get('overdue_expiration', 0)
        if overdue > 10:
            health_check['status'] = 'warning'
            health_check['issues'].append(f"{overdue} demo users are overdue for expiration")
            health_check['recommendations'].append("Increase cleanup task frequency")
        
        # Check for high number of expiring users
        expiring_soon = stats.get('expiring_soon', 0)
        if expiring_soon > 50:
            health_check['issues'].append(f"{expiring_soon} demo users expiring in next 3 days")
            health_check['recommendations'].append("Consider sending additional upgrade reminders")
        
        # Check active demo user ratio
        total_demo = stats.get('total_demo_users', 0)
        active_demo = stats.get('active_demo_users', 0)
        
        if total_demo > 0:
            active_ratio = (active_demo / total_demo) * 100
            if active_ratio < 30:
                health_check['issues'].append(f"Low active demo ratio: {active_ratio:.1f}%")
                health_check['recommendations'].append("Review demo user engagement strategies")
        
        # Set overall status
        if len(health_check['issues']) > 2:
            health_check['status'] = 'critical'
        elif len(health_check['issues']) > 0:
            health_check['status'] = 'warning'
        
        return health_check
        
    except Exception as e:
        logger.error(f"Demo user health check failed: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'issues': ['Health check failed'],
            'recommendations': ['Check system logs']
        }


# Schedule periodic tasks (these would be configured in celery beat)
def schedule_demo_user_tasks():
    """Schedule periodic demo user tasks.
    
    This function defines the schedule for demo user maintenance tasks.
    It should be called during application startup to register the schedules.
    """
    from celery.schedules import crontab
    
    # Schedule tasks in celery beat configuration
    schedules = {
        # Clean up expired users daily at 2 AM
        'demo-user-cleanup': {
            'task': 'demo_user_cleanup',
            'schedule': crontab(hour=2, minute=0),
            'kwargs': {'batch_size': 100}
        },
        
        # Send 1-day warnings daily at 10 AM
        'demo-expiration-warnings-1day': {
            'task': 'demo_user_expiration_warnings',
            'schedule': crontab(hour=10, minute=0),
            'kwargs': {'days_before': 1}
        },
        
        # Send 3-day warnings daily at 10:30 AM
        'demo-expiration-warnings-3day': {
            'task': 'demo_user_expiration_warnings',
            'schedule': crontab(hour=10, minute=30),
            'kwargs': {'days_before': 3}
        },
        
        # Generate stats report daily at 6 AM
        'demo-user-stats-report': {
            'task': 'demo_user_stats_report',
            'schedule': crontab(hour=6, minute=0)
        },
        
        # Comprehensive maintenance weekly on Sundays at 3 AM
        'demo-user-maintenance': {
            'task': 'demo_user_maintenance',
            'schedule': crontab(hour=3, minute=0, day_of_week=0)
        }
    }
    
    return schedules