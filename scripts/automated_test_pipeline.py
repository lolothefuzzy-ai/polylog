#!/usr/bin/env python3
"""
Automated test pipeline - starts servers, runs tests, watches for changes
Runs in visible browser mode for real-time feedback
"""

import subprocess
import sys
import time
import signal
import os
from pathlib import Path
from threading import Thread

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
FRONTEND_DIR = PROJECT_ROOT / "src" / "frontend"

# Global process references for cleanup
dev_process = None
test_process = None

def start_dev_servers():
    """Start API and frontend dev servers"""
    global dev_process
    print("[PIPELINE] Starting dev servers...")
    
    # Start integrated dev (API + Frontend) in background
    dev_process = subprocess.Popen(
        [sys.executable, "scripts/dev_integrated.py"],
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
    )
    
    # Wait for servers to be ready
    print("[PIPELINE] Waiting for servers to start...")
    time.sleep(5)  # Initial wait
    
    # Check if servers are running
    try:
        import requests
    except ImportError:
        print("[PIPELINE] WARNING: requests not available, skipping server check")
        time.sleep(10)
        return True
    
    max_retries = 60  # 2 minutes total
    for i in range(max_retries):
        try:
            api_check = requests.get("http://localhost:8000/health", timeout=2)
            frontend_check = requests.get("http://localhost:5173", timeout=2)
            if api_check.status_code == 200 and frontend_check.status_code == 200:
                print("[PIPELINE] Servers are ready!")
                return True
        except:
            pass
        time.sleep(2)
        if i % 5 == 0:
            print(f"[PIPELINE] Still waiting for servers... ({i*2}s/{max_retries*2}s)")
    
    print("[PIPELINE] WARNING: Servers may not be fully ready, but continuing...")
    return True  # Continue anyway - servers might be starting

def run_tests_headed():
    """Run tests in headed mode (visible browser)"""
    global test_process
    print("[PIPELINE] Running tests in visible browser mode...")
    
    test_process = subprocess.Popen(
        [sys.executable, "scripts/run_tests_in_workspace.py", "--type", "all", "--headed"],
        cwd=PROJECT_ROOT,
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    
    return test_process

def run_watch_mode():
    """Run watch mode for continuous testing"""
    print("[PIPELINE] Starting watch mode...")
    print("[PIPELINE] Tests will run automatically on file changes")
    print("[PIPELINE] Browser will be visible for visual feedback")
    
    subprocess.run(
        [sys.executable, "scripts/watch_tests.py"],
        cwd=PROJECT_ROOT
    )

def cleanup():
    """Cleanup processes on exit"""
    global dev_process, test_process
    
    print("\n[PIPELINE] Cleaning up...")
    
    if test_process:
        test_process.terminate()
        test_process.wait(timeout=5)
    
    if dev_process:
        dev_process.terminate()
        dev_process.wait(timeout=5)
    
    # Kill any remaining processes
    try:
        if sys.platform == "win32":
            os.system("taskkill /F /IM node.exe 2>nul")
            os.system("taskkill /F /IM python.exe 2>nul")
        else:
            os.system("pkill -f 'vite|uvicorn|playwright' 2>/dev/null")
    except:
        pass

def signal_handler(sig, frame):
    """Handle Ctrl+C"""
    cleanup()
    sys.exit(0)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Automated test pipeline")
    parser.add_argument("--watch", action="store_true", help="Run in watch mode")
    parser.add_argument("--no-servers", action="store_true", help="Don't start servers (assume already running)")
    
    args = parser.parse_args()
    
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start servers if needed
        if not args.no_servers:
            if not start_dev_servers():
                print("[PIPELINE] ERROR: Failed to start servers")
                print("[PIPELINE] You may need to start them manually:")
                print("[PIPELINE]   python scripts/unified_launcher.py dev")
                sys.exit(1)
        
        if args.watch:
            # Run in watch mode
            run_watch_mode()
        else:
            # Run tests once
            process = run_tests_headed()
            process.wait()
            
            if process.returncode == 0:
                print("\n[PIPELINE] All tests passed!")
            else:
                print("\n[PIPELINE] Some tests failed")
                sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n[PIPELINE] Interrupted by user")
    finally:
        if not args.watch:
            cleanup()

if __name__ == "__main__":
    main()

