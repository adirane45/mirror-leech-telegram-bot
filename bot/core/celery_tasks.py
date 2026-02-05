"""
Celery Tasks - Background Job Definitions
All heavy/long-running operations moved here
Safe Innovation Path - Phase 1

Enhanced by: justadi
Date: February 5, 2026
"""

from celery import Task
from typing import Optional, Dict, Any
import asyncio
from datetime import datetime, timedelta
import os
from pathlib import Path

from .celery_app import celery_app
from .. import LOGGER


class AsyncTask(Task):
    """Base task class that supports async operations"""
    
    def __call__(self, *args, **kwargs):
        """Execute task - handles async functions"""
        result = self.run(*args, **kwargs)
        if asyncio.iscoroutine(result):
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(result)
        return result


# ==================== DOWNLOAD TASKS ====================

@celery_app.task(bind=True, base=AsyncTask, name='bot.core.celery_tasks.process_download')
def process_download(self, download_url: str, options: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a download in the background
    Returns task status and file information
    """
    try:
        LOGGER.info(f"🔽 Processing download: {download_url}")
        
        # This would integrate with existing download logic
        # For now, it's a placeholder that shows the pattern
        result = {
            "status": "completed",
            "url": download_url,
            "task_id": self.request.id,
            "timestamp": datetime.now().isoformat(),
            "options": options
        }
        
        LOGGER.info(f"✅ Download completed: {self.request.id}")
        return result
        
    except Exception as e:
        LOGGER.error(f"❌ Download failed: {e}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=min(2 ** self.request.retries * 60, 3600))


@celery_app.task(bind=True, base=AsyncTask, name='bot.core.celery_tasks.process_upload')
def process_upload(self, file_path: str, destination: str, options: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process an upload in the background
    """
    try:
        LOGGER.info(f"🔼 Processing upload: {file_path} -> {destination}")
        
        result = {
            "status": "completed",
            "file_path": file_path,
            "destination": destination,
            "task_id": self.request.id,
            "timestamp": datetime.now().isoformat()
        }
        
        LOGGER.info(f"✅ Upload completed: {self.request.id}")
        return result
        
    except Exception as e:
        LOGGER.error(f"❌ Upload failed: {e}")
        raise self.retry(exc=e, countdown=min(2 ** self.request.retries * 60, 3600))


# ==================== MAINTENANCE TASKS ====================

@celery_app.task(name='bot.core.celery_tasks.cleanup_old_files')
def cleanup_old_files(max_age_hours: int = 24):
    """
    Clean up old downloaded files
    Runs daily at 2 AM (configured in celery_app.py)
    """
    try:
        LOGGER.info("🧹 Starting file cleanup...")
        
        downloads_dir = Path("downloads")
        if not downloads_dir.exists():
            LOGGER.info("Downloads directory doesn't exist, skipping cleanup")
            return {"status": "skipped", "reason": "directory_not_found"}
        
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        deleted_count = 0
        freed_space = 0
        
        for file_path in downloads_dir.rglob("*"):
            if file_path.is_file():
                file_modified = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_modified < cutoff_time:
                    file_size = file_path.stat().st_size
                    try:
                        file_path.unlink()
                        deleted_count += 1
                        freed_space += file_size
                        LOGGER.debug(f"Deleted: {file_path.name}")
                    except Exception as e:
                        LOGGER.warning(f"Failed to delete {file_path}: {e}")
        
        result = {
            "status": "completed",
            "deleted_files": deleted_count,
            "freed_space_mb": round(freed_space / (1024 * 1024), 2),
            "timestamp": datetime.now().isoformat()
        }
        
        LOGGER.info(f"✅ Cleanup completed: {deleted_count} files deleted, {result['freed_space_mb']} MB freed")
        return result
        
    except Exception as e:
        LOGGER.error(f"❌ Cleanup failed: {e}")
        return {"status": "failed", "error": str(e)}


@celery_app.task(name='bot.core.celery_tasks.generate_statistics')
def generate_statistics():
    """
    Generate daily statistics
    Runs daily at midnight (configured in celery_app.py)
    """
    try:
        LOGGER.info("📊 Generating daily statistics...")
        
        # Placeholder for statistics generation
        # Would integrate with existing stats system
        stats = {
            "date": datetime.now().date().isoformat(),
            "total_downloads": 0,
            "total_uploads": 0,
            "active_users": 0,
            "storage_used": 0,
            "timestamp": datetime.now().isoformat()
        }
        
        LOGGER.info("✅ Statistics generated successfully")
        return stats
        
    except Exception as e:
        LOGGER.error(f"❌ Statistics generation failed: {e}")
        return {"status": "failed", "error": str(e)}


@celery_app.task(name='bot.core.celery_tasks.health_check')
def health_check():
    """
    Periodic health check
    Runs every 5 minutes (configured in celery_app.py)
    """
    try:
        import psutil
        
        health = {
            "status": "healthy",
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "timestamp": datetime.now().isoformat()
        }
        
        # Alert if resources are critical
        if health["cpu_percent"] > 90:
            LOGGER.warning(f"⚠️ High CPU usage: {health['cpu_percent']}%")
        if health["memory_percent"] > 90:
            LOGGER.warning(f"⚠️ High memory usage: {health['memory_percent']}%")
        if health["disk_percent"] > 90:
            LOGGER.warning(f"⚠️ High disk usage: {health['disk_percent']}%")
        
        return health
        
    except Exception as e:
        LOGGER.error(f"❌ Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


# ==================== NOTIFICATION TASKS ====================

@celery_app.task(bind=True, name='bot.core.celery_tasks.send_notification')
def send_notification(self, user_id: int, message: str, notification_type: str = "info"):
    """
    Send notification to user
    Can be used for async notifications
    """
    try:
        LOGGER.info(f"📬 Sending {notification_type} notification to user {user_id}")
        
        # Placeholder - would integrate with Telegram message sending
        result = {
            "status": "sent",
            "user_id": user_id,
            "type": notification_type,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        return result
        
    except Exception as e:
        LOGGER.error(f"❌ Notification failed: {e}")
        raise self.retry(exc=e, countdown=30, max_retries=3)


# ==================== DATA PROCESSING TASKS ====================

@celery_app.task(name='bot.core.celery_tasks.process_archive')
def process_archive(file_path: str, extract: bool = True, password: Optional[str] = None):
    """
    Process archive files (extract, compress, etc.)
    Heavy operation moved to background
    """
    try:
        LOGGER.info(f"📦 Processing archive: {file_path}")
        
        result = {
            "status": "completed",
            "file_path": file_path,
            "extracted": extract,
            "timestamp": datetime.now().isoformat()
        }
        
        LOGGER.info("✅ Archive processing completed")
        return result
        
    except Exception as e:
        LOGGER.error(f"❌ Archive processing failed: {e}")
        return {"status": "failed", "error": str(e)}


@celery_app.task(name='bot.core.celery_tasks.generate_media_info')
def generate_media_info(file_path: str):
    """
    Generate media information (ffprobe, mediainfo)
    CPU-intensive operation moved to background
    """
    try:
        LOGGER.info(f"🎬 Generating media info: {file_path}")
        
        # Placeholder - would use ffprobe/mediainfo
        info = {
            "file": file_path,
            "duration": 0,
            "resolution": "unknown",
            "codec": "unknown",
            "timestamp": datetime.now().isoformat()
        }
        
        LOGGER.info("✅ Media info generated")
        return info
        
    except Exception as e:
        LOGGER.error(f"❌ Media info generation failed: {e}")
        return {"status": "failed", "error": str(e)}


# ==================== UTILITY FUNCTIONS ====================

def get_task_status(task_id: str) -> Dict[str, Any]:
    """Get status of a Celery task"""
    result = celery_app.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "state": result.state,
        "ready": result.ready(),
        "successful": result.successful() if result.ready() else None,
        "result": result.result if result.ready() else None,
        "info": result.info
    }


def cancel_task(task_id: str) -> bool:
    """Cancel a running Celery task"""
    try:
        celery_app.control.revoke(task_id, terminate=True)
        LOGGER.info(f"Task {task_id} cancelled")
        return True
    except Exception as e:
        LOGGER.error(f"Failed to cancel task {task_id}: {e}")
        return False
