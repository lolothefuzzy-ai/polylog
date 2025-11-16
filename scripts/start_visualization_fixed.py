#!/usr/bin/env python3
"""
Fixed Visualization Launcher
Properly starts servers and opens browser with error handling
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

def start_api_server():
    """Start API server directly"""
    print("[INFO] Starting API server...")
    
    # Add src to Python path
    env = os.environ.copy()
    src_path = str(PROJECT_ROOT / "src")
    if 'PYTHONPATH' in env:
        env['PYTHONPATH'] = src_path + os.pathsep + env['PYTHONPATH']
    else:
        env['PYTHONPATH'] = src_path
    
    # Use shell=True on Windows for better compatibility
    is_windows = os.name == 'nt'
    
    process = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn",
            "polylog6.api.main:app",
            "--host", "127.0.0.1",
            "--port", "8000",
            "--reload"
        ],
        cwd=PROJECT_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # Combine stderr with stdout
        shell=is_windows,
        text=True
    )
    
    # Print initial output to see errors
    import threading
    def print_output():
        try:
            for line in iter(process.stdout.readline, ''):
                if line:
                    print(f"[API] {line.rstrip()}")
        except:
            pass
    
    output_thread = threading.Thread(target=print_output, daemon=True)
    output_thread.start()
    
    return process

def start_frontend_server():
    """Start frontend dev server"""
    print("[INFO] Starting frontend server...")
    
    # Check if node_modules exists
    if not (FRONTEND_DIR / "node_modules").exists():
        print("[WARN] node_modules not found. Run 'npm install' in frontend directory first.")
        return None
    
    process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=FRONTEND_DIR,
        shell=True,  # Windows compatibility
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    return process

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
    print("Polylog6 Visualization Launcher")
    print("=" * 70)
    
    # Check if servers are already running
    api_ready = check_server("http://localhost:8000/health", timeout=2)
    frontend_ready = check_server("http://localhost:5173", timeout=2)
    
    api_process = None
    frontend_process = None
    
    try:
        if not api_ready:
            api_process = start_api_server()
            if not wait_for_server("http://localhost:8000/health", "API Server"):
                return 1
        else:
            print("[OK] API server is already running")
        
        if not frontend_ready:
            frontend_process = start_frontend_server()
            if frontend_process is None:
                return 1
            if not wait_for_server("http://localhost:5173", "Frontend Server"):
                return 1
        else:
            print("[OK] Frontend server is already running")
        
        # Open browser
        print("\n[INFO] Opening browser...")
        time.sleep(1)  # Small delay to ensure page is ready
        webbrowser.open("http://localhost:5173")
        
        print("\n" + "=" * 70)
        print("Visualization is ready!")
        print("=" * 70)
        print("\nBrowser should be open at http://localhost:5173")
        print("Press Ctrl+C to stop servers")
        print("=" * 70)
        
        # Keep running
        try:
            while True:
                time.sleep(1)
                # Check if processes are still alive
                if api_process and api_process.poll() is not None:
                    print("\n[ERROR] API server stopped unexpectedly")
                    break
                if frontend_process and frontend_process.poll() is not None:
                    print("\n[ERROR] Frontend server stopped unexpectedly")
                    break
        except KeyboardInterrupt:
            print("\n\n[INFO] Stopping servers...")
        
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] Failed to start visualization: {e}")
        return 1
    finally:
        # Cleanup
        if api_process:
            try:
                api_process.terminate()
                api_process.wait(timeout=5)
            except:
                try:
                    api_process.kill()
                except:
                    pass
        if frontend_process:
            try:
                frontend_process.terminate()
                frontend_process.wait(timeout=5)
            except:
                try:
                    frontend_process.kill()
                except:
                    pass

if __name__ == "__main__":
    sys.exit(main())

