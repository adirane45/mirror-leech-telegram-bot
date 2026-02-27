"""
Scheduled and priority-based download management

Features:
- Recurring download schedules (daily, weekly, monthly)
- Download queue with priority levels
- Download templates for quick reuse
- Pause/resume individual downloads
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
from logging import getLogger
import threading
import heapq

LOGGER = getLogger(__name__)

DB_PATH = Path("/app/data/scheduled_downloads.db")


class PriorityQueue:
    """Thread-safe priority queue for downloads"""
    
    def __init__(self):
        self.queue = []
        self.lock = threading.Lock()
        self.counter = 0  # For stable sorting of same-priority items
    
    def add(self, download_id: str, priority: int = 5, url: str = "", operation: str = ""):
        """Add download to queue (priority 1=highest, 10=lowest)"""
        with self.lock:
            self.counter += 1
            heapq.heappush(self.queue, (priority, self.counter, {
                'id': download_id,
                'url': url,
                'operation': operation,
                'added_at': datetime.now().isoformat()
            }))
    
    def get_priority(self, download_id: str) -> int:
        """Get current priority of a download"""
        with self.lock:
            for priority, _, item in self.queue:
                if item['id'] == download_id:
                    return priority
            return None
    
    def set_priority(self, download_id: str, new_priority: int) -> bool:
        """Change priority of a queued download"""
        with self.lock:
            # Find and remove
            self.queue = [(p, c, item) for p, c, item in self.queue 
                         if item['id'] != download_id]
            heapq.heapify(self.queue)
            
            # Re-add with new priority (if found)
            if any(item[2]['id'] == download_id for item in self.queue 
                   if len(item) > 2):
                self.counter += 1
                heapq.heappush(self.queue, (new_priority, self.counter, {
                    'id': download_id,
                    'priority_changed': datetime.now().isoformat()
                }))
                return True
            return False
    
    def peek(self) -> Optional[Dict]:
        """Get next download without removing"""
        with self.lock:
            if self.queue:
                return self.queue[0][2]
            return None
    
    def pop(self) -> Optional[Dict]:
        """Get and remove next download"""
        with self.lock:
            if self.queue:
                _, _, item = heapq.heappop(self.queue)
                return item
            return None
    
    def size(self) -> int:
        """Get queue size"""
        with self.lock:
            return len(self.queue)
    
    def list_all(self) -> List[Dict[str, Any]]:
        """List all queued downloads"""
        with self.lock:
            return [{'priority': p, 'download': item} for p, _, item in self.queue]


class ScheduledDownloads:
    """SQLite database for scheduled downloads, templates, and pause states"""
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = Path(db_path) if isinstance(db_path, str) else db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.priority_queue = PriorityQueue()
        self._init_database()
    
    def _get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_database(self):
        """Initialize database schema"""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Scheduled downloads table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scheduled_downloads (
                    id TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    schedule_type TEXT,  -- 'once', 'daily', 'weekly', 'monthly'
                    schedule_data TEXT,  -- JSON with cron/time details
                    status TEXT DEFAULT 'active',  -- 'active', 'paused', 'completed', 'failed'
                    next_run TIMESTAMP,
                    last_run TIMESTAMP,
                    run_count INTEGER DEFAULT 0,
                    failed_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    destination TEXT,
                    options TEXT,  -- JSON with download options
                    metadata TEXT
                )
            """)
            
            # Download templates table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS download_templates (
                    id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    operation TEXT NOT NULL,
                    url_pattern TEXT,  -- Optional pattern for URL
                    options TEXT,  -- JSON with default options
                    destination TEXT,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    usage_count INTEGER DEFAULT 0
                )
            """)
            
            # Download pause state table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS download_pause_state (
                    download_id TEXT PRIMARY KEY,
                    is_paused INTEGER DEFAULT 0,
                    paused_at TIMESTAMP,
                    resume_at TIMESTAMP,
                    reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Queue priority table (for persistence)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS download_queue (
                    id TEXT PRIMARY KEY,
                    download_id TEXT NOT NULL UNIQUE,
                    priority INTEGER DEFAULT 5,
                    status TEXT DEFAULT 'queued',
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_scheduled_status ON scheduled_downloads(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_next_run ON scheduled_downloads(next_run)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_queue_priority ON download_queue(priority)")
            
            conn.commit()
            conn.close()
    
    # === Scheduled Downloads ===
    
    def add_scheduled_download(self, download_id: str, url: str, operation: str,
                              schedule_type: str = "once", schedule_data: Dict = None,
                              next_run: datetime = None, destination: str = "",
                              options: Dict = None) -> bool:
        """Create a scheduled download"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                if not next_run:
                    next_run = datetime.now()
                
                cursor.execute("""
                    INSERT INTO scheduled_downloads
                    (id, url, operation, schedule_type, schedule_data, next_run, destination, options)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    download_id,
                    url,
                    operation,
                    schedule_type,
                    json.dumps(schedule_data) if schedule_data else None,
                    next_run,
                    destination,
                    json.dumps(options) if options else None
                ))
                
                conn.commit()
                conn.close()
                return True
            except Exception as e:
                LOGGER.error(f"Error adding scheduled download: {e}")
                return False
    
    def get_due_downloads(self) -> List[Dict[str, Any]]:
        """Get all downloads due to run"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM scheduled_downloads
                    WHERE status = 'active' AND next_run <= CURRENT_TIMESTAMP
                """)
                
                rows = cursor.fetchall()
                conn.close()
                return [dict(row) for row in rows]
            except Exception as e:
                LOGGER.error(f"Error getting due downloads: {e}")
                return []
    
    def update_scheduled_status(self, download_id: str, status: str, 
                               next_run: datetime = None, last_run: datetime = None) -> bool:
        """Update scheduled download status"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                updates = ["status = ?", "updated_at = CURRENT_TIMESTAMP"]
                params = [status]
                
                if next_run:
                    updates.append("next_run = ?")
                    params.append(next_run)
                
                if last_run:
                    updates.append("last_run = ?")
                    updates.append("run_count = run_count + 1")
                    params.append(last_run)
                
                params.append(download_id)
                
                query = f"UPDATE scheduled_downloads SET {', '.join(updates)} WHERE id = ?"
                cursor.execute(query, params)
                
                conn.commit()
                conn.close()
                return True
            except Exception as e:
                LOGGER.error(f"Error updating scheduled status: {e}")
                return False
    
    def get_scheduled_downloads(self, status: str = None) -> List[Dict[str, Any]]:
        """Get all scheduled downloads"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                if status:
                    cursor.execute("SELECT * FROM scheduled_downloads WHERE status = ? ORDER BY next_run", (status,))
                else:
                    cursor.execute("SELECT * FROM scheduled_downloads ORDER BY next_run")
                
                rows = cursor.fetchall()
                conn.close()
                return [dict(row) for row in rows]
            except Exception as e:
                LOGGER.error(f"Error getting scheduled downloads: {e}")
                return []
    
    # === Download Templates ===
    
    def add_template(self, template_id: str, name: str, operation: str,
                    destination: str = "", options: Dict = None,
                    url_pattern: str = "", description: str = "") -> bool:
        """Create a download template"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO download_templates
                    (id, name, operation, destination, options, url_pattern, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    template_id,
                    name,
                    operation,
                    destination,
                    json.dumps(options) if options else None,
                    url_pattern,
                    description
                ))
                
                conn.commit()
                conn.close()
                return True
            except Exception as e:
                LOGGER.error(f"Error adding template: {e}")
                return False
    
    def get_templates(self) -> List[Dict[str, Any]]:
        """Get all templates"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM download_templates ORDER BY created_at DESC")
                rows = cursor.fetchall()
                conn.close()
                return [dict(row) for row in rows]
            except Exception as e:
                LOGGER.error(f"Error getting templates: {e}")
                return []
    
    def delete_template(self, template_id: str) -> bool:
        """Delete a template"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM download_templates WHERE id = ?", (template_id,))
                conn.commit()
                conn.close()
                return True
            except Exception as e:
                LOGGER.error(f"Error deleting template: {e}")
                return False
    
    # === Pause/Resume ===
    
    def pause_download(self, download_id: str, reason: str = "") -> bool:
        """Pause a download"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO download_pause_state
                    (download_id, is_paused, paused_at, reason)
                    VALUES (?, 1, CURRENT_TIMESTAMP, ?)
                """, (download_id, reason))
                
                conn.commit()
                conn.close()
                return True
            except Exception as e:
                LOGGER.error(f"Error pausing download: {e}")
                return False
    
    def resume_download(self, download_id: str) -> bool:
        """Resume a download"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO download_pause_state
                    (download_id, is_paused)
                    VALUES (?, 0)
                """, (download_id,))
                
                conn.commit()
                conn.close()
                return True
            except Exception as e:
                LOGGER.error(f"Error resuming download: {e}")
                return False
    
    def is_paused(self, download_id: str) -> bool:
        """Check if download is paused"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute(
                    "SELECT is_paused FROM download_pause_state WHERE download_id = ?",
                    (download_id,)
                )
                row = cursor.fetchone()
                conn.close()
                
                return row['is_paused'] == 1 if row else False
            except Exception as e:
                LOGGER.error(f"Error checking pause state: {e}")
                return False
    
    # === Queue Management ===
    
    def enqueue_download(self, download_id: str, priority: int = 5, url: str = "",
                        operation: str = "") -> bool:
        """Add download to priority queue"""
        try:
            self.priority_queue.add(download_id, priority, url, operation)
            
            # Also persist to DB
            with self.lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO download_queue
                    (id, download_id, priority, status)
                    VALUES (?, ?, ?, 'queued')
                """, (f"queue_{download_id}", download_id, priority))
                
                conn.commit()
                conn.close()
            return True
        except Exception as e:
            LOGGER.error(f"Error enqueueing download: {e}")
            return False
    
    def dequeue_download(self) -> Optional[Dict]:
        """Get next download from queue"""
        item = self.priority_queue.pop()
        if item:
            with self.lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE download_queue SET status = 'started' WHERE download_id = ?",
                    (item['id'],)
                )
                conn.commit()
                conn.close()
        return item
    
    def change_priority(self, download_id: str, new_priority: int) -> bool:
        """Change download priority in queue"""
        try:
            self.priority_queue.set_priority(download_id, new_priority)
            
            with self.lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE download_queue SET priority = ? WHERE download_id = ?",
                    (new_priority, download_id)
                )
                conn.commit()
                conn.close()
            return True
        except Exception as e:
            LOGGER.error(f"Error changing priority: {e}")
            return False
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) as count FROM download_queue WHERE status = 'queued'")
                queued = cursor.fetchone()['count']
                
                cursor.execute("SELECT COUNT(*) as count FROM download_queue WHERE status = 'started'")
                started = cursor.fetchone()['count']
                
                conn.close()
                return {
                    'queued': queued,
                    'in_progress': started,
                    'total_size': self.priority_queue.size()
                }
            except Exception as e:
                LOGGER.error(f"Error getting queue status: {e}")
                return {}
