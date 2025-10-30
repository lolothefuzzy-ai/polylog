#!/usr/bin/env python3
"""
Comprehensive dependency and loose ends audit for Polylog
"""
import sys
import importlib.util
from pathlib import Path
import re

print("=" * 70)
print("POLYLOG BACKEND DEPENDENCY AUDIT")
print("=" * 70)

# 1. Core dependencies
print("\n[1/5] CORE DEPENDENCIES")
print("-" * 70)

core_deps = [
    'PySide6',
    'pyqtgraph',
    'numpy',
    'psutil',
]

missing_core = []
for dep in core_deps:
    spec = importlib.util.find_spec(dep)
    status = "✅" if spec else "❌"
    print(f"{status} {dep}")
    if not spec:
        missing_core.append(dep)

if missing_core:
    print(f"\n⚠️  Missing core dependencies: {', '.join(missing_core)}")
else:
    print("\n✅ All core dependencies present")

# 2. Import statements in code
print("\n[2/5] SCANNING IMPORTS IN CODE")
print("-" * 70)

py_files = list(Path('.').glob('*.py'))
print(f"Found {len(py_files)} Python files")

all_imports = set()
import_errors = []

for py_file in py_files:
    try:
        with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            # Find all imports
            imports = re.findall(r'(?:^|\n)(?:from|import)\s+(\S+)', content)
            for imp in imports:
                # Extract module name
                mod = imp.split('.')[0].strip('()')
                if mod and not mod.startswith('_'):
                    all_imports.add(mod)
    except Exception as e:
        import_errors.append(f"{py_file}: {e}")

print(f"Unique imports found: {len(all_imports)}")
print(f"Import scan errors: {len(import_errors)}")

if import_errors:
    print("\n⚠️  Scan errors:")
    for err in import_errors[:5]:
        print(f"  - {err}")

# 3. External module dependencies (non-stdlib)
print("\n[3/5] EXTERNAL DEPENDENCIES CHECK")
print("-" * 70)

stdlib_modules = {
    'sys', 'os', 'json', 'time', 'math', 'random', 'datetime',
    'typing', 'collections', 'pathlib', 'traceback', 'functools',
    're', 'threading', 'queue', 'copy', 'inspect', 'ast',
}

external_imports = all_imports - stdlib_modules
print(f"External imports needed: {len(external_imports)}")

available = []
missing = []

for ext_imp in sorted(external_imports):
    spec = importlib.util.find_spec(ext_imp)
    if spec:
        available.append(ext_imp)
        print(f"✅ {ext_imp}")
    else:
        missing.append(ext_imp)
        print(f"❌ {ext_imp}")

if missing:
    print(f"\n⚠️  Missing external dependencies: {missing}")
else:
    print("\n✅ All external dependencies available")

# 4. Check for common loose ends
print("\n[4/5] LOOSE ENDS DETECTION")
print("-" * 70)

loose_ends = []

# Check for unconnected signals
for py_file in py_files:
    try:
        with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            # Find signal definitions
            signals = re.findall(r'(\w+)\s*=\s*Signal\(', content)
            
            # Find connections
            connections = re.findall(r'\.connect\(', content)
            emissions = re.findall(r'\.emit\(', content)
            
            if signals and (not connections or not emissions):
                loose_ends.append(f"{py_file}: {len(signals)} signals, {len(connections)} connections")
                
    except Exception as e:
        pass

print("Potential loose ends:")
if loose_ends:
    for item in loose_ends:
        print(f"  - {item}")
else:
    print("  ✅ No obvious loose ends detected")

# 5. Check for TODO/FIXME/XXX
print("\n[5/5] CODE COMMENTS AUDIT")
print("-" * 70)

todos = []
fixmes = []
xxxs = []

for py_file in py_files:
    try:
        with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line_no, line in enumerate(f, 1):
                if 'TODO' in line:
                    todos.append(f"{py_file}:{line_no}")
                if 'FIXME' in line:
                    fixmes.append(f"{py_file}:{line_no}")
                if 'XXX' in line:
                    xxxs.append(f"{py_file}:{line_no}")
    except Exception:
        pass

print(f"TODO comments: {len(todos)}")
print(f"FIXME comments: {len(fixmes)}")
print(f"XXX comments: {len(xxxs)}")

if todos:
    print(f"\n⚠️  TODOs found:")
    for item in todos[:3]:
        print(f"  - {item}")

if fixmes:
    print(f"\n⚠️  FIXMEs found:")
    for item in fixmes[:3]:
        print(f"  - {item}")

# Summary
print("\n" + "=" * 70)
print("AUDIT SUMMARY")
print("=" * 70)

issues = len(missing_core) + len(missing) + len(fixmes) + len(xxxs)

print(f"\nMissing core deps: {len(missing_core)}")
print(f"Missing external deps: {len(missing)}")
print(f"FIXME comments: {len(fixmes)}")
print(f"XXX comments: {len(xxxs)}")
print(f"\nTotal issues: {issues}")

if issues == 0:
    print("\n✅ ALL SYSTEMS GREEN - NO BACKEND ISSUES DETECTED")
    sys.exit(0)
else:
    print(f"\n⚠️  {issues} issue(s) need attention")
    sys.exit(1)
