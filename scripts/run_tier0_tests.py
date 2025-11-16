#!/usr/bin/env python3
"""
Run Tier 0 Integration Tests
Starts servers and runs Tier 0 specific tests
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
    import urllib.error
    
    api_running = False
    frontend_running = False
    
    try:
        with urllib.request.urlopen("http://localhost:8000/health", timeout=2) as response:
            api_running = response.status == 200
    except:
        pass
    
    try:
        with urllib.request.urlopen("http://localhost:5173", timeout=2) as response:
            frontend_running = response.status == 200
    except:
        pass
    
    return api_running, frontend_running

def start_servers():
    """Start API and frontend servers"""
    print("[INFO] Starting servers...")
    
    # Start unified launcher in background
    process = subprocess.Popen(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "unified_launcher.py"), "dev"],
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for servers to start
    print("[INFO] Waiting for servers to start...")
    for i in range(60):  # Wait up to 60 seconds
        api_running, frontend_running = check_servers()
        if api_running and frontend_running:
            print("[OK] Servers are running!")
            return process
        time.sleep(1)
    
    print("[WARN] Servers may not have started properly")
    return process

def run_tier0_tests():
    """Run Tier 0 integration tests"""
    print("[TEST] Running Tier 0 integration tests...")
    
    # Check if servers are running
    api_running, frontend_running = check_servers()
    
    if not api_running or not frontend_running:
        print("[INFO] Starting servers...")
        server_process = start_servers()
        
        # Wait a bit more for servers to be fully ready
        time.sleep(5)
    else:
        print("[OK] Servers already running")
        server_process = None
    
    # Run tests
    print("[TEST] Executing tests...")
    result = subprocess.run(
        ["npx", "playwright", "test", 
         "tests/integration/tier0-integration.spec.js",
         "tests/integration/tier0-workflow.spec.js",
         "--headed", "--project=chromium"],
        cwd=FRONTEND_DIR,
        timeout=300  # 5 minutes max
    )
    
    return result.returncode == 0

if __name__ == "__main__":
    success = run_tier0_tests()
    sys.exit(0 if success else 1)

