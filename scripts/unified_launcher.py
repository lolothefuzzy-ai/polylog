#!/usr/bin/env python3
"""
Polylog6 Unified Desktop Launcher
Complete launcher for desktop application with visual testing support
"""

import argparse
import subprocess
import sys
import os
import threading
import time
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
FRONTEND_DIR = PROJECT_ROOT / "src" / "frontend"
DESKTOP_DIR = PROJECT_ROOT / "src" / "desktop"
API_DIR = PROJECT_ROOT / "src" / "polylog6" / "api"

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
    try:
        print(f"{Colors.OKGREEN}[OK] {text}{Colors.ENDC}")
    except UnicodeEncodeError:
        print(f"[OK] {text}")

def print_info(text: str):
    try:
        print(f"{Colors.OKCYAN}[INFO] {text}{Colors.ENDC}")
    except UnicodeEncodeError:
        print(f"[INFO] {text}")

def print_warning(text: str):
    try:
        print(f"{Colors.WARNING}[WARN] {text}{Colors.ENDC}")
    except UnicodeEncodeError:
        print(f"[WARN] {text}")

def print_error(text: str):
    try:
        print(f"{Colors.FAIL}[ERROR] {text}{Colors.ENDC}")
    except UnicodeEncodeError:
        print(f"[ERROR] {text}")

def run_command(cmd: list, cwd: Optional[Path] = None, check: bool = True, silent: bool = False):
    """Run a command with proper error handling"""
    if not silent:
        print_info(f"Running: {' '.join(cmd)}")
    
    result = subprocess.run(
        cmd,
        cwd=cwd or PROJECT_ROOT,
        check=check,
        capture_output=silent,
        text=True
    )
    return result.returncode == 0

def ensure_venv():
    """Ensure virtual environment exists"""
    venv_path = PROJECT_ROOT / "venv"
    if not venv_path.exists():
        print_info("Creating virtual environment...")
        run_command([sys.executable, "-m", "venv", "venv"])
        print_success("Virtual environment created")
    
    if sys.platform == "win32":
        return venv_path / "Scripts" / "python.exe"
    else:
        return venv_path / "bin" / "python"

def install_deps():
    """Install Python dependencies"""
    print_info("Installing Python dependencies...")
    python = ensure_venv()
    
    req_file = PROJECT_ROOT / "requirements.txt"
    if req_file.exists():
        run_command([str(python), "-m", "pip", "install", "-r", str(req_file)])
        print_success("Python dependencies installed")
    else:
        print_warning("requirements.txt not found")

def install_node_deps():
    """Install Node.js dependencies"""
    print_info("Installing Node.js dependencies...")
    if (FRONTEND_DIR / "package.json").exists():
        run_command(["npm", "install"], cwd=FRONTEND_DIR)
        print_success("Node.js dependencies installed")
    else:
        print_warning("Frontend package.json not found")

def install_all():
    """Install all dependencies"""
    print_header("Installing Dependencies")
    ensure_venv()
    install_deps()
    install_node_deps()
    print_success("All dependencies installed")

def build_frontend():
    """Build frontend for production"""
    print_info("Building frontend...")
    if not (FRONTEND_DIR / "package.json").exists():
        print_error("Frontend package.json not found")
        return False
    
    success = run_command(["npm", "run", "build"], cwd=FRONTEND_DIR)
    if success:
        print_success("Frontend built successfully")
    return success

def build_tauri():
    """Build Tauri desktop application"""
    print_info("Building Tauri application...")
    tauri_dir = DESKTOP_DIR / "src-tauri"
    
    if not (tauri_dir / "Cargo.toml").exists():
        print_error("Tauri Cargo.toml not found")
        return False
    
    # Build Rust backend
    success = run_command(["cargo", "build", "--release"], cwd=tauri_dir)
    if success:
        print_success("Tauri backend built successfully")
    
    return success

def build_all():
    """Build complete application"""
    print_header("Building Polylog6 Desktop Application")
    
    if not build_frontend():
        return False
    
    if not build_tauri():
        return False
    
    print_success("Complete application built successfully!")
    return True

def start_api_server():
    """Start FastAPI development server"""
    print_info("Starting API server...")
    python = ensure_venv()
    
    # Find API main file
    api_main = API_DIR / "main.py"
    if not api_main.exists():
        print_error(f"API main.py not found at {api_main}")
        return
    
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT / "src")
    
    try:
        subprocess.run(
            [str(python), "-m", "uvicorn", "polylog6.api.main:app", "--reload", "--port", "8000"],
            cwd=PROJECT_ROOT,
            env=env,
            check=False
        )
    except KeyboardInterrupt:
        print_info("API server stopped")

def start_frontend_dev():
    """Start frontend development server"""
    print_info("Starting frontend development server...")
    run_command(["npm", "run", "dev"], cwd=FRONTEND_DIR, check=False)

