#!/usr/bin/env python3
"""Validate all engine structures and run comprehensive tests"""
import subprocess
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

def run_python_tests():
    """Run Python engine tests"""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    return result.returncode == 0, result.stdout, result.stderr

def run_frontend_tests():
    """Run frontend tests"""
    import shutil
    frontend_dir = PROJECT_ROOT / "src" / "frontend"
    
    # Check if npm exists
    npm_path = shutil.which("npm")
    if not npm_path:
        return False, "", "npm not found in PATH"
    
    # Check if package.json exists
    if not (frontend_dir / "package.json").exists():
        return False, "", "package.json not found"
    
    result = subprocess.run(
        ["npm", "run", "test:all"],
        cwd=frontend_dir,
        capture_output=True,
        text=True,
        timeout=300
    )
    return result.returncode == 0, result.stdout, result.stderr

def validate_engine_imports():
    """Validate all engine modules can be imported"""
    engines = [
        "polylog6.simulation.engine",
        "polylog6.storage.encoder",
        "polylog6.storage.polyform_storage",
        "polylog6.simulation.placement.runtime",
        "polylog6.simulation.stability.calculator",
        "polylog6.api.generator",
    ]
    
    results = {}
    for engine in engines:
        try:
            __import__(engine)
            results[engine] = True
        except Exception as e:
            results[engine] = str(e)
    
    return results

def main():
    print("Validating engine structures...")
    
    # Validate imports
    print("\n1. Validating engine imports...")
    import_results = validate_engine_imports()
    for engine, status in import_results.items():
        if status is True:
            print(f"  [OK] {engine}")
        else:
            print(f"  [FAIL] {engine}: {status}")
    
    # Run Python tests
    print("\n2. Running Python tests...")
    py_ok, py_out, py_err = run_python_tests()
    if py_ok:
        print("  [OK] Python tests passed")
    else:
        print("  [FAIL] Python tests failed")
        print(py_err[:500])
    
    # Run frontend tests
    print("\n3. Running frontend tests...")
    fe_ok, fe_out, fe_err = run_frontend_tests()
    if fe_ok:
        print("  [OK] Frontend tests passed")
    else:
        print("  [FAIL] Frontend tests failed")
        print(fe_err[:500])
    
    # Summary
    all_ok = all(import_results.values()) and py_ok and fe_ok
    print(f"\n{'='*60}")
    if all_ok:
        print("[SUCCESS] All engine validations passed")
        return 0
    else:
        print("[FAILURE] Some validations failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())

