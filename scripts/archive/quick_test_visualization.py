#!/usr/bin/env python3
"""
Quick Test Visualization
Simple script to test if visualization works
"""

import sys
import subprocess
import time
import webbrowser
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

def check_server(url, timeout=5):
    """Check if server is running"""
    import urllib.request
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return response.status == 200
    except:
        return False

def main():
    print("=" * 70)
    print("Quick Visualization Test")
    print("=" * 70)
    
    # Check if servers are already running
    api_ready = check_server("http://localhost:8000/health")
    frontend_ready = check_server("http://localhost:5173")
    
    if api_ready and frontend_ready:
        print("\n[OK] Servers are already running!")
        print("[INFO] Opening browser at http://localhost:5173")
        webbrowser.open("http://localhost:5173")
        print("[SUCCESS] Browser should open shortly")
        return True
    
    print("\n[INFO] Starting servers...")
    print("[INFO] This will:")
    print("  1. Start API server (http://localhost:8000)")
    print("  2. Start frontend server (http://localhost:5173)")
    print("  3. Open browser automatically")
    print("\n[INFO] Starting unified launcher...")
    
    # Start in background
    process = subprocess.Popen(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "unified_launcher.py"), "dev"],
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for servers
    print("\n[WAIT] Waiting for servers to start (up to 60 seconds)...")
    for i in range(60):
        api_ready = check_server("http://localhost:8000/health")
        frontend_ready = check_server("http://localhost:5173")
        
        if api_ready and frontend_ready:
            print("\n[OK] Servers are ready!")
            print("[INFO] Opening browser...")
            webbrowser.open("http://localhost:5173")
            print("\n[SUCCESS] Visualization window should be open!")
            print("[INFO] Servers are running in background")
            print("[INFO] Press Ctrl+C in the launcher window to stop")
            return True
        
        if i % 5 == 0 and i > 0:
            print(f"[WAIT] Still waiting... ({i}s)")
        time.sleep(1)
    
    print("\n[WARN] Servers may not have started")
    print("[INFO] Check the output above for errors")
    print("[INFO] Try manually: python scripts/unified_launcher.py dev")
    return False

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[INFO] Exiting...")
        sys.exit(0)

