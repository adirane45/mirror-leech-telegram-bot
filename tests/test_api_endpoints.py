#!/usr/bin/env python3
"""
Phase 1 API Endpoint Testing Suite
Validates all major services and endpoints
"""

import requests
import redis
import json
import time
from pymongo import MongoClient
from urllib.parse import urljoin

class APITester:
    def __init__(self):
        self.app_base_url = "http://localhost:8000"
        self.metrics_base_url = "http://localhost:9090"
        self.prometheus_url = "http://localhost:9091"
        self.grafana_url = "http://localhost:3000"
        self.redis_host = "localhost"
        self.redis_port = 6379
        self.mongo_uri = "mongodb://localhost:27017/"
        self.results = {"passed": [], "failed": [], "warnings": []}
    
    def test_web_endpoint(self):
        """Test bot web interface"""
        try:
            response = requests.get(f"{self.app_base_url}/", timeout=5)
            if response.status_code == 200:
                self.results["passed"].append("✅ Web endpoint (port 8000) - ONLINE")
                return True
            else:
                self.results["failed"].append(f"❌ Web endpoint - Status {response.status_code}")
                return False
        except Exception as e:
            self.results["failed"].append(f"❌ Web endpoint - {str(e)}")
            return False
    
    def test_metrics_endpoint(self):
        """Test metrics endpoint"""
        try:
            response = requests.get(f"{self.metrics_base_url}/metrics", timeout=5)
            if response.status_code == 200:
                lines = response.text.split('\n')
                metric_count = len([l for l in lines if l and not l.startswith('#')])
                self.results["passed"].append(f"✅ Metrics endpoint (port 9090) - {metric_count} metrics")
                return True
            else:
                self.results["failed"].append(f"❌ Metrics endpoint - Status {response.status_code}")
                return False
        except Exception as e:
            self.results["failed"].append(f"❌ Metrics endpoint - {str(e)}")
            return False
    
    def test_prometheus(self):
        """Test Prometheus server"""
        try:
            response = requests.get(f"{self.prometheus_url}/api/v1/query", 
                                   params={"query": "up"}, timeout=5)
            if response.status_code == 200:
                self.results["passed"].append("✅ Prometheus server (port 9091) - ONLINE")
                return True
            else:
                self.results["failed"].append(f"❌ Prometheus - Status {response.status_code}")
                return False
        except Exception as e:
            self.results["failed"].append(f"❌ Prometheus - {str(e)}")
            return False
    
    def test_grafana(self):
        """Test Grafana server"""
        try:
            response = requests.get(f"{self.grafana_url}/api/health", timeout=5)
            if response.status_code in [200, 302]:
                self.results["passed"].append("✅ Grafana (port 3000) - ONLINE")
                return True
            else:
                self.results["failed"].append(f"❌ Grafana - Status {response.status_code}")
                return False
        except Exception as e:
            self.results["failed"].append(f"❌ Grafana - {str(e)}")
            return False
    
    def test_redis_connection(self):
        """Test Redis connectivity"""
        try:
            r = redis.Redis(host=self.redis_host, port=self.redis_port, decode_responses=True)
            pong = r.ping()
            if pong:
                info = r.info()
                mem_used = info.get('used_memory_human', 'N/A')
                self.results["passed"].append(f"✅ Redis (port 6379) - Memory: {mem_used}")
                return True
            else:
                self.results["failed"].append("❌ Redis - No ping response")
                return False
        except Exception as e:
            self.results["failed"].append(f"❌ Redis - {str(e)}")
            return False
    
    def test_mongodb_connection(self):
        """Test MongoDB connectivity"""
        try:
            client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
            client.admin.command('ping')
            self.results["passed"].append("✅ MongoDB (port 27017) - Connected")
            client.close()
            return True
        except Exception as e:
            self.results["failed"].append(f"❌ MongoDB - {str(e)}")
            return False
    
    def test_redis_performance(self):
        """Benchmark Redis performance"""
        try:
            r = redis.Redis(host=self.redis_host, port=self.redis_port, decode_responses=True)
            
            # Throughput test
            start = time.time()
            for i in range(1000):
                r.set(f"bench_key_{i}", f"value_{i}")
            duration = time.time() - start
            ops_per_sec = 1000 / duration
            
            self.results["passed"].append(f"✅ Redis Performance - {ops_per_sec:.0f} ops/sec")
            
            # Cleanup
            for i in range(1000):
                r.delete(f"bench_key_{i}")
            return True
        except Exception as e:
            self.results["failed"].append(f"❌ Redis Performance - {str(e)}")
            return False
    
    def test_metrics_quality(self):
        """Validate metrics data quality"""
        try:
            response = requests.get(f"{self.metrics_base_url}/metrics", timeout=5)
            lines = response.text.split('\n')
            
            # Check for key metrics
            required_metrics = [
                'mltb_downloads_total',
                'mltb_uploads_total',
                'mltb_active_downloads',
                'mltb_active_uploads',
                'mltb_active_tasks',
                'mltb_cpu_usage_percent',
                'mltb_memory_usage_percent'
            ]
            
            found_metrics = set()
            for line in lines:
                for metric in required_metrics:
                    if metric in line and not line.startswith('#'):
                        found_metrics.add(metric)
            
            missing = set(required_metrics) - found_metrics
            if missing:
                self.results["warnings"].append(f"⚠️  Missing metrics: {', '.join(missing)}")
            else:
                self.results["passed"].append(f"✅ Metrics Quality - All {len(required_metrics)} required metrics present")
            return True
        except Exception as e:
            self.results["failed"].append(f"❌ Metrics Quality - {str(e)}")
            return False
    
    def test_prometheus_targets(self):
        """Check Prometheus scrape targets"""
        try:
            response = requests.get(f"{self.prometheus_url}/api/v1/targets", timeout=5)
            if response.status_code == 200:
                data = response.json()
                targets = data.get('data', {}).get('activeTargets', [])
                up = sum(1 for t in targets if t.get('health') == 'up')
                total = len(targets)
                self.results["passed"].append(f"✅ Prometheus Targets - {up}/{total} UP")
                return True
            return False
        except Exception as e:
            self.results["failed"].append(f"❌ Prometheus Targets - {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*60)
        print("🧪 PHASE 1 API ENDPOINT VALIDATION TEST SUITE")
        print("="*60 + "\n")
        
        print("Testing Web Endpoints...")
        self.test_web_endpoint()
        self.test_metrics_endpoint()
        self.test_grafana()
        
        print("Testing Services...")
        self.test_prometheus()
        self.test_redis_connection()
        self.test_mongodb_connection()
        
        print("Testing Performance...")
        self.test_redis_performance()
        self.test_metrics_quality()
        self.test_prometheus_targets()
        
        print("\n" + "="*60)
        print("📊 TEST RESULTS")
        print("="*60 + "\n")
        
        print(f"✅ PASSED: {len(self.results['passed'])}")
        for result in self.results["passed"]:
            print(f"  {result}")
        
        if self.results["warnings"]:
            print(f"\n⚠️  WARNINGS: {len(self.results['warnings'])}")
            for warning in self.results["warnings"]:
                print(f"  {warning}")
        
        if self.results["failed"]:
            print(f"\n❌ FAILED: {len(self.results['failed'])}")
            for result in self.results["failed"]:
                print(f"  {result}")
        
        print("\n" + "="*60)
        success_rate = len(self.results['passed']) / (len(self.results['passed']) + len(self.results['failed'])) * 100
        print(f"✨ SUCCESS RATE: {success_rate:.1f}%")
        print("="*60 + "\n")
        
        return len(self.results['failed']) == 0

if __name__ == "__main__":
    tester = APITester()
    success = tester.run_all_tests()
    exit(0 if success else 1)
