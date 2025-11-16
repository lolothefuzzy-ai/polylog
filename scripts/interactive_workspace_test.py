#!/usr/bin/env python3
"""
Interactive Workspace Test Runner
Starts servers, runs interactive tests, monitors results, and fixes issues
"""

import subprocess
import sys
import time
import json
import re
from pathlib import Path
from typing import Dict, List, Optional

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
FRONTEND_DIR = PROJECT_ROOT / "src" / "frontend"

def check_servers():
    """Check if servers are running"""
    import urllib.request
    import urllib.error
    
    api_running = False
    frontend_running = False
    
    try:
        with urllib.request.urlopen("http://localhost:8000/health", timeout=2) as response:
            api_running = response.status == 200
    except:
        pass
    
    try:
        with urllib.request.urlopen("http://localhost:5173", timeout=2) as response:
            frontend_running = response.status == 200
    except:
        pass
    
    return api_running, frontend_running

def start_servers():
    """Start API and frontend servers"""
    print("[INFO] Starting servers...")
    
    # Start unified launcher in background
    process = subprocess.Popen(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "unified_launcher.py"), "dev"],
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for servers to start
    print("[INFO] Waiting for servers to start...")
    for i in range(60):  # Wait up to 60 seconds
        api_running, frontend_running = check_servers()
        if api_running and frontend_running:
            print("[OK] Servers are running!")
            return process
        time.sleep(1)
        if i % 10 == 0:
            print(f"[INFO] Still waiting... ({i}s)")
    
    print("[WARN] Servers may not have started properly")
    return process

def analyze_test_output(output: str) -> Dict[str, any]:
    """Analyze test output for issues"""
    issues = {
        'errors': [],
        'warnings': [],
        'missing_functionality': [],
        'api_issues': [],
        'tier0_issues': []
    }
    
    lines = output.split('\n')
    
    for line in lines:
        # Check for errors
        if 'error' in line.lower() or 'failed' in line.lower():
            if '[BROWSER ERROR]' in line or '[PAGE ERROR]' in line:
                issues['errors'].append(line)
        
        # Check for warnings
        if 'warning' in line.lower() or 'warn' in line.lower():
            if '[MONITOR]' in line and '⚠️' in line:
                issues['warnings'].append(line)
        
        # Check for missing functionality
        if 'missing' in line.lower() or 'not implemented' in line.lower():
            issues['missing_functionality'].append(line)
        
        # Check for API issues
        if '/api/' in line and ('404' in line or 'failed' in line.lower()):
            issues['api_issues'].append(line)
        
        # Check for Tier 0 issues
        if 'tier0' in line.lower() or 'tier 0' in line.lower():
            if 'not generated' in line.lower() or 'failed' in line.lower():
                issues['tier0_issues'].append(line)
    
    return issues

def suggest_fixes(issues: Dict[str, List[str]]) -> List[str]:
    """Suggest fixes based on issues found"""
    fixes = []
    
    if issues['errors']:
        fixes.append("Fix browser errors - check console logs")
        fixes.append("Verify API endpoints are accessible")
        fixes.append("Check CORS configuration")
    
    if issues['api_issues']:
        fixes.append("Verify API server is running on port 8000")
        fixes.append("Check API routes are registered in main.py")
        fixes.append("Verify API endpoints match frontend calls")
    
    if issues['tier0_issues']:
        fixes.append("Check Tier 0 symbol generation logic")
        fixes.append("Verify workspace manager is creating chains")
        fixes.append("Check Tier 0 API endpoints")
    
    if issues['missing_functionality']:
        fixes.append("Implement missing functionality")
        fixes.append("Check feature flags")
    
    return fixes

def run_interactive_test(max_iterations: int = 5):
    """Run interactive test with monitoring and issue resolution"""
    print("=" * 70)
    print("Interactive Workspace Test Runner")
    print("=" * 70)
    print("\n[INFO] This will:")
    print("  1. Start API and frontend servers")
    print("  2. Run interactive workspace monitor test")
    print("  3. Analyze results for issues")
    print("  4. Suggest fixes")
    print("  5. Repeat until stable\n")
    
    # Check if servers are running
    api_running, frontend_running = check_servers()
    
    if not api_running or not frontend_running:
        print("[INFO] Starting servers...")
        server_process = start_servers()
        time.sleep(5)  # Give servers time to fully start
    else:
        print("[OK] Servers already running")
        server_process = None
    
    iteration = 0
    stable = False
    
    while iteration < max_iterations and not stable:
        iteration += 1
        print(f"\n{'=' * 70}")
        print(f"Iteration {iteration}/{max_iterations}")
        print(f"{'=' * 70}\n")
        
        # Run test
        print("[TEST] Running interactive workspace monitor test...")
        result = subprocess.run(
            ["npx", "playwright", "test", 
             "tests/integration/interactive-workspace-monitor.spec.js",
             "--headed", "--project=chromium", "--timeout=360000"],  # 6 minute timeout
            cwd=FRONTEND_DIR,
            capture_output=True,
            text=True,
            timeout=400  # 6.5 minutes max
        )
        
        # Analyze output
        output = result.stdout + result.stderr
        issues = analyze_test_output(output)
        
        # Print results
        print("\n[ANALYSIS] Test Results:")
        print(f"  - Exit code: {result.returncode}")
        print(f"  - Errors: {len(issues['errors'])}")
        print(f"  - Warnings: {len(issues['warnings'])}")
        print(f"  - Missing functionality: {len(issues['missing_functionality'])}")
        print(f"  - API issues: {len(issues['api_issues'])}")
        print(f"  - Tier 0 issues: {len(issues['tier0_issues'])}")
        
        # Show issues
        if issues['errors']:
            print("\n[ERRORS] Found errors:")
            for error in issues['errors'][:5]:  # Show first 5
                print(f"  - {error}")
        
        if issues['warnings']:
            print("\n[WARNINGS] Found warnings:")
            for warning in issues['warnings'][:5]:  # Show first 5
                print(f"  - {warning}")
        
        # Check if stable
        if result.returncode == 0 and len(issues['errors']) == 0:
            stable = True
            print("\n[SUCCESS] ✅ Browser deployment is stable!")
            print("[SUCCESS] No errors detected, test passed")
        else:
            # Suggest fixes
            fixes = suggest_fixes(issues)
            if fixes:
                print("\n[FIXES] Suggested fixes:")
                for fix in fixes:
                    print(f"  - {fix}")
            
            if iteration < max_iterations:
                print(f"\n[INFO] Will retry (iteration {iteration + 1}/{max_iterations})")
                print("[INFO] Please review and fix issues, then press Enter to continue...")
                input()
    
    if stable:
        print("\n" + "=" * 70)
        print("✅ INTERACTIVE WORKSPACE TEST COMPLETE - STABLE")
        print("=" * 70)
        return True
    else:
        print("\n" + "=" * 70)
        print("⚠️  INTERACTIVE WORKSPACE TEST COMPLETE - ISSUES REMAIN")
        print("=" * 70)
        print("\n[INFO] Review issues above and fix manually")
        return False

if __name__ == "__main__":
    try:
        success = run_interactive_test(max_iterations=5)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n[INFO] Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

