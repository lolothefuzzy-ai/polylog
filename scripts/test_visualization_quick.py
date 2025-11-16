#!/usr/bin/env python3
"""
Quick Visualization Test
Tests if visualization window works
"""

import sys
import subprocess
import time
import webbrowser
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

def check_server(url, timeout=2):
    """Check if server is running"""
    import urllib.request
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return response.status == 200
    except:
        return False

def main():
    print("=" * 70)
    print("Quick Visualization Test")
    print("=" * 70)
    
    # Check if servers are running
    api_ready = check_server("http://localhost:8000/health")
    frontend_ready = check_server("http://localhost:5173")
    
    if api_ready and frontend_ready:
        print("\n[OK] Servers are running!")
        print("[INFO] Opening browser at http://localhost:5173")
        webbrowser.open("http://localhost:5173")
        print("[SUCCESS] Browser opened - visualization should be visible")
        return True
    
    print("\n[INFO] Starting servers...")
    print("[INFO] Run: python scripts/unified_launcher.py dev")
    print("[INFO] Then open: http://localhost:5173")
    return False

if __name__ == "__main__":
    main()

