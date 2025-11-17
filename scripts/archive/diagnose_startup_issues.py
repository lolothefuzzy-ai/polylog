#!/usr/bin/env python3
"""
Diagnose Startup Issues
Comprehensive diagnosis of potential startup problems
"""

import sys
import subprocess
import importlib.util
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
FRONTEND_DIR = PROJECT_ROOT / "src" / "frontend"

def check_python_dependencies():
    """Check Python dependencies"""
    print("\n[DIAGNOSIS] Checking Python dependencies...")
    issues = []
    
    required_modules = [
        'fastapi',
        'uvicorn',
        'pydantic',
        'numpy',
    ]
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"  [OK] {module}")
        except ImportError:
            print(f"  [MISSING] {module}")
            issues.append(f"Missing Python module: {module}")
    
    return issues

def check_node_dependencies():
    """Check Node dependencies"""
    print("\n[DIAGNOSIS] Checking Node dependencies...")
    issues = []
    
    try:
        result = subprocess.run(
            ["npm", "list", "--depth=0"],
            cwd=FRONTEND_DIR,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print("  [FAIL] npm list failed")
            issues.append("Node dependencies may not be installed")
            print("  Run: cd src/frontend && npm install")
        else:
            print("  [OK] Node dependencies installed")
    except Exception as e:
        print(f"  [ERROR] Error checking Node dependencies: {e}")
        issues.append(f"Error checking Node: {e}")
    
    return issues

def check_api_imports():
    """Check if API modules can be imported"""
    print("\n[DIAGNOSIS] Checking API imports...")
    issues = []
    
    try:
        # Add src to path for imports
        src_path = PROJECT_ROOT / "src"
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
        
        # Check main API
        spec = importlib.util.spec_from_file_location(
            "main", PROJECT_ROOT / "src" / "polylog6" / "api" / "main.py"
        )
        if spec is None:
            issues.append("Cannot load API main.py")
            return issues
        
        main_module = importlib.util.module_from_spec(spec)
        
        # Try to load (this will show import errors)
        try:
            spec.loader.exec_module(main_module)
            print("  [OK] API main.py imports successfully")
        except Exception as e:
            print(f"  [FAIL] API import error: {e}")
            issues.append(f"API import error: {e}")
        
        # Check Tier 0 router
        try:
            from polylog6.api import tier0
            print("  [OK] Tier 0 router imports successfully")
        except Exception as e:
            print(f"  [FAIL] Tier 0 router import error: {e}")
            issues.append(f"Tier 0 router import error: {e}")
        
        # Check geometry router
        try:
            from polylog6.api import geometry
            print("  [OK] Geometry router imports successfully")
        except Exception as e:
            print(f"  [FAIL] Geometry router import error: {e}")
            issues.append(f"Geometry router import error: {e}")
            
    except Exception as e:
        print(f"  [ERROR] Error checking imports: {e}")
        issues.append(f"Import check error: {e}")
    
    return issues

def check_file_structure():
    """Check critical file structure"""
    print("\n[DIAGNOSIS] Checking file structure...")
    issues = []
    
    critical_files = [
        PROJECT_ROOT / "src" / "polylog6" / "api" / "main.py",
        PROJECT_ROOT / "src" / "polylog6" / "api" / "tier0.py",
        PROJECT_ROOT / "src" / "polylog6" / "api" / "geometry.py",
        PROJECT_ROOT / "src" / "frontend" / "package.json",
        PROJECT_ROOT / "src" / "frontend" / "vite.config.js",
        PROJECT_ROOT / "src" / "frontend" / "src" / "main.jsx",
        PROJECT_ROOT / "scripts" / "unified_launcher.py",
    ]
    
    for file_path in critical_files:
        if file_path.exists():
            print(f"  [OK] {file_path.relative_to(PROJECT_ROOT)}")
        else:
            print(f"  [MISSING] {file_path.relative_to(PROJECT_ROOT)}")
            issues.append(f"Missing file: {file_path}")
    
    return issues

def check_port_availability():
    """Check if ports are available"""
    print("\n[DIAGNOSIS] Checking port availability...")
    issues = []
    
    import socket
    
    ports = [8000, 5173]
    for port in ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        
        if result == 0:
            print(f"  [WARN] Port {port} is in use")
            issues.append(f"Port {port} is already in use")
        else:
            print(f"  [OK] Port {port} is available")
    
    return issues

def check_configuration():
    """Check configuration files"""
    print("\n[DIAGNOSIS] Checking configuration...")
    issues = []
    
    # Check Playwright config
    playwright_config = FRONTEND_DIR / "playwright.config.js"
    if playwright_config.exists():
        content = playwright_config.read_text()
        if "baseURL" in content and "localhost:5173" in content:
            print("  [OK] Playwright config looks good")
        else:
            print("  [WARN] Playwright config may need review")
    else:
        print("  [MISSING] Playwright config")
        issues.append("Playwright config missing")
    
    # Check Vite config
    vite_config = FRONTEND_DIR / "vite.config.js"
    if vite_config.exists():
        content = vite_config.read_text()
        if "server" in content.lower() or "port" in content.lower():
            print("  [OK] Vite config exists")
        else:
            print("  [WARN] Vite config may need server configuration")
    else:
        print("  [MISSING] Vite config")
        issues.append("Vite config missing")
    
    return issues

def main():
    print("=" * 70)
    print("Startup Issue Diagnosis")
    print("=" * 70)
    
    all_issues = []
    
    # Run all checks
    all_issues.extend(check_file_structure())
    all_issues.extend(check_python_dependencies())
    all_issues.extend(check_node_dependencies())
    all_issues.extend(check_api_imports())
    all_issues.extend(check_port_availability())
    all_issues.extend(check_configuration())
    
    # Summary
    print("\n" + "=" * 70)
    print("Diagnosis Summary")
    print("=" * 70)
    
    if not all_issues:
        print("\n[SUCCESS] No issues detected!")
        print("System should be ready to start.")
    else:
        print(f"\n[WARN] Found {len(all_issues)} issue(s):")
        for i, issue in enumerate(all_issues, 1):
            print(f"  {i}. {issue}")
        
        print("\nRecommended fixes:")
        if any("Missing Python module" in issue for issue in all_issues):
            print("  - Install Python dependencies: pip install -r requirements.txt")
        if any("Node dependencies" in issue for issue in all_issues):
            print("  - Install Node dependencies: cd src/frontend && npm install")
        if any("Port" in issue and "in use" in issue for issue in all_issues):
            print("  - Kill processes on ports 8000/5173 or use different ports")
        if any("import error" in issue.lower() for issue in all_issues):
            print("  - Check Python path and module structure")
            print("  - Verify all API routers are properly registered")
    
    print("=" * 70)
    
    return len(all_issues) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

