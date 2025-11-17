#!/usr/bin/env python3
"""
Run Unified Test Suite
Launches system, tracks interactions, and runs all tests in one session
"""

import subprocess
import sys
import time
import webbrowser
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
FRONTEND_DIR = PROJECT_ROOT / "src" / "frontend"

def main():
    print("=" * 70)
    print("Unified Test Suite Runner")
    print("=" * 70)
    print("\nThis will:")
    print("  1. Launch API and Frontend servers")
    print("  2. Open browser for interactive testing")
    print("  3. Run automated tests in the same browser session")
    print("  4. Track all user interactions")
    print("  5. Generate test cases from interactions")
    print("\n" + "=" * 70 + "\n")
    
    # Step 1: Cleanup and start servers
    print("[STEP 1] Starting servers...")
    cleanup_script = PROJECT_ROOT / "scripts" / "cleanup_processes.py"
    if cleanup_script.exists():
        subprocess.run([sys.executable, str(cleanup_script)], 
                      capture_output=True, timeout=10)
        time.sleep(2)
    
    launch_script = PROJECT_ROOT / "scripts" / "launch_visualization_visible.py"
    if launch_script.exists():
        subprocess.Popen([sys.executable, str(launch_script)], 
                        cwd=PROJECT_ROOT)
        print("[WAIT] Waiting for servers...")
        time.sleep(45)
        
        # Check servers
        import urllib.request
        try:
            urllib.request.urlopen("http://localhost:8000/health", timeout=2)
            urllib.request.urlopen("http://localhost:5173", timeout=2)
            print("[OK] Servers ready!")
        except:
            print("[WARN] Servers may not be ready")
    
    # Step 2: Open browser
    print("\n[STEP 2] Opening browser...")
    time.sleep(2)
    webbrowser.open("http://localhost:5173")
    
    # Step 3: Run unified interactive tests
    print("\n[STEP 3] Running unified interactive tests...")
    print("=" * 70)
    
    cmd = [
        "npx", "playwright", "test",
        "tests/integration/unified-interactive-test.spec.js",
        "--headed",
        "--project=chromium",
        "--trace=on",
        "--video=on"
    ]
    
    result = subprocess.run(
        cmd,
        cwd=FRONTEND_DIR,
        shell=True
    )
    
    # Step 4: Run other test suites
    print("\n[STEP 4] Running additional test suites...")
    print("=" * 70)
    
    test_suites = [
        "tests/visual/backend-stability.spec.js",
        "tests/integration/workspace-interaction.spec.js",
        "tests/integration/api-coverage.spec.js"
    ]
    
    for suite in test_suites:
        print(f"\n[TEST] Running {suite}...")
        subprocess.run(
            ["npx", "playwright", "test", suite, "--headed", "--project=chromium"],
            cwd=FRONTEND_DIR,
            shell=True
        )
    
    # Step 5: Show test report
    print("\n[STEP 5] Opening test report...")
    subprocess.run(
        ["npx", "playwright", "show-report"],
        cwd=FRONTEND_DIR,
        shell=True
    )
    
    print("\n" + "=" * 70)
    print("Test Suite Complete!")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Review test results in the report")
    print("  2. Check interaction logs in test-results/interactions/")
    print("  3. Review generated test cases")
    print("  4. Provide feedback on what works and what needs improvement")
    print("=" * 70)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

