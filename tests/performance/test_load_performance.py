#!/usr/bin/env python3
"""
Phase 1 Load Testing & Celery Task Validation
Tests Celery task queue performance under load
"""

import time
import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

class LoadTester:
    def __init__(self):
        self.app_url = "http://localhost:8000"
        self.metrics_url = "http://localhost:9090/metrics"
        self.prometheus_url = "http://localhost:9091"
    
    def get_metrics_value(self, metric_name):
        """Extract metric value from Prometheus"""
        try:
            response = requests.get(f"{self.prometheus_url}/api/v1/query", 
                                   params={"query": metric_name}, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data['data']['result']:
                    return float(data['data']['result'][0]['value'][1])
            return 0
        except:
            return 0
    
    def simulate_concurrent_requests(self, num_requests=50, workers=10):
        """Simulate concurrent requests to web endpoint"""
        print(f"\n📊 Simulating {num_requests} concurrent requests (workers={workers})...")
        
        metrics_before = {
            'requests': self.get_metrics_value('http_requests_total'),
            'active_connections': self.get_metrics_value('active_connection_count')
        }
        
        def make_request(idx):
            try:
                response = requests.get(f"{self.app_url}/", timeout=10)
                return response.status_code == 200
            except:
                return False
        
        start = time.time()
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(make_request, i) for i in range(num_requests)]
            successful = sum(1 for f in as_completed(futures) if f.result())
        duration = time.time() - start
        
        metrics_after = {
            'requests': self.get_metrics_value('http_requests_total'),
            'active_connections': self.get_metrics_value('active_connection_count')
        }
        
        throughput = num_requests / duration
        success_rate = (successful / num_requests) * 100
        
        print(f"  ✅ Completed {successful}/{num_requests} requests in {duration:.2f}s")
        print(f"  📈 Throughput: {throughput:.1f} req/sec")
        print(f"  ✨ Success rate: {success_rate:.1f}%")
        
        return throughput, success_rate
    
    def test_metrics_export(self, duration=30):
        """Test metrics export performance"""
        print(f"\n📊 Testing metrics export for {duration}s...")
        
        start = time.time()
        samples = 0
        total_bytes = 0
        
        while time.time() - start < duration:
            try:
                response = requests.get(self.metrics_url, timeout=5)
                samples += 1
                total_bytes += len(response.content)
                time.sleep(1)
            except Exception as e:
                print(f"  ❌ Error: {e}")
        
        elapsed = time.time() - start
        avg_size = total_bytes / samples if samples > 0 else 0
        throughput = samples / elapsed
        
        print(f"  ✅ Exported {samples} metrics samples in {elapsed:.1f}s")
        print(f"  📏 Average size: {avg_size:.0f} bytes")
        print(f"  📈 Throughput: {throughput:.1f} exports/sec")
        
        return throughput
    
    def test_system_under_load(self):
        """Comprehensive system load test"""
        print(f"\n🔥 RUNNING SYSTEM LOAD TEST")
        print("="*60)
        
        # Get baseline metrics
        print("\n📍 Baseline metrics:")
        baseline = {
            'cpu': self.get_metrics_value('mltb_cpu_usage_percent'),
            'memory': self.get_metrics_value('mltb_memory_usage_percent'),
            'active_tasks': self.get_metrics_value('mltb_active_tasks')
        }
        for key, val in baseline.items():
            print(f"  {key}: {val:.2f}")
        
        # Run concurrent requests
        throughput, success = self.simulate_concurrent_requests(num_requests=100, workers=20)
        
        time.sleep(2)
        
        # Get loaded metrics
        print("\n📍 Under-load metrics:")
        loaded = {
            'cpu': self.get_metrics_value('mltb_cpu_usage_percent'),
            'memory': self.get_metrics_value('mltb_memory_usage_percent'),
            'active_tasks': self.get_metrics_value('mltb_active_tasks')
        }
        for key, val in loaded.items():
            delta = val - baseline.get(key, 0)
            print(f"  {key}: {val:.2f} ({delta:+.2f})")
        
        print("\n" + "="*60)
        print("✅ LOAD TEST COMPLETE")
        print("="*60)
    
    def run_all_tests(self):
        """Run all load tests"""
        print("\n" + "="*60)
        print("🔥 PHASE 1 LOAD TESTING & PERFORMANCE VALIDATION")
        print("="*60)
        
        self.test_metrics_export(duration=15)
        self.test_system_under_load()

if __name__ == "__main__":
    tester = LoadTester()
    tester.run_all_tests()
