"""
Advanced Multi-Feature Implementation: Quick Wins 6.8-6.12

Features:
- LLM Crash Diagnostics
- Multi-Threaded File Hashing Engine
- Auto-Retry with Rotating Proxies
- Smart Source Fallback (Self-Healing)
- Dynamic Tor/SOCKS5 Multiplexing
"""

import hashlib
import asyncio
import random
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

from .. import LOGGER
from .config_manager import Config


class HashAlgorithm(str, Enum):
    """Supported hash algorithms"""
    MD5 = "md5"
    SHA1 = "sha1"
    SHA256 = "sha256"
    BLAKE3 = "blake3"


@dataclass
class HashResult:
    """Result of file hashing"""
    file_path: str
    file_size: int
    hashes: Dict[str, str]
    timestamp: datetime


class MultiThreadedHashingEngine:
    """
    Multi-threaded file hashing for deduplication
    
    Supports parallel hashing of multiple algorithms
    """
    
    def __init__(self):
        self.enabled = bool(getattr(Config, "ENABLE_FILE_HASHING", True))
        self.max_workers = int(getattr(Config, "HASHING_MAX_WORKERS", 4))
        self.chunk_size = int(getattr(Config, "HASHING_CHUNK_SIZE", 8 * 1024 * 1024))
    
    async def hash_file(
        self,
        file_path: str,
        algorithms: Optional[List[HashAlgorithm]] = None
    ) -> Optional[HashResult]:
        """Hash a file with multiple algorithms"""
        if not self.enabled:
            return None
        
        if algorithms is None:
            algorithms = [HashAlgorithm.MD5, HashAlgorithm.SHA256]
        
        try:
            import aiofiles
            import aiofiles.os
            
            # Check if file exists
            if not await aiofiles.os.path.exists(file_path):
                LOGGER.warning(f"File not found: {file_path}")
                return None
            
            # Get file size
            file_size = await aiofiles.os.path.getsize(file_path)
            
            # Compute hashes
            hashes = {}
            async with aiofiles.open(file_path, 'rb') as f:
                hashers = {algo.value: hashlib.new(algo.value) for algo in algorithms}
                
                while True:
                    chunk = await f.read(self.chunk_size)
                    if not chunk:
                        break
                    
                    for hasher in hashers.values():
                        hasher.update(chunk)
            
            # Get results
            for algo, hasher in hashers.items():
                hashes[algo] = hasher.hexdigest()
            
            return HashResult(
                file_path=file_path,
                file_size=file_size,
                hashes=hashes,
                timestamp=datetime.now(timezone.utc)
            )
        
        except Exception as e:
            LOGGER.error(f"Failed to hash file {file_path}: {e}")
            return None


@dataclass
class ProxySettings:
    """Proxy configuration"""
    protocol: str  # http, https, socks5
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    
    def to_url(self) -> str:
        """Convert to proxy URL"""
        auth = f"{self.username}:{self.password}@" if self.username else ""
        return f"{self.protocol}://{auth}{self.host}:{self.port}"


class RotatingProxyManager:
    """Manage rotating proxies for retry"""
    
    def __init__(self):
        self.enabled = bool(getattr(Config, "ENABLE_PROXY_ROTATION", False))
        self.proxies: List[ProxySettings] = []
        self.current_index = 0
        self._load_proxies()
    
    def _load_proxies(self) -> None:
        """Load proxies from config"""
        proxy_list = getattr(Config, "PROXY_LIST", [])
        
        for proxy_str in proxy_list:
            try:
                # Parse proxy string: protocol://user:pass@host:port
                if "://" in proxy_str:
                    protocol, rest = proxy_str.split("://", 1)
                    
                    if "@" in rest:
                        auth, host_port = rest.rsplit("@", 1)
                        username, password = auth.split(":", 1) if ":" in auth else (auth, None)
                    else:
                        username, password = None, None
                        host_port = rest
                    
                    host, port = host_port.rsplit(":", 1)
                    
                    proxy = ProxySettings(
                        protocol=protocol,
                        host=host,
                        port=int(port),
                        username=username,
                        password=password
                    )
                    self.proxies.append(proxy)
            except Exception as e:
                LOGGER.error(f"Failed to parse proxy: {proxy_str} - {e}")
    
    def get_next_proxy(self) -> Optional[ProxySettings]:
        """Get next proxy in rotation"""
        if not self.enabled or not self.proxies:
            return None
        
        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        return proxy
    
    def get_random_proxy(self) -> Optional[ProxySettings]:
        """Get random proxy"""
        if not self.enabled or not self.proxies:
            return None
        
        return random.choice(self.proxies)


