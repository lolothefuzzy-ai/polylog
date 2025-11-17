#!/usr/bin/env python3
"""
Build script for Polylog6
Builds frontend and Tauri desktop application for production
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
FRONTEND_DIR = PROJECT_ROOT / "src" / "frontend"
DESKTOP_DIR = PROJECT_ROOT / "src" / "desktop"
TAURI_DIR = DESKTOP_DIR / "src-tauri"

def build_frontend():
    """Build frontend for production"""
    print("[BUILD] Building frontend...")
    if not (FRONTEND_DIR / "package.json").exists():
        print("[ERROR] Frontend package.json not found")
        return False
    
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=FRONTEND_DIR,
        capture_output=False
    )
    return result.returncode == 0

def build_tauri():
    """Build Tauri desktop application"""
    print("[BUILD] Building Tauri application...")
    if not TAURI_DIR.exists():
        print("[ERROR] Tauri directory not found")
        return False
    
    # Build Rust backend
    result = subprocess.run(
        ["cargo", "build", "--release"],
        cwd=TAURI_DIR,
        capture_output=False
    )
    if result.returncode != 0:
        return False
    
    return True

def build_all():
    """Build complete application"""
    print("[BUILD] Building Polylog6 Desktop Application")
    print("=" * 60)
    
    if not build_frontend():
        print("[ERROR] Frontend build failed")
        return False
    
    if not build_tauri():
        print("[ERROR] Tauri build failed")
        return False
    
    print("[SUCCESS] Build complete!")
    return True

if __name__ == "__main__":
    success = build_all()
    sys.exit(0 if success else 1)

