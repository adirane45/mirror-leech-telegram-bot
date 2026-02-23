"""
Celery Performance Optimization Configuration
Phase 1 Safe Innovation Path - Enhanced Settings
Date: February 5, 2026
"""

from kombu import Exchange, Queue
import os

# ========== BROKER & BACKEND CONFIGURATION ==========
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')

# ========== TASK EXECUTION SETTINGS ==========
CELERY_TASK_SERIALIZER = 'json'  # JSON is faster than pickle for most cases
CELERY_ACCEPT_CONTENT = ['json']
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_ENABLE_UTC = True

# ========== PERFORMANCE TUNING ==========
CELERY_TASK_ACKS_LATE = True  # Acknowledged after execution
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_WORKER_DISABLE_RATE_LIMITS = False
CELERY_WORKER_PREFETCH_MULTIPLIER = 4  # Fetch more tasks at once
CELERY_WORKER_MAX_TASKS_PER_CHILD = 100  # Recycle worker after N tasks

# ========== TIMEOUTS ==========
CELERY_TASK_SOFT_TIME_LIMIT = 3600  # 1 hour soft limit
CELERY_TASK_TIME_LIMIT = 3700  # 1 hour 1 min hard limit
CELERY_TASK_TRACK_STARTED = True  # Track when task starts (for status updates)

# ========== RESULT BACKEND SETTINGS ==========
CELERY_RESULT_EXPIRES = 3600  # Results expire after 1 hour
CELERY_RESULT_EXTENDED = True  # Include task traceback in results
CELERY_RESULT_BACKEND_TRANSPORT_OPTIONS = {
    'master_name': 'mymaster',
    'retry_on_timeout': True,
    'socket_connect_timeout': 5,
    'socket_timeout': 5,
}

# ========== QUEUE CONFIGURATION ==========
CELERY_DEFAULT_QUEUE = 'default'
CELERY_DEFAULT_EXCHANGE = 'tasks'
CELERY_DEFAULT_ROUTING_KEY = 'task.default'

CELERY_QUEUES = (
    Queue('default', Exchange('tasks', type='direct'), routing_key='task.default'),
    Queue('high_priority', Exchange('tasks', type='direct'), routing_key='task.high'),
    Queue('low_priority', Exchange('tasks', type='direct'), routing_key='task.low'),
    Queue('download', Exchange('tasks', type='direct'), routing_key='task.download'),
    Queue('upload', Exchange('tasks', type='direct'), routing_key='task.upload'),
)

# ========== TASK ROUTING ==========
CELERY_TASK_ROUTES = {
    'bot.core.celery_tasks.download_task': {
        'queue': 'download',
        'routing_key': 'task.download',
        'priority': 8
    },
    'bot.core.celery_tasks.upload_task': {
        'queue': 'upload',
        'routing_key': 'task.upload',
        'priority': 7
    },
    'bot.core.celery_tasks.priority_task': {
        'queue': 'high_priority',
        'routing_key': 'task.high',
        'priority': 9
    },
}

# ========== ERROR HANDLING & RETRIES ==========
CELERY_TASK_MAX_RETRIES = 3
CELERY_TASK_DEFAULT_RETRY_DELAY = 60  # 1 minute
CELERY_TASK_DEFAULT_RATE_LIMIT = '100/m'  # 100 tasks per minute

# ========== WORKER CONFIGURATION RECOMMENDATIONS ==========
"""
Recommended startup command for optimal performance:

celery -A bot.core.celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --pool=prefork \
    --max-tasks-per-child=100 \
    --time-limit=3700 \
    --soft-time-limit=3600 \
    --prefetch-multiplier=4 \
    --autoscale=10,3 \
    -Q default,download,upload,high_priority,low_priority

Autoscale: Start with 3 workers, scale up to 10 based on load
"""

# ========== CACHING SETTINGS ==========
CELERY_CACHE_BACKEND = 'redis'
CELERY_CACHE_REDIS_URL = CELERY_BROKER_URL

# ========== MONITORING ==========
CELERY_SEND_TASK_ERROR_EMAILS = True
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_SEND_SENT_SIGNAL = True

# ========== BEAT SCHEDULER SETTINGS (For periodic tasks) ==========
CELERY_BEAT_SCHEDULER = 'celery.beat:PersistentScheduler'
CELERY_BEAT_DB_URI = 'mongodb://localhost:27017/celery'

# ========== OPTIMIZATION NOTES ==========
"""
Performance Optimizations:

1. Prefetch Multiplier (4):
   - Worker fetches 4 tasks at once instead of 1
   - Reduces latency for quick tasks
   - Prevents worker idle time

2. Max Tasks Per Child (100):
   - Recycles worker process after 100 tasks
   - Prevents memory leaks
   - Ensures fresh process state

3. Task Routing:
   - Separate queues for different task types
   - Prevents slow tasks from blocking fast ones
   - High priority tasks get faster processing

4. Autoscaling:
   - Start 3 workers, scale up to 10 if needed
   - Automatically scales down when load drops
   - Saves resources during low activity

5. Timeouts:
   - Soft limit (3600s): Task kills gracefully
   - Hard limit (3700s): Forcefully terminates
   - Prevents hung tasks from blocking forever

6. Result Backend:
   - Results expire after 1 hour
   - Extended results include traceback for debugging
   - Redis retry on timeout ensures reliability
"""
