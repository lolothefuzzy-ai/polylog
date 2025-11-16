#!/usr/bin/env python3
"""
Verify Full System Integration
Checks that all components are properly integrated
"""

import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
SRC_DIR = PROJECT_ROOT / "src"

def check_python_imports():
    """Check Python imports work"""
    print("[CHECK] Python imports...")
    try:
        sys.path.insert(0, str(SRC_DIR))
        from polylog6.api import main
        print("  [OK] Python API imports")
        return True
    except Exception as e:
        print(f"  [FAIL] Python imports: {e}")
        return False

def check_frontend_build():
    """Check frontend can build"""
    print("[CHECK] Frontend build...")
    frontend_dir = PROJECT_ROOT / "src" / "frontend"
    if not frontend_dir.exists():
        print("  [SKIP] Frontend directory not found")
        return True
    
    try:
        result = subprocess.run(
            ["npm", "list", "--depth=0"],
            cwd=frontend_dir,
            capture_output=True,
            timeout=10
        )
        if result.returncode == 0:
            print("  [OK] Frontend dependencies installed")
            return True
        else:
            print("  [WARN] Frontend dependencies may be missing")
            return False
    except Exception as e:
        print(f"  [WARN] Frontend check failed: {e}")
        return False

def check_scripts():
    """Check essential scripts exist"""
    print("[CHECK] Essential scripts...")
    essential = [
        "unified_launcher.py",
        "run_tests_in_workspace.py",
        "organize_project.py",
        "final_cleanup.py"
    ]
    
    scripts_dir = PROJECT_ROOT / "scripts"
    missing = []
    for script in essential:
        if not (scripts_dir / script).exists():
            missing.append(script)
    
    if missing:
        print(f"  [FAIL] Missing scripts: {missing}")
        return False
    else:
        print("  [OK] All essential scripts present")
        return True

def check_workflows():
    """Check GitHub Actions workflows"""
    print("[CHECK] GitHub Actions workflows...")
    workflows_dir = PROJECT_ROOT / ".github" / "workflows"
    
    if not workflows_dir.exists():
        print("  [WARN] .github/workflows directory not found")
        return False
    
    workflows = list(workflows_dir.glob("*.yml"))
    if workflows:
        print(f"  [OK] Found {len(workflows)} workflow(s)")
        return True
    else:
        print("  [WARN] No workflows found")
        return False

def check_docs():
    """Check essential documentation"""
    print("[CHECK] Essential documentation...")
    essential = [
        "README.md",
        "docs/ARCHITECTURE.md",
        "docs/DEVELOPMENT.md"
    ]
    
    missing = []
    for doc in essential:
        if not (PROJECT_ROOT / doc).exists():
            missing.append(doc)
    
    if missing:
        print(f"  [WARN] Missing docs: {missing}")
        return False
    else:
        print("  [OK] Essential documentation present")
        return True

def main():
    print("=" * 70)
    print("Full System Integration Check")
    print("=" * 70)
    
    checks = [
        check_python_imports(),
        check_frontend_build(),
        check_scripts(),
        check_workflows(),
        check_docs()
    ]
    
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    
    passed = sum(checks)
    total = len(checks)
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n[SUCCESS] All integration checks passed!")
        return 0
    else:
        print("\n[WARN] Some checks failed - review above")
        return 1

if __name__ == "__main__":
    sys.exit(main())

