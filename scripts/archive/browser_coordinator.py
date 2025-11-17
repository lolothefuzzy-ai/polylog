#!/usr/bin/env python3
"""
Browser Launch Coordinator
Manages browser launches for testing with rate limiting and test-driven workflow.

Key Features:
- Minimum 1-minute cooldown between browser launches
- Test result analysis (pass/fail)
- Early termination if missing functionality detected
- Test-driven development workflow guidance
"""

import time
import json
import subprocess
import sys
import os
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
STATE_FILE = PROJECT_ROOT / ".browser_coordinator_state.json"
MIN_COOLDOWN_SECONDS = 60  # 1 minute minimum between launches


class TestResult(Enum):
    """Test execution result"""
    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"
    MISSING_FUNCTIONALITY = "missing_functionality"
    IN_PROGRESS = "in_progress"


@dataclass
class BrowserSession:
    """Represents a browser testing session"""
    session_id: str
    launch_time: float
    test_result: Optional[TestResult] = None
    test_output: str = ""
    terminated: bool = False
    termination_reason: str = ""
    missing_features: List[str] = None
    
    def __post_init__(self):
        if self.missing_features is None:
            self.missing_features = []


@dataclass
class CoordinatorState:
    """State of the browser coordinator"""
    last_launch_time: Optional[float] = None
    active_sessions: Dict[str, BrowserSession] = None
    test_history: List[Dict] = None
    next_steps: List[str] = None
    
    def __post_init__(self):
        if self.active_sessions is None:
            self.active_sessions = {}
        if self.test_history is None:
            self.test_history = []
        if self.next_steps is None:
            self.next_steps = []


