#!/usr/bin/env python3
"""
Coordinated Test Runner
Runs tests with browser coordination, result analysis, and workflow guidance.
"""

import subprocess
import sys
import time
import re
from pathlib import Path
from typing import Tuple, List, Optional

# Add scripts directory to path for imports
SCRIPTS_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPTS_DIR))

from browser_coordinator import BrowserCoordinator, TestResult

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
FRONTEND_DIR = PROJECT_ROOT / "src" / "frontend"


class TestRunner:
    """Runs tests with coordination and result analysis"""
    
    def __init__(self):
        self.coordinator = BrowserCoordinator()
    
    def analyze_test_output(self, output: str) -> Tuple[TestResult, List[str]]:
        """
        Analyze test output to determine result and missing features.
        Returns (result, missing_features)
        """
        output_lower = output.lower()
        missing_features = []
        
        # Check for missing functionality indicators
        missing_patterns = [
            r"missing.*functionality",
            r"not.*implemented",
            r"not.*found",
            r"endpoint.*not.*found",
            r"404",
            r"method.*not.*allowed",
            r"feature.*not.*available",
            r"not.*supported",
        ]
        
        for pattern in missing_patterns:
            if re.search(pattern, output_lower):
                # Try to extract feature name
                match = re.search(r"(?:missing|not.*implemented|not.*found).*?([a-z_]+)", output_lower)
                if match:
                    missing_features.append(match.group(1))
        
        # Determine result
        if missing_features:
            return TestResult.MISSING_FUNCTIONALITY, missing_features
        elif "passed" in output_lower and "failed" not in output_lower:
            return TestResult.PASS, []
        elif "failed" in output_lower or "error" in output_lower:
            return TestResult.FAIL, []
        else:
            return TestResult.ERROR, []
    
    def run_tests(
        self,
        test_type: str = "visual",
        test_files: Optional[List[str]] = None,
        timeout: int = 300
    ) -> Tuple[bool, str]:
        """
        Run tests with browser coordination.
        Returns (success, output)
        """
        # Check if we can launch
        can_launch, reason = self.coordinator.can_launch_browser()
        if not can_launch:
            print(f"[TEST RUNNER] Cannot run tests: {reason}")
            return False, reason
        
        # Build test command - use npx playwright directly for better control
        cmd = ["npx", "playwright", "test"]
        
        if test_files:
            # Add specific test files
            cmd.extend(test_files)
        elif test_type == "visual":
            cmd.append("tests/visual")
        elif test_type == "integration":
            cmd.append("tests/integration")
        elif test_type == "all":
            pass  # Run all tests
        else:
            cmd.append("tests")
        
        cmd.extend(["--project=chromium", "--headed"])
        
        # Launch browser session
        session_id = self.coordinator.launch_browser(cmd, test_type)
        if not session_id:
            return False, "Could not launch browser session"
        
        print(f"[TEST RUNNER] Running tests in session {session_id}...")
        print(f"[TEST RUNNER] Command: {' '.join(cmd)}")
        
        # Run tests
        try:
            result = subprocess.run(
                cmd,
                cwd=FRONTEND_DIR,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            output = result.stdout + result.stderr
            
            # Analyze results
            test_result, missing_features = self.analyze_test_output(output)
            
            # Record results
            self.coordinator.record_test_result(
                session_id,
                test_result,
                output,
                missing_features
            )
            
            # Print summary
            print("\n" + "=" * 60)
            print("Test Results Summary")
            print("=" * 60)
            print(f"Session ID: {session_id}")
            print(f"Result: {test_result.value}")
            if missing_features:
                print(f"Missing Features: {', '.join(missing_features)}")
            print(f"Exit Code: {result.returncode}")
            
            # Show next steps
            status = self.coordinator.get_status()
            if status['next_steps']:
                print("\nNext Steps:")
                for step in status['next_steps']:
                    print(f"  {step}")
            
            print("=" * 60)
            
            # If missing functionality detected, terminate immediately
            if test_result == TestResult.MISSING_FUNCTIONALITY:
                print("\n[TEST RUNNER] Missing functionality detected - session terminated")
                print("[TEST RUNNER] Implement missing features before running tests again")
            
            return result.returncode == 0, output
            
        except subprocess.TimeoutExpired:
            self.coordinator.record_test_result(
                session_id,
                TestResult.ERROR,
                "Test execution timed out",
                []
            )
            return False, "Test execution timed out"
        
        except Exception as e:
            self.coordinator.record_test_result(
                session_id,
                TestResult.ERROR,
                str(e),
                []
            )
            return False, str(e)
    
    def run_with_workflow(self, test_type: str = "visual"):
        """
        Run tests following the test-driven workflow:
        1. Check if browser can launch
        2. Run tests
        3. Analyze results
        4. Provide guidance for next steps
        5. Wait for user to implement fixes before next launch
        """
        print("\n" + "=" * 60)
        print("Test-Driven Development Workflow")
        print("=" * 60)
        
        # Step 1: Check readiness
        can_launch, reason = self.coordinator.can_launch_browser()
        if not can_launch:
            print(f"\n[WORKFLOW] Cannot proceed: {reason}")
            print("[WORKFLOW] Please wait or terminate existing sessions")
            return False
        
        # Step 2: Run tests
        print("\n[WORKFLOW] Step 1: Running tests...")
        success, output = self.run_tests(test_type)
        
        # Step 3: Analyze and provide guidance
        print("\n[WORKFLOW] Step 2: Analyzing results...")
        status = self.coordinator.get_status()
        
        if status['next_steps']:
            print("\n[WORKFLOW] Step 3: Development Guidance")
            print("-" * 60)
            for step in status['next_steps']:
                # Replace Unicode characters for Windows compatibility
                step_safe = step.replace('✓', '[OK]').replace('✗', '[FAIL]').replace('⚠', '[WARN]').replace('→', '->')
                print(f"  {step_safe}")
            print("-" * 60)
        
        # Step 4: Cooldown reminder
        if not success:
            print(f"\n[WORKFLOW] Tests failed or missing functionality detected")
            print(f"[WORKFLOW] Implement fixes before running tests again")
            print(f"[WORKFLOW] Minimum {BrowserCoordinator.MIN_COOLDOWN_SECONDS} seconds between test runs")
        else:
            print(f"\n[WORKFLOW] Tests passed!")
            print(f"[WORKFLOW] You can run tests again after {BrowserCoordinator.MIN_COOLDOWN_SECONDS} seconds")
        
        return success


def main():
    """CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Coordinated Test Runner")
    parser.add_argument(
        "--type",
        choices=["visual", "integration", "all"],
        default="visual",
        help="Test type to run"
    )
    parser.add_argument(
        "--files",
        nargs="+",
        help="Specific test files to run"
    )
    parser.add_argument(
        "--workflow",
        action="store_true",
        help="Run with full test-driven workflow"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Test timeout in seconds (default: 300)"
    )
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    if args.workflow:
        success = runner.run_with_workflow(args.type)
        sys.exit(0 if success else 1)
    else:
        success, output = runner.run_tests(args.type, args.files, args.timeout)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

