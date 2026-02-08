"""
Smart Thumbnail Manager - Intelligent thumbnail generation and caching
- Cache thumbnails with TTL (7 days)
- Auto-regenerate if dimensions changed
- Generate sprite sheets for video
- Async processing
- Serve from cache when available

Enhanced by: justadi
Date: February 8, 2026
"""

import hashlib
import asyncio
from typing import Optional, Dict, Tuple, Any
from datetime import datetime, timedelta
from pathlib import Path
import json

from .. import LOGGER


class ThumbnailCache:
    """In-memory + disk cache for thumbnails"""
    
    def __init__(self, cache_dir: str = "data/thumbnails"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache with TTL
        self.memory_cache: Dict[str, Dict] = {}
        self.cache_ttl = timedelta(days=7)
        
        # Metadata file for disk cache
        self.metadata_file = self.cache_dir / ".metadata.json"
        self._load_metadata()
    
    def _load_metadata(self):
        """Load cache metadata from disk"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file) as f:
                    self.metadata = json.load(f)
            except Exception as e:
                LOGGER.warning(f"Failed to load cache metadata: {e}")
                self.metadata = {}
        else:
            self.metadata = {}
    
    def _save_metadata(self):
        """Save cache metadata to disk"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f)
        except Exception as e:
            LOGGER.error(f"Failed to save cache metadata: {e}")
    
    def _get_cache_key(self, file_path: str, dimensions: Optional[Tuple[int, int]] = None) -> str:
        """Generate cache key from file path and dimensions"""
        key = f"{file_path}"
        if dimensions:
            key += f"_{dimensions[0]}x{dimensions[1]}"
        return hashlib.md5(key.encode()).hexdigest()
    
    def get(self, file_path: str, dimensions: Optional[Tuple[int, int]] = None) -> Optional[Path]:
        """
        Get cached thumbnail
        
        Returns:
            Path to cached thumbnail or None if expired/missing
        """
        cache_key = self._get_cache_key(file_path, dimensions)
        
        # Check memory cache first
        if cache_key in self.memory_cache:
            entry = self.memory_cache[cache_key]
            if datetime.now() < entry["expires"]:
                return Path(entry["path"])
            else:
                del self.memory_cache[cache_key]
        
        # Check disk cache
        if cache_key in self.metadata:
            meta = self.metadata[cache_key]
            thumb_path = Path(meta["path"])
            
            if thumb_path.exists():
                # Check expiry
                cached_at = datetime.fromisoformat(meta["cached_at"])
                if datetime.now() - cached_at < self.cache_ttl:
                    # Add to memory cache
                    self.memory_cache[cache_key] = {
                        "path": str(thumb_path),
                        "expires": datetime.now() + self.cache_ttl,
                    }
                    return thumb_path
                else:
                    # Expired, remove
                    try:
                        thumb_path.unlink()
                        del self.metadata[cache_key]
                        self._save_metadata()
                    except Exception as e:
                        LOGGER.warning(f"Failed to delete expired cache: {e}")
        
        return None
    
    def set(self, file_path: str, thumb_path: Path, dimensions: Optional[Tuple[int, int]] = None):
        """
        Cache a thumbnail
        
        Args:
            file_path: Source file path
            thumb_path: Generated thumbnail path
            dimensions: Thumbnail dimensions (width, height)
        """
        cache_key = self._get_cache_key(file_path, dimensions)
        
        # Memory cache
        self.memory_cache[cache_key] = {
            "path": str(thumb_path),
            "expires": datetime.now() + self.cache_ttl,
        }
        
        # Disk metadata
        self.metadata[cache_key] = {
            "source": file_path,
            "path": str(thumb_path),
            "cached_at": datetime.now().isoformat(),
            "dimensions": dimensions,
            "expires_at": (datetime.now() + self.cache_ttl).isoformat(),
        }
        self._save_metadata()
        
        LOGGER.debug(f"💾 Cached thumbnail: {cache_key}")
    
    def invalidate(self, file_path: str):
        """Invalidate all cache entries for a file"""
        keys_to_remove = [
            k for k in self.metadata.keys()
            if self.metadata[k]["source"] == file_path
        ]
        
        for key in keys_to_remove:
            try:
                Path(self.metadata[key]["path"]).unlink()
            except Exception:
                pass
            del self.metadata[key]
            if key in self.memory_cache:
                del self.memory_cache[key]
        
        self._save_metadata()
        
        if keys_to_remove:
            LOGGER.info(f"🗑️  Invalidated {len(keys_to_remove)} cached thumbnails for {file_path}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        memory_items = len(self.memory_cache)
        disk_items = len(self.metadata)
        
        total_size = 0
        for meta in self.metadata.values():
            try:
                total_size += Path(meta["path"]).stat().st_size
            except Exception:
                pass
        
        return {
            "memory_cache_items": memory_items,
            "disk_cache_items": disk_items,
            "total_size_mb": total_size / (1024 * 1024),
            "ttl_days": self.cache_ttl.days,
        }


class SmartThumbnailManager:
    """Singleton smart thumbnail generator with caching"""
    
    _instance: Optional['SmartThumbnailManager'] = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, cache_dir: str = "data/thumbnails"):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.cache = ThumbnailCache(cache_dir)
        self.generation_tasks: Dict[str, asyncio.Task] = {}
        
        LOGGER.info("✅ Smart Thumbnail Manager initialized")
    
    @classmethod
    def get_instance(cls, cache_dir: str = "data/thumbnails") -> 'SmartThumbnailManager':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls(cache_dir)
        return cls._instance
    
    # ==================== THUMBNAIL GENERATION ====================
    
    async def get_thumbnail(
        self,
        file_path: str,
        width: int = 120,
        height: int = 90,
        force_regenerate: bool = False,
    ) -> Optional[Path]:
        """
        Get thumbnail with smart caching
        
        Returns cached version if available, otherwise generates async
        """
        # Check cache first (unless force_regenerate)
        if not force_regenerate:
            cached = self.cache.get(file_path, (width, height))
            if cached:
                LOGGER.debug(f"📷 Using cached thumbnail for {Path(file_path).name}")
                return cached
        
        # Generate (async, non-blocking)
        return await self._generate_or_queue(file_path, width, height)
    
    async def _generate_or_queue(self, file_path: str, width: int, height: int) -> Optional[Path]:
        """
        Generate thumbnail or return queued task
        If already generating, return existing task instead of duplicating work
        """
        task_key = f"{file_path}_{width}x{height}"
        
        # If already generating, wait for existing task
        if task_key in self.generation_tasks:
            LOGGER.debug(f"⏳ Thumbnail already generating: {task_key}")
            try:
                return await self.generation_tasks[task_key]
            except Exception as e:
                LOGGER.error(f"Error retrieving generated thumbnail: {e}")
                return None
        
        # Create new generation task
        task = asyncio.create_task(
            self._generate_thumbnail_async(file_path, width, height)
        )
        self.generation_tasks[task_key] = task
        
        try:
            result = await task
            return result
        finally:
            # Clean up task reference
            if task_key in self.generation_tasks:
                del self.generation_tasks[task_key]
    
    async def _generate_thumbnail_async(self, file_path: str, width: int, height: int) -> Optional[Path]:
        """
        Async thumbnail generation (runs in executor to avoid blocking)
        """
        try:
            loop = asyncio.get_event_loop()
            thumb_path = await loop.run_in_executor(
                None,
                self._generate_thumbnail_sync,
                file_path,
                width,
                height
            )
            
            if thumb_path:
                self.cache.set(file_path, thumb_path, (width, height))
                LOGGER.info(f"📷 Generated thumbnail: {Path(file_path).name} ({width}x{height})")
                return thumb_path
            return None
        except Exception as e:
            LOGGER.error(f"Error generating thumbnail: {e}")
            return None
    
    def _generate_thumbnail_sync(self, file_path: str, width: int, height: int) -> Optional[Path]:
        """Synchronous thumbnail generation (ffmpeg)"""
        try:
            import subprocess
            from pathlib import Path
            
            file_path = Path(file_path)
            if not file_path.exists():
                LOGGER.error(f"File not found: {file_path}")
                return None
            
            # Generate thumbnail filename
            thumb_name = f"{file_path.stem}_{width}x{height}.jpg"
            thumb_path = self.cache.cache_dir / thumb_name
            
            # Use ffmpeg to extract thumbnail
            cmd = [
                "ffmpeg",
                "-i", str(file_path),
                "-ss", "00:00:05",  # 5 seconds in
                "-vframes", "1",
                "-vf", f"scale={width}:{height}",
                "-y",
                str(thumb_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            
            if result.returncode == 0 and thumb_path.exists():
                return thumb_path
            else:
                LOGGER.error(f"ffmpeg failed: {result.stderr.decode()}")
                return None
        except Exception as e:
            LOGGER.error(f"Thumbnail generation failed: {e}")
            return None
    
    # ==================== SPRITE GENERATION ====================
    
    async def generate_video_sprite(
        self,
        file_path: str,
        grid_cols: int = 4,
        thumb_width: int = 120,
        thumb_height: int = 90,
    ) -> Optional[Path]:
        """
        Generate sprite sheet for video preview
        Captures frames at intervals and stitches them together
        """
        cache_key = f"{file_path}_sprite_{grid_cols}x{grid_cols}"
        
        # Check cache
        cached = self.cache.get(file_path, (thumb_width * grid_cols, thumb_height * grid_cols))
        if cached:
            LOGGER.debug(f"🎬 Using cached sprite for {Path(file_path).name}")
            return cached
        
        try:
            loop = asyncio.get_event_loop()
            sprite_path = await loop.run_in_executor(
                None,
                self._generate_sprite_sync,
                file_path,
                grid_cols,
                thumb_width,
                thumb_height
            )
            
            if sprite_path:
                self.cache.set(
                    file_path,
                    sprite_path,
                    (thumb_width * grid_cols, thumb_height * grid_cols)
                )
                LOGGER.info(f"🎬 Generated sprite sheet: {Path(file_path).name}")
                return sprite_path
            return None
        except Exception as e:
            LOGGER.error(f"Sprite generation failed: {e}")
            return None
    
    def _generate_sprite_sync(
        self,
        file_path: str,
        grid_cols: int,
        thumb_w: int,
        thumb_h: int
    ) -> Optional[Path]:
        """Generate sprite sheet (ffmpeg + imagemagick)"""
        try:
            import subprocess
            from pathlib import Path
            
            file_path = Path(file_path)
            sprite_path = self.cache.cache_dir / f"{file_path.stem}_sprite.jpg"
            
            # Generate grid of thumbnails
            cmd = [
                "ffmpeg",
                "-i", str(file_path),
                "-vf", f"fps=1/30,scale={thumb_w}:{thumb_h},tile={grid_cols}x{grid_cols}",
                "-y",
                str(sprite_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=30)
            
            if result.returncode == 0 and sprite_path.exists():
                return sprite_path
            else:
                LOGGER.error(f"Sprite generation failed: {result.stderr.decode()}")
                return None
        except Exception as e:
            LOGGER.error(f"Sprite generation error: {e}")
            return None
    
    # ==================== CACHE MANAGEMENT ====================
    
    async def cleanup_expired(self):
        """Clean up expired cache entries"""
        removed = 0
        
        for cache_key, meta in list(self.cache.metadata.items()):
            try:
                expires_at = datetime.fromisoformat(meta["expires_at"])
                if datetime.now() > expires_at:
                    thumb_path = Path(meta["path"])
                    if thumb_path.exists():
                        thumb_path.unlink()
                    del self.cache.metadata[cache_key]
                    removed += 1
            except Exception as e:
                LOGGER.debug(f"Error cleaning up cache entry: {e}")
        
        if removed > 0:
            self.cache._save_metadata()
            LOGGER.info(f"🧹 Cleaned up {removed} expired thumbnails")
        
        return removed
    
    def invalidate_file(self, file_path: str):
        """Invalidate all thumbnails for a file"""
        self.cache.invalidate(file_path)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return self.cache.get_stats()
    
    # ==================== STATUS ====================
    
    def get_status(self) -> Dict[str, Any]:
        """Get thumbnail manager status"""
        stats = self.cache.get_stats()
        
        return {
            "memory_cache_items": stats["memory_cache_items"],
            "disk_cache_items": stats["disk_cache_items"],
            "cache_size_mb": stats["total_size_mb"],
            "cache_ttl_days": stats["ttl_days"],
            "pending_generations": len(self.generation_tasks),
            "cache_dir": str(self.cache.cache_dir),
        }


# Global instance
thumbnail_manager = SmartThumbnailManager.get_instance()
