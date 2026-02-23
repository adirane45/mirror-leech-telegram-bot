"""
Async Database Layer for PostgreSQL

Implements:
- Async connection pooling
- Database schemas
- ORM-style queries
- Connection management
- Migration support
"""

import asyncio
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timezone

try:
    import asyncpg
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False

from .. import LOGGER


@dataclass
class DatabaseConfig:
    """Database configuration"""
    host: str = "localhost"
    port: int = 5432
    database: str = "mltb"
    user: str = "postgres"
    password: str = "postgres"
    min_pool_size: int = 5
    max_pool_size: int = 20
    timeout: int = 30


class AsyncDatabasePool:
    """Async database connection pool"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.pool = None
        self.connected = False
    
    async def connect(self) -> bool:
        """Connect to database"""
        if not ASYNCPG_AVAILABLE:
            LOGGER.warning("asyncpg not available, database features disabled")
            return False
        
        try:
            self.pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password,
                min_size=self.config.min_pool_size,
                max_size=self.config.max_pool_size,
                command_timeout=self.config.timeout,
            )
            
            self.connected = True
            LOGGER.info(f"Connected to PostgreSQL database: {self.config.database}")
            return True
        
        except Exception as e:
            LOGGER.error(f"Failed to connect to database: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from database"""
        try:
            if self.pool:
                await self.pool.close()
            self.connected = False
            LOGGER.info("Disconnected from database")
            return True
        except Exception as e:
            LOGGER.error(f"Failed to disconnect: {e}")
            return False
    
    async def execute(self, query: str, *args) -> Any:
        """Execute a query"""
        if not self.pool:
            return None
        
        try:
            async with self.pool.acquire() as connection:
                return await connection.execute(query, *args)
        except Exception as e:
            LOGGER.error(f"Query execution failed: {e}")
            return None
    
    async def fetch(self, query: str, *args) -> List[Dict]:
        """Fetch query results"""
        if not self.pool:
            return []
        
        try:
            async with self.pool.acquire() as connection:
                rows = await connection.fetch(query, *args)
                return [dict(row) for row in rows]
        except Exception as e:
            LOGGER.error(f"Fetch failed: {e}")
            return []
    
    async def fetchrow(self, query: str, *args) -> Optional[Dict]:
        """Fetch single row"""
        if not self.pool:
            return None
        
        try:
            async with self.pool.acquire() as connection:
                row = await connection.fetchrow(query, *args)
                return dict(row) if row else None
        except Exception as e:
            LOGGER.error(f"Fetchrow failed: {e}")
            return None
    
    async def fetchval(self, query: str, *args) -> Any:
        """Fetch single value"""
        if not self.pool:
            return None
        
        try:
            async with self.pool.acquire() as connection:
                return await connection.fetchval(query, *args)
        except Exception as e:
            LOGGER.error(f"Fetchval failed: {e}")
            return None


class DatabaseModels:
    """Database tables and schemas"""
    
    # Users table
    USERS_TABLE = """
    CREATE TABLE IF NOT EXISTS users (
        user_id BIGINT PRIMARY KEY,
        username VARCHAR(255),
        is_authorized BOOLEAN DEFAULT false,
        is_premium BOOLEAN DEFAULT false,
        total_downloads BIGINT DEFAULT 0,
        total_uploaded_gb DECIMAL(15,2) DEFAULT 0,
        last_seen TIMESTAMP,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );
    
    CREATE INDEX IF NOT EXISTS idx_users_auth ON users(is_authorized);
    CREATE INDEX IF NOT EXISTS idx_users_premium ON users(is_premium);
    """
    
    # Tasks table
    TASKS_TABLE = """
    CREATE TABLE IF NOT EXISTS tasks (
        task_id UUID PRIMARY KEY,
        user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
        download_type VARCHAR(50),
        source_url TEXT,
        status VARCHAR(20) DEFAULT 'running',
        progress_percent DECIMAL(5,2) DEFAULT 0,
        size_bytes BIGINT,
        started_at TIMESTAMP,
        completed_at TIMESTAMP,
        error_message TEXT,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );
    
    CREATE INDEX IF NOT EXISTS idx_tasks_user ON tasks(user_id);
    CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
    CREATE INDEX IF NOT EXISTS idx_tasks_created ON tasks(created_at DESC);
    """
    
    # File index table
    FILE_INDEX_TABLE = """
    CREATE TABLE IF NOT EXISTS file_index (
        file_hash VARCHAR(64) PRIMARY KEY,
        file_size BIGINT,
        file_name TEXT,
        content_type VARCHAR(100),
        metadata JSONB,
        first_seen TIMESTAMP DEFAULT NOW(),
        last_accessed TIMESTAMP,
        cache_hits BIGINT DEFAULT 0,
        created_at TIMESTAMP DEFAULT NOW()
    );
    
    CREATE INDEX IF NOT EXISTS idx_files_name 
        ON file_index USING GIN(to_tsvector('english', file_name));
    CREATE INDEX IF NOT EXISTS idx_files_size ON file_index(file_size);
    """
    
    # Download history table
    DOWNLOAD_HISTORY_TABLE = """
    CREATE TABLE IF NOT EXISTS download_history (
        id SERIAL PRIMARY KEY,
        user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
        task_id UUID REFERENCES tasks(task_id),
        file_name TEXT,
        file_size BIGINT,
        download_time_seconds DECIMAL(10,2),
        status VARCHAR(20),
        created_at TIMESTAMP DEFAULT NOW()
    );
    
    CREATE INDEX IF NOT EXISTS idx_history_user ON download_history(user_id);
    CREATE INDEX IF NOT EXISTS idx_history_created ON download_history(created_at DESC);
    """


