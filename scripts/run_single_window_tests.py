#!/usr/bin/env python3
"""
Run Single Window Test Suite
ONE browser window, background servers, continuous testing
"""

import subprocess
import sys
import time
import webbrowser
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
FRONTEND_DIR = PROJECT_ROOT / "src" / "frontend"

def main():
    print("=" * 70)
    print("Single Window Test Environment")
    print("=" * 70)
    print("\nLaunching unified test environment...")
    print("  • Servers: Background (no windows)")
    print("  • Browser: ONE window")
    print("  • Tests: Continuous in same window")
    print("=" * 70 + "\n")
    
    # Use the unified single window script
    script = PROJECT_ROOT / "scripts" / "unified_single_window_test.py"
    if script.exists():
        subprocess.run([sys.executable, str(script)])
    else:
        print("[ERROR] Unified script not found")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

