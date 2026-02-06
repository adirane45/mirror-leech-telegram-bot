#!/usr/bin/env python3
"""
Code Complexity Analysis
Analyzes cognitive complexity, cyclomatic complexity, and code metrics
"""

import os
import json
import ast
import sys
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict
import re


class ComplexityAnalyzer:
    """Analyze code complexity metrics"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.results = {
            'files': [],
            'summary': {
                'total_files': 0,
                'total_functions': 0,
                'high_complexity_count': 0,
                'avg_complexity': 0.0,
                'max_complexity': 0
            },
            'hotspots': []
        }
    
    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a single Python file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content)
            
            file_info = {
                'path': str(file_path.relative_to(self.project_root)),
                'lines': len(content.split('\n')),
                'functions': [],
                'classes': [],
                'complexity_score': 0
            }
            
            # Analyze functions and classes
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_info = self._analyze_function(node, content)
                    file_info['functions'].append(func_info)
                    file_info['complexity_score'] += func_info['complexity']
                
                elif isinstance(node, ast.ClassDef):
                    class_info = {
                        'name': node.name,
                        'methods': len([n for n in node.body if isinstance(n, ast.FunctionDef)]),
                        'lines': self._count_lines(node)
                    }
                    file_info['classes'].append(class_info)
            
            # Calculate average complexity
            if file_info['functions']:
                file_info['avg_complexity'] = file_info['complexity_score'] / len(file_info['functions'])
            
            return file_info
            
        except Exception as e:
            return {
                'path': str(file_path.relative_to(self.project_root)),
                'error': str(e)
            }
    
    def _analyze_function(self, node: ast.FunctionDef, content: str) -> Dict[str, Any]:
        """Analyze a single function"""
        complexity = self._calculate_complexity(node)
        
        return {
            'name': node.name,
            'line': node.lineno,
            'lines': self._count_lines(node),
            'complexity': complexity,
            'parameters': len(node.args.args),
            'returns': self._has_return(node),
            'is_async': isinstance(node, ast.AsyncFunctionDef),
            'rating': self._rate_complexity(complexity)
        }
    
    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            # Decision points
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            # Boolean operations
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            # Comprehensions
            elif isinstance(child, (ast.ListComp, ast.DictComp, ast.SetComp)):
                complexity += 1
        
        return complexity
    
    def _count_lines(self, node: ast.AST) -> int:
        """Count lines of code in a node"""
        if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
            return node.end_lineno - node.lineno + 1
        return 0
    
    def _has_return(self, node: ast.FunctionDef) -> bool:
        """Check if function has return statement"""
        for child in ast.walk(node):
            if isinstance(child, ast.Return) and child.value is not None:
                return True
        return False
    
    def _rate_complexity(self, complexity: int) -> str:
        """Rate complexity level"""
        if complexity <= 5:
            return "Low"
        elif complexity <= 10:
            return "Medium"
        elif complexity <= 20:
            return "High"
        else:
            return "Very High"
    
    def analyze_project(self):
        """Analyze entire project"""
        # Find all Python files
        python_files = []
        for pattern in ['bot/**/*.py', 'tests/**/*.py', 'scripts/**/*.py', 'integrations/**/*.py']:
            python_files.extend(self.project_root.glob(pattern))
        
        # Exclude certain patterns
        excluded = {'__pycache__', 'venv', 'mltbenv', '.pytest_cache', 'node_modules'}
        python_files = [f for f in python_files if not any(ex in str(f) for ex in excluded)]
        
        print(f"Analyzing {len(python_files)} Python files...", file=sys.stderr)
        
        for file_path in python_files:
            file_info = self.analyze_file(file_path)
            if 'error' not in file_info:
                self.results['files'].append(file_info)
        
        # Calculate summary
        self._calculate_summary()
        
        # Identify hotspots
        self._identify_hotspots()
    
    def _calculate_summary(self):
        """Calculate summary statistics"""
        total_complexity = 0
        total_functions = 0
        high_complexity_count = 0
        max_complexity = 0
        
        for file_info in self.results['files']:
            for func in file_info['functions']:
                total_functions += 1
                total_complexity += func['complexity']
                max_complexity = max(max_complexity, func['complexity'])
                
                if func['complexity'] > 15:
                    high_complexity_count += 1
        
        self.results['summary'] = {
            'total_files': len(self.results['files']),
            'total_functions': total_functions,
            'high_complexity_count': high_complexity_count,
            'avg_complexity': round(total_complexity / total_functions, 2) if total_functions > 0 else 0,
            'max_complexity': max_complexity
        }
    
    def _identify_hotspots(self):
        """Identify complexity hotspots"""
        hotspots = []
        
        for file_info in self.results['files']:
            for func in file_info['functions']:
                if func['complexity'] > 15:
                    hotspots.append({
                        'file': file_info['path'],
                        'function': func['name'],
                        'line': func['line'],
                        'complexity': func['complexity'],
                        'rating': func['rating'],
                        'recommendation': self._get_recommendation(func)
                    })
        
        # Sort by complexity
        hotspots.sort(key=lambda x: x['complexity'], reverse=True)
        self.results['hotspots'] = hotspots[:20]  # Top 20
    
    def _get_recommendation(self, func: Dict[str, Any]) -> str:
        """Get refactoring recommendation"""
        if func['complexity'] > 25:
            return "Urgent: Split into smaller functions"
        elif func['complexity'] > 20:
            return "High priority: Refactor to reduce complexity"
        elif func['complexity'] > 15:
            return "Medium priority: Consider simplification"
        else:
            return "Review for potential improvements"
    
    def generate_report(self) -> str:
        """Generate JSON report"""
        return json.dumps(self.results, indent=2)


def main():
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Run analysis
    analyzer = ComplexityAnalyzer(project_root)
    analyzer.analyze_project()
    
    # Output report
    print(analyzer.generate_report())
    
    # Print summary to stderr
    summary = analyzer.results['summary']
    print(f"\n📊 Complexity Analysis Summary:", file=sys.stderr)
    print(f"   Total Files: {summary['total_files']}", file=sys.stderr)
    print(f"   Total Functions: {summary['total_functions']}", file=sys.stderr)
    print(f"   Average Complexity: {summary['avg_complexity']}", file=sys.stderr)
    print(f"   Max Complexity: {summary['max_complexity']}", file=sys.stderr)
    print(f"   High Complexity Functions: {summary['high_complexity_count']}", file=sys.stderr)
    
    if analyzer.results['hotspots']:
        print(f"\n🔥 Top 5 Complexity Hotspots:", file=sys.stderr)
        for i, hotspot in enumerate(analyzer.results['hotspots'][:5], 1):
            print(f"   {i}. {hotspot['file']}:{hotspot['line']} - {hotspot['function']}()", file=sys.stderr)
            print(f"      Complexity: {hotspot['complexity']} ({hotspot['rating']})", file=sys.stderr)
            print(f"      → {hotspot['recommendation']}", file=sys.stderr)


if __name__ == '__main__':
    main()
