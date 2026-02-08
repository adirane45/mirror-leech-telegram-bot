#!/usr/bin/env python3
"""
Performance Baseline Measurement Tool
Establishes baseline metrics for Phase 4 optimization monitoring
"""

import asyncio
import time
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import subprocess

class PerformanceBaseline:
    """Measure and record performance baselines"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.baseline_dir = self.project_root / '.metrics' / 'baselines'
        self.baseline_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.now().isoformat()
        self.results = {
            'timestamp': self.timestamp,
            'tests': {},
            'system': {},
            'database': {},
            'network': {},
            'summary': {}
        }
    
    async def measure_phase4_performance(self) -> Dict[str, Any]:
        """Run Phase 4 performance tests"""
        print("🎯 Measuring Phase 4 Performance Baseline...")
        
        cmd = [
            'python3', '-m', 'pytest',
            'tests/test_phase4_integration.py::TestPhase4Performance',
            '-v', '--tb=short'
        ]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Parse test output
            output = result.stdout + result.stderr
            
            # Extract metrics
            metrics = {
                'cache_performance': self._extract_metric(output, 'cache_performance'),
                'rate_limiter_throughput': self._extract_metric(output, 'rate_limiter_throughput'),
                'test_duration_seconds': self._extract_duration(output),
                'success': 'passed' in output.lower()
            }
            
            return metrics
            
        except Exception as e:
            print(f"❌ Error measuring Phase 4 performance: {e}")
            return {'success': False, 'error': str(e)}
    
    async def measure_system_resources(self) -> Dict[str, Any]:
        """Measure current system resource usage"""
        print("📊 Measuring System Resources...")
        
        metrics = {}
        
        try:
            # CPU usage
            cpu_result = subprocess.run(
                ['top', '-bn1'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            for line in cpu_result.stdout.split('\n'):
                if 'Cpu(s)' in line:
                    metrics['cpu_percent'] = self._parse_top_cpu(line)
                    break
            
            # Memory usage
            mem_result = subprocess.run(
                ['free', '-h'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            lines = mem_result.stdout.split('\n')
            if len(lines) > 1:
                metrics['memory'] = self._parse_free_output(lines)
            
            # Docker stats
            docker_result = subprocess.run(
                ['docker', 'stats', '--no-stream'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            metrics['containers'] = self._parse_docker_stats(docker_result.stdout)
            
        except Exception as e:
            print(f"⚠️  Could not measure all system resources: {e}")
        
        return metrics
    
    async def measure_response_times(self) -> Dict[str, Any]:
        """Measure API response times"""
        print("⚡ Measuring Response Times...")
        
        metrics = {}
        endpoints = [
            ('Health Check', 'http://localhost:8060/health'),
            ('Metrics', 'http://localhost:9090/metrics'),
            ('API', 'http://localhost:8060/api/status'),
        ]
        
        for name, url in endpoints:
            try:
                start = time.time()
                result = subprocess.run(
                    ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', url],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                duration_ms = (time.time() - start) * 1000
                
                metrics[name] = {
                    'response_time_ms': round(duration_ms, 2),
                    'http_status': result.stdout.strip()
                }
            except Exception as e:
                metrics[name] = {'error': str(e)}
        
        return metrics
    
    async def measure_database_performance(self) -> Dict[str, Any]:
        """Measure database performance (if available)"""
        print("🗄️  Measuring Database Performance...")
        
        metrics = {}
        
        try:
            # Check Redis
            redis_result = subprocess.run(
                ['redis-cli', 'info', 'stats'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if redis_result.returncode == 0:
                metrics['redis'] = self._parse_redis_info(redis_result.stdout)
            
        except Exception as e:
            print(f"⚠️  Could not measure database performance: {e}")
        
        return metrics
    
    def _extract_metric(self, output: str, metric_name: str) -> float:
        """Extract metric value from test output"""
        for line in output.split('\n'):
            if metric_name in line:
                # Try to extract number
                parts = line.split()
                for part in parts:
                    try:
                        return float(part)
                    except ValueError:
                        continue
        return 0.0
    
    def _extract_duration(self, output: str) -> float:
        """Extract test duration"""
        for line in output.split('\n'):
            if 'passed' in line and 's' in line:
                # Parse "26 passed in 3.49s"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part.endswith('s'):
                        try:
                            return float(part[:-1])
                        except ValueError:
                            pass
        return 0.0
    
    def _parse_top_cpu(self, line: str) -> Dict[str, float]:
        """Parse CPU line from top"""
        # Format: Cpu(s):  1.0%us,  0.5%sy,  0.0%ni, 98.5%id
        try:
            parts = line.split(',')
            data = {}
            for part in parts:
                if '%us' in part:
                    data['user'] = float(part.split('%')[0].strip())
                elif '%sy' in part:
                    data['system'] = float(part.split('%')[0].strip())
                elif '%id' in part:
                    data['idle'] = float(part.split('%')[0].strip())
            return data
        except:
            return {}
    
    def _parse_free_output(self, lines: List[str]) -> Dict[str, str]:
        """Parse memory info from free command"""
        data = {}
        for line in lines:
            if line.startswith('Mem:'):
                parts = line.split()
                if len(parts) >= 3:
                    data['total'] = parts[1]
                    data['used'] = parts[2]
                    data['free'] = parts[3]
        return data
    
    def _parse_docker_stats(self, output: str) -> List[Dict[str, str]]:
        """Parse docker stats output"""
        containers = []
        lines = output.strip().split('\n')[1:]  # Skip header
        
        for line in lines[:10]:  # Top 10 containers
            parts = line.split()
            if len(parts) >= 6:
                containers.append({
                    'name': parts[0],
                    'cpu': parts[1],
                    'memory': parts[2],
                    'memory_limit': parts[3]
                })
        return containers
    
    def _parse_redis_info(self, output: str) -> Dict[str, Any]:
        """Parse Redis INFO output"""
        data = {}
        for line in output.split('\n'):
            if ':' in line and not line.startswith('#'):
                key, value = line.split(':', 1)
                data[key.strip()] = value.strip()
        return data
    
    async def run_all_measurements(self):
        """Run all baseline measurements"""
        print("\n" + "="*60)
        print("📈 TIER 2.1 - Performance Baseline Establishment")
        print("="*60 + "\n")
        
        # Run measurements
        self.results['tests'] = await self.measure_phase4_performance()
        self.results['system'] = await self.measure_system_resources()
        self.results['network'] = await self.measure_response_times()
        self.results['database'] = await self.measure_database_performance()
        
        # Generate summary
        self._generate_summary()
        
        # Save baseline
        self._save_baseline()
        
        # Print report
        self._print_report()
        
        return self.results
    
    def _generate_summary(self):
        """Generate summary metrics"""
        summary = {
            'baseline_timestamp': self.timestamp,
            'phase4_tests_passed': self.results['tests'].get('success', False),
            'system_okay': self.results['system'].get('cpu_percent', {}).get('idle', 0) > 10,
            'api_healthy': all(
                c.get('http_status') == '200'
                for c in self.results['network'].values()
                if isinstance(c, dict) and 'http_status' in c
            )
        }
        self.results['summary'] = summary
    
    def _save_baseline(self):
        """Save baseline to file"""
        filename = f"baseline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.baseline_dir / filename
        
        try:
            with open(filepath, 'w') as f:
                json.dump(self.results, f, indent=2)
            print(f"\n✅ Baseline saved to: {filepath}")
        except Exception as e:
            print(f"❌ Error saving baseline: {e}")
    
    def _print_report(self):
        """Print formatted report"""
        print("\n" + "="*60)
        print("📊 PERFORMANCE BASELINE REPORT")
        print("="*60)
        
        print("\n🧪 Phase 4 Tests:")
        for key, value in self.results['tests'].items():
            if key != 'success':
                print(f"   {key}: {value}")
        
        print("\n📊 System Resources:")
        if self.results['system'].get('cpu_percent'):
            cpu = self.results['system']['cpu_percent']
            print(f"   CPU: User {cpu.get('user', 0)}% | System {cpu.get('system', 0)}% | Idle {cpu.get('idle', 0)}%")
        
        if self.results['system'].get('memory'):
            mem = self.results['system']['memory']
            print(f"   Memory: {mem.get('used')} / {mem.get('total')} (Free: {mem.get('free')})")
        
        print("\n⚡ Response Times:")
        for name, data in self.results['network'].items():
            if isinstance(data, dict) and 'response_time_ms' in data:
                print(f"   {name}: {data['response_time_ms']}ms ({data.get('http_status', 'N/A')})")
        
        print("\n🗄️  Database:")
        if self.results['database'].get('redis'):
            redis = self.results['database']['redis']
            print(f"   Redis: {redis.get('total_connections_received', 'N/A')} connections")
        
        print("\n✅ Summary:")
        summary = self.results['summary']
        print(f"   Phase 4 Tests: {'✅ Passed' if summary.get('phase4_tests_passed') else '❌ Failed'}")
        print(f"   System Health: {'✅ Good' if summary.get('system_okay') else '⚠️  Monitor'}")
        print(f"   API Health: {'✅ All endpoints up' if summary.get('api_healthy') else '⚠️  Some endpoints down'}")
        
        print("\n" + "="*60)


async def main():
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    baseline = PerformanceBaseline(project_root)
    results = await baseline.run_all_measurements()
    
    # Return success
    sys.exit(0 if results['summary'].get('phase4_tests_passed') else 1)


if __name__ == '__main__':
    asyncio.run(main())
