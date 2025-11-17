#!/usr/bin/env python3
"""
Polylog6 Unified Launcher
Handles all build, launch, and development tasks
"""

import argparse
import subprocess
import sys
from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).parent.parent.resolve()


def run_command(cmd, cwd=None, check=True):
    """Run a command with proper error handling"""
    print(f"Running: {' '.join(cmd)}")
    if cwd:
        print(f"Working directory: {cwd}")
    
    result = subprocess.run(cmd, cwd=cwd or PROJECT_ROOT, check=check)
    return result.returncode


def ensure_venv():
    """Ensure virtual environment exists"""
    venv_path = PROJECT_ROOT / "venv"
    if not venv_path.exists():
        print("Creating virtual environment...")
        run_command([sys.executable, "-m", "venv", "venv"])
    
    # Return activation command for Windows
    if sys.platform == "win32":
        return venv_path / "Scripts" / "activate"
    else:
        return venv_path / "bin" / "activate"


def install_deps():
    """Install Python dependencies"""
    requirements_files = [
        PROJECT_ROOT / "requirements" / "base.txt",
        PROJECT_ROOT / "requirements" / "dev.txt"
    ]
    
    for req_file in requirements_files:
        if req_file.exists():
            print(f"Installing from {req_file}")
            run_command(["pip", "install", "-r", str(req_file)])
    
    # Check for requirements.txt in root for backward compatibility
    root_req = PROJECT_ROOT / "requirements.txt"
    if root_req.exists():
        print("Installing from requirements.txt")
        run_command(["pip", "install", "-r", str(root_req)])


def install_node_deps():
    """Install Node.js dependencies"""
    package_json = PROJECT_ROOT / "src" / "frontend" / "package.json"
    if package_json.exists():
        print("Installing Node.js dependencies...")
        run_command(["npm", "install"], cwd=PROJECT_ROOT / "src" / "frontend")


def build_tauri():
    """Build Tauri desktop application"""
    print("Building Tauri application...")
    run_command(["cargo", "build", "--release"], cwd=PROJECT_ROOT / "src" / "desktop" / "src-tauri")


def build_frontend():
    """Build frontend for production"""
    print("Building frontend...")
    run_command(["npm", "run", "build"], cwd=PROJECT_ROOT / "src" / "frontend")


def build_all():
    """Build complete application"""
    print("=== Building Polylog6 ===")
    ensure_venv()
    install_deps()
    install_node_deps()
    build_frontend()
    build_tauri()
    print("Build complete!")


def dev_frontend():
    """Start frontend development server"""
    print("Starting frontend development server...")
    run_command(["npm", "run", "dev"], cwd=PROJECT_ROOT / "src" / "frontend")


def dev_api():
    """Start API development server"""
    print("Starting API development server...")
    activate = ensure_venv()
    env = os.environ.copy()
    if sys.platform == "win32":
        env["PATH"] = str(activate.parent) + os.pathsep + env["PATH"]
    
    # Look for main.py in the new structure
    main_paths = [
        PROJECT_ROOT / "src" / "polylog6" / "api" / "main.py",
        PROJECT_ROOT / "src" / "polylog6" / "main.py",
        PROJECT_ROOT / "src" / "polylog6" / "api" / "__main__.py"
    ]
    
    main_py = None
    for path in main_paths:
        if path.exists():
            main_py = path
            break
    
    if main_py:
        run_command(["python", str(main_py), "api"], env=env)
    else:
        print("API main.py not found. Please check the source structure.")


def dev_tauri():
    """Start Tauri development mode"""
    print("Starting Tauri development...")
    run_command(["npm", "run", "tauri", "dev"], cwd=PROJECT_ROOT / "src" / "frontend")


def run_tests():
    """Run all tests"""
    print("Running Python tests...")
    activate = ensure_venv()
    env = os.environ.copy()
    if sys.platform == "win32":
        env["PATH"] = str(activate.parent) + os.pathsep + env["PATH"]
    
    run_command(["python", "-m", "pytest"], cwd=PROJECT_ROOT / "tests", env=env)
    
    print("Running frontend tests...")
    run_command(["npm", "run", "test:integration"], cwd=PROJECT_ROOT / "src" / "frontend")


def clean():
    """Clean build artifacts and caches"""
    print("Cleaning build artifacts...")
    
    # Clean Python caches
    for pattern in ["__pycache__", "*.pyc", ".pytest_cache", ".ruff_cache"]:
        for item in PROJECT_ROOT.rglob(pattern):
            if item.is_dir():
                print(f"Removing directory: {item}")
                item.rmdir()
            else:
                print(f"Removing file: {item}")
                item.unlink()
    
    # Clean Node modules
    node_modules = PROJECT_ROOT / "src" / "frontend" / "node_modules"
    if node_modules.exists():
        print(f"Removing: {node_modules}")
        import shutil
        shutil.rmtree(node_modules, ignore_errors=True)
    
    # Clean Tauri build artifacts
    target_dir = PROJECT_ROOT / "src" / "desktop" / "src-tauri" / "target"
    if target_dir.exists():
        print(f"Removing: {target_dir}")
        import shutil
        shutil.rmtree(target_dir, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description="Polylog6 Unified Launcher")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Build commands
    subparsers.add_parser("build", help="Build complete application")
    subparsers.add_parser("build:frontend", help="Build frontend only")
    subparsers.add_parser("build:tauri", help="Build Tauri backend only")
    
    # Development commands
    subparsers.add_parser("dev", help="Start full development environment")
    subparsers.add_parser("dev:frontend", help="Start frontend dev server")
    subparsers.add_parser("dev:api", help="Start API dev server")
    subparsers.add_parser("dev:tauri", help="Start Tauri dev mode")
    
    # Utility commands
    subparsers.add_parser("install", help="Install all dependencies")
    subparsers.add_parser("test", help="Run all tests")
    subparsers.add_parser("clean", help="Clean build artifacts")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == "build":
        build_all()
    elif args.command == "build:frontend":
        build_frontend()
    elif args.command == "build:tauri":
        build_tauri()
    elif args.command == "dev":
        # Start dev API and frontend concurrently
        import threading
        api_thread = threading.Thread(target=dev_api)
        api_thread.daemon = True
        api_thread.start()
        dev_frontend()
    elif args.command == "dev:frontend":
        dev_frontend()
    elif args.command == "dev:api":
        dev_api()
    elif args.command == "dev:tauri":
        dev_tauri()
    elif args.command == "install":
        ensure_venv()
        install_deps()
        install_node_deps()
    elif args.command == "test":
        run_tests()
    elif args.command == "clean":
        clean()


if __name__ == "__main__":
    main()