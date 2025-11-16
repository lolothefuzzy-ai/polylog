#!/usr/bin/env python3
"""Run visual tests with workspace browser viewport"""
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
FRONTEND_DIR = PROJECT_ROOT / "src" / "frontend"

def main():
    print("Starting visual tests in workspace browser...")
    
    # Run Playwright with headed mode for workspace visibility
    result = subprocess.run(
        ["npm", "run", "test:visual", "--", "--headed", "--workers=1"],
        cwd=FRONTEND_DIR,
        capture_output=False
    )
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())

