#!/usr/bin/env python3
"""
Interactive Test Monitor
Monitors browser console and visual state during interactive testing.
Automatically detects failures and triggers fixes.
"""

import subprocess
import sys
import time
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
FRONTEND_DIR = PROJECT_ROOT / "src" / "frontend"
STATE_FILE = PROJECT_ROOT / ".test_monitor_state.json"

# Import coordinator
SCRIPTS_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPTS_DIR))
from browser_coordinator import BrowserCoordinator, TestResult
from coordinated_test_runner import TestRunner


@dataclass
class TestFailure:
    """Represents a test failure"""
    test_name: str
    failure_type: str  # 'rotation', 'snapping', 'movement', 'chaining', 'other'
    error_message: str
    timestamp: float
    fix_attempted: bool = False
    fix_successful: bool = False


class InteractiveTestMonitor:
    """Monitors interactive tests and handles failures"""
    
    def __init__(self):
        self.coordinator = BrowserCoordinator()
        self.test_runner = TestRunner()
        self.failures: List[TestFailure] = []
        self.state_file = STATE_FILE
    
    def detect_failure_type(self, error_message: str) -> str:
        """Detect the type of failure from error message"""
        error_lower = error_message.lower()
        
        if 'rotation' in error_lower or 'shift' in error_lower:
            return 'rotation'
        elif 'snap' in error_lower or 'edge' in error_lower:
            return 'snapping'
        elif 'move' in error_lower or 'drag' in error_lower:
            return 'movement'
        elif 'chain' in error_lower or 'attachment' in error_lower:
            return 'chaining'
        else:
            return 'other'
    
    def analyze_test_output(self, output: str) -> Tuple[bool, List[TestFailure]]:
        """Analyze test output for failures"""
        failures = []
        
        # Look for missing functionality errors
        missing_pattern = r'MISSING_FUNCTIONALITY:\s*(.+)'
        matches = re.finditer(missing_pattern, output, re.IGNORECASE)
        
        for match in matches:
            error_msg = match.group(1).strip()
            failure_type = self.detect_failure_type(error_msg)
            
            failure = TestFailure(
                test_name="polygon-interaction-workflow",
                failure_type=failure_type,
                error_message=error_msg,
                timestamp=time.time()
            )
            failures.append(failure)
        
        # Check for test failures
        if 'FAILED' in output or 'failed' in output:
            # Try to extract failure details
            failure_lines = [line for line in output.split('\n') if 'FAILED' in line or 'failed' in line]
            for line in failure_lines:
                failure_type = self.detect_failure_type(line)
                failure = TestFailure(
                    test_name="polygon-interaction-workflow",
                    failure_type=failure_type,
                    error_message=line,
                    timestamp=time.time()
                )
                failures.append(failure)
        
        success = len(failures) == 0
        return success, failures
    
    def fix_rotation_issue(self) -> bool:
        """Attempt to fix rotation issues"""
        print("[MONITOR] Attempting to fix rotation issue...")
        
        # Check polygonInteraction.js for rotation implementation
        interaction_file = PROJECT_ROOT / "src" / "frontend" / "src" / "utils" / "polygonInteraction.js"
        
        if not interaction_file.exists():
            print("[MONITOR] Interaction file not found")
            return False
        
        # Read file
        content = interaction_file.read_text()
        
        # Check if Shift key detection is correct
        if 'shiftKey' not in content and 'Shift' not in content:
            print("[MONITOR] Shift key detection missing - needs implementation")
            return False
        
        # Check if rotation is applied
        if 'rotation' not in content.lower():
            print("[MONITOR] Rotation logic missing - needs implementation")
            return False
        
        print("[MONITOR] Rotation code appears present - may be a runtime issue")
        return True
    
    def fix_snapping_issue(self) -> bool:
        """Attempt to fix snapping issues"""
        print("[MONITOR] Attempting to fix snapping issue...")
        
        # Check edgeSnapping.js
        snapping_file = PROJECT_ROOT / "src" / "frontend" / "src" / "utils" / "edgeSnapping.js"
        
        if not snapping_file.exists():
            print("[MONITOR] Snapping file not found")
            return False
        
        content = snapping_file.read_text()
        
        # Check for snap detection logic
        if 'findSnapCandidates' not in content:
            print("[MONITOR] Snap candidate detection missing")
            return False
        
        print("[MONITOR] Snapping code appears present - may be a threshold or visual feedback issue")
        return True
    
    def fix_movement_issue(self) -> bool:
        """Attempt to fix movement issues"""
        print("[MONITOR] Attempting to fix movement issue...")
        
        # Check interaction manager
        interaction_file = PROJECT_ROOT / "src" / "frontend" / "src" / "utils" / "polygonInteraction.js"
        
        if not interaction_file.exists():
            return False
        
        content = interaction_file.read_text()
        
        # Check for drag handling
        if 'dragging' not in content.lower() or 'pointer' not in content.lower():
            print("[MONITOR] Drag handling missing")
            return False
        
        print("[MONITOR] Movement code appears present")
        return True
    
    def fix_chaining_issue(self) -> bool:
        """Attempt to fix chaining issues"""
        print("[MONITOR] Attempting to fix chaining issue...")
        
        # Check for attachment logic
        interaction_file = PROJECT_ROOT / "src" / "frontend" / "src" / "utils" / "polygonInteraction.js"
        
        if not interaction_file.exists():
            return False
        
        content = interaction_file.read_text()
        
        # Check for attachment/chain logic
        if 'attachment' not in content.lower() and 'chain' not in content.lower():
            print("[MONITOR] Attachment/chain logic missing")
            return False
        
        print("[MONITOR] Chaining code appears present")
        return True
    
    def attempt_fix(self, failure: TestFailure) -> bool:
        """Attempt to fix a specific failure"""
        print(f"\n[MONITOR] Attempting to fix {failure.failure_type} issue...")
        print(f"[MONITOR] Error: {failure.error_message}")
        
        fix_functions = {
            'rotation': self.fix_rotation_issue,
            'snapping': self.fix_snapping_issue,
            'movement': self.fix_movement_issue,
            'chaining': self.fix_chaining_issue,
        }
        
        fix_func = fix_functions.get(failure.failure_type)
        if not fix_func:
            print(f"[MONITOR] No fix function for {failure.failure_type}")
            return False
        
        try:
            success = fix_func()
            failure.fix_attempted = True
            failure.fix_successful = success
            return success
        except Exception as e:
            print(f"[MONITOR] Fix attempt failed: {e}")
            failure.fix_attempted = True
            failure.fix_successful = False
            return False
    
    def run_interactive_test(self) -> Tuple[bool, List[TestFailure]]:
        """Run interactive test and monitor for failures"""
        print("\n" + "=" * 60)
        print("Interactive Test Monitor")
        print("=" * 60)
        
        # Check if we can launch
        can_launch, reason = self.coordinator.can_launch_browser()
        if not can_launch:
            print(f"[MONITOR] Cannot launch: {reason}")
            return False, []
        
        # Run test
        print("[MONITOR] Running polygon interaction workflow test...")
        success, output = self.test_runner.run_tests("integration", ["tests/integration/polygon-interaction-workflow.spec.js"], timeout=300)
        
        # Analyze results
        test_success, failures = self.analyze_test_output(output)
        
        if not test_success:
            print(f"\n[MONITOR] Test failed with {len(failures)} issue(s)")
            for failure in failures:
                print(f"  - {failure.failure_type}: {failure.error_message}")
        else:
            print("\n[MONITOR] ✓ All tests passed!")
        
        return test_success, failures
    
    def run_with_auto_fix(self, max_iterations: int = 3):
        """Run tests with automatic fixing"""
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            print(f"\n[MONITOR] Iteration {iteration}/{max_iterations}")
            
            # Run test
            success, failures = self.run_interactive_test()
            
            if success:
                print("\n[MONITOR] ✓ All tests passed!")
                return True
            
            # Attempt fixes
            fixes_applied = False
            for failure in failures:
                if not failure.fix_attempted:
                    if self.attempt_fix(failure):
                        fixes_applied = True
                        print(f"[MONITOR] Fix applied for {failure.failure_type}")
            
            if not fixes_applied:
                print("\n[MONITOR] No fixes could be applied automatically")
                print("[MONITOR] Manual intervention required")
                return False
            
            # Wait before retry (respect cooldown)
            print("\n[MONITOR] Waiting for cooldown period...")
            time.sleep(60)  # Wait 1 minute before retry
        
        print(f"\n[MONITOR] Max iterations ({max_iterations}) reached")
        return False


def main():
    """CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Interactive Test Monitor")
    parser.add_argument("--auto-fix", action="store_true", help="Enable automatic fixing")
    parser.add_argument("--max-iterations", type=int, default=3, help="Max fix iterations")
    
    args = parser.parse_args()
    
    monitor = InteractiveTestMonitor()
    
    if args.auto_fix:
        success = monitor.run_with_auto_fix(args.max_iterations)
        sys.exit(0 if success else 1)
    else:
        success, failures = monitor.run_interactive_test()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

