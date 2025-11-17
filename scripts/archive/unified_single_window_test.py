#!/usr/bin/env python3
"""
Unified Single Window Test Runner
Launches everything in ONE browser window with background servers
Similar to MCP/Bubble/Lovable - all in one unified environment
"""

import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
FRONTEND_DIR = PROJECT_ROOT / "src" / "frontend"

# Global server processes
_api_process = None
_frontend_process = None

def cleanup_processes():
    """Clean up any existing processes"""
    cleanup_script = PROJECT_ROOT / "scripts" / "cleanup_processes.py"
    if cleanup_script.exists():
        subprocess.run([sys.executable, str(cleanup_script)], 
                      capture_output=True, timeout=10)
        time.sleep(2)

def start_api_server_background():
    """Start API server in background (no window)"""
    global _api_process
    
    import os
    env = os.environ.copy()
    src_path = str(PROJECT_ROOT / "src")
    if 'PYTHONPATH' in env:
        env['PYTHONPATH'] = src_path + os.pathsep + env['PYTHONPATH']
    else:
        env['PYTHONPATH'] = src_path
    
    # Check if already running
    try:
        urllib.request.urlopen("http://localhost:8000/health", timeout=1)
        print("[OK] API server already running")
        return True
    except:
        pass
    
    _api_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", 
         "polylog6.api.main:app", 
         "--host", "127.0.0.1", 
         "--port", "8000", 
         "--reload"],
        cwd=PROJECT_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    )
    
    print("[OK] API server starting in background...")
    return True

def start_frontend_server_background():
    """Start frontend server in background (no window)"""
    global _frontend_process
    
    # Check if already running
    try:
        urllib.request.urlopen("http://localhost:5173", timeout=1)
        print("[OK] Frontend server already running")
        return True
    except:
        pass
    
    # Check if node_modules exists
    if not (FRONTEND_DIR / "node_modules").exists():
        print("[WARN] node_modules not found, installing...")
        subprocess.run(["npm", "install"], cwd=FRONTEND_DIR, 
                      shell=True, capture_output=True)
    
    _frontend_process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=FRONTEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    )
    
    print("[OK] Frontend server starting in background...")
    return True

def wait_for_servers(max_wait=60):
    """Wait for servers to be ready"""
    print("[WAIT] Waiting for servers to be ready...")
    
    for i in range(max_wait):
        api_ready = False
        frontend_ready = False
        
        try:
            urllib.request.urlopen("http://localhost:8000/health", timeout=2)
            api_ready = True
        except:
            pass
        
        try:
            urllib.request.urlopen("http://localhost:5173", timeout=2)
            frontend_ready = True
        except:
            pass
        
        if api_ready and frontend_ready:
            print("[OK] Both servers are ready!")
            return True
        
        time.sleep(1)
        if i % 5 == 0 and i > 0:
            print(f"[WAIT] Still waiting... ({i}s)")
    
    print("[WARN] Servers may not be fully ready")
    return False

def run_tests_in_browser():
    """Run Playwright tests in the same browser window"""
    print("\n[TEST] Starting continuous testing in browser...")
    print("[INFO] Tests will run in the same browser window")
    print("[INFO] Use Playwright UI for test management")
    
    # Option 1: Run with UI mode (recommended for continuous testing)
    # This opens ONE window with test UI
    cmd = [
        "npx", "playwright", "test",
        "--ui",  # Playwright UI - single window with test interface
        "--project=chromium"
    ]
    
    # Start test runner
    test_process = subprocess.Popen(
        cmd,
        cwd=FRONTEND_DIR,
        shell=True
    )
    
    return test_process

def main():
    print("=" * 70)
    print("Unified Single Window Test Environment")
    print("=" * 70)
    print("\nThis will:")
    print("  1. Start servers in background (no windows)")
    print("  2. Open ONE browser window")
    print("  3. Run continuous tests in that same window")
    print("  4. Track all your interactions")
    print("\n" + "=" * 70 + "\n")
    
    # Step 1: Cleanup
    print("[STEP 1] Cleaning up existing processes...")
    cleanup_processes()
    
    # Step 2: Start servers in background
    print("\n[STEP 2] Starting servers in background...")
    start_api_server_background()
    start_frontend_server_background()
    
    # Step 3: Wait for servers
    if not wait_for_servers():
        print("[ERROR] Servers failed to start")
        return 1
    
    # Step 4: Open single browser window
    print("\n[STEP 3] Opening single browser window...")
    time.sleep(2)
    webbrowser.open("http://localhost:5173")
    
    # Step 5: Start continuous testing (optional - can run manually)
    print("\n[STEP 4] Test environment ready!")
    print("\n" + "=" * 70)
    print("Unified Single Window Test Environment")
    print("=" * 70)
    print("\nStatus:")
    print("  ✓ API server running in background (port 8000)")
    print("  ✓ Frontend server running in background (port 5173)")
    print("  ✓ Browser window opened: http://localhost:5173")
    print("\nTo run tests in the same window:")
    print("  Option 1: Use Playwright UI (recommended)")
    print("    npx playwright test --ui")
    print("\n  Option 2: Run specific test suite")
    print("    npx playwright test tests/integration/unified-interactive-test.spec.js --headed")
    print("\n  Option 3: Run all tests")
    print("    npx playwright test --headed --workers=1")
    print("\nAll tests will run in the SAME browser window!")
    print("\nInteract with the visualization - your actions are tracked!")
    print("\nPress Ctrl+C in this terminal to stop servers...")
    print("=" * 70)
    
    try:
        # Keep running - servers stay alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n[INFO] Stopping servers...")
        if _api_process:
            _api_process.terminate()
            _api_process.wait(timeout=5)
        if _frontend_process:
            _frontend_process.terminate()
            _frontend_process.wait(timeout=5)
        print("[OK] All servers stopped")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

