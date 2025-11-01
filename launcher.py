#!/usr/bin/env python3
"""
Polylog Launcher - Simplified project startup

Automates environment setup and mode selection
"""

import os
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()

# Update the path to migration_workflow
MIGRATION_SCRIPT = "scripts/migration_workflow.py"

def ensure_venv():
    """Ensure virtual environment exists and is activated"""
    venv_path = PROJECT_ROOT / "venv"
    if not venv_path.exists():
        print("Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", "venv"], cwd=PROJECT_ROOT)
    
    # Activate venv
    if sys.platform == "win32":
        activate_script = "venv\\Scripts\\activate.bat"
        activate_cmd = f"call {activate_script}"
    else:
        activate_script = "venv/bin/activate"
        activate_cmd = f"source {activate_script}"
    
    print(f"Activating virtual environment: {activate_cmd}")
    return activate_cmd


def install_dependencies():
    """Install required packages"""
    requirements = PROJECT_ROOT / "requirements.txt"
    if requirements.exists():
        print("Installing dependencies...")
        subprocess.run(["pip", "install", "-r", "requirements.txt"], cwd=PROJECT_ROOT)
    else:
        print("Warning: requirements.txt not found")


def run_main(mode):
    """Run main.py with specified mode"""
    main_script = PROJECT_ROOT / "Properties" / "Code" / "main.py"
    if not main_script.exists():
        print("Error: main.py not found")
        return
    
    print(f"Starting Polylog in {mode} mode...")
    subprocess.run(["python", "Properties/Code/main.py", mode], cwd=PROJECT_ROOT)


def main():
    # Ensure environment
    activate_cmd = ensure_venv()
    install_dependencies()
    
    # Mode selection
    print("\nSelect mode:")
    print("  1. GUI")
    print("  2. API")
    print("  3. Demo")
    choice = input("Enter choice (1-3): ").strip()
    
    if choice == "1":
        run_main("gui")
    elif choice == "2":
        run_main("api")
    elif choice == "3":
        run_main("demo")
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
