#!/usr/bin/env python3
"""
Interactive Visualization Test
Starts servers, opens browser, and monitors for issues
"""

import subprocess
import sys
import time
import webbrowser
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

def check_server(url, timeout=2, max_attempts=60):
    """Check if server is running"""
    for i in range(max_attempts):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as response:
                if response.status == 200:
                    return True
        except:
            pass
        time.sleep(1)
        if i % 5 == 0 and i > 0:
            print(f"[WAIT] Still waiting for {url}... ({i}s)")
    return False

def start_servers():
    """Start development servers"""
    print("=" * 70)
    print("Starting Visualization System")
    print("=" * 70)
    
    # Use the fixed launcher
    launcher_script = PROJECT_ROOT / "scripts" / "start_visualization_fixed.py"
    if launcher_script.exists():
        print("\n[INFO] Using fixed launcher...")
        process = subprocess.Popen(
            [sys.executable, str(launcher_script)],
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    else:
        print("\n[INFO] Starting servers via unified launcher...")
        process = subprocess.Popen(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "unified_launcher.py"), "dev"],
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    
    return process

def main():
    print("=" * 70)
    print("Interactive Visualization Test")
    print("=" * 70)
    
    # Check if servers are already running
    api_ready = check_server("http://localhost:8000/health", timeout=2, max_attempts=1)
    frontend_ready = check_server("http://localhost:5173", timeout=2, max_attempts=1)
    
    if api_ready and frontend_ready:
        print("\n[OK] Servers are already running!")
    else:
        print("\n[INFO] Starting servers...")
        process = start_servers()
        
        # Wait for API server
        print("\n[WAIT] Waiting for API server (http://localhost:8000)...")
        if not check_server("http://localhost:8000/health"):
            print("[ERROR] API server failed to start")
            return 1
        
        # Wait for frontend server
        print("\n[WAIT] Waiting for frontend server (http://localhost:5173)...")
        if not check_server("http://localhost:5173"):
            print("[ERROR] Frontend server failed to start")
            return 1
    
    print("\n[SUCCESS] Both servers are ready!")
    
    # Open browser
    print("\n[INFO] Opening browser at http://localhost:5173...")
    webbrowser.open("http://localhost:5173")
    
    print("\n" + "=" * 70)
    print("Visualization is ready for interaction!")
    print("=" * 70)
    print("\nYou can now:")
    print("  - Interact with the 3D workspace")
    print("  - Place polygons using the slider")
    print("  - Move and attach polygons")
    print("  - Test chain movement")
    print("\nPress Ctrl+C to stop servers when done.")
    print("=" * 70)
    
    try:
        # Keep script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n[INFO] Stopping servers...")
        return 0

if __name__ == "__main__":
    sys.exit(main())

