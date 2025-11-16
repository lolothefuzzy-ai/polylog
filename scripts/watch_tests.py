#!/usr/bin/env python3
"""
Watch mode for tests - automatically runs tests when files change
"""

import subprocess
import sys
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
FRONTEND_DIR = PROJECT_ROOT / "src" / "frontend"

class TestWatcher(FileSystemEventHandler):
    def __init__(self, test_type: str = "all"):
        self.test_type = test_type
        self.last_run = 0
        self.debounce_seconds = 2  # Wait 2 seconds after last change
        
    def should_run_tests(self) -> bool:
        """Debounce test runs"""
        now = time.time()
        if now - self.last_run < self.debounce_seconds:
            return False
        self.last_run = now
        return True
    
    def on_modified(self, event):
        if event.is_directory:
            return
        
        # Only watch relevant files
        if not event.src_path.endswith(('.py', '.js', '.jsx', '.ts', '.tsx', '.css')):
            return
        
        # Ignore test files themselves and node_modules
        if 'node_modules' in event.src_path or '__pycache__' in event.src_path:
            return
        
        if not self.should_run_tests():
            return
        
        print(f"\n[WATCH] File changed: {Path(event.src_path).relative_to(PROJECT_ROOT)}")
        print("[WATCH] Running tests...")
        
        # Determine which tests to run based on file type
        if event.src_path.endswith('.py'):
            # Python file changed - run backend tests
            self.run_backend_tests()
        elif event.src_path.endswith(('.js', '.jsx', '.ts', '.tsx', '.css')):
            # Frontend file changed - run frontend tests
            self.run_frontend_tests()
    
    def run_backend_tests(self):
        """Run backend tests"""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short", "-x"],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode == 0:
                print("[OK] Backend tests passed")
            else:
                print("[FAIL] Backend tests failed")
                print(result.stdout[-500:] + result.stderr[-500:])
        except Exception as e:
            print(f"[ERROR] Failed to run backend tests: {e}")
    
    def run_frontend_tests(self):
        """Run frontend tests"""
        try:
            # Run visual tests in headed mode for immediate feedback
            result = subprocess.run(
                ["npx", "playwright", "test", "tests/visual", "--headed", "--project=chromium", "-x"],
                cwd=FRONTEND_DIR,
                capture_output=True,
                text=True,
                timeout=180
            )
            if result.returncode == 0:
                print("[OK] Frontend tests passed")
            else:
                print("[FAIL] Frontend tests failed")
                print(result.stdout[-500:] + result.stderr[-500:])
        except Exception as e:
            print(f"[ERROR] Failed to run frontend tests: {e}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Watch for file changes and run tests")
    parser.add_argument("--type", choices=["all", "backend", "frontend"], default="all",
                       help="Which tests to run on changes")
    
    args = parser.parse_args()
    
    print("[WATCH] Starting test watcher...")
    print("[WATCH] Watching for file changes in src/ and tests/")
    print("[WATCH] Press Ctrl+C to stop")
    print("=" * 60)
    
    event_handler = TestWatcher(args.type)
    observer = Observer()
    
    # Watch source directories
    observer.schedule(event_handler, str(PROJECT_ROOT / "src"), recursive=True)
    observer.schedule(event_handler, str(PROJECT_ROOT / "tests"), recursive=True)
    
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[WATCH] Stopping watcher...")
        observer.stop()
    
    observer.join()

if __name__ == "__main__":
    main()

