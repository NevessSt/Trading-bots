"""Maintenance-related Celery tasks for system cleanup and health checks."""

import logging
import os
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from celery import Task

from celery_app import celery_app
from models.user import User
from models.trade import Trade
from models.bot import Bot
from models.portfolio import Portfolio
from services.notification_service import NotificationService
from utils.logging_config import get_api_logger
from database import db

logger = get_api_logger('maintenance_tasks')

class MaintenanceTask(Task):
    """Base class for maintenance tasks with error handling."""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        logger.error(f"Maintenance task {task_id} failed: {exc}")

@celery_app.task(bind=True, base=MaintenanceTask)
def system_health_check(self):
    """Perform comprehensive system health check."""
    try:
        logger.info("Starting system health check")
        
        health_status = {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': 'healthy',
            'checks': {}
        }
        
        # Database connectivity check
        try:
            db.session.execute('SELECT 1')
            health_status['checks']['database'] = {
                'status': 'healthy',
                'message': 'Database connection successful'
            }
        except Exception as e:
            health_status['checks']['database'] = {
                'status': 'unhealthy',
                'message': f'Database connection failed: {str(e)}'
            }
            health_status['overall_status'] = 'unhealthy'
        
        # System resources check
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # CPU check
            cpu_status = 'healthy' if cpu_percent < 80 else 'warning' if cpu_percent < 95 else 'critical'
            health_status['checks']['cpu'] = {
                'status': cpu_status,
                'usage_percent': cpu_percent,
                'message': f'CPU usage: {cpu_percent}%'
            }
            
            # Memory check
            memory_percent = memory.percent
            memory_status = 'healthy' if memory_percent < 80 else 'warning' if memory_percent < 95 else 'critical'
            health_status['checks']['memory'] = {
                'status': memory_status,
                'usage_percent': memory_percent,
                'available_gb': round(memory.available / (1024**3), 2),
                'message': f'Memory usage: {memory_percent}%'
            }
            
            # Disk check
            disk_percent = disk.percent
            disk_status = 'healthy' if disk_percent < 80 else 'warning' if disk_percent < 95 else 'critical'
            health_status['checks']['disk'] = {
                'status': disk_status,
                'usage_percent': disk_percent,
                'free_gb': round(disk.free / (1024**3), 2),
                'message': f'Disk usage: {disk_percent}%'
            }
            
            # Update overall status based on resource checks
            if any(check['status'] == 'critical' for check in [health_status['checks']['cpu'], health_status['checks']['memory'], health_status['checks']['disk']]):
                health_status['overall_status'] = 'critical'
            elif any(check['status'] == 'warning' for check in [health_status['checks']['cpu'], health_status['checks']['memory'], health_status['checks']['disk']]):
                if health_status['overall_status'] == 'healthy':
                    health_status['overall_status'] = 'warning'
            
        except Exception as e:
            health_status['checks']['system_resources'] = {
                'status': 'unhealthy',
                'message': f'Failed to check system resources: {str(e)}'
            }
            health_status['overall_status'] = 'unhealthy'
        
        # Active bots check
        try:
            total_bots = Bot.query.count()
            active_bots = Bot.query.filter_by(status='active').count()
            error_bots = Bot.query.filter_by(status='error').count()
            
            bot_status = 'healthy'
            if error_bots > total_bots * 0.1:  # More than 10% bots in error
                bot_status = 'warning'
            if error_bots > total_bots * 0.25:  # More than 25% bots in error
                bot_status = 'critical'
            
            health_status['checks']['bots'] = {
                'status': bot_status,
                'total_bots': total_bots,
                'active_bots': active_bots,
                'error_bots': error_bots,
                'message': f'{active_bots}/{total_bots} bots active, {error_bots} in error'
            }
            
            if bot_status == 'critical' and health_status['overall_status'] != 'unhealthy':
                health_status['overall_status'] = 'critical'
            elif bot_status == 'warning' and health_status['overall_status'] == 'healthy':
                health_status['overall_status'] = 'warning'
            
        except Exception as e:
            health_status['checks']['bots'] = {
                'status': 'unhealthy',
                'message': f'Failed to check bot status: {str(e)}'
            }
            health_status['overall_status'] = 'unhealthy'
        
        # Recent trades check
        try:
            last_hour = datetime.utcnow() - timedelta(hours=1)
            recent_trades = Trade.query.filter(Trade.created_at >= last_hour).count()
            failed_trades = Trade.query.filter(
                Trade.created_at >= last_hour,
                Trade.status == 'failed'
            ).count()
            
            trade_status = 'healthy'
            if recent_trades > 0:
                failure_rate = failed_trades / recent_trades
                if failure_rate > 0.1:  # More than 10% failure rate
                    trade_status = 'warning'
                if failure_rate > 0.25:  # More than 25% failure rate
                    trade_status = 'critical'
            
            health_status['checks']['trades'] = {
                'status': trade_status,
                'recent_trades': recent_trades,
                'failed_trades': failed_trades,
                'failure_rate': round(failed_trades / recent_trades * 100, 2) if recent_trades > 0 else 0,
                'message': f'{recent_trades} trades in last hour, {failed_trades} failed'
            }
            
            if trade_status == 'critical' and health_status['overall_status'] != 'unhealthy':
                health_status['overall_status'] = 'critical'
            elif trade_status == 'warning' and health_status['overall_status'] == 'healthy':
                health_status['overall_status'] = 'warning'
            
        except Exception as e:
            health_status['checks']['trades'] = {
                'status': 'unhealthy',
                'message': f'Failed to check trade status: {str(e)}'
            }
            health_status['overall_status'] = 'unhealthy'
        
        # Log file size check
        try:
            log_files = ['trading_bot.log', 'error.log', 'access.log']
            log_status = 'healthy'
            log_info = []
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    size_mb = os.path.getsize(log_file) / (1024 * 1024)
                    log_info.append({
                        'file': log_file,
                        'size_mb': round(size_mb, 2)
                    })
                    
                    if size_mb > 100:  # Log file larger than 100MB
                        log_status = 'warning'
                    if size_mb > 500:  # Log file larger than 500MB
                        log_status = 'critical'
            
            health_status['checks']['logs'] = {
                'status': log_status,
                'files': log_info,
                'message': f'Checked {len(log_info)} log files'
            }
            
            if log_status == 'warning' and health_status['overall_status'] == 'healthy':
                health_status['overall_status'] = 'warning'
            
        except Exception as e:
            health_status['checks']['logs'] = {
                'status': 'unhealthy',
                'message': f'Failed to check log files: {str(e)}'
            }
        
        # Send alerts for critical issues
        if health_status['overall_status'] in ['critical', 'unhealthy']:
            try:
                from tasks.notifications import send_alert_notification
                
                critical_checks = [
                    check_name for check_name, check_data in health_status['checks'].items()
                    if check_data['status'] in ['critical', 'unhealthy']
                ]
                
                alert_data = {
                    'title': 'System Health Alert',
                    'message': f'System health check failed. Critical issues: {", ".join(critical_checks)}',
                    'severity': 'critical' if health_status['overall_status'] == 'unhealthy' else 'high',
                    'admin_only': True
                }
                
                send_alert_notification.delay(alert_data)
                
            except Exception as e:
                logger.error(f"Failed to send health check alert: {e}")
        
        logger.info(f"System health check completed: {health_status['overall_status']}")
        
        return health_status
        
    except Exception as exc:
        logger.error(f"System health check failed: {exc}")
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': 'unhealthy',
            'error': str(exc)
        }

