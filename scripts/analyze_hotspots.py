#!/usr/bin/env python3
"""
Code Hotspots Analysis
Identifies files with high change frequency and complexity
"""

import os
import json
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict


class HotspotAnalyzer:
    """Analyze code hotspots using git history"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.results = {
            'hotspots': [],
            'summary': {
                'total_commits': 0,
                'most_changed_files': [],
                'coupling_detected': []
            }
        }
    
    def get_git_file_changes(self) -> Dict[str, int]:
        """Get file change counts from git history"""
        try:
            # Run git log to get file change counts
            cmd = ['git', 'log', '--format=', '--name-only', '--diff-filter=ACMR', '--', '*.py']
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"Warning: Git command failed: {result.stderr}", file=sys.stderr)
                return {}
            
            # Count changes per file
            changes = defaultdict(int)
            for line in result.stdout.strip().split('\n'):
                if line and line.endswith('.py'):
                    changes[line] += 1
            
            return dict(changes)
            
        except Exception as e:
            print(f"Warning: Could not analyze git history: {e}", file=sys.stderr)
            return {}
    
    def get_file_complexity(self, file_path: Path) -> int:
        """Get file complexity (simplified - line count for now)"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = len([l for l in f.readlines() if l.strip() and not l.strip().startswith('#')])
            return lines
        except:
            return 0
    
    def analyze_hotspots(self):
        """Identify hotspots (high change + high complexity)"""
        file_changes = self.get_git_file_changes()
        
        if not file_changes:
            print("No git history available. Using static analysis only.", file=sys.stderr)
            return
        
        hotspots = []
        
        for file_path, change_count in file_changes.items():
            full_path = self.project_root / file_path
            
            if not full_path.exists():
                continue
            
            complexity = self.get_file_complexity(full_path)
            
            # Calculate hotspot score
            # Score = (change_frequency * 10) + (complexity / 10)
            score = (change_count * 10) + (complexity / 10)
            
            hotspot = {
                'file': file_path,
                'changes': change_count,
                'complexity': complexity,
                'score': round(score, 2),
                'priority': self._get_priority(score),
                'recommendation': self._get_hotspot_recommendation(change_count, complexity)
            }
            
            hotspots.append(hotspot)
        
        # Sort by score
        hotspots.sort(key=lambda x: x['score'], reverse=True)
        self.results['hotspots'] = hotspots
        
        # Summary
        self.results['summary']['total_commits'] = sum(file_changes.values())
        self.results['summary']['most_changed_files'] = [
            {'file': h['file'], 'changes': h['changes']} 
            for h in hotspots[:10]
        ]
    
    def _get_priority(self, score: float) -> str:
        """Get priority level"""
        if score > 500:
            return "Critical"
        elif score > 300:
            return "High"
        elif score > 100:
            return "Medium"
        else:
            return "Low"
    
    def _get_hotspot_recommendation(self, changes: int, complexity: int) -> str:
        """Get recommendation for hotspot"""
        if changes > 50 and complexity > 300:
            return "Critical: Consider splitting this file - high change rate and complexity"
        elif changes > 30 and complexity > 200:
            return "High: Refactor to reduce complexity and improve stability"
        elif changes > 20:
            return "Medium: Monitor for stability issues"
        else:
            return "Low: Normal change pattern"
    
    def generate_report(self) -> str:
        """Generate JSON report"""
        return json.dumps(self.results, indent=2)


def main():
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Run analysis
    analyzer = HotspotAnalyzer(project_root)
    analyzer.analyze_hotspots()
    
    # Output report
    print(analyzer.generate_report())
    
    # Print summary to stderr
    if analyzer.results['hotspots']:
        print(f"\n🔥 Hotspot Analysis Summary:", file=sys.stderr)
        print(f"   Total Commits Analyzed: {analyzer.results['summary']['total_commits']}", file=sys.stderr)
        print(f"   Hotspots Detected: {len(analyzer.results['hotspots'])}", file=sys.stderr)
        
        print(f"\n🎯 Top 10 Critical Hotspots:", file=sys.stderr)
        for i, hotspot in enumerate(analyzer.results['hotspots'][:10], 1):
            print(f"   {i}. {hotspot['file']}", file=sys.stderr)
            print(f"      Changes: {hotspot['changes']} | Complexity: {hotspot['complexity']} | Score: {hotspot['score']}", file=sys.stderr)
            print(f"      Priority: {hotspot['priority']}", file=sys.stderr)
            print(f"      → {hotspot['recommendation']}", file=sys.stderr)
            print("", file=sys.stderr)


if __name__ == '__main__':
    main()
