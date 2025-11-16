#!/usr/bin/env python3
"""
Integrated Development Environment for Polylog6
Runs everything needed for development with visual feedback in Cursor
"""

import subprocess
import sys
import time
import webbrowser
import threading
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
FRONTEND_DIR = PROJECT_ROOT / "src" / "frontend"
API_PORT = 8000
FRONTEND_PORT = 5173

class Colors:
    OKGREEN = '\033[92m'
    OKCYAN = '\033[96m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_info(msg):
    print(f"{Colors.OKCYAN}ℹ {msg}{Colors.ENDC}")

def print_success(msg):
    print(f"{Colors.OKGREEN}✓ {msg}{Colors.ENDC}")

def print_warning(msg):
    print(f"{Colors.WARNING}⚠ {msg}{Colors.ENDC}")

def print_error(msg):
    print(f"{Colors.FAIL}✗ {msg}{Colors.ENDC}")

def run_background(cmd, cwd=None, name=""):
    """Run command in background"""
    def run():
        try:
            process = subprocess.Popen(
                cmd,
                cwd=cwd or PROJECT_ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            for line in process.stdout:
                if name:
                    print(f"[{name}] {line.rstrip()}")
        except Exception as e:
            print_error(f"{name} error: {e}")
    
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return thread

def wait_for_server(url, timeout=30):
    """Wait for server to be ready"""
    try:
        import requests
    except ImportError:
        # If requests not available, just wait a bit
        time.sleep(3)
        return True
    
    start = time.time()
    while time.time() - start < timeout:
        try:
            response = requests.get(url, timeout=1)
            if response.status_code == 200:
                return True
        except:
            pass
        time.sleep(0.5)
    return False

def main():
    print(f"{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}Polylog6 Integrated Development Environment{Colors.ENDC}")
    print(f"{Colors.BOLD}{'='*60}{Colors.ENDC}\n")
    
    print_info("Starting integrated development environment...")
    print_info("This will run:")
    print_info("  1. API server (Python FastAPI)")
    print_info("  2. Frontend dev server (Vite)")
    print_info("  3. Visual test watcher (Playwright)")
    print_info("  4. Open browser preview\n")
    
    # Start API server
    print_info("Starting API server...")
    api_thread = run_background(
        [sys.executable, "-m", "uvicorn", "polylog6.api.main:app", "--host", "127.0.0.1", "--port", str(API_PORT), "--reload"],
        name="API"
    )
    
    # Wait for API
    print_info("Waiting for API server...")
    if wait_for_server(f"http://localhost:{API_PORT}/health"):
        print_success("API server ready")
    else:
        print_warning("API server may not be ready yet")
    
    # Start frontend dev server
    print_info("Starting frontend dev server...")
    frontend_thread = run_background(
        ["npm", "run", "dev"],
        cwd=FRONTEND_DIR,
        name="Frontend"
    )
    
    # Wait for frontend
    print_info("Waiting for frontend server...")
    time.sleep(3)  # Give Vite time to start
    if wait_for_server(f"http://localhost:{FRONTEND_PORT}"):
        print_success("Frontend server ready")
    else:
        print_warning("Frontend server may not be ready yet")
    
    # Open browser
    print_info("Opening browser preview...")
    time.sleep(2)
    try:
        webbrowser.open(f"http://localhost:{FRONTEND_PORT}")
        print_success("Browser opened")
    except:
        print_warning("Could not open browser automatically")
        print_info(f"Manually open: http://localhost:{FRONTEND_PORT}")
    
    # Start visual test watcher (optional, in background)
    print_info("Starting visual test watcher...")
    test_thread = run_background(
        ["npm", "run", "test:visual", "--", "--watch"],
        cwd=FRONTEND_DIR,
        name="Tests"
    )
    
    print(f"\n{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print_success("Development environment ready!")
    print(f"{Colors.BOLD}{'='*60}{Colors.ENDC}\n")
    print_info("Services running:")
    print_info(f"  • API: http://localhost:{API_PORT}")
    print_info(f"  • Frontend: http://localhost:{FRONTEND_PORT}")
    print_info(f"  • Visual Tests: Watching for changes")
    print("\nPress Ctrl+C to stop all services\n")
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nStopping all services...")
        print_success("Development environment stopped")

if __name__ == "__main__":
    main()

