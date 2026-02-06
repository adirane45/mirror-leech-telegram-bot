#!/usr/bin/env python3
"""
Code Health Analysis
Analyzes overall code health metrics including duplication, documentation, and structure
"""

import os
import json
import sys
from pathlib import Path
from typing import Dict, List, Any
import re


class CodeHealthAnalyzer:
    """Analyze overall code health"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.results = {
            'health_score': 0.0,
            'metrics': {
                'documentation': {},
                'structure': {},
                'duplication': {},
                'maintainability': {}
            },
            'recommendations': []
        }
    
    def analyze_documentation(self) -> Dict[str, Any]:
        """Analyze code documentation"""
        total_files = 0
        documented_files = 0
        total_functions = 0
        documented_functions = 0
        
        python_files = list(self.project_root.glob('bot/**/*.py'))
        
        for file_path in python_files:
            if '__pycache__' in str(file_path):
                continue
                
            total_files += 1
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check file-level docstring
                if content.strip().startswith('"""') or content.strip().startswith("'''"):
                    documented_files += 1
                
                # Count functions and their documentation
                func_pattern = r'^\s*(?:async\s+)?def\s+(\w+)\s*\([^)]*\):'
                functions = re.findall(func_pattern, content, re.MULTILINE)
                total_functions += len(functions)
                
                # Count documented functions (have docstring after def)
                doc_pattern = r'(?:async\s+)?def\s+\w+\s*\([^)]*\):\s*(?:\n\s*)?(?:"""|\'\'\')' 
                documented = len(re.findall(doc_pattern, content, re.MULTILINE))
                documented_functions += documented
                
            except Exception as e:
                continue
        
        doc_coverage = (documented_functions / total_functions * 100) if total_functions > 0 else 0
        
        return {
            'total_files': total_files,
            'documented_files': documented_files,
            'file_documentation_rate': round(documented_files / total_files * 100, 2) if total_files > 0 else 0,
            'total_functions': total_functions,
            'documented_functions': documented_functions,
            'function_documentation_rate': round(doc_coverage, 2),
            'score': round((doc_coverage + (documented_files / total_files * 100)) / 2, 2) if total_files > 0 else 0
        }
    
    def analyze_structure(self) -> Dict[str, Any]:
        """Analyze code structure"""
        files_by_size = {'small': 0, 'medium': 0, 'large': 0, 'very_large': 0}
        total_lines = 0
        total_files = 0
        
        python_files = list(self.project_root.glob('bot/**/*.py'))
        
        for file_path in python_files:
            if '__pycache__' in str(file_path):
                continue
            
            total_files += 1
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = len(f.readlines())
                
                total_lines += lines
                
                if lines < 100:
                    files_by_size['small'] += 1
                elif lines < 300:
                    files_by_size['medium'] += 1
                elif lines < 500:
                    files_by_size['large'] += 1
                else:
                    files_by_size['very_large'] += 1
                    
            except Exception:
                continue
        
        # Calculate score (prefer smaller, well-structured files)
        structure_score = 100
        if files_by_size['very_large'] > total_files * 0.2:
            structure_score -= 30
        if files_by_size['large'] > total_files * 0.3:
            structure_score -= 20
        
        return {
            'total_files': total_files,
            'total_lines': total_lines,
            'avg_lines_per_file': round(total_lines / total_files, 2) if total_files > 0 else 0,
            'files_by_size': files_by_size,
            'score': max(structure_score, 0)
        }
    
    def analyze_maintainability(self) -> Dict[str, Any]:
        """Analyze maintainability indicators"""
        # Check for common anti-patterns
        antipatterns = {
            'long_parameter_lists': 0,
            'deep_nesting': 0,
            'global_variables': 0,
            'bare_except': 0
        }
        
        python_files = list(self.project_root.glob('bot/**/*.py'))
        total_files = len([f for f in python_files if '__pycache__' not in str(f)])
        
        for file_path in python_files:
            if '__pycache__' in str(file_path):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Long parameter list (>5 parameters)
                long_params = len(re.findall(r'def\s+\w+\s*\([^)]{60,}\):', content))
                antipatterns['long_parameter_lists'] += long_params
                
                # Bare except
                bare_except = len(re.findall(r'except\s*:', content))
                antipatterns['bare_except'] += bare_except
                
                # Global variables (rough heuristic)
                globals_found = len(re.findall(r'^[A-Z_]{2,}\s*=', content, re.MULTILINE))
                antipatterns['global_variables'] += globals_found
                
            except Exception:
                continue
        
        # Calculate score
        total_antipatterns = sum(antipatterns.values())
        score = max(100 - (total_antipatterns / total_files * 10), 0) if total_files > 0 else 0
        
        return {
            'antipatterns': antipatterns,
            'total_antipatterns': total_antipatterns,
            'antipatterns_per_file': round(total_antipatterns / total_files, 2) if total_files > 0 else 0,
            'score': round(score, 2)
        }
    
    def calculate_health_score(self):
        """Calculate overall health score"""
        doc = self.results['metrics']['documentation']
        structure = self.results['metrics']['structure']
        maintain = self.results['metrics']['maintainability']
        
        # Weighted average
        weights = {'documentation': 0.3, 'structure': 0.3, 'maintainability': 0.4}
        
        health_score = (
            doc['score'] * weights['documentation'] +
            structure['score'] * weights['structure'] +
            maintain['score'] * weights['maintainability']
        )
        
        self.results['health_score'] = round(health_score, 2)
        
        # Generate recommendations
        self._generate_recommendations()
    
    def _generate_recommendations(self):
        """Generate actionable recommendations"""
        recommendations = []
        
        doc = self.results['metrics']['documentation']
        if doc['function_documentation_rate'] < 60:
            recommendations.append({
                'priority': 'High',
                'category': 'Documentation',
                'issue': f"Low function documentation rate: {doc['function_documentation_rate']}%",
                'action': 'Add docstrings to functions, especially in bot/core/ and bot/modules/'
            })
        
        structure = self.results['metrics']['structure']
        if structure['files_by_size']['very_large'] > 5:
            recommendations.append({
                'priority': 'Medium',
                'category': 'Structure',
                'issue': f"{structure['files_by_size']['very_large']} files exceed 500 lines",
                'action': 'Consider splitting large files into smaller, focused modules'
            })
        
        maintain = self.results['metrics']['maintainability']
        if maintain['antipatterns']['bare_except'] > 10:
            recommendations.append({
                'priority': 'High',
                'category': 'Maintainability',
                'issue': f"{maintain['antipatterns']['bare_except']} bare except clauses found",
                'action': 'Replace bare except with specific exception types'
            })
        
        if maintain['antipatterns']['long_parameter_lists'] > 5:
            recommendations.append({
                'priority': 'Medium',
                'category': 'Maintainability',
                'issue': f"{maintain['antipatterns']['long_parameter_lists']} functions with >5 parameters",
                'action': 'Refactor to use configuration objects or keyword arguments'
            })
        
        self.results['recommendations'] = recommendations
    
    def analyze(self):
        """Run all analyses"""
        print("Analyzing documentation...", file=sys.stderr)
        self.results['metrics']['documentation'] = self.analyze_documentation()
        
        print("Analyzing structure...", file=sys.stderr)
        self.results['metrics']['structure'] = self.analyze_structure()
        
        print("Analyzing maintainability...", file=sys.stderr)
        self.results['metrics']['maintainability'] = self.analyze_maintainability()
        
        print("Calculating health score...", file=sys.stderr)
        self.calculate_health_score()
    
    def generate_report(self) -> str:
        """Generate JSON report"""
        return json.dumps(self.results, indent=2)


