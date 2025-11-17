#!/usr/bin/env python3
"""
Check Integration Status
Diagnoses issues preventing browser launch
"""

import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
FRONTEND_DIR = PROJECT_ROOT / "src" / "frontend"

def check_python_imports():
    """Check if Python imports work"""
    print("[CHECK] Python imports...")
    try:
        sys.path.insert(0, str(PROJECT_ROOT / "src"))
        from polylog6.api import main
        print("[OK] Python imports successful")
        return True
    except Exception as e:
        print(f"[FAIL] Python import error: {e}")
        return False

def check_dependencies():
    """Check required dependencies"""
    print("[CHECK] Dependencies...")
    required = {
        "fastapi": "FastAPI",
        "uvicorn": "Uvicorn",
        "psutil": "psutil"
    }
    
    missing = []
    for module, name in required.items():
        try:
            __import__(module)
            print(f"[OK] {name} installed")
        except ImportError:
            print(f"[FAIL] {name} missing")
            missing.append(module)
    
    if missing:
        print(f"\n[INFO] Installing missing: {', '.join(missing)}")
        for dep in missing:
            subprocess.run([sys.executable, "-m", "pip", "install", dep], check=True)
        print("[OK] Dependencies installed")
    
    return len(missing) == 0

def check_node_modules():
    """Check if node_modules exists"""
    print("[CHECK] Node modules...")
    if (FRONTEND_DIR / "node_modules").exists():
        print("[OK] node_modules exists")
        return True
    else:
        print("[FAIL] node_modules missing")
        print("[INFO] Run: cd src/frontend && npm install")
        return False

def check_ports():
    """Check if ports are available"""
    print("[CHECK] Port availability...")
    import socket
    
    ports = [8000, 5173]
    available = True
    
    for port in ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        
        if result == 0:
            print(f"[WARN] Port {port} is in use")
            available = False
        else:
            print(f"[OK] Port {port} available")
    
    return available

def main():
    print("=" * 70)
    print("Integration Check")
    print("=" * 70)
    print()
    
    all_ok = True
    
    # Check dependencies
    if not check_dependencies():
        all_ok = False
    print()
    
    # Check Python imports
    if not check_python_imports():
        all_ok = False
    print()
    
    # Check node modules
    if not check_node_modules():
        all_ok = False
    print()
    
    # Check ports
    if not check_ports():
        all_ok = False
    print()
    
    print("=" * 70)
    if all_ok:
        print("[SUCCESS] All checks passed - ready to launch!")
        return 0
    else:
        print("[WARN] Some checks failed - fix issues above")
        return 1

if __name__ == "__main__":
    sys.exit(main())