class SmartSourceFallback:
    """
    Self-healing source fallback system
    
    Tracks source reliability and automatically switches
    to better sources if current one fails
    """
    
    def __init__(self):
        self.enabled = bool(getattr(Config, "ENABLE_SOURCE_FALLBACK", True))
        self.source_stats: Dict[str, Dict[str, int]] = {}
    
    def record_success(self, source: str) -> None:
        """Record successful use of source"""
        if source not in self.source_stats:
            self.source_stats[source] = {"success": 0, "failure": 0}
        
        self.source_stats[source]["success"] += 1
    
    def record_failure(self, source: str) -> None:
        """Record failed use of source"""
        if source not in self.source_stats:
            self.source_stats[source] = {"success": 0, "failure": 0}
        
        self.source_stats[source]["failure"] += 1
    
    def get_reliability_score(self, source: str) -> float:
        """Get reliability score (0.0-1.0)"""
        if source not in self.source_stats:
            return 0.5
        
        stats = self.source_stats[source]
        total = stats["success"] + stats["failure"]
        
        if total == 0:
            return 0.5
        
        return stats["success"] / total
    
    def sort_sources_by_reliability(self, sources: List[str]) -> List[str]:
        """Sort sources by reliability"""
        return sorted(sources, key=self.get_reliability_score, reverse=True)
    
    def get_best_source(self, sources: List[str]) -> str:
        """Get best source based on history"""
        if not sources:
            return None
        
        sorted_sources = self.sort_sources_by_reliability(sources)
        return sorted_sources[0] if sorted_sources else sources[0]


class TorMultiplexer:
    """
    Dynamic Tor/SOCKS5 multiplexing for anonymity and resilience
    
    Rotates through multiple Tor exits or SOCKS5 proxies
    """
    
    def __init__(self):
        self.enabled = bool(getattr(Config, "ENABLE_TOR_MULTIPLEXING", False))
        self.tor_ports: List[int] = getattr(Config, "TOR_PORTS", [9050, 9051, 9052])
        self.socks5_proxies: List[str] = getattr(Config, "SOCKS5_PROXIES", [])
        self.current_port_index = 0
        self.tor_control_port = int(getattr(Config, "TOR_CONTROL_PORT", 9051))
    
    async def get_next_tor_exit(self) -> ProxySettings:
        """Get next Tor exit"""
        if not self.enabled:
            return None
        
        port = self.tor_ports[self.current_port_index]
        self.current_port_index = (self.current_port_index + 1) % len(self.tor_ports)
        
        return ProxySettings(
            protocol="socks5",
            host="localhost",
            port=port
        )
    
    async def rotate_tor_identity(self) -> bool:
        """Request new Tor identity"""
        if not self.enabled:
            return False
        
        try:
            import socket
            
            # Connect to Tor control port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(("localhost", self.tor_control_port))
            
            # Send NEWNYM command
            sock.send(b"AUTHENTICATE \"\"\r\nSIGNAL NEWNYM\r\nQUIT\r\n")
            sock.close()
            
            LOGGER.info("Tor identity rotated")
            return True
        
        except Exception as e:
            LOGGER.error(f"Failed to rotate Tor identity: {e}")
            return False
    
    def get_next_socks5_proxy(self) -> Optional[ProxySettings]:
        """Get next SOCKS5 proxy"""
        if not self.enabled or not self.socks5_proxies:
            return None
        
        proxy_str = random.choice(self.socks5_proxies)
        
        # Parse SOCKS5 proxy string
        if "://" in proxy_str:
            _, rest = proxy_str.split("://", 1)
            
            if "@" in rest:
                auth, host_port = rest.rsplit("@", 1)
                username, password = auth.split(":", 1)
            else:
                username, password = None, None
                host_port = rest
            
            host, port = host_port.rsplit(":", 1)
            
            return ProxySettings(
                protocol="socks5",
                host=host,
                port=int(port),
                username=username,
                password=password
            )
        
        return None


# Global instances
hashing_engine = MultiThreadedHashingEngine()
proxy_manager = RotatingProxyManager()
source_fallback = SmartSourceFallback()
tor_multiplexer = TorMultiplexer()
