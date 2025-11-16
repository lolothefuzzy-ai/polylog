#!/usr/bin/env python3
"""
Launch Visualization with Visible Output
Starts servers in separate windows so you can see everything
"""

import subprocess
import sys
import time
import webbrowser
import urllib.request
from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
FRONTEND_DIR = PROJECT_ROOT / "src" / "frontend"

def check_server(url, timeout=2):
    """Check if server is running"""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return response.status == 200
    except:
        return False

def check_dependencies():
    """Check and install missing dependencies"""
    missing = []
    try:
        import psutil
    except ImportError:
        missing.append("psutil")
    
    if missing:
        print(f"[INFO] Installing missing dependencies: {', '.join(missing)}")
        for dep in missing:
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-q", dep],
                    check=True,
                    capture_output=True
                )
                print(f"[OK] Installed {dep}")
            except:
                print(f"[WARN] Failed to install {dep} automatically")

def start_api_server_visible():
    """Start API server in new window"""
    print("[INFO] Starting API server in new window...")
    
    check_dependencies()
    
    # Add src to Python path
    env = os.environ.copy()
    src_path = str(PROJECT_ROOT / "src")
    if 'PYTHONPATH' in env:
        env['PYTHONPATH'] = src_path + os.pathsep + env['PYTHONPATH']
    else:
        env['PYTHONPATH'] = src_path
    
    # Create batch file to set PYTHONPATH and run uvicorn
    batch_file = PROJECT_ROOT / "start_api.bat"
    with open(batch_file, 'w') as f:
        f.write(f'@echo off\n')
        f.write(f'title API Server - Port 8000\n')
        f.write(f'set PYTHONPATH={src_path}\n')
        f.write(f'cd /d "{PROJECT_ROOT}"\n')
        f.write(f'"{sys.executable}" -m uvicorn polylog6.api.main:app --host 127.0.0.1 --port 8000 --reload\n')
        f.write(f'pause\n')
    
    # Start in new window
    subprocess.Popen(
        ["cmd", "/c", "start", "API Server", str(batch_file)],
        shell=False
    )
    
    print("[OK] API server window opened")

def start_frontend_server_visible():
    """Start frontend server in new window"""
    print("[INFO] Starting frontend server in new window...")
    
    # Check if node_modules exists
    if not (FRONTEND_DIR / "node_modules").exists():
        print("[WARN] node_modules not found, installing...")
        print("[INFO] This may take a few minutes...")
        install_result = subprocess.run(
            ["npm", "install"],
            cwd=FRONTEND_DIR,
            shell=True,
            capture_output=True,
            text=True
        )
        if install_result.returncode != 0:
            print("[ERROR] npm install failed!")
            print(install_result.stderr)
            return False
        print("[OK] Dependencies installed")
    
    # Create batch file to run npm dev
    batch_file = FRONTEND_DIR / "start_frontend.bat"
    with open(batch_file, 'w') as f:
        f.write(f'@echo off\n')
        f.write(f'title Frontend Server - Port 5173\n')
        f.write(f'cd /d "{FRONTEND_DIR}"\n')
        f.write(f'npm run dev\n')
        f.write(f'pause\n')
    
    # Start in new window
    subprocess.Popen(
        ["cmd", "/c", "start", "Frontend Server", str(batch_file)],
        shell=False
    )
    
    print("[OK] Frontend server window opened")
    return True

def wait_for_server(url, name, max_attempts=60):
    """Wait for server to be ready"""
    print(f"[WAIT] Waiting for {name} ({url})...")
    
    for i in range(max_attempts):
        if check_server(url, timeout=2):
            print(f"[OK] {name} is ready!")
            return True
        time.sleep(1)
        if i % 5 == 0 and i > 0:
            print(f"[WAIT] Still waiting... ({i}s)")
    
    print(f"[ERROR] {name} failed to start after {max_attempts} seconds")
    return False

def main():
    print("=" * 70)
    print("Polylog6 Visualization Launcher (Visible Windows)")
    print("=" * 70)
    print("\nThis will open:")
    print("  1. API Server window (port 8000)")
    print("  2. Frontend Server window (port 5173)")
    print("  3. Browser window (http://localhost:5173)")
    print("\n" + "=" * 70 + "\n")
    
    # Check if servers are already running
    api_ready = check_server("http://localhost:8000/health", timeout=2)
    frontend_ready = check_server("http://localhost:5173", timeout=2)
    
    if not api_ready:
        start_api_server_visible()
        if not wait_for_server("http://localhost:8000/health", "API Server"):
            print("\n[ERROR] API server failed to start")
            print("[INFO] Check the API Server window for errors")
            return 1
    else:
        print("[OK] API server is already running")
    
    if not frontend_ready:
        if not start_frontend_server_visible():
            return 1
        if not wait_for_server("http://localhost:5173", "Frontend Server"):
            print("\n[ERROR] Frontend server failed to start")
            print("[INFO] Check the Frontend Server window for errors")
            return 1
    else:
        print("[OK] Frontend server is already running")
    
    # Open browser
    print("\n[INFO] Opening browser...")
    time.sleep(2)  # Give servers a moment to fully initialize
    webbrowser.open("http://localhost:5173")
    
    print("\n" + "=" * 70)
    print("Visualization is ready!")
    print("=" * 70)
    print("\nYou should see:")
    print("  • API Server window - showing API logs")
    print("  • Frontend Server window - showing Vite logs")
    print("  • Browser window - showing the visualization")
    print("\nAll windows are visible in your workspace!")
    print("=" * 70)
    
    # Keep this window open
    try:
        input("\nPress Enter to exit (servers will keep running)...\n")
    except KeyboardInterrupt:
        print("\n\n[INFO] Exiting...")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

