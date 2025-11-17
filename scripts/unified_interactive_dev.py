#!/usr/bin/env python3
"""
Unified Interactive Development Service
Launches the actual program (API + Frontend) with integrated testing support
Allows interactive development with real-time test feedback
"""

import argparse
import subprocess
import sys
import os
import threading
import time
import signal
import atexit
from pathlib import Path
from typing import Optional, Dict, Any
import json

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
FRONTEND_DIR = PROJECT_ROOT / "src" / "frontend"
API_DIR = PROJECT_ROOT / "src" / "polylog6" / "api"

# Global process references
_api_process: Optional[subprocess.Popen] = None
_frontend_process: Optional[subprocess.Popen] = None
_test_process: Optional[subprocess.Popen] = None

# Colors for output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_success(text: str):
    print(f"{Colors.OKGREEN}[OK] {text}{Colors.ENDC}")

def print_info(text: str):
    print(f"{Colors.OKCYAN}[INFO] {text}{Colors.ENDC}")

def print_warning(text: str):
    print(f"{Colors.WARNING}[WARN] {text}{Colors.ENDC}")

def print_error(text: str):
    print(f"{Colors.FAIL}[ERROR] {text}{Colors.ENDC}")

def check_server(url: str, timeout: int = 2) -> bool:
    """Check if a server is running"""
    try:
        import urllib.request
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return response.status == 200
    except:
        return False

def ensure_venv():
    """Ensure virtual environment exists"""
    venv_path = PROJECT_ROOT / "venv"
    if not venv_path.exists():
        print_info("Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print_success("Virtual environment created")
    
    if sys.platform == "win32":
        return venv_path / "Scripts" / "python.exe"
    else:
        return venv_path / "bin" / "python"

def start_api_server() -> Optional[subprocess.Popen]:
    """Start FastAPI development server"""
    global _api_process
    
    if check_server("http://localhost:8000/health"):
        print_info("API server already running")
        return None
    
    print_info("Starting API server...")
    python = ensure_venv()
    
    api_main = API_DIR / "main.py"
    if not api_main.exists():
        print_error(f"API main.py not found at {api_main}")
        return None
    
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT / "src")
    
    _api_process = subprocess.Popen(
        [str(python), "-m", "uvicorn", "polylog6.api.main:app", 
         "--host", "127.0.0.1", "--port", "8000", "--reload"],
        cwd=PROJECT_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # Wait for API to be ready
    print_info("Waiting for API server...")
    for i in range(30):
        if check_server("http://localhost:8000/health"):
            print_success("API server ready")
            return _api_process
        time.sleep(1)
        if i % 5 == 0:
            print_info(f"Still waiting... ({i}s)")
    
    print_warning("API server may not be ready")
    return _api_process

def start_frontend_server() -> Optional[subprocess.Popen]:
    """Start frontend development server"""
    global _frontend_process
    
    if check_server("http://localhost:5173"):
        print_info("Frontend server already running")
        return None
    
    print_info("Starting frontend development server...")
    
    if not (FRONTEND_DIR / "package.json").exists():
        print_error("Frontend package.json not found")
        return None
    
    _frontend_process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=FRONTEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # Wait for frontend to be ready
    print_info("Waiting for frontend server...")
    for i in range(30):
        if check_server("http://localhost:5173"):
            print_success("Frontend server ready")
            return _frontend_process
        time.sleep(1)
        if i % 5 == 0:
            print_info(f"Still waiting... ({i}s)")
    
    print_warning("Frontend server may not be ready")
    return _frontend_process

def run_interactive_tests():
    """Run Playwright tests in interactive mode"""
    global _test_process
    
    print_info("Starting interactive tests...")
    print_info("Tests will run in headed mode - you can interact with the browser")
    
    _test_process = subprocess.Popen(
        ["npx", "playwright", "test", "--headed", "--project=chromium"],
        cwd=FRONTEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # Stream output
    if _test_process.stdout:
        for line in _test_process.stdout:
            print(line.rstrip())
    
    return _test_process.wait()

def cleanup_all():
    """Clean up all processes"""
    global _api_process, _frontend_process, _test_process
    
    print_info("\nCleaning up processes...")
    
    for name, proc in [("API", _api_process), ("Frontend", _frontend_process), ("Test", _test_process)]:
        if proc:
            try:
                print_info(f"Stopping {name} server...")
                proc.terminate()
                proc.wait(timeout=5)
                print_success(f"{name} server stopped")
            except subprocess.TimeoutExpired:
                print_warning(f"{name} server didn't stop gracefully, killing...")
                proc.kill()
            except Exception as e:
                print_warning(f"Error stopping {name} server: {e}")
    
    _api_process = None
    _frontend_process = None
    _test_process = None

def signal_handler(signum, frame):
    """Handle termination signals"""
    cleanup_all()
    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(
        description="Unified Interactive Development Service",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python unified_interactive_dev.py              # Start dev environment
  python unified_interactive_dev.py --test       # Start dev + run tests
  python unified_interactive_dev.py --api-only   # Start API only
  python unified_interactive_dev.py --frontend-only  # Start frontend only
        """
    )
    
    parser.add_argument("--test", action="store_true", 
                       help="Run interactive tests after starting servers")
    parser.add_argument("--api-only", action="store_true",
                       help="Start API server only")
    parser.add_argument("--frontend-only", action="store_true",
                       help="Start frontend server only")
    parser.add_argument("--no-browser", action="store_true",
                       help="Don't open browser automatically")
    
    args = parser.parse_args()
    
    # Register cleanup handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    atexit.register(cleanup_all)
    
    print_header("Polylog6 Unified Interactive Development")
    
    try:
        # Start servers
        if not args.frontend_only:
            start_api_server()
        
        if not args.api_only:
            start_frontend_server()
        
        # Wait a bit for everything to stabilize
        time.sleep(2)
        
        print_header("Development Environment Ready")
        print_success("Services running:")
        if not args.frontend_only:
            print_info(f"  • API: http://localhost:8000")
            print_info(f"  • API Health: http://localhost:8000/health")
        if not args.api_only:
            print_info(f"  • Frontend: http://localhost:5173")
        
        if args.test:
            print_info("\nStarting interactive tests...")
            run_interactive_tests()
        else:
            print_info("\nDevelopment environment is ready!")
            print_info("You can now:")
            print_info("  • Open http://localhost:5173 in your browser")
            print_info("  • Interact with the application")
            print_info("  • Run tests manually: npx playwright test --headed")
            print_info("\nPress Ctrl+C to stop all services")
            
            # Keep running
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print_info("\nShutting down...")
    
    except KeyboardInterrupt:
        print_info("\nShutting down...")
    except Exception as e:
        print_error(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cleanup_all()

if __name__ == "__main__":
    main()

