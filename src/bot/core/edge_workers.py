"""
Serverless Edge Workers for Phase 8 Advanced Intelligence

Cloudflare Workers integration for zero-bandwidth proxying and global CDN.
Target: <100ms edge worker latency worldwide.

Features:
- Edge function deployment
- Zero-bandwidth proxying
- Global CDN integration
- Request routing
- Cache optimization
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, List, Any, Callable, Tuple
from enum import Enum
import json

logger = logging.getLogger(__name__)


class EdgeLocation(str, Enum):
    """Edge worker locations worldwide"""
    US_EAST = "us-east"
    US_WEST = "us-west"
    EU_WEST = "eu-west"
    EU_CENTRAL = "eu-central"
    ASIA_SE = "asia-southeast"
    ASIA_NE = "asia-northeast"
    OCEANIA = "oceania"
    SOUTH_AMERICA = "south-america"


@dataclass
class EdgeWorkerConfig:
    """Configuration for edge worker"""
    name: str
    script: str
    routes: List[str]
    locations: List[EdgeLocation]
    environment_vars: Dict[str, str]
    timeout_ms: int = 50000
    memory_mb: int = 128


@dataclass
class EdgeRequest:
    """Incoming request to edge worker"""
    method: str
    url: str
    headers: Dict[str, str]
    body: Optional[str] = None
    client_ip: Optional[str] = None
    location: Optional[EdgeLocation] = None


@dataclass
class EdgeResponse:
    """Response from edge worker"""
    status_code: int
    headers: Dict[str, str]
    body: str
    latency_ms: float
    cache_hit: bool = False


class EdgeWorkerRuntime:
    """
    Edge worker runtime environment.
    
    Simulates Cloudflare Workers runtime with:
    - Request/response handling
    - KV storage access
    - Cache API
    - Fetch API
    """
    
    def __init__(self, worker_config: EdgeWorkerConfig) -> None:
        """
        Initialize edge worker runtime.
        
        Args:
            worker_config: Worker configuration
        """
        self.config = worker_config
        self.kv_store: Dict[str, Any] = {}
        self.cache: Dict[str, Tuple[str, datetime]] = {}  # key -> (data, expiry)
        self.request_count = 0
        self.total_latency_ms = 0.0
        
        logger.info(f"EdgeWorkerRuntime initialized: {worker_config.name}")
    
    async def handle_request(self, request: EdgeRequest) -> EdgeResponse:
        """
        Handle incoming request at edge.
        
        Args:
            request: EdgeRequest to process
            
        Returns:
            EdgeResponse
        """
        import time
        start_time = time.perf_counter()
        
        self.request_count += 1
        
        try:
            # Check cache first
            cache_key = f"{request.method}:{request.url}"
            cached = self._check_cache(cache_key)
            
            if cached:
                latency_ms = (time.perf_counter() - start_time) * 1000
                return EdgeResponse(
                    status_code=200,
                    headers={"content-type": "application/json"},
                    body=cached,
                    latency_ms=latency_ms,
                    cache_hit=True
                )
            
            # Execute worker script (mock)
            response_body = await self._execute_worker(request)
            
            # Cache response
            self._set_cache(cache_key, response_body, ttl=300)
            
            latency_ms = (time.perf_counter() - start_time) * 1000
            self.total_latency_ms += latency_ms
            
            return EdgeResponse(
                status_code=200,
                headers={"content-type": "application/json"},
                body=response_body,
                latency_ms=latency_ms,
                cache_hit=False
            )
            
        except Exception as e:
            logger.error(f"Edge worker error: {e}")
            
            latency_ms = (time.perf_counter() - start_time) * 1000
            
            return EdgeResponse(
                status_code=500,
                headers={"content-type": "application/json"},
                body=json.dumps({"error": str(e)}),
                latency_ms=latency_ms
            )
    
    async def _execute_worker(self, request: EdgeRequest) -> str:
        """Execute worker script (mock implementation)"""
        # Simulate processing delay (edge workers are very fast)
        await asyncio.sleep(0.01)  # 10ms
        
        # Mock response
        response = {
            "processed_at": datetime.now().isoformat(),
            "location": request.location.value if request.location else "unknown",
            "method": request.method,
            "url": request.url
        }
        
        return json.dumps(response)
    
    def _check_cache(self, key: str) -> Optional[str]:
        """Check if key exists in cache and is not expired"""
        if key in self.cache:
            data, expiry = self.cache[key]
            if datetime.now() < expiry:
                return data
            else:
                del self.cache[key]
        return None
    
    def _set_cache(self, key: str, data: str, ttl: int) -> None:
        """Set cache with TTL in seconds"""
        expiry = datetime.now().timestamp() + ttl
        self.cache[key] = (data, datetime.fromtimestamp(expiry))
    
    def get_kv(self, key: str) -> Optional[Any]:
        """Get value from KV store"""
        return self.kv_store.get(key)
    
    def set_kv(self, key: str, value: Any) -> None:
        """Set value in KV store"""
        self.kv_store[key] = value
    
    def get_stats(self) -> Dict[str, Any]:
        """Get runtime statistics"""
        avg_latency = (
            self.total_latency_ms / self.request_count
            if self.request_count > 0 else 0
        )
        
        return {
            "request_count": self.request_count,
            "avg_latency_ms": avg_latency,
            "cache_size": len(self.cache),
            "kv_size": len(self.kv_store)
        }


class EdgeWorkerManager:
    """
    Manager for deploying and managing edge workers.
    
    Handles:
    - Worker deployment
    - Request routing
    - Load balancing
    - Performance monitoring
    """
    
    def __init__(self) -> None:
        """Initialize edge worker manager"""
        self.workers: Dict[str, EdgeWorkerRuntime] = {}
        self.deployment_log: List[Dict[str, Any]] = []
        self.global_stats = {
            "total_requests": 0,
            "total_latency_ms": 0.0,
            "deployments": 0
        }
        
        logger.info("EdgeWorkerManager initialized")
    
    async def deploy_worker(
        self,
        config: EdgeWorkerConfig
    ) -> bool:
        """
        Deploy an edge worker.
        
        Args:
            config: EdgeWorkerConfig
            
        Returns:
            True if deployment successful
        """
        try:
            # Create runtime for each location
            for location in config.locations:
                worker_name = f"{config.name}-{location.value}"
                runtime = EdgeWorkerRuntime(config)
                self.workers[worker_name] = runtime
                
                logger.info(f"Deployed worker: {worker_name}")
            
            # Log deployment
            self.deployment_log.append({
                "name": config.name,
                "locations": [loc.value for loc in config.locations],
                "deployed_at": datetime.now().isoformat(),
                "routes": config.routes
            })
            
            self.global_stats["deployments"] += 1
            
            logger.info(
                f"Worker '{config.name}' deployed to "
                f"{len(config.locations)} locations"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to deploy worker '{config.name}': {e}")
            return False
    
    async def route_request(
        self,
        request: EdgeRequest,
        preferred_location: Optional[EdgeLocation] = None
    ) -> EdgeResponse:
        """
        Route request to appropriate edge worker.
        
        Args:
            request: EdgeRequest to route
            preferred_location: Preferred edge location (closest to client)
            
        Returns:
            EdgeResponse
        """
        # Select worker based on location
        location = preferred_location or EdgeLocation.US_EAST
        request.location = location
        
        # Find worker for this location
        worker = self._select_worker(location)
        
        if not worker:
            # Fallback to any available worker
            if self.workers:
                worker = list(self.workers.values())[0]
            else:
                return EdgeResponse(
                    status_code=503,
                    headers={},
                    body="No workers available",
                    latency_ms=0.0
                )
        
        # Handle request
        response = await worker.handle_request(request)
        
        # Update global stats
        self.global_stats["total_requests"] += 1
        self.global_stats["total_latency_ms"] += response.latency_ms
        
        return response
    
    def _select_worker(self, location: EdgeLocation) -> Optional[EdgeWorkerRuntime]:
        """Select worker for location"""
        # Try exact location match
        for worker_name, worker in self.workers.items():
            if location.value in worker_name:
                return worker
        return None
    
    def get_worker(self, name: str) -> Optional[EdgeWorkerRuntime]:
        """Get worker by name"""
        return self.workers.get(name)
    
    def list_workers(self) -> List[str]:
        """List all deployed workers"""
        return list(self.workers.keys())
    
    def get_global_stats(self) -> Dict[str, Any]:
        """Get global statistics"""
        avg_latency = (
            self.global_stats["total_latency_ms"] /
            self.global_stats["total_requests"]
            if self.global_stats["total_requests"] > 0 else 0
        )
        
        return {
            **self.global_stats,
            "avg_latency_ms": avg_latency,
            "active_workers": len(self.workers),
            "cache_hit_rate": self._calculate_cache_hit_rate()
        }
    
    def _calculate_cache_hit_rate(self) -> float:
        """Calculate overall cache hit rate"""
        # Aggregate from all workers
        total_requests = sum(
            w.request_count for w in self.workers.values()
        )
        
        # Mock calculation (would track actual cache hits)
        return 0.65 if total_requests > 0 else 0.0


class ZeroBandwidthProxy:
    """
    Zero-bandwidth proxy using edge workers.
    
    Proxies requests through edge network, processing and caching
    at the edge to minimize origin bandwidth usage.
    """
    
    def __init__(self, edge_manager: EdgeWorkerManager):
        """
        Initialize zero-bandwidth proxy.
        
        Args:
            edge_manager: EdgeWorkerManager instance
        """
        self.edge_manager = edge_manager
        self.origin_requests = 0
        self.edge_requests = 0
        self.bandwidth_saved_bytes = 0
        
        logger.info("ZeroBandwidthProxy initialized")
    
    async def proxy_request(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        client_location: Optional[EdgeLocation] = None
    ) -> EdgeResponse:
        """
        Proxy request through edge network.
        
        Args:
            url: Target URL
            method: HTTP method
            headers: Request headers
            client_location: Client's geographic location
            
        Returns:
            EdgeResponse
        """
        request = EdgeRequest(
            method=method,
            url=url,
            headers=headers or {},
            location=client_location
        )
        
        # Route to edge worker
        response = await self.edge_manager.route_request(
            request,
            preferred_location=client_location
        )
        
        # Track metrics
        if response.cache_hit:
            self.edge_requests += 1
            # Estimate bandwidth saved (mock: 1MB per cached response)
            self.bandwidth_saved_bytes += 1024 * 1024
        else:
            self.origin_requests += 1
        
        logger.debug(
            f"Proxied {method} {url} -> {response.status_code} "
            f"({response.latency_ms:.2f}ms, cache_hit={response.cache_hit})"
        )
        
        return response
    
    def get_bandwidth_savings(self) -> Dict[str, Any]:
        """Calculate bandwidth savings from edge caching"""
        total_requests = self.origin_requests + self.edge_requests
        cache_efficiency = (
            self.edge_requests / total_requests
            if total_requests > 0 else 0
        )
        
        return {
            "origin_requests": self.origin_requests,
            "edge_requests": self.edge_requests,
            "total_requests": total_requests,
            "cache_efficiency": cache_efficiency,
            "bandwidth_saved_bytes": self.bandwidth_saved_bytes,
            "bandwidth_saved_mb": self.bandwidth_saved_bytes / (1024 * 1024)
        }


class GlobalCDN:
    """
    Global CDN implementation using edge workers.
    
    Features:
    - Content distribution to edge locations
    - Automatic cache invalidation
    - Geographic routing
    - Performance optimization
    """
    
    def __init__(self, edge_manager: EdgeWorkerManager):
        """
        Initialize global CDN.
        
        Args:
            edge_manager: EdgeWorkerManager instance
        """
        self.edge_manager = edge_manager
        self.content_distribution: Dict[str, List[EdgeLocation]] = {}
        self.cache_invalidations = 0
        
        logger.info("GlobalCDN initialized")
    
    async def distribute_content(
        self,
        content_url: str,
        locations: Optional[List[EdgeLocation]] = None
    ) -> bool:
        """
        Distribute content to edge locations.
        
        Args:
            content_url: URL of content to distribute
            locations: Target locations (all if None)
            
        Returns:
            True if successful
        """
        target_locations = locations or list(EdgeLocation)
        
        # Mock distribution
        await asyncio.sleep(0.05)
        
        self.content_distribution[content_url] = target_locations
        
        logger.info(
            f"Distributed {content_url} to {len(target_locations)} locations"
        )
        
        return True
    
    async def invalidate_cache(self, content_url: str) -> None:
        """Invalidate cached content across all edge locations"""
        # Mock invalidation
        await asyncio.sleep(0.02)
        
        self.cache_invalidations += 1
        
        logger.info(f"Invalidated cache for {content_url}")
    
    def get_closest_edge(
        self,
        client_ip: str
    ) -> EdgeLocation:
        """
        Determine closest edge location for client.
        
        Args:
            client_ip: Client IP address
            
        Returns:
            Closest EdgeLocation
        """
        # Mock geolocation (in production, use GeoIP database)
        # For now, return US_EAST as default
        return EdgeLocation.US_EAST
    
    def get_cdn_stats(self) -> Dict[str, Any]:
        """Get CDN statistics"""
        return {
            "distributed_content": len(self.content_distribution),
            "cache_invalidations": self.cache_invalidations,
            "edge_locations": len(list(EdgeLocation)),
            "edge_manager_stats": self.edge_manager.get_global_stats()
        }


# High-level API
async def deploy_edge_function(
    name:str,
    script: str,
    routes: List[str],
    locations: Optional[List[EdgeLocation]] = None
) -> bool:
    """
    Deploy an edge function globally.
    
    Args:
        name: Function name
        script: Worker script code
        routes: URL routes to handle
        locations: Deployment locations (all if None)
        
    Returns:
        True if deployment successful
    """
    manager = EdgeWorkerManager()
    
    config = EdgeWorkerConfig(
        name=name,
        script=script,
        routes=routes,
        locations=locations or list(EdgeLocation),
        environment_vars={}
    )
    
    return await manager.deploy_worker(config)


async def proxy_via_edge(
    url: str,
    client_location: Optional[EdgeLocation] = None
) -> EdgeResponse:
    """
    Proxy a request through edge network.
    
    Args:
        url: Target URL
        client_location: Client's location
        
    Returns:
        EdgeResponse
    """
    manager = EdgeWorkerManager()
    proxy = ZeroBandwidthProxy(manager)
    
    return await proxy.proxy_request(url, client_location=client_location)