def main():
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Run analysis
    analyzer = CodeHealthAnalyzer(project_root)
    analyzer.analyze()
    
    # Output report
    print(analyzer.generate_report())
    
    # Print summary to stderr
    print(f"\n💊 Code Health Summary:", file=sys.stderr)
    print(f"   Overall Health Score: {analyzer.results['health_score']}/100", file=sys.stderr)
    
    doc = analyzer.results['metrics']['documentation']
    print(f"\n📚 Documentation:", file=sys.stderr)
    print(f"   Function Documentation: {doc['function_documentation_rate']}%", file=sys.stderr)
    print(f"   File Documentation: {doc['file_documentation_rate']}%", file=sys.stderr)
    
    structure = analyzer.results['metrics']['structure']
    print(f"\n🏗️  Structure:", file=sys.stderr)
    print(f"   Average Lines per File: {structure['avg_lines_per_file']}", file=sys.stderr)
    print(f"   Very Large Files (>500 lines): {structure['files_by_size']['very_large']}", file=sys.stderr)
    
    maintain = analyzer.results['metrics']['maintainability']
    print(f"\n🔧 Maintainability:", file=sys.stderr)
    print(f"   Total Anti-patterns: {maintain['total_antipatterns']}", file=sys.stderr)
    
    if analyzer.results['recommendations']:
        print(f"\n💡 Top Recommendations:", file=sys.stderr)
        for i, rec in enumerate(analyzer.results['recommendations'][:5], 1):
            print(f"   {i}. [{rec['priority']}] {rec['category']}: {rec['issue']}", file=sys.stderr)
            print(f"      → {rec['action']}", file=sys.stderr)


if __name__ == '__main__':
    main()
