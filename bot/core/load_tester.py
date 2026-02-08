"""
Load Testing Framework
Comprehensive performance and stress testing tools

Phase 4: Performance Optimization
Created by: justadi
Date: February 8, 2026
"""

import time
import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class LoadTestResult:
    """Load test execution result"""
    test_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_duration_seconds: float
    requests_per_second: float
    avg_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    p50_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    errors: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


class LoadTester:
    """
    Load testing framework for performance validation
    
    Features:
    - Concurrent request testing
    - Response time measurement
    - Throughput analysis
    - Error rate tracking
    - Statistical analysis (percentiles)
    """
    
    def __init__(self, base_url: str = "http://localhost"):
        self.base_url = base_url
        self.results: List[LoadTestResult] = []
        
        logger.info(f"LoadTester initialized (base_url={base_url})")
    
    async def run_load_test(
        self,
        test_name: str,
        endpoint: str,
        method: str = "GET",
        num_requests: int = 100,
        concurrency: int = 10,
        payload: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> LoadTestResult:
        """
        Run load test against an endpoint
        
        Args:
            test_name: Name of the test
            endpoint: API endpoint to test
            method: HTTP method (GET, POST, etc.)
            num_requests: Total number of requests
            concurrency: Number of concurrent requests
            payload: Request payload for POST/PUT
            headers: Request headers
        """
        logger.info(
            f"Starting load test '{test_name}': {num_requests} requests, "
            f"concurrency={concurrency}"
        )
        
        start_time = time.time()
        response_times: List[float] = []
        successful = 0
        failed = 0
        errors: List[str] = []
        
        # Create request batches
        batches = [num_requests // concurrency] * concurrency
        batches[-1] += num_requests % concurrency
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for batch_size in batches:
                task = self._run_batch(
                    session, endpoint, method, batch_size, payload, headers
                )
                tasks.append(task)
            
            # Execute all batches concurrently
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Aggregate results
            for result in batch_results:
                if isinstance(result, Exception):
                    failed += 1
                    errors.append(str(result))
                else:
                    batch_times, batch_success, batch_failed, batch_errors = result
                    response_times.extend(batch_times)
                    successful += batch_success
                    failed += batch_failed
                    errors.extend(batch_errors)
        
        total_duration = time.time() - start_time
        
        # Calculate statistics
        if response_times:
            sorted_times = sorted(response_times)
            n = len(sorted_times)
            
            result = LoadTestResult(
                test_name=test_name,
                total_requests=num_requests,
                successful_requests=successful,
                failed_requests=failed,
                total_duration_seconds=total_duration,
                requests_per_second=num_requests / total_duration if total_duration > 0 else 0,
                avg_response_time_ms=sum(sorted_times) / n,
                min_response_time_ms=sorted_times[0],
                max_response_time_ms=sorted_times[-1],
                p50_response_time_ms=sorted_times[int(n * 0.50)],
                p95_response_time_ms=sorted_times[int(n * 0.95)],
                p99_response_time_ms=sorted_times[int(n * 0.99)],
                errors=errors[:10]  # Keep only first 10 errors
            )
        else:
            result = LoadTestResult(
                test_name=test_name,
                total_requests=num_requests,
                successful_requests=0,
                failed_requests=num_requests,
                total_duration_seconds=total_duration,
                requests_per_second=0,
                avg_response_time_ms=0,
                min_response_time_ms=0,
                max_response_time_ms=0,
                p50_response_time_ms=0,
                p95_response_time_ms=0,
                p99_response_time_ms=0,
                errors=errors[:10]
            )
        
        self.results.append(result)
        
        logger.info(
            f"Load test '{test_name}' complete: {successful}/{num_requests} successful, "
            f"{result.requests_per_second:.2f} req/s, "
            f"avg={result.avg_response_time_ms:.2f}ms"
        )
        
        return result
    
    async def _run_batch(
        self,
        session: aiohttp.ClientSession,
        endpoint: str,
        method: str,
        num_requests: int,
        payload: Optional[Dict[str, Any]],
        headers: Optional[Dict[str, str]]
    ) -> Tuple[List[float], int, int, List[str]]:
        """Run a batch of requests"""
        response_times: List[float] = []
        successful = 0
        failed = 0
        errors: List[str] = []
        
        url = f"{self.base_url}{endpoint}"
        
        for _ in range(num_requests):
            start = time.time()
            try:
                async with session.request(
                    method,
                    url,
                    json=payload if payload else None,
                    headers=headers
                ) as response:
                    await response.text()
                    
                    if response.status < 400:
                        successful += 1
                        response_time_ms = (time.time() - start) * 1000
                        response_times.append(response_time_ms)
                    else:
                        failed += 1
                        errors.append(f"HTTP {response.status}")
            except Exception as e:
                failed += 1
                errors.append(str(e))
        
        return response_times, successful, failed, errors
    
    async def run_stress_test(
        self,
        test_name: str,
        endpoint: str,
        duration_seconds: int = 60,
        initial_concurrency: int = 10,
        max_concurrency: int = 100,
        ramp_up_seconds: int = 30
    ) -> List[LoadTestResult]:
        """
        Run stress test with gradual concurrency increase
        
        Args:
            test_name: Name of the test
            endpoint: API endpoint to test
            duration_seconds: Total test duration
            initial_concurrency: Starting concurrency level
            max_concurrency: Maximum concurrency level
            ramp_up_seconds: Time to reach max concurrency
        """
        logger.info(
            f"Starting stress test '{test_name}': duration={duration_seconds}s, "
            f"concurrency={initial_concurrency}-{max_concurrency}"
        )
        
        results: List[LoadTestResult] = []
        start_time = time.time()
        
        # Calculate concurrency steps
        num_steps = 5
        concurrency_step = (max_concurrency - initial_concurrency) // num_steps
        time_per_step = ramp_up_seconds / num_steps
        
        for step in range(num_steps + 1):
            if time.time() - start_time >= duration_seconds:
                break
            
            concurrency = min(initial_concurrency + (step * concurrency_step), max_concurrency)
            requests_per_step = concurrency * 10  # 10 requests per concurrent connection
            
            result = await self.run_load_test(
                test_name=f"{test_name}_step{step}",
                endpoint=endpoint,
                num_requests=requests_per_step,
                concurrency=concurrency
            )
            results.append(result)
            
            # Wait between steps
            if step < num_steps:
                await asyncio.sleep(time_per_step)
        
        logger.info(f"Stress test '{test_name}' complete: {len(results)} steps")
        return results
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        if not self.results:
            return {"status": "no_tests_run"}
        
        total_requests = sum(r.total_requests for r in self.results)
        total_successful = sum(r.successful_requests for r in self.results)
        total_failed = sum(r.failed_requests for r in self.results)
        
        return {
            "summary": {
                "total_tests": len(self.results),
                "total_requests": total_requests,
                "successful_requests": total_successful,
                "failed_requests": total_failed,
                "success_rate": round(total_successful / total_requests * 100, 2) if total_requests > 0 else 0
            },
            "tests": [
                {
                    "name": r.test_name,
                    "requests": r.total_requests,
                   "success": r.successful_requests,
                    "failed": r.failed_requests,
                    "rps": round(r.requests_per_second, 2),
                    "avg_ms": round(r.avg_response_time_ms, 2),
                    "p95_ms": round(r.p95_response_time_ms, 2),
                    "p99_ms": round(r.p99_response_time_ms, 2),
                    "timestamp": datetime.fromtimestamp(r.timestamp).isoformat()
                }
                for r in self.results
            ]
        }


# Singleton instance
_load_tester_instance: Optional[LoadTester] = None


def get_load_tester(base_url: str = "http://localhost") -> LoadTester:
    """Get singleton load tester instance"""
    global _load_tester_instance
    if _load_tester_instance is None:
        _load_tester_instance = LoadTester(base_url=base_url)
    return _load_tester_instance
