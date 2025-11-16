#!/usr/bin/env python3
"""Automated integration planning based on test results"""
import subprocess
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

def get_test_results():
    """Run tests and get results"""
    result = subprocess.run(
        [sys.executable, "scripts/validate_engines.py"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    return result.returncode == 0, result.stdout

def create_integration_plan(tests_passed):
    """Create next integration plan based on test results"""
    if tests_passed:
        plan = {
            "phase": "Phase 2: Pre-computation",
            "tasks": [
                "Generate scalar variants (485 total)",
                "Generate attachment patterns (750 total)",
                "Compute full attachment matrix",
                "Update API endpoints for new data",
                "Build frontend components for full library",
                "Test with complete dataset"
            ],
            "estimated_time": "7-8 hours",
            "priority": "high"
        }
    else:
        plan = {
            "phase": "Phase 1: Fix Current Issues",
            "tasks": [
                "Fix failing engine imports",
                "Resolve test failures",
                "Verify API endpoints",
                "Test storage persistence"
            ],
            "estimated_time": "2-3 hours",
            "priority": "critical"
        }
    
    return plan

def main():
    print("Running automated integration planning...")
    tests_passed, output = get_test_results()
    
    print("\nTest Results:")
    print(output)
    
    plan = create_integration_plan(tests_passed)
    
    print(f"\n{'='*60}")
    print(f"Next Integration Phase: {plan['phase']}")
    print(f"{'='*60}\n")
    
    for i, task in enumerate(plan['tasks'], 1):
        print(f"{i}. {task}")
    
    print(f"\nEstimated Time: {plan['estimated_time']}")
    print(f"Priority: {plan['priority']}")
    
    # Save plan
    plan_file = PROJECT_ROOT / "NEXT_INTEGRATION_PLAN.json"
    with open(plan_file, "w") as f:
        json.dump(plan, f, indent=2)
    
    print(f"\nPlan saved to: {plan_file}")

if __name__ == "__main__":
    main()