def start_tauri_dev():
    """Start Tauri development mode"""
    print_info("Starting Tauri development mode...")
    
    # Start API in background
    api_thread = threading.Thread(target=start_api_server, daemon=True)
    api_thread.start()
    time.sleep(2)  # Give API time to start
    
    # Start Tauri
    run_command(["npm", "run", "tauri", "dev"], cwd=FRONTEND_DIR, check=False)

def start_desktop():
    """Start complete desktop application (production mode)"""
    print_header("Starting Polylog6 Desktop Application")
    
    # Build if needed
    if not (FRONTEND_DIR / "dist").exists():
        print_info("Frontend not built, building now...")
        if not build_frontend():
            print_error("Failed to build frontend")
            return
    
    # Start API in background
    api_thread = threading.Thread(target=start_api_server, daemon=True)
    api_thread.start()
    time.sleep(2)
    
    # Start Tauri
    print_info("Launching desktop application...")
    run_command(["npm", "run", "tauri", "dev"], cwd=FRONTEND_DIR, check=False)

def run_visual_tests():
    """Run visual tests with virtual window"""
    print_header("Running Visual Tests")
    
    print_info("Starting test environment...")
    
    # Start API
    api_thread = threading.Thread(target=start_api_server, daemon=True)
    api_thread.start()
    time.sleep(2)
    
    # Build test frontend
    print_info("Building test frontend...")
    run_command(["npm", "run", "build"], cwd=FRONTEND_DIR)
    
    # Run Playwright tests
    print_info("Running Playwright visual tests...")
    run_command(["npx", "playwright", "test", "--headed"], cwd=FRONTEND_DIR)

def run_tests():
    """Run all tests"""
    print_header("Running Tests")
    
    python = ensure_venv()
    
    # Python tests
    print_info("Running Python tests...")
    run_command([str(python), "-m", "pytest", "tests/"], cwd=PROJECT_ROOT)
    
    # Frontend tests
    print_info("Running frontend tests...")
    run_command(["npm", "test"], cwd=FRONTEND_DIR)

def package_app():
    """Package application for distribution"""
    print_header("Packaging Application")
    
    # Build everything
    if not build_all():
        print_error("Build failed, cannot package")
        return
    
    # Package with Tauri
    print_info("Creating application package...")
    run_command(["npm", "run", "tauri", "build"], cwd=FRONTEND_DIR)
    
    print_success("Application packaged successfully!")
    print_info(f"Package location: {DESKTOP_DIR / 'src-tauri' / 'target' / 'release'}")

def clean():
    """Clean build artifacts"""
    print_header("Cleaning Build Artifacts")
    
    import shutil
    
    # Clean Python
    for pattern in ["__pycache__", "*.pyc"]:
        for item in PROJECT_ROOT.rglob(pattern):
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
    
    # Clean frontend
    dist_dir = FRONTEND_DIR / "dist"
    if dist_dir.exists():
        shutil.rmtree(dist_dir, ignore_errors=True)
        print_success("Frontend dist cleaned")
    
    # Clean Tauri
    target_dir = DESKTOP_DIR / "src-tauri" / "target"
    if target_dir.exists():
        shutil.rmtree(target_dir, ignore_errors=True)
        print_success("Tauri target cleaned")
    
    print_success("Clean complete")

def benchmark():
    """Run performance benchmarks"""
    print_info("Running performance benchmarks...")
    import sys
    from pathlib import Path
    opt_script = PROJECT_ROOT / "scripts" / "optimization_tasks.py"
    if opt_script.exists():
        run_command([sys.executable, str(opt_script), "benchmark"])
    else:
        print_warning("Optimization tasks script not found")

def optimize_validate():
    """Validate optimizations"""
    print_info("Validating optimizations...")
    import sys
    from pathlib import Path
    opt_script = PROJECT_ROOT / "scripts" / "optimization_tasks.py"
    if opt_script.exists():
        run_command([sys.executable, str(opt_script), "validate"])
    else:
        print_warning("Optimization tasks script not found")

def monitor():
    """Monitor system metrics"""
    print_info("Starting system monitoring...")
    import sys
    from pathlib import Path
    opt_script = PROJECT_ROOT / "scripts" / "optimization_tasks.py"
    if opt_script.exists():
        run_command([sys.executable, str(opt_script), "monitor"], check=False)
    else:
        print_warning("Optimization tasks script not found")