@celery_app.task(bind=True, base=MaintenanceTask)
def cleanup_old_trades(self, days_to_keep: int = 365):
    """Clean up old completed trades to save database space.
    
    Args:
        days_to_keep: Number of days of trade history to retain
    """
    try:
        logger.info(f"Cleaning up trades older than {days_to_keep} days")
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Only delete completed trades that are older than cutoff
        old_trades = Trade.query.filter(
            Trade.created_at < cutoff_date,
            Trade.status.in_(['completed', 'cancelled'])
        )
        
        trade_count = old_trades.count()
        
        if trade_count > 0:
            # Delete in batches to avoid locking the database
            batch_size = 1000
            deleted_count = 0
            
            while True:
                batch = old_trades.limit(batch_size).all()
                if not batch:
                    break
                
                for trade in batch:
                    db.session.delete(trade)
                
                db.session.commit()
                deleted_count += len(batch)
                
                logger.info(f"Deleted {deleted_count}/{trade_count} old trades")
        
        cleanup_result = {
            'success': True,
            'cleanup_date': datetime.utcnow().isoformat(),
            'cutoff_date': cutoff_date.isoformat(),
            'deleted_trades': trade_count,
            'days_kept': days_to_keep
        }
        
        logger.info(f"Trade cleanup completed: {trade_count} trades deleted")
        
        return cleanup_result
        
    except Exception as exc:
        logger.error(f"Trade cleanup failed: {exc}")
        db.session.rollback()
        return {'success': False, 'error': str(exc)}

