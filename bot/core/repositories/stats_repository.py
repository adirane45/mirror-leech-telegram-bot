"""
Statistics Repository - Handles Redis statistics and monitoring
Focused on gathering server information and metrics
"""

from redis.exceptions import RedisError

from bot import LOGGER
from . import BaseRepository


class StatsRepository(BaseRepository):
    """Manages Redis statistics and monitoring information"""
    
    async def get_stats(self) -> dict:
        """
        Get Redis statistics and server information
        
        Returns:
            Dictionary containing various Redis metrics and info
        """
        if not self.is_enabled:
            return {"enabled": False, "message": "Redis not enabled"}
        
        try:
            info = await self._client.info()
            return {
                "enabled": True,
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "used_memory_peak_human": info.get("used_memory_peak_human", "0B"),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "total_connections_received": info.get("total_connections_received", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0),
                "uptime_in_days": info.get("uptime_in_days", 0),
                "redis_version": info.get("redis_version", "unknown"),
            }
        except RedisError as e:
            self._log_error("GET_STATS", e)
            return {"enabled": True, "error": str(e)}
    
    async def get_memory_stats(self) -> dict:
        """
        Get detailed memory usage statistics
        
        Returns:
            Dictionary with memory-related metrics
        """
        if not self.is_enabled:
            return {"enabled": False}
        
        try:
            info = await self._client.info("memory")
            return {
                "enabled": True,
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "used_memory_rss": info.get("used_memory_rss", 0),
                "used_memory_rss_human": info.get("used_memory_rss_human", "0B"),
                "used_memory_peak": info.get("used_memory_peak", 0),
                "used_memory_peak_human": info.get("used_memory_peak_human", "0B"),
                "mem_fragmentation_ratio": info.get("mem_fragmentation_ratio", 0),
                "mem_fragmentation_bytes": info.get("mem_fragmentation_bytes", 0),
            }
        except RedisError as e:
            self._log_error("GET_MEMORY_STATS", e)
            return {"enabled": True, "error": str(e)}
    
    async def get_client_stats(self) -> dict:
        """
        Get client connection statistics
        
        Returns:
            Dictionary with client-related metrics
        """
        if not self.is_enabled:
            return {"enabled": False}
        
        try:
            info = await self._client.info("clients")
            return {
                "enabled": True,
                "connected_clients": info.get("connected_clients", 0),
                "client_recent_max_input_buffer": info.get("client_recent_max_input_buffer", 0),
                "client_recent_max_output_buffer": info.get("client_recent_max_output_buffer", 0),
                "blocked_clients": info.get("blocked_clients", 0),
            }
        except RedisError as e:
            self._log_error("GET_CLIENT_STATS", e)
            return {"enabled": True, "error": str(e)}
    
    async def get_keyspace_stats(self) -> dict:
        """
        Get keyspace statistics (number of keys per database)
        
        Returns:
            Dictionary with keyspace information
        """
        if not self.is_enabled:
            return {"enabled": False}
        
        try:
            info = await self._client.info("keyspace")
            keyspace = {}
            for key, value in info.items():
                if key.startswith("db"):
                    keyspace[key] = value
            
            return {
                "enabled": True,
                "keyspace": keyspace,
                "total_keys": sum(
                    int(v.split(",")[0].split("=")[1])
                    for v in keyspace.values()
                    if "keys=" in v
                ) if keyspace else 0,
            }
        except RedisError as e:
            self._log_error("GET_KEYSPACE_STATS", e)
            return {"enabled": True, "error": str(e)}
    
    async def get_cache_hit_ratio(self) -> float:
        """
        Get cache hit ratio (0.0 to 1.0)
        
        Returns:
            Hit ratio as a float (0 = no hits, 1 = all hits)
        """
        if not self.is_enabled:
            return 0.0
        
        try:
            info = await self._client.info("stats")
            hits = info.get("keyspace_hits", 0)
            misses = info.get("keyspace_misses", 0)
            
            total = hits + misses
            if total == 0:
                return 0.0
            
            return hits / total
        except RedisError as e:
            self._log_error("GET_CACHE_HIT_RATIO", e)
            return 0.0
    
    async def close(self):
        """Cleanup statistics repository"""
        pass
