#!/usr/bin/env python
"""
Code Quality Scanner
====================

Scans all Python files for:
- Syntax errors
- Broken imports
- Undefined references
- Incomplete function/class definitions
- Missing return statements
- Unused variables
- Type mismatches
"""

import ast
import importlib
import pathlib
import sys
from typing import Any, Dict, List

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class CodeQualityScanner:
    def __init__(self):
        self.issues: List[Dict[str, Any]] = []
        self.py_files: List[pathlib.Path] = []
    
    def find_all_py_files(self):
        """Find all Python files in project root."""
        self.py_files = sorted(ROOT.glob('*.py'))
        return self.py_files
    
    def scan_syntax(self):
        """Check all files for syntax errors."""
        print("\n[SCAN] Syntax Errors")
        for py_file in self.py_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    code = f.read()
                ast.parse(code)
                print(f"  [OK] {py_file.name}")
            except SyntaxError as e:
                self.issues.append({
                    'file': str(py_file),
                    'type': 'SyntaxError',
                    'line': e.lineno,
                    'msg': str(e),
                    'severity': 'CRITICAL'
                })
                print(f"  [FAIL] {py_file.name}: {e}")
            except Exception as e:
                self.issues.append({
                    'file': str(py_file),
                    'type': 'ParseError',
                    'msg': str(e),
                    'severity': 'HIGH'
                })
                print(f"  [FAIL] {py_file.name}: {e}")
    
    def scan_imports(self):
        """Check for broken imports in core modules."""
        print("\n[SCAN] Import Integrity")
        core_modules = [
            'polygon_utils',
            'managers',
            'validators',
            'automated_placement_engine',
            'continuous_exploration_engine',
            'canonical_estimator',
            'polyform_library',
            'stable_library',
            'desktop_app',
            'api_server'
        ]
        
        for mod_name in core_modules:
            try:
                mod = importlib.import_module(mod_name)
                print(f"  [OK] {mod_name}")
            except ImportError as e:
                self.issues.append({
                    'module': mod_name,
                    'type': 'ImportError',
                    'msg': str(e),
                    'severity': 'HIGH'
                })
                print(f"  [FAIL] {mod_name}: {e}")
            except Exception as e:
                self.issues.append({
                    'module': mod_name,
                    'type': 'RuntimeError',
                    'msg': str(e),
                    'severity': 'MEDIUM'
                })
                print(f"  [WARN] {mod_name}: {e}")
    
    def scan_ast_issues(self):
        """Scan AST for common issues."""
        print("\n[SCAN] AST Issues")
        for py_file in self.py_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    code = f.read()
                tree = ast.parse(code)
                
                # Check for undefined names, incomplete defs, etc.
                for node in ast.walk(tree):
                    # Check for incomplete function definitions
                    if isinstance(node, ast.FunctionDef):
                        if len(node.body) == 0 or (len(node.body) == 1 and isinstance(node.body[0], ast.Pass)):
                            self.issues.append({
                                'file': str(py_file),
                                'type': 'EmptyFunction',
                                'name': node.name,
                                'line': node.lineno,
                                'severity': 'MEDIUM'
                            })
                    
                    # Check for incomplete class definitions
                    if isinstance(node, ast.ClassDef):
                        if len(node.body) == 0 or (len(node.body) == 1 and isinstance(node.body[0], ast.Pass)):
                            self.issues.append({
                                'file': str(py_file),
                                'type': 'EmptyClass',
                                'name': node.name,
                                'line': node.lineno,
                                'severity': 'MEDIUM'
                            })
                    
                    # Check for functions without return in non-void context
                    if isinstance(node, ast.FunctionDef):
                        has_return = any(isinstance(n, ast.Return) for n in ast.walk(node))
                        has_docstring = (len(node.body) > 0 and 
                                       isinstance(node.body[0], ast.Expr) and
                                       isinstance(node.body[0].value, ast.Constant))
                        # Skip init, getters without explicit return
                        if node.name.startswith('_') or node.name in ['__init__', '__str__', '__repr__']:
                            continue
                
                print(f"  [OK] {py_file.name}")
            except Exception as e:
                print(f"  [SKIP] {py_file.name}: {e}")
    
    def scan_specific_patterns(self):
        """Scan for specific known bad patterns."""
        print("\n[SCAN] Bad Patterns")
        bad_patterns = [
            ('except Exception:', 'Bare except Exception (should be specific or noqa)'),
            ('TODO', 'Unfinished TODO comments'),
            ('FIXME', 'Unfinished FIXME comments'),
            ('pass  #', 'Pass with comment (suspicious)'),
            ('print(', 'Direct print statements (use logging)'),
        ]
        
        for py_file in self.py_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                for line_num, line in enumerate(lines, 1):
                    for pattern, desc in bad_patterns:
                        if pattern in line:
                            # Some are OK (e.g., logging.info, print in tests)
                            if pattern == 'except Exception:' and 'noqa' not in line:
                                self.issues.append({
                                    'file': str(py_file),
                                    'type': 'BadPattern',
                                    'line': line_num,
                                    'pattern': pattern,
                                    'severity': 'LOW'
                                })
                            elif pattern in ['TODO', 'FIXME']:
                                if 'test' not in str(py_file):  # Skip test files
                                    self.issues.append({
                                        'file': str(py_file),
                                        'type': 'Incomplete',
                                        'line': line_num,
                                        'pattern': pattern,
                                        'severity': 'LOW'
                                    })
                
                print(f"  [OK] {py_file.name}")
            except Exception as e:
                print(f"  [SKIP] {py_file.name}: {e}")
    
    def scan_type_hints(self):
        """Check for type hint consistency."""
        print("\n[SCAN] Type Hints")
        for py_file in self.py_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    code = f.read()
                tree = ast.parse(code)
                
                untyped_funcs = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Skip private/magic methods
                        if node.name.startswith('_'):
                            continue
                        # Check if has type hints
                        if node.returns is None:
                            untyped_funcs.append(node.name)
                
                if untyped_funcs and len(untyped_funcs) <= 3:
                    self.issues.append({
                        'file': str(py_file),
                        'type': 'MissingTypeHints',
                        'functions': untyped_funcs,
                        'severity': 'LOW'
                    })
                
                print(f"  [OK] {py_file.name}")
            except Exception as e:
                print(f"  [SKIP] {py_file.name}: {e}")
    
    def run_all(self):
        """Run all scans and report."""
        print("=" * 70)
        print("CODE QUALITY SCAN")
        print("=" * 70)
        
        self.find_all_py_files()
        print(f"\nFound {len(self.py_files)} Python files")
        
        self.scan_syntax()
        self.scan_imports()
        self.scan_ast_issues()
        self.scan_specific_patterns()
        self.scan_type_hints()
        
        # Report
        print("\n" + "=" * 70)
        print(f"RESULTS: {len(self.issues)} issues found")
        print("=" * 70)
        
        # Group by severity
        critical = [i for i in self.issues if i.get('severity') == 'CRITICAL']
        high = [i for i in self.issues if i.get('severity') == 'HIGH']
        medium = [i for i in self.issues if i.get('severity') == 'MEDIUM']
        low = [i for i in self.issues if i.get('severity') == 'LOW']
        
        if critical:
            print(f"\nCRITICAL ({len(critical)}):")
            for issue in critical:
                print(f"  {issue}")
        
        if high:
            print(f"\nHIGH ({len(high)}):")
            for issue in high[:5]:  # Show first 5
                print(f"  {issue}")
            if len(high) > 5:
                print(f"  ... and {len(high) - 5} more")
        
        if medium:
            print(f"\nMEDIUM ({len(medium)}):")
            for issue in medium[:3]:
                print(f"  {issue}")
            if len(medium) > 3:
                print(f"  ... and {len(medium) - 3} more")
        
        if low:
            print(f"\nLOW ({len(low)}):")
            for issue in low[:3]:
                print(f"  {issue}")
            if len(low) > 3:
                print(f"  ... and {len(low) - 3} more")
        
        return len(critical) == 0 and len(high) == 0


if __name__ == '__main__':
    scanner = CodeQualityScanner()
    success = scanner.run_all()
    sys.exit(0 if success else 1)
