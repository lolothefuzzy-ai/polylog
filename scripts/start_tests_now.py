#!/usr/bin/env python3
"""
Start tests immediately with visible browser
"""

import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
FRONTEND_DIR = PROJECT_ROOT / "src" / "frontend"

def main():
    print("=" * 60)
    print("Starting test pipeline with visible browser...")
    print("=" * 60)
    
    # Start servers in background
    print("\n[1/3] Starting servers...")
    dev_process = subprocess.Popen(
        [sys.executable, "scripts/dev_integrated.py"],
        cwd=PROJECT_ROOT,
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
    )
    
    # Wait for servers
    print("[2/3] Waiting for servers to start (15 seconds)...")
    time.sleep(15)
    
    # Run tests in headed mode
    print("[3/3] Running tests in visible browser...")
    print("Browser window will open now!")
    print("=" * 60)
    
    # Run Playwright tests directly with headed mode
    # Use npm script which handles npx properly
    import shutil
    npm_path = shutil.which("npm")
    if not npm_path:
        print("ERROR: npm not found in PATH")
        print("Please ensure Node.js is installed and in PATH")
        return 1
    
    result = subprocess.run(
        [npm_path, "run", "test:visual", "--", "tests/integration", "--project=chromium"],
        cwd=FRONTEND_DIR
    )
    
    print("\n" + "=" * 60)
    if result.returncode == 0:
        print("All tests passed!")
    else:
        print("Some tests failed - check browser window for details")
    print("=" * 60)
    
    return result.returncode

if __name__ == "__main__":
    import os
    sys.exit(main())

