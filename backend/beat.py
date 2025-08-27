"""Celery beat scheduler startup script for periodic tasks."""

import os
import sys
from celery.bin import beat

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the configured Celery app
from celery_app import celery_app
from utils.logging_config import setup_logging, get_api_logger

# Setup logging for beat scheduler
setup_logging(enable_monitoring=True)
logger = get_api_logger('beat')

if __name__ == '__main__':
    # Start the beat scheduler
    logger.info("Starting Celery beat scheduler...")
    
    # Configure beat arguments
    beat_args = [
        'beat',
        '--loglevel=info',
        '--schedule=/tmp/celerybeat-schedule',
        '--pidfile=/tmp/celerybeat.pid',
    ]
    
    # Start beat scheduler with arguments
    try:
        celery_app.start(beat_args)
    except KeyboardInterrupt:
        logger.info("Celery beat scheduler stopped by user")
    except Exception as e:
        logger.error(f"Celery beat scheduler failed: {e}")
        sys.exit(1)