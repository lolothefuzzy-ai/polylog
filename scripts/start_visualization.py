#!/usr/bin/env python3
"""
Start Visualization System
Comprehensive startup script that handles all issues and starts the visualization
"""

import sys
import subprocess
import time
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
SRC_DIR = PROJECT_ROOT / "src"
FRONTEND_DIR = PROJECT_ROOT / "src" / "frontend"

# Add src to Python path
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

def check_and_install_numpy():
    """Check if numpy is installed, install if missing"""
    try:
        import numpy
        print("[OK] numpy is installed")
        return True
    except ImportError:
        print("[INFO] Installing numpy...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "numpy"], 
                                cwd=PROJECT_ROOT)
            print("[OK] numpy installed successfully")
            return True
        except Exception as e:
            print(f"[WARN] Could not install numpy: {e}")
            print("[INFO] Continuing anyway - numpy may not be critical")
            return False

def check_python_imports():
    """Verify Python imports work"""
    print("\n[CHECK] Verifying Python imports...")
    try:
        from polylog6.api import main
        print("[OK] API imports successfully")
        return True
    except Exception as e:
        print(f"[FAIL] Import error: {e}")
        return False

def start_servers():
    """Start API and frontend servers"""
    print("\n" + "=" * 70)
    print("Starting Visualization System")
    print("=" * 70)
    
    # Check numpy
    check_and_install_numpy()
    
    # Verify imports
    if not check_python_imports():
        print("\n[ERROR] Python imports failed - cannot start API server")
        print("[INFO] Check error messages above")
        return False
    
    # Start API server
    print("\n[START] Starting API server on port 8000...")
    api_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "polylog6.api.main:app", 
         "--host", "127.0.0.1", "--port", "8000", "--reload"],
        cwd=PROJECT_ROOT,
        env={**os.environ, "PYTHONPATH": str(SRC_DIR)}
    )
    
    # Wait for API
    print("[WAIT] Waiting for API server...")
    import urllib.request
    for i in range(30):
        try:
            with urllib.request.urlopen("http://localhost:8000/health", timeout=1) as response:
                if response.status == 200:
                    print("[OK] API server is ready!")
                    break
        except:
            pass
        time.sleep(1)
        if i % 5 == 0:
            print(f"[WAIT] Still waiting... ({i}s)")
    else:
        print("[WARN] API server may not be ready")
    
    # Start frontend server
    print("\n[START] Starting frontend server on port 5173...")
    frontend_process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=FRONTEND_DIR,
        shell=True  # Use shell on Windows
    )
    
    # Wait for frontend
    print("[WAIT] Waiting for frontend server...")
    time.sleep(3)
    for i in range(20):
        try:
            with urllib.request.urlopen("http://localhost:5173", timeout=1) as response:
                if response.status == 200:
                    print("[OK] Frontend server is ready!")
                    break
        except:
            pass
        time.sleep(1)
        if i % 5 == 0:
            print(f"[WAIT] Still waiting... ({i}s)")
    else:
        print("[WARN] Frontend server may not be ready")
    
    print("\n" + "=" * 70)
    print("[SUCCESS] Visualization system started!")
    print("=" * 70)
    print("\n[INFO] Servers running:")
    print("  - API: http://localhost:8000")
    print("  - Frontend: http://localhost:5173")
    print("\n[INFO] Press Ctrl+C to stop servers")
    print("=" * 70 + "\n")
    
    try:
        # Keep running
        api_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        print("\n[INFO] Stopping servers...")
        api_process.terminate()
        frontend_process.terminate()
        print("[OK] Servers stopped")
    
    return True

if __name__ == "__main__":
    try:
        success = start_servers()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Failed to start: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

