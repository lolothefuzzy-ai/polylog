#!/usr/bin/env python3
"""
Run tests in workspace with browser automation
Supports visual testing, integration tests, and watch mode
"""

import subprocess
import sys
import time
import json
from pathlib import Path
from typing import Dict, List, Optional

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
FRONTEND_DIR = PROJECT_ROOT / "src" / "frontend"

def run_backend_tests() -> tuple[bool, str]:
    """Run Python backend tests"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=300
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "Tests timed out after 5 minutes"
    except Exception as e:
        return False, str(e)

def run_frontend_tests(test_type: str = "all") -> tuple[bool, str]:
    """Run frontend tests with Playwright"""
    try:
        if test_type == "visual":
            cmd = ["npm", "run", "test:visual"]
        elif test_type == "integration":
            cmd = ["npm", "run", "test:integration"]
        elif test_type == "performance":
            cmd = ["npm", "run", "test:performance"]
        else:
            cmd = ["npm", "run", "test:all"]
        
        result = subprocess.run(
            cmd,
            cwd=FRONTEND_DIR,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes for browser tests
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "Tests timed out after 10 minutes"
    except Exception as e:
        return False, str(e)

def run_playwright_ui() -> None:
    """Run Playwright UI mode for interactive testing"""
    print("[INFO] Starting Playwright UI mode...")
    print("[INFO] This will open a browser window for interactive test running")
    subprocess.run(
        ["npm", "run", "test:watch"],
        cwd=FRONTEND_DIR
    )

def run_visual_tests_headed() -> tuple[bool, str]:
    """Run visual tests in headed mode (visible browser)"""
    try:
        # Run integration tests (real system tests) in headed mode
        result = subprocess.run(
            ["npx", "playwright", "test", "tests/integration", "--headed", "--project=chromium"],
            cwd=FRONTEND_DIR,
            capture_output=True,
            text=True,
            timeout=600
        )
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)

def ensure_servers_running() -> bool:
    """Ensure API and frontend servers are running"""
    import requests
    
    # Check API
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        api_running = response.status_code == 200
    except:
        api_running = False
    
    # Check frontend
    try:
        response = requests.get("http://localhost:5173", timeout=2)
        frontend_running = response.status_code == 200
    except:
        frontend_running = False
    
    if not api_running:
        print("[WARN] API server not running on http://localhost:8000")
        print("[INFO] Start it with: python scripts/unified_launcher.py dev")
    
    if not frontend_running:
        print("[WARN] Frontend server not running on http://localhost:5173")
        print("[INFO] Start it with: python scripts/unified_launcher.py dev")
    
    return api_running and frontend_running

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Run tests in workspace")
    parser.add_argument("--type", choices=["all", "backend", "frontend", "visual", "integration", "performance", "ui"],
                       default="all", help="Test type to run")
    parser.add_argument("--watch", action="store_true", help="Watch mode - run tests on file changes")
    parser.add_argument("--headed", action="store_true", help="Run browser tests in headed mode (visible)")
    parser.add_argument("--check-servers", action="store_true", help="Check if servers are running")
    
    args = parser.parse_args()
    
    if args.check_servers:
        ensure_servers_running()
        return
    
    if args.type == "ui":
        run_playwright_ui()
        return
    
    print(f"[TEST] Running {args.type} tests...")
    print("=" * 60)
    
    results = {}
    
    # Run backend tests
    if args.type in ["all", "backend"]:
        print("\n[TEST] Backend tests...")
        success, output = run_backend_tests()
        results["backend"] = success
        if not success:
            print("[FAIL] Backend tests failed")
            print(output[-1000:])  # Last 1000 chars
        else:
            print("[OK] Backend tests passed")
    
    # Run frontend tests
    if args.type in ["all", "frontend", "visual", "integration", "performance"]:
        print("\n[TEST] Frontend tests...")
        if args.headed or args.type == "visual":
            success, output = run_visual_tests_headed()
        else:
            success, output = run_frontend_tests(args.type)
        results["frontend"] = success
        if not success:
            print("[FAIL] Frontend tests failed")
            print(output[-1000:])
        else:
            print("[OK] Frontend tests passed")
    
    # Summary
    print("\n" + "=" * 60)
    if all(results.values()):
        print("[SUCCESS] All tests passed!")
        sys.exit(0)
    else:
        print("[FAILURE] Some tests failed")
        for test_type, passed in results.items():
            status = "[OK]" if passed else "[FAIL]"
            print(f"  {status} {test_type}")
        sys.exit(1)

if __name__ == "__main__":
    main()

