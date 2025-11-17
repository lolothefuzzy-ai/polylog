#!/usr/bin/env python3
"""
Run Backend Stability Visual Tests
Focuses on backend API stability, performance, and error handling
"""

import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
FRONTEND_DIR = PROJECT_ROOT / "src" / "frontend"

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

# Global process reference for cleanup
_server_process = None

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

def cleanup_servers():
    """Clean up server processes"""
    global _server_process
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

def run_backend_stability_tests():
    """Run backend stability visual tests"""
    print("=" * 70)
    print("Backend Stability Visual Tests")
    print("=" * 70)
    
    # Ensure servers are running
    if not start_servers():
        print("[ERROR] Cannot start servers")
        return False
    
    # Run tests
    print("\n[TEST] Running backend stability tests...")
    result = subprocess.run(
        ["npx", "playwright", "test", "tests/visual/backend-stability.spec.js", "--headed", "--project=chromium"],
        cwd=FRONTEND_DIR,
        capture_output=False
    )
    
    if result.returncode == 0:
        print("\n[SUCCESS] Backend stability tests passed!")
        return True
    else:
        print("\n[FAIL] Backend stability tests failed")
        return False

def run_backend_integration_tests():
    """Run backend integration stability tests"""
    print("\n[TEST] Running backend integration tests...")
    result = subprocess.run(
        ["npx", "playwright", "test", "tests/visual/backend-integration-stability.spec.js", "--headed", "--project=chromium"],
        cwd=FRONTEND_DIR,
        capture_output=False
    )
    
    if result.returncode == 0:
        print("\n[SUCCESS] Backend integration tests passed!")
        return True
    else:
        print("\n[FAIL] Backend integration tests failed")
        return False

def main():
    import atexit
    
    # Register cleanup handler
    atexit.register(cleanup_servers)
    
    try:
        print("=" * 70)
        print("Backend Stability Test Suite")
        print("=" * 70)
        
        # Run backend stability tests
        stability_passed = run_backend_stability_tests()
        
        # Run backend integration tests
        integration_passed = run_backend_integration_tests()
        
        # Summary
        print("\n" + "=" * 70)
        print("Test Summary")
        print("=" * 70)
        print(f"Backend Stability: {'PASS' if stability_passed else 'FAIL'}")
        print(f"Backend Integration: {'PASS' if integration_passed else 'FAIL'}")
        
        if stability_passed and integration_passed:
            print("\n[SUCCESS] All backend stability tests passed!")
            return 0
        else:
            print("\n[WARN] Some tests failed - review output above")
            return 1
    finally:
        cleanup_servers()

