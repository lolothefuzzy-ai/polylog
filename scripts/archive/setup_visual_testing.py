#!/usr/bin/env python3
"""Set up visual testing with workspace browser viewport"""
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
FRONTEND_DIR = PROJECT_ROOT / "src" / "frontend"

def start_servers():
    """Start API and frontend servers for visual testing"""
    import threading
    
    def start_api():
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "polylog6.api.main:app",
            "--host", "127.0.0.1",
            "--port", "8000",
            "--reload"
        ], cwd=PROJECT_ROOT)
    
    def start_frontend():
        subprocess.run(["npm", "run", "dev"], cwd=FRONTEND_DIR)
    
    api_thread = threading.Thread(target=start_api, daemon=True)
    frontend_thread = threading.Thread(target=start_frontend, daemon=True)
    
    api_thread.start()
    frontend_thread.start()
    
    time.sleep(5)  # Wait for servers to start
    print("Servers started: API on :8000, Frontend on :5173")
    return api_thread, frontend_thread

if __name__ == "__main__":
    start_servers()
    print("Visual testing servers running. Open http://localhost:5173 in browser.")

