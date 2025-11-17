#!/usr/bin/env python3
"""
Test Visualization Window
Quick test to verify visualization system works
"""

import sys
import subprocess
import time
import webbrowser
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

def start_visualization():
    """Start visualization test"""
    print("=" * 70)
    print("Test Visualization Window")
    print("=" * 70)
    
    # Check if servers are already running
    api_running, frontend_running = check_servers()
    
    if api_running and frontend_running:
        print("\n[OK] Servers are already running!")
        print("[INFO] Opening browser...")
        webbrowser.open("http://localhost:5173")
        print("[SUCCESS] Browser opened at http://localhost:5173")
        return True
    
    # Start servers using unified launcher
    print("\n[INFO] Starting servers...")
    print("[INFO] This will start:")
    print("  - API server on http://localhost:8000")
    print("  - Frontend server on http://localhost:5173")
    print("\n[INFO] Starting unified launcher...")
    
    process = subprocess.Popen(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "unified_launcher.py"), "dev"],
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for servers to start
    print("[WAIT] Waiting for servers to start...")
    max_wait = 60  # 60 seconds
    for i in range(max_wait):
        api_running, frontend_running = check_servers()
        if api_running and frontend_running:
            print("\n[OK] Servers are ready!")
            print("[INFO] Opening browser...")
            webbrowser.open("http://localhost:5173")
            print("[SUCCESS] Browser opened at http://localhost:5173")
            print("\n[INFO] Visualization window should be open now")
            print("[INFO] Press Ctrl+C to stop servers")
            return True
        time.sleep(1)
        if i % 5 == 0:
            print(f"[WAIT] Still waiting... ({i}s/{max_wait}s)")
    
    print("\n[WARN] Servers may not have started properly")
    print("[INFO] Check the output above for errors")
    return False

if __name__ == "__main__":
    try:
        start_visualization()
        # Keep running
        print("\n[INFO] Servers running. Press Ctrl+C to stop...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[INFO] Stopping servers...")
        sys.exit(0)