@celery_app.task(bind=True, base=MaintenanceTask)
def cleanup_log_files(self, max_size_mb: int = 100):
    """Clean up and rotate log files that exceed size limit.
    
    Args:
        max_size_mb: Maximum size in MB before rotating log files
    """
    try:
        logger.info(f"Cleaning up log files larger than {max_size_mb}MB")
        
        log_files = ['trading_bot.log', 'error.log', 'access.log', 'celery.log']
        cleanup_results = []
        
        for log_file in log_files:
            if os.path.exists(log_file):
                size_mb = os.path.getsize(log_file) / (1024 * 1024)
                
                if size_mb > max_size_mb:
                    try:
                        # Create backup with timestamp
                        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                        backup_name = f"{log_file}.{timestamp}"
                        
                        # Rename current log to backup
                        os.rename(log_file, backup_name)
                        
                        # Create new empty log file
                        open(log_file, 'w').close()
                        
                        cleanup_results.append({
                            'file': log_file,
                            'original_size_mb': round(size_mb, 2),
                            'backup_name': backup_name,
                            'status': 'rotated'
                        })
                        
                        logger.info(f"Rotated log file {log_file} ({size_mb:.2f}MB) to {backup_name}")
                        
                    except Exception as e:
                        cleanup_results.append({
                            'file': log_file,
                            'original_size_mb': round(size_mb, 2),
                            'status': 'failed',
                            'error': str(e)
                        })
                        logger.error(f"Failed to rotate log file {log_file}: {e}")
                else:
                    cleanup_results.append({
                        'file': log_file,
                        'size_mb': round(size_mb, 2),
                        'status': 'ok'
                    })
        
        # Clean up old backup files (keep only last 5)
        try:
            for log_file in log_files:
                backup_pattern = f"{log_file}.*"
                backup_files = [f for f in os.listdir('.') if f.startswith(log_file) and f != log_file]
                backup_files.sort(reverse=True)  # Most recent first
                
                # Remove old backups (keep only 5 most recent)
                for old_backup in backup_files[5:]:
                    try:
                        os.remove(old_backup)
                        logger.info(f"Removed old backup: {old_backup}")
                    except Exception as e:
                        logger.error(f"Failed to remove old backup {old_backup}: {e}")
        
        except Exception as e:
            logger.error(f"Failed to clean up old backups: {e}")
        
        result = {
            'success': True,
            'cleanup_date': datetime.utcnow().isoformat(),
            'max_size_mb': max_size_mb,
            'files_processed': len(cleanup_results),
            'files_rotated': len([r for r in cleanup_results if r['status'] == 'rotated']),
            'results': cleanup_results
        }
        
        logger.info(f"Log cleanup completed: {result['files_rotated']} files rotated")
        
        return result
        
    except Exception as exc:
        logger.error(f"Log cleanup failed: {exc}")
        return {'success': False, 'error': str(exc)}

