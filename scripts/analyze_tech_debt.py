#!/usr/bin/env python3
"""
Technical Debt Analysis
Identifies and quantifies technical debt in the codebase
"""

import os
import json
import sys
import re
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


class TechnicalDebtAnalyzer:
    """Analyze technical debt indicators"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.results = {
            'total_debt_hours': 0.0,
            'debt_by_category': {},
            'debt_items': [],
            'summary': {}
        }
    
    def find_todos_and_fixmes(self) -> List[Dict[str, Any]]:
        """Find TODO, FIXME, HACK comments"""
        debt_items = []
        patterns = {
            'TODO': r'#\s*TODO:?\s*(.+)',
            'FIXME': r'#\s*FIXME:?\s*(.+)',
            'HACK': r'#\s*HACK:?\s*(.+)',
            'XXX': r'#\s*XXX:?\s*(.+)',
            'BUG': r'#\s*BUG:?\s*(.+)',
        }
        
        python_files = list(self.project_root.glob('**/*.py'))
        
        for file_path in python_files:
            if any(ex in str(file_path) for ex in ['__pycache__', 'venv', 'mltbenv', '.pytest_cache']):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                for line_num, line in enumerate(lines, 1):
                    for category, pattern in patterns.items():
                        match = re.search(pattern, line, re.IGNORECASE)
                        if match:
                            debt_items.append({
                                'file': str(file_path.relative_to(self.project_root)),
                                'line': line_num,
                                'category': category,
                                'description': match.group(1).strip(),
                                'effort_hours': self._estimate_effort(category),
                                'priority': self._get_priority(category)
                            })
            except Exception:
                continue
        
        return debt_items
    
    def find_deprecated_code(self) -> List[Dict[str, Any]]:
        """Find deprecated functions and patterns"""
        debt_items = []
        
        python_files = list(self.project_root.glob('**/*.py'))
        
        for file_path in python_files:
            if any(ex in str(file_path) for ex in ['__pycache__', 'venv', 'mltbenv']):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Look for @deprecated decorator or comments
                deprecated_pattern = r'@deprecated|#\s*deprecated|#\s*obsolete'
                matches = re.finditer(deprecated_pattern, content, re.IGNORECASE)
                
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    debt_items.append({
                        'file': str(file_path.relative_to(self.project_root)),
                        'line': line_num,
                        'category': 'DEPRECATED',
                        'description': 'Deprecated code found',
                        'effort_hours': 2.0,
                        'priority': 'Medium'
                    })
            except Exception:
                continue
        
        return debt_items
    
    def find_code_smells(self) -> List[Dict[str, Any]]:
        """Find common code smells"""
        debt_items = []
        
        python_files = list(self.project_root.glob('**/*.py'))
        
        for file_path in python_files:
            if any(ex in str(file_path) for ex in ['__pycache__', 'venv', 'mltbenv']):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                
                # Long functions (>100 lines)
                func_pattern = r'(?:async\s+)?def\s+(\w+)\s*\('
                functions = list(re.finditer(func_pattern, content))
                
                for i, func_match in enumerate(functions):
                    func_start = content[:func_match.start()].count('\n') + 1
                    func_name = func_match.group(1)
                    
                    # Find next function or end of file
                    if i + 1 < len(functions):
                        func_end = content[:functions[i + 1].start()].count('\n')
                    else:
                        func_end = len(lines)
                    
                    func_length = func_end - func_start
                    
                    if func_length > 100:
                        debt_items.append({
                            'file': str(file_path.relative_to(self.project_root)),
                            'line': func_start,
                            'category': 'CODE_SMELL',
                            'description': f'Long function: {func_name}() ({func_length} lines)',
                            'effort_hours': 4.0,
                            'priority': 'Medium'
                        })
                
                # God objects (classes with too many methods)
                class_pattern = r'class\s+(\w+)'
                for class_match in re.finditer(class_pattern, content):
                    class_name = class_match.group(1)
                    class_start = class_match.start()
                    
                    # Count methods in class (rough)
                    # Find content until next class or end
                    next_class = re.search(r'\nclass\s+\w+', content[class_start + 10:])
                    if next_class:
                        class_content = content[class_start:class_start + 10 + next_class.start()]
                    else:
                        class_content = content[class_start:]
                    
                    method_count = len(re.findall(r'def\s+\w+\s*\(', class_content))
                    
                    if method_count > 20:
                        line_num = content[:class_start].count('\n') + 1
                        debt_items.append({
                            'file': str(file_path.relative_to(self.project_root)),
                            'line': line_num,
                            'category': 'CODE_SMELL',
                            'description': f'God object: {class_name} ({method_count} methods)',
                            'effort_hours': 8.0,
                            'priority': 'High'
                        })
                
            except Exception:
                continue
        
        return debt_items
    
    def _estimate_effort(self, category: str) -> float:
        """Estimate effort in hours"""
        effort_map = {
            'TODO': 2.0,
            'FIXME': 4.0,
            'HACK': 6.0,
            'XXX': 4.0,
            'BUG': 8.0,
        }
        return effort_map.get(category, 2.0)
    
    def _get_priority(self, category: str) -> str:
        """Get priority level"""
        priority_map = {
            'TODO': 'Low',
            'FIXME': 'Medium',
            'HACK': 'High',
            'XXX': 'High',
            'BUG': 'Critical',
        }
        return priority_map.get(category, 'Low')
    
    def analyze(self):
        """Run all debt analyses"""
        print("Finding TODOs and FIXMEs...", file=sys.stderr)
        todos = self.find_todos_and_fixmes()
        
        print("Finding deprecated code...", file=sys.stderr)
        deprecated = self.find_deprecated_code()
        
        print("Finding code smells...", file=sys.stderr)
        smells = self.find_code_smells()
        
        # Combine all debt items
        all_debt = todos + deprecated + smells
        self.results['debt_items'] = sorted(all_debt, key=lambda x: x['effort_hours'], reverse=True)
        
        # Calculate totals
        self.results['total_debt_hours'] = round(sum(item['effort_hours'] for item in all_debt), 2)
        
        # Group by category
        debt_by_cat = {}
        for item in all_debt:
            cat = item['category']
            if cat not in debt_by_cat:
                debt_by_cat[cat] = {'count': 0, 'hours': 0.0}
            debt_by_cat[cat]['count'] += 1
            debt_by_cat[cat]['hours'] += item['effort_hours']
        
        self.results['debt_by_category'] = debt_by_cat
        
        # Summary
        self.results['summary'] = {
            'total_items': len(all_debt),
            'total_hours': self.results['total_debt_hours'],
            'total_days': round(self.results['total_debt_hours'] / 8, 1),
            'critical_items': len([i for i in all_debt if i['priority'] == 'Critical']),
            'high_priority_items': len([i for i in all_debt if i['priority'] == 'High']),
        }
    
    def generate_report(self) -> str:
        """Generate JSON report"""
        return json.dumps(self.results, indent=2)


def main():
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Run analysis
    analyzer = TechnicalDebtAnalyzer(project_root)
    analyzer.analyze()
    
    # Output report
    print(analyzer.generate_report())
    
    # Print summary to stderr
    summary = analyzer.results['summary']
    print(f"\n💳 Technical Debt Summary:", file=sys.stderr)
    print(f"   Total Debt Items: {summary['total_items']}", file=sys.stderr)
    print(f"   Estimated Hours: {summary['total_hours']}", file=sys.stderr)
    print(f"   Estimated Days: {summary['total_days']}", file=sys.stderr)
    print(f"   Critical Items: {summary['critical_items']}", file=sys.stderr)
    print(f"   High Priority Items: {summary['high_priority_items']}", file=sys.stderr)
    
    print(f"\n📊 Debt by Category:", file=sys.stderr)
    for cat, data in sorted(analyzer.results['debt_by_category'].items(), 
                           key=lambda x: x[1]['hours'], reverse=True):
        print(f"   {cat}: {data['count']} items ({data['hours']:.1f} hours)", file=sys.stderr)
    
    if analyzer.results['debt_items']:
        print(f"\n🔴 Top 5 Technical Debt Items:", file=sys.stderr)
        for i, item in enumerate(analyzer.results['debt_items'][:5], 1):
            print(f"   {i}. [{item['priority']}] {item['file']}:{item['line']}", file=sys.stderr)
            print(f"      {item['category']}: {item['description']}", file=sys.stderr)
            print(f"      Estimated effort: {item['effort_hours']} hours", file=sys.stderr)


if __name__ == '__main__':
    main()