def main():
    parser = argparse.ArgumentParser(
        description="Polylog6 Unified Desktop Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python unified_launcher.py install      # Install all dependencies
  python unified_launcher.py desktop      # Start desktop app
  python unified_launcher.py test:visual  # Run visual tests
  python unified_launcher.py benchmark    # Performance benchmarks
  python unified_launcher.py optimize     # Validate optimizations
  python unified_launcher.py monitor     # Monitor system metrics
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Installation
    subparsers.add_parser("install", help="Install all dependencies")
    
    # Development
    subparsers.add_parser("dev", help="Start integrated dev environment (API + Frontend + Tests)")
    subparsers.add_parser("desktop", help="Start desktop application (dev mode)")
    subparsers.add_parser("dev:api", help="Start API server only")
    subparsers.add_parser("dev:frontend", help="Start frontend dev server only")
    
    # Building
    subparsers.add_parser("build", help="Build complete application")
    subparsers.add_parser("build:frontend", help="Build frontend only")
    subparsers.add_parser("build:tauri", help="Build Tauri backend only")
    
    # Testing
    subparsers.add_parser("test", help="Run all tests")
    subparsers.add_parser("test:visual", help="Run visual tests with virtual window")
    subparsers.add_parser("test:integration", help="Run integration tests")
    
    # Optimization
    subparsers.add_parser("benchmark", help="Run performance benchmarks")
    subparsers.add_parser("optimize", help="Validate optimizations")
    subparsers.add_parser("monitor", help="Monitor system metrics continuously")
    subparsers.add_parser("profile", help="Run performance profiler")
    
    # Automated testing
    subparsers.add_parser("test:auto", help="Run automated test suite")
    subparsers.add_parser("test:visual:workspace", help="Run visual tests in workspace browser")
    subparsers.add_parser("test:watch", help="Watch mode - run tests on file changes")
    subparsers.add_parser("test:ui", help="Open Playwright UI for interactive testing")
    subparsers.add_parser("test:headed", help="Run browser tests in visible mode")
    subparsers.add_parser("test:pipeline", help="Automated test pipeline (start servers + run tests)")
    subparsers.add_parser("test:pipeline:watch", help="Automated test pipeline in watch mode")
    
    # Packaging
    subparsers.add_parser("package", help="Package application for distribution")
    
    # Utilities
    subparsers.add_parser("clean", help="Clean build artifacts")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == "install":
            install_all()
        elif args.command == "dev":
            # Use unified interactive dev service
            dev_script = PROJECT_ROOT / "scripts" / "unified_interactive_dev.py"
            if dev_script.exists():
                run_command([sys.executable, str(dev_script)], check=False)
            else:
                print_warning("Unified interactive dev script not found, starting basic dev...")
                start_api_server()
                time.sleep(2)
                start_frontend_dev()
        elif args.command == "desktop":
            start_desktop()
        elif args.command == "dev:api":
            start_api_server()
        elif args.command == "dev:frontend":
            start_frontend_dev()
        elif args.command == "build":
            build_all()
        elif args.command == "build:frontend":
            build_frontend()
        elif args.command == "build:tauri":
            build_tauri()
        elif args.command == "test":
            run_tests()
        elif args.command == "test:visual":
            run_visual_tests()
        elif args.command == "test:integration":
            import sys
            opt_script = PROJECT_ROOT / "scripts" / "optimization_tasks.py"
            if opt_script.exists():
                run_command([sys.executable, str(opt_script), "integration"])
        elif args.command == "benchmark":
            benchmark()
        elif args.command == "optimize":
            optimize_validate()
        elif args.command == "monitor":
            monitor()
        elif args.command == "profile":
            import sys
            opt_script = PROJECT_ROOT / "scripts" / "optimization_tasks.py"
            if opt_script.exists():
                run_command([sys.executable, str(opt_script), "profile"], check=False)
        elif args.command == "package":
            package_app()
        elif args.command == "clean":
            clean()
        elif args.command == "test:auto":
            import sys
            auto_test = PROJECT_ROOT / "scripts" / "auto_test.py"
            if auto_test.exists():
                run_command([sys.executable, str(auto_test)], check=False)
        elif args.command == "test:visual:workspace":
            import sys
            visual_test = PROJECT_ROOT / "scripts" / "run_visual_tests_in_workspace.py"
            if visual_test.exists():
                run_command([sys.executable, str(visual_test)], check=False)
        elif args.command == "test:watch":
            import sys
            watch_test = PROJECT_ROOT / "scripts" / "watch_tests.py"
            if watch_test.exists():
                run_command([sys.executable, str(watch_test)], check=False)
        elif args.command == "test:ui":
            import sys
            test_runner = PROJECT_ROOT / "scripts" / "run_tests_in_workspace.py"
            if test_runner.exists():
                run_command([sys.executable, str(test_runner), "--type", "ui"], check=False)
        elif args.command == "test:headed":
            import sys
            test_runner = PROJECT_ROOT / "scripts" / "run_tests_in_workspace.py"
            if test_runner.exists():
                run_command([sys.executable, str(test_runner), "--type", "visual", "--headed"], check=False)
        elif args.command == "test:pipeline":
            import sys
            pipeline = PROJECT_ROOT / "scripts" / "automated_test_pipeline.py"
            if pipeline.exists():
                run_command([sys.executable, str(pipeline)], check=False)
        elif args.command == "test:pipeline:watch":
            import sys
            pipeline = PROJECT_ROOT / "scripts" / "automated_test_pipeline.py"
            if pipeline.exists():
                run_command([sys.executable, str(pipeline), "--watch"], check=False)
    except KeyboardInterrupt:
        print_info("\nOperation cancelled by user")
    except Exception as e:
        print_error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

