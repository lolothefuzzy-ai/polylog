#!/usr/bin/env python3
"""
Automated Test Suite
Fully automated testing with backend-frontend integration focus
"""

import subprocess
import sys
import time
import signal
import atexit
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
FRONTEND_DIR = PROJECT_ROOT / "src" / "frontend"

# Global process references
_server_process = None
_test_processes = []

def signal_handler(signum, frame):
    """Handle termination signals"""
    cleanup_all()
    sys.exit(0)

def cleanup_all():
    """Clean up all processes"""
    global _server_process, _test_processes
    
    print("\n[CLEANUP] Stopping all processes...")
    
    # Stop test processes
    for proc in _test_processes:
        try:
            proc.terminate()
            proc.wait(timeout=3)
        except:
            try:
                proc.kill()
            except:
                pass
    
    # Stop server process
    if _server_process:
        try:
            _server_process.terminate()
            _server_process.wait(timeout=5)
        except:
            try:
                _server_process.kill()
            except:
                pass
    
    _server_process = None
    _test_processes = []

def check_servers():
    """Check if servers are running"""
    import urllib.request
    
    api_running = False
    frontend_running = False
    
    try:
        with urllib.request.urlopen("http://localhost:8000/health", timeout=2) as response:
            if response.status == 200:
                api_running = True
    except:
        pass
    
    try:
        with urllib.request.urlopen("http://localhost:5173", timeout=2) as response:
            if response.status == 200:
                frontend_running = True
    except:
        pass
    
    return api_running, frontend_running

def start_servers():
    """Start servers if not running"""
    global _server_process
    
    api_running, frontend_running = check_servers()
    
    if api_running and frontend_running:
        print("[OK] Servers are already running")
        return True
    
    print("[INFO] Starting servers...")
    _server_process = subprocess.Popen(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "unified_launcher.py"), "dev"],
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for servers
    print("[WAIT] Waiting for servers to start...")
    for i in range(60):
        api_running, frontend_running = check_servers()
        if api_running and frontend_running:
            print("[OK] Servers are ready!")
            return True
        time.sleep(1)
        if i % 5 == 0:
            print(f"[WAIT] Still waiting... ({i}s)")
    
    print("[WARN] Servers may not be ready")
    return False

def run_test_suite(test_type="all"):
    """Run test suite"""
    global _test_processes
    
    test_suites = {
        "backend-stability": "tests/visual/backend-stability.spec.js",
        "backend-integration": "tests/visual/backend-integration-stability.spec.js",
        "frontend-integration": "tests/integration/backend-frontend-integration.spec.js",
        "all": None  # Run all tests
    }
    
    if test_type not in test_suites and test_type != "all":
        print(f"[ERROR] Unknown test type: {test_type}")
        return False
    
    print("=" * 70)
    print(f"Running Test Suite: {test_type}")
    print("=" * 70)
    
    if test_type == "all":
        # Run all test suites
        all_passed = True
        for suite_name, suite_path in test_suites.items():
            if suite_path:
                print(f"\n[TEST] Running {suite_name}...")
                result = subprocess.run(
                    ["npx", "playwright", "test", suite_path, "--headed", "--project=chromium"],
                    cwd=FRONTEND_DIR,
                    capture_output=False
                )
                if result.returncode != 0:
                    all_passed = False
        return all_passed
    else:
        # Run specific test suite
        suite_path = test_suites[test_type]
        result = subprocess.run(
            ["npx", "playwright", "test", suite_path, "--headed", "--project=chromium"],
            cwd=FRONTEND_DIR,
            capture_output=False
        )
        return result.returncode == 0

def main():
    import argparse
    
    # Register cleanup handlers
    atexit.register(cleanup_all)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    parser = argparse.ArgumentParser(description="Automated Test Suite")
    parser.add_argument(
        "--type",
        choices=["all", "backend-stability", "backend-integration", "frontend-integration"],
        default="all",
        help="Test suite to run"
    )
    parser.add_argument(
        "--no-servers",
        action="store_true",
        help="Assume servers are already running"
    )
    
    args = parser.parse_args()
    
    try:
        # Start servers if needed
        if not args.no_servers:
            if not start_servers():
                print("[ERROR] Failed to start servers")
                return 1
        
        # Run tests
        success = run_test_suite(args.type)
        
        # Summary
        print("\n" + "=" * 70)
        print("Test Suite Summary")
        print("=" * 70)
        print(f"Status: {'PASS' if success else 'FAIL'}")
        print("=" * 70)
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n[INFO] Test suite interrupted")
        return 130
    finally:
        if not args.no_servers:
            cleanup_all()

if __name__ == "__main__":
    sys.exit(main())

