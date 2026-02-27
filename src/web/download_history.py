"""
Download history and analytics database

Tracks:
- All downloads with timestamps
- Status history
- Performance metrics
- User statistics
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
from logging import getLogger
import threading

LOGGER = getLogger(__name__)

DB_PATH = Path("/app/data/download_history.db")


class DownloadHistory:
    """SQLite database for download history and analytics"""
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = Path(db_path) if isinstance(db_path, str) else db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
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
            
            # Downloads table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS downloads (
                    id TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    total_size INTEGER,
                    downloaded_size INTEGER,
                    destination TEXT,
                    error_message TEXT,
                    metadata TEXT
                )
            """)
            
            # Download progress history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS download_progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    download_id TEXT NOT NULL,
                    progress_percent REAL,
                    speed INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(download_id) REFERENCES downloads(id)
                )
            """)
            
            # Statistics table (aggregated)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE DEFAULT CURRENT_DATE,
                    total_downloads INTEGER,
                    successful_downloads INTEGER,
                    failed_downloads INTEGER,
                    total_size_downloaded INTEGER,
                    average_speed INTEGER,
                    operation_type TEXT,
                    UNIQUE(date, operation_type)
                )
            """)
            
            # Create indexes for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_downloads_created 
                ON downloads(created_at)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_downloads_status 
                ON downloads(status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_progress_download 
                ON download_progress(download_id)
            """)
            
            conn.commit()
            conn.close()
    
    def add_download(self, download_id: str, url: str, operation: str, 
                     destination: str = "", metadata: Dict[str, Any] = None) -> bool:
        """Record a new download"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO downloads 
                    (id, url, operation, status, destination, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    download_id,
                    url,
                    operation,
                    "queued",
                    destination,
                    json.dumps(metadata) if metadata else None
                ))
                
                conn.commit()
                conn.close()
                return True
            except Exception as e:
                LOGGER.error(f"Error adding download to history: {e}")
                return False
    
    def update_download_status(self, download_id: str, status: str, 
                               total_size: int = None, error: str = None) -> bool:
        """Update download status"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                updates = ["status = ?"]
                params = [status]
                
                if status == "downloading" and total_size:
                    updates.append("started_at = CURRENT_TIMESTAMP")
                    updates.append("total_size = ?")
                    params.append(total_size)
                
                if status == "completed":
                    updates.append("completed_at = CURRENT_TIMESTAMP")
                
                if error:
                    updates.append("error_message = ?")
                    params.append(error)
                
                params.append(download_id)
                
                query = f"""
                    UPDATE downloads 
                    SET {", ".join(updates)}
                    WHERE id = ?
                """
                
                cursor.execute(query, params)
                conn.commit()
                conn.close()
                return True
            except Exception as e:
                LOGGER.error(f"Error updating download status: {e}")
                return False
    
    def record_progress(self, download_id: str, progress_percent: float, speed: int) -> bool:
        """Record download progress"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO download_progress 
                    (download_id, progress_percent, speed)
                    VALUES (?, ?, ?)
                """, (download_id, progress_percent, speed))
                
                conn.commit()
                conn.close()
                return True
            except Exception as e:
                LOGGER.error(f"Error recording progress: {e}")
                return False
    
    def get_download_history(self, limit: int = 100, operation: str = None) -> List[Dict[str, Any]]:
        """Get download history"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                query = "SELECT * FROM downloads"
                params = []
                
                if operation:
                    query += " WHERE operation = ?"
                    params.append(operation)
                
                query += " ORDER BY created_at DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                conn.close()
                
                return [dict(row) for row in rows]
            except Exception as e:
                LOGGER.error(f"Error getting download history: {e}")
                return []
    
    def get_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get download statistics"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                # Overall stats
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful,
                        SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as failed,
                        SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled,
                        SUM(total_size) as total_size,
                        AVG(CASE WHEN started_at IS NOT NULL AND completed_at IS NOT NULL 
                            THEN (julianday(completed_at) - julianday(started_at)) * 86400 
                            ELSE NULL END) as avg_duration_seconds
                    FROM downloads
                    WHERE created_at > datetime('now', '-' || ? || ' days')
                """, (days,))
                
                overall_stats = dict(cursor.fetchone() or {})
                
                # Stats by operation
                cursor.execute("""
                    SELECT 
                        operation,
                        COUNT(*) as count,
                        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful,
                        SUM(total_size) as total_size
                    FROM downloads
                    WHERE created_at > datetime('now', '-' || ? || ' days')
                    GROUP BY operation
                """, (days,))
                
                operation_stats = [dict(row) for row in cursor.fetchall()]
                
                # Daily stats
                cursor.execute("""
                    SELECT 
                        DATE(created_at) as date,
                        COUNT(*) as downloads,
                        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful,
                        SUM(total_size) as total_size
                    FROM downloads
                    WHERE created_at > datetime('now', '-' || ? || ' days')
                    GROUP BY DATE(created_at)
                    ORDER BY date DESC
                """, (days,))
                
                daily_stats = [dict(row) for row in cursor.fetchall()]
                
                conn.close()
                
                return {
                    "overall": overall_stats,
                    "by_operation": operation_stats,
                    "daily": daily_stats,
                    "period_days": days
                }
            except Exception as e:
                LOGGER.error(f"Error getting statistics: {e}")
                return {}
    
    def get_top_downloads(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get largest downloads"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, url, operation, status, total_size, created_at
                    FROM downloads
                    WHERE total_size IS NOT NULL
                    ORDER BY total_size DESC
                    LIMIT ?
                """, (limit,))
                
                rows = cursor.fetchall()
                conn.close()
                
                return [dict(row) for row in rows]
            except Exception as e:
                LOGGER.error(f"Error getting top downloads: {e}")
                return []
    
    def get_success_rate(self, days: int = 30) -> Dict[str, Any]:
        """Calculate success rate"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        operation,
                        COUNT(*) as total,
                        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful
                    FROM downloads
                    WHERE created_at > datetime('now', '-' || ? || ' days')
                    GROUP BY operation
                """, (days,))
                
                results = []
                for row in cursor.fetchall():
                    row_dict = dict(row)
                    row_dict['success_rate'] = (
                        row_dict['successful'] / row_dict['total'] * 100 
                        if row_dict['total'] > 0 else 0
                    )
                    results.append(row_dict)
                
                conn.close()
                return {"by_operation": results, "period_days": days}
            except Exception as e:
                LOGGER.error(f"Error calculating success rate: {e}")
                return {}
    
    def cleanup_old_records(self, days: int = 90) -> int:
        """Delete records older than specified days"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                # Delete progress records
                cursor.execute("""
                    DELETE FROM download_progress
                    WHERE download_id IN (
                        SELECT id FROM downloads
                        WHERE created_at < datetime('now', '-' || ? || ' days')
                    )
                """, (days,))
                
                # Delete downloads
                cursor.execute("""
                    DELETE FROM downloads
                    WHERE created_at < datetime('now', '-' || ? || ' days')
                """, (days,))
                
                deleted = cursor.rowcount
                conn.commit()
                conn.close()
                
                LOGGER.info(f"Cleaned up {deleted} old records")
                return deleted
            except Exception as e:
                LOGGER.error(f"Error cleaning up records: {e}")
                return 0


# Global instance
history_db = DownloadHistory()
