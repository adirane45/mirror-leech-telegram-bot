"""
Celery Application - Distributed Task Queue
Handles background processing and heavy operations
Safe Innovation Path - Phase 1

Enhanced by: justadi
Date: February 5, 2026
"""

from celery import Celery
from celery.schedules import crontab
from kombu import Exchange, Queue
import os

from .. import LOGGER
from .config_manager import Config


# Create Celery instance
celery_app = Celery(
    'mltb_tasks',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1'),
)

# Celery Configuration
celery_app.conf.update(
    # Task routing
    task_routes={
        'bot.core.celery_tasks.process_download': {'queue': 'downloads'},
        'bot.core.celery_tasks.process_upload': {'queue': 'uploads'},
        'bot.core.celery_tasks.cleanup_old_files': {'queue': 'maintenance'},
        'bot.core.celery_tasks.generate_statistics': {'queue': 'analytics'},
    },
    
    # Task execution
    task_serializer='pickle',
    result_serializer='pickle',
    accept_content=['pickle', 'json'],
    timezone='UTC',
    enable_utc=True,
    
    # Task timeouts
    task_soft_time_limit=3600,  # 1 hour
    task_time_limit=7200,  # 2 hours
    
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_persistent=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,  # Process one task at a time
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks
    worker_disable_rate_limits=False,
    
    # Task acknowledgment
    task_acks_late=True,  # Acknowledge after task completion
    task_reject_on_worker_lost=True,
    
    # Error handling
    task_ignore_result=False,
    task_store_errors_even_if_ignored=True,
    
    # Beat schedule for periodic tasks
    beat_schedule={
        'cleanup-old-downloads': {
            'task': 'bot.core.celery_tasks.cleanup_old_files',
            'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
        },
        'generate-daily-stats': {
            'task': 'bot.core.celery_tasks.generate_statistics',
            'schedule': crontab(hour=0, minute=0),  # Daily at midnight
        },
        'health-check': {
            'task': 'bot.core.celery_tasks.health_check',
            'schedule': 300.0,  # Every 5 minutes
        },
    },
    
    # Queue definitions
    task_queues=(
        Queue('default', Exchange('default'), routing_key='default'),
        Queue('downloads', Exchange('downloads'), routing_key='downloads.#'),
        Queue('uploads', Exchange('uploads'), routing_key='uploads.#'),
        Queue('maintenance', Exchange('maintenance'), routing_key='maintenance.#'),
        Queue('analytics', Exchange('analytics'), routing_key='analytics.#'),
    ),
    
    # Default queue
    task_default_queue='default',
    task_default_exchange='default',
    task_default_routing_key='default',
)


@celery_app.task(bind=True, max_retries=3)
def test_task(self, param: str):
    """Test task to verify Celery is working"""
    try:
        LOGGER.info(f"Test task executed with param: {param}")
        return f"Success: {param}"
    except Exception as e:
        LOGGER.error(f"Test task failed: {e}")
        raise self.retry(exc=e, countdown=60)


# Event handlers
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Setup periodic tasks after Celery configuration"""
    LOGGER.info("✅ Celery periodic tasks configured")


@celery_app.on_after_finalize.connect
def final_setup(sender, **kwargs):
    """Final setup after Celery is configured"""
    LOGGER.info("✅ Celery application initialized")


if __name__ == '__main__':
    celery_app.start()