class BrowserCoordinator:
    """Manages browser launches with rate limiting and test-driven workflow"""
    
    def __init__(self, state_file: Path = STATE_FILE):
        self.state_file = state_file
        self.state = self._load_state()
    
    def _load_state(self) -> CoordinatorState:
        """Load coordinator state from file"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    # Convert active_sessions back to BrowserSession objects
                    sessions = {}
                    for sid, session_data in data.get('active_sessions', {}).items():
                        session = BrowserSession(**session_data)
                        # Convert test_result string back to enum
                        if session.test_result:
                            session.test_result = TestResult(session.test_result)
                        sessions[sid] = session
                    data['active_sessions'] = sessions
                    return CoordinatorState(**data)
            except Exception as e:
                print(f"[COORDINATOR] Warning: Could not load state: {e}")
        
        return CoordinatorState()
    
    def _save_state(self):
        """Save coordinator state to file"""
        try:
            # Convert state to JSON-serializable format
            data = {
                'last_launch_time': self.state.last_launch_time,
                'active_sessions': {
                    sid: {
                        **asdict(session),
                        'test_result': session.test_result.value if session.test_result else None
                    }
                    for sid, session in self.state.active_sessions.items()
                },
                'test_history': self.state.test_history,
                'next_steps': self.state.next_steps
            }
            with open(self.state_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[COORDINATOR] Warning: Could not save state: {e}")
    
    def can_launch_browser(self) -> Tuple[bool, str]:
        """
        Check if a browser can be launched now.
        Returns (can_launch, reason)
        """
        # Check for active sessions that haven't been terminated
        active_count = sum(
            1 for s in self.state.active_sessions.values()
            if not s.terminated and s.test_result != TestResult.MISSING_FUNCTIONALITY
        )
        
        if active_count > 0:
            return False, f"Active browser session(s) still running. Terminate existing sessions first."
        
        # Check cooldown period
        if self.state.last_launch_time:
            elapsed = time.time() - self.state.last_launch_time
            if elapsed < MIN_COOLDOWN_SECONDS:
                remaining = MIN_COOLDOWN_SECONDS - elapsed
                return False, f"Cooldown period active. Wait {remaining:.1f} more seconds."
        
        return True, "Ready to launch"
    
    def launch_browser(self, test_command: List[str], test_type: str = "visual") -> Optional[str]:
        """
        Launch a browser for testing.
        Returns session_id if successful, None otherwise.
        """
        can_launch, reason = self.can_launch_browser()
        if not can_launch:
            print(f"[COORDINATOR] Cannot launch browser: {reason}")
            return None
        
        session_id = f"session_{int(time.time())}"
        session = BrowserSession(
            session_id=session_id,
            launch_time=time.time(),
            test_result=TestResult.IN_PROGRESS
        )
        
        self.state.active_sessions[session_id] = session
        self.state.last_launch_time = time.time()
        self._save_state()
        
        print(f"[COORDINATOR] Browser session {session_id} launched")
        print(f"[COORDINATOR] Running tests: {' '.join(test_command)}")
        print(f"[COORDINATOR] Cooldown period: {MIN_COOLDOWN_SECONDS} seconds")
        
        return session_id
    
    def terminate_session(self, session_id: str, reason: str = "User request"):
        """Terminate a browser session"""
        if session_id not in self.state.active_sessions:
            print(f"[COORDINATOR] Session {session_id} not found")
            return False
        
        session = self.state.active_sessions[session_id]
        session.terminated = True
        session.termination_reason = reason
        
        # Kill any running browser/playwright processes for this session
        self._kill_browser_processes()
        
        self._save_state()
        print(f"[COORDINATOR] Session {session_id} terminated: {reason}")
        return True
    
    def _kill_browser_processes(self):
        """Kill browser and Playwright processes"""
        try:
            if sys.platform == "win32":
                # Kill Playwright browsers
                subprocess.run(
                    ["taskkill", "/F", "/IM", "msedge.exe", "/FI", "WINDOWTITLE eq *Playwright*"],
                    capture_output=True,
                    timeout=5
                )
                subprocess.run(
                    ["taskkill", "/F", "/IM", "chrome.exe", "/FI", "WINDOWTITLE eq *Playwright*"],
                    capture_output=True,
                    timeout=5
                )
            else:
                # Unix-like systems
                subprocess.run(["pkill", "-f", "playwright"], capture_output=True, timeout=5)
        except Exception as e:
            print(f"[COORDINATOR] Warning: Could not kill browser processes: {e}")
    
    def record_test_result(
        self,
        session_id: str,
        result: TestResult,
        output: str = "",
        missing_features: List[str] = None
    ):
        """Record test results for a session"""
        if session_id not in self.state.active_sessions:
            print(f"[COORDINATOR] Session {session_id} not found")
            return
        
        session = self.state.active_sessions[session_id]
        session.test_result = result
        session.test_output = output
        
        if missing_features:
            session.missing_features = missing_features
            # If missing functionality detected, terminate immediately
            if result == TestResult.MISSING_FUNCTIONALITY:
                session.terminated = True
                session.termination_reason = f"Missing functionality detected: {', '.join(missing_features)}"
                self._kill_browser_processes()
                print(f"[COORDINATOR] Session terminated due to missing functionality")
        
        # Add to history
        self.state.test_history.append({
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'result': result.value,
            'missing_features': missing_features or []
        })
        
        # Generate next steps based on test results
        self._generate_next_steps(session)
        
        self._save_state()
    
    def _generate_next_steps(self, session: BrowserSession):
        """Generate development next steps based on test results"""
        self.state.next_steps = []
        
        if session.test_result == TestResult.PASS:
            self.state.next_steps.append("[OK] All tests passed!")
            self.state.next_steps.append("-> Review test coverage and add new features if needed")
            self.state.next_steps.append("-> Consider adding edge case tests")
        
        elif session.test_result == TestResult.FAIL:
            self.state.next_steps.append("[FAIL] Tests failed - analyze failures:")
            self.state.next_steps.append("-> Review test output for specific failures")
            self.state.next_steps.append("-> Fix backend code based on failure patterns")
            self.state.next_steps.append("-> Re-run tests after fixes")
        
        elif session.test_result == TestResult.MISSING_FUNCTIONALITY:
            self.state.next_steps.append("[WARN] Missing functionality detected:")
            for feature in session.missing_features:
                self.state.next_steps.append(f"  - {feature}")
            self.state.next_steps.append("-> Implement missing features in backend")
            self.state.next_steps.append("-> Update API endpoints if needed")
            self.state.next_steps.append("-> Re-run tests after implementation")
        
        elif session.test_result == TestResult.ERROR:
            self.state.next_steps.append("[FAIL] Test execution error")
            self.state.next_steps.append("-> Check server status (API:8000, Frontend:5173)")
            self.state.next_steps.append("-> Review error logs")
            self.state.next_steps.append("-> Fix infrastructure issues before retesting")
    
    def get_status(self) -> Dict:
        """Get current coordinator status"""
        can_launch, reason = self.can_launch_browser()
        
        active_sessions = [
            {
                'id': sid,
                'launch_time': datetime.fromtimestamp(s.launch_time).isoformat(),
                'result': s.test_result.value if s.test_result else None,
                'terminated': s.terminated
            }
            for sid, s in self.state.active_sessions.items()
            if not s.terminated
        ]
        
        return {
            'can_launch': can_launch,
            'reason': reason,
            'active_sessions': active_sessions,
            'next_steps': self.state.next_steps,
            'last_launch': datetime.fromtimestamp(self.state.last_launch_time).isoformat() if self.state.last_launch_time else None
        }
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Remove old sessions from state"""
        cutoff_time = time.time() - (max_age_hours * 3600)
        to_remove = [
            sid for sid, session in self.state.active_sessions.items()
            if session.launch_time < cutoff_time
        ]
        for sid in to_remove:
            del self.state.active_sessions[sid]
        self._save_state()


def main():
    """CLI interface for browser coordinator"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Browser Launch Coordinator")
    parser.add_argument("--status", action="store_true", help="Show coordinator status")
    parser.add_argument("--terminate", type=str, help="Terminate a session by ID")
    parser.add_argument("--cleanup", action="store_true", help="Clean up old sessions")
    parser.add_argument("--can-launch", action="store_true", help="Check if browser can be launched")
    
    args = parser.parse_args()
    
    coordinator = BrowserCoordinator()
    
    if args.cleanup:
        coordinator.cleanup_old_sessions()
        print("[COORDINATOR] Cleaned up old sessions")
    
    if args.terminate:
        coordinator.terminate_session(args.terminate)
    
    if args.can_launch:
        can_launch, reason = coordinator.can_launch_browser()
        print(f"Can launch: {can_launch}")
        print(f"Reason: {reason}")
        sys.exit(0 if can_launch else 1)
    
    if args.status:
        status = coordinator.get_status()
        print("\n" + "=" * 60)
        print("Browser Coordinator Status")
        print("=" * 60)
        print(f"Can launch browser: {status['can_launch']}")
        print(f"Reason: {status['reason']}")
        if status['last_launch']:
            print(f"Last launch: {status['last_launch']}")
        print(f"\nActive sessions: {len(status['active_sessions'])}")
        for session in status['active_sessions']:
            print(f"  - {session['id']}: {session['result']}")
        if status['next_steps']:
            print("\nNext steps:")
            for step in status['next_steps']:
                print(f"  {step}")
        print("=" * 60)


if __name__ == "__main__":
    main()