class AsyncDatabase:
    """Async database manager"""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self.pool = AsyncDatabasePool(self.config)
    
    async def initialize(self) -> bool:
        """Initialize database"""
        if not await self.pool.connect():
            return False
        
        try:
            # Create tables
            for table_sql in [
                DatabaseModels.USERS_TABLE,
                DatabaseModels.TASKS_TABLE,
                DatabaseModels.FILE_INDEX_TABLE,
                DatabaseModels.DOWNLOAD_HISTORY_TABLE,
            ]:
                await self.pool.execute(table_sql)
            
            LOGGER.info("Database tables initialized successfully")
            return True
        
        except Exception as e:
            LOGGER.error(f"Failed to initialize database: {e}")
            return False
    
    async def close(self) -> None:
        """Close database connection"""
        await self.pool.disconnect()
    
    # User operations
    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        return await self.pool.fetchrow(
            "SELECT * FROM users WHERE user_id = $1",
            user_id
        )
    
    async def create_user(self, user_id: int, username: str) -> bool:
        """Create new user"""
        try:
            await self.pool.execute(
                "INSERT INTO users (user_id, username, created_at, updated_at) VALUES ($1, $2, NOW(), NOW())",
                user_id,
                username
            )
            return True
        except Exception as e:
            LOGGER.error(f"Failed to create user: {e}")
            return False
    
    async def update_user(self, user_id: int, **kwargs) -> bool:
        """Update user attributes"""
        try:
            # Build SET clause
            set_parts = []
            args = []
            idx = 1
            
            for key, value in kwargs.items():
                set_parts.append(f"{key} = ${idx}")
                args.append(value)
                idx += 1
            
            args.append(user_id)
            idx += 1
            
            query = f"""
                UPDATE users 
                SET {', '.join(set_parts)}, updated_at = NOW()
                WHERE user_id = ${idx}
            """
            
            await self.pool.execute(query, *args)
            return True
        
        except Exception as e:
            LOGGER.error(f"Failed to update user: {e}")
            return False
    
    # Task operations
    async def create_task(
        self,
        task_id: str,
        user_id: int,
        download_type: str,
        source_url: str,
        size_bytes: int
    ) -> bool:
        """Create new task"""
        try:
            await self.pool.execute(
                """INSERT INTO tasks 
                   (task_id, user_id, download_type, source_url, size_bytes, started_at)
                   VALUES ($1, $2, $3, $4, $5, NOW())""",
                task_id,
                user_id,
                download_type,
                source_url,
                size_bytes
            )
            return True
        except Exception as e:
            LOGGER.error(f"Failed to create task: {e}")
            return False
    
    async def update_task_progress(
        self,
        task_id: str,
        progress: float,
        status: str = "running"
    ) -> bool:
        """Update task progress"""
        try:
            await self.pool.execute(
                """UPDATE tasks 
                   SET progress_percent = $1, status = $2, updated_at = NOW()
                   WHERE task_id = $3""",
                progress,
                status,
                task_id
            )
            return True
        except Exception as e:
            LOGGER.error(f"Failed to update task progress: {e}")
            return False
    
    async def get_user_tasks(
        self,
        user_id: int,
        limit: int = 50
    ) -> List[Dict]:
        """Get tasks for user"""
        return await self.pool.fetch(
            "SELECT * FROM tasks WHERE user_id = $1 ORDER BY created_at DESC LIMIT $2",
            user_id,
            limit
        )


# Global database instance
database = AsyncDatabase()
