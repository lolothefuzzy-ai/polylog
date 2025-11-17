#!/usr/bin/env python3
"""Automated testing runner - runs tests continuously and reports results"""
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
FRONTEND_DIR = PROJECT_ROOT / "src" / "frontend"

def run_tests():
    """Run all tests and return success status"""
    results = {}
    
    # Frontend tests
    try:
        result = subprocess.run(
            ["npm", "run", "test:all"],
            cwd=FRONTEND_DIR,
            capture_output=True,
            text=True,
            timeout=300
        )
        results["frontend"] = result.returncode == 0
    except:
        results["frontend"] = False
    
    # Python tests
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-v"],
            capture_output=True,
            text=True,
            timeout=300
        )
        results["backend"] = result.returncode == 0
    except:
        results["backend"] = False
    
    return results

if __name__ == "__main__":
    results = run_tests()
    sys.exit(0 if all(results.values()) else 1)