@celery_app.task(bind=True, base=MaintenanceTask)
def database_maintenance(self):
    """Perform database maintenance tasks like analyzing tables and updating statistics."""
    try:
        logger.info("Starting database maintenance")
        
        maintenance_results = []
        
        # Update table statistics (PostgreSQL specific)
        try:
            tables = ['users', 'bots', 'trades', 'portfolios']
            
            for table in tables:
                try:
                    db.session.execute(f'ANALYZE {table}')
                    maintenance_results.append({
                        'task': f'analyze_{table}',
                        'status': 'completed'
                    })
                except Exception as e:
                    maintenance_results.append({
                        'task': f'analyze_{table}',
                        'status': 'failed',
                        'error': str(e)
                    })
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Failed to analyze tables: {e}")
            maintenance_results.append({
                'task': 'analyze_tables',
                'status': 'failed',
                'error': str(e)
            })
        
        # Check for orphaned records
        try:
            # Find trades without valid users
            orphaned_trades = db.session.query(Trade).filter(
                ~Trade.user_id.in_(db.session.query(User.id))
            ).count()
            
            # Find bots without valid users
            orphaned_bots = db.session.query(Bot).filter(
                ~Bot.user_id.in_(db.session.query(User.id))
            ).count()
            
            maintenance_results.append({
                'task': 'orphaned_records_check',
                'status': 'completed',
                'orphaned_trades': orphaned_trades,
                'orphaned_bots': orphaned_bots
            })
            
            # Clean up orphaned records if found
            if orphaned_trades > 0:
                db.session.query(Trade).filter(
                    ~Trade.user_id.in_(db.session.query(User.id))
                ).delete(synchronize_session=False)
                
                maintenance_results.append({
                    'task': 'cleanup_orphaned_trades',
                    'status': 'completed',
                    'deleted_count': orphaned_trades
                })
            
            if orphaned_bots > 0:
                db.session.query(Bot).filter(
                    ~Bot.user_id.in_(db.session.query(User.id))
                ).delete(synchronize_session=False)
                
                maintenance_results.append({
                    'task': 'cleanup_orphaned_bots',
                    'status': 'completed',
                    'deleted_count': orphaned_bots
                })
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Failed to check orphaned records: {e}")
            db.session.rollback()
            maintenance_results.append({
                'task': 'orphaned_records_check',
                'status': 'failed',
                'error': str(e)
            })
        
        # Database size check
        try:
            db_size_query = """
                SELECT pg_size_pretty(pg_database_size(current_database())) as size
            """
            result = db.session.execute(db_size_query).fetchone()
            db_size = result[0] if result else 'unknown'
            
            maintenance_results.append({
                'task': 'database_size_check',
                'status': 'completed',
                'database_size': db_size
            })
            
        except Exception as e:
            logger.error(f"Failed to check database size: {e}")
            maintenance_results.append({
                'task': 'database_size_check',
                'status': 'failed',
                'error': str(e)
            })
        
        result = {
            'success': True,
            'maintenance_date': datetime.utcnow().isoformat(),
            'tasks_completed': len([r for r in maintenance_results if r['status'] == 'completed']),
            'tasks_failed': len([r for r in maintenance_results if r['status'] == 'failed']),
            'results': maintenance_results
        }
        
        logger.info(f"Database maintenance completed: {result['tasks_completed']} tasks completed, {result['tasks_failed']} failed")
        
        return result
        
    except Exception as exc:
        logger.error(f"Database maintenance failed: {exc}")
        return {'success': False, 'error': str(exc)}

@celery_app.task
def schedule_maintenance_tasks():
    """Schedule all maintenance tasks to run."""
    try:
        logger.info("Scheduling maintenance tasks")
        
        scheduled_tasks = []
        
        # Schedule system health check
        health_check_task = system_health_check.delay()
        scheduled_tasks.append({
            'task': 'system_health_check',
            'task_id': health_check_task.id
        })
        
        # Schedule log cleanup
        log_cleanup_task = cleanup_log_files.delay()
        scheduled_tasks.append({
            'task': 'cleanup_log_files',
            'task_id': log_cleanup_task.id
        })
        
        # Schedule database maintenance
        db_maintenance_task = database_maintenance.delay()
        scheduled_tasks.append({
            'task': 'database_maintenance',
            'task_id': db_maintenance_task.id
        })
        
        # Schedule old trade cleanup (weekly)
        trade_cleanup_task = cleanup_old_trades.delay(days_to_keep=365)
        scheduled_tasks.append({
            'task': 'cleanup_old_trades',
            'task_id': trade_cleanup_task.id
        })
        
        result = {
            'success': True,
            'scheduled_at': datetime.utcnow().isoformat(),
            'scheduled_tasks': scheduled_tasks,
            'total_tasks': len(scheduled_tasks)
        }
        
        logger.info(f"Maintenance tasks scheduled: {len(scheduled_tasks)} tasks")
        
        return result
        
    except Exception as exc:
        logger.error(f"Failed to schedule maintenance tasks: {exc}")
        return {'success': False, 'error': str(exc)}