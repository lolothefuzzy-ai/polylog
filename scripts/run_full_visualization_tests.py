#!/usr/bin/env python3
"""
Run Full Visualization Test Suite
Starts servers, runs all tests, and provides interactive feedback
"""

import subprocess
import sys
import time
import webbrowser
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
FRONTEND_DIR = PROJECT_ROOT / "src" / "frontend"

def run_command(cmd, cwd=None, check=True):
    """Run a command and return result"""
    print(f"\n[RUN] {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    result = subprocess.run(
        cmd if isinstance(cmd, list) else cmd.split(),
        cwd=cwd or PROJECT_ROOT,
        shell=True,
        capture_output=True,
        text=True
    )
    if check and result.returncode != 0:
        print(f"[ERROR] Command failed: {result.stderr}")
        return False
    return result.returncode == 0

def main():
    print("=" * 70)
    print("Full Visualization Test Suite")
    print("=" * 70)
    print("\nThis will:")
    print("  1. Clean up existing processes")
    print("  2. Start API and Frontend servers")
    print("  3. Run all visualization tests")
    print("  4. Open browser for interactive testing")
    print("  5. Generate test report")
    print("\n" + "=" * 70 + "\n")
    
    # Step 1: Cleanup
    print("[STEP 1] Cleaning up existing processes...")
    cleanup_script = PROJECT_ROOT / "scripts" / "cleanup_processes.py"
    if cleanup_script.exists():
        run_command([sys.executable, str(cleanup_script)], check=False)
    time.sleep(2)
    
    # Step 2: Start servers
    print("\n[STEP 2] Starting servers...")
    launch_script = PROJECT_ROOT / "scripts" / "launch_visualization_visible.py"
    if launch_script.exists():
        print("[INFO] Starting servers in background...")
        subprocess.Popen([sys.executable, str(launch_script)], 
                        cwd=PROJECT_ROOT)
        print("[WAIT] Waiting for servers to be ready...")
        time.sleep(45)  # Give servers time to start
        
        # Check if servers are ready
        import urllib.request
        api_ready = False
        frontend_ready = False
        
        for i in range(30):
            try:
                urllib.request.urlopen("http://localhost:8000/health", timeout=2)
                api_ready = True
            except:
                pass
            
            try:
                urllib.request.urlopen("http://localhost:5173", timeout=2)
                frontend_ready = True
            except:
                pass
            
            if api_ready and frontend_ready:
                break
            time.sleep(2)
        
        if not api_ready or not frontend_ready:
            print("[WARN] Servers may not be fully ready, continuing anyway...")
    else:
        print("[ERROR] Launch script not found!")
        return 1
    
    # Step 3: Run tests
    print("\n[STEP 3] Running visualization tests...")
    print("\n" + "-" * 70)
    print("Running Backend Stability Tests...")
    print("-" * 70)
    run_command([sys.executable, "scripts/run_backend_stability_tests.py"], check=False)
    
    print("\n" + "-" * 70)
    print("Running Playwright Visual Tests...")
    print("-" * 70)
    run_command(["npx", "playwright", "test", "tests/visual"], 
                cwd=FRONTEND_DIR, check=False)
    
    print("\n" + "-" * 70)
    print("Running Playwright Integration Tests...")
    print("-" * 70)
    run_command(["npx", "playwright", "test", "tests/integration"], 
                cwd=FRONTEND_DIR, check=False)
    
    # Step 4: Open browser for interactive testing
    print("\n[STEP 4] Opening browser for interactive testing...")
    time.sleep(2)
    webbrowser.open("http://localhost:5173")
    
    # Step 5: Generate test report
    print("\n[STEP 5] Generating test report...")
    run_command(["npx", "playwright", "show-report"], 
                cwd=FRONTEND_DIR, check=False)
    
    print("\n" + "=" * 70)
    print("Test Suite Complete!")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Review test results above")
    print("  2. Interact with the visualization in the browser")
    print("  3. Check the test report (should have opened automatically)")
    print("  4. Provide feedback on what works and what needs improvement")
    print("\nTest report location: src/frontend/playwright-report/")
    print("=" * 70)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

