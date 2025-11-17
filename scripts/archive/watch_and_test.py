#!/usr/bin/env python3
"""Watch for file changes and run tests automatically"""
import subprocess
import sys
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

class TestHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith(('.py', '.js', '.jsx', '.ts', '.tsx')):
            print(f"\n[TEST] File changed: {event.src_path}")
            subprocess.run([sys.executable, "scripts/auto_test.py"])

if __name__ == "__main__":
    event_handler = TestHandler()
    observer = Observer()
    observer.schedule(event_handler, str(PROJECT_ROOT / "src"), recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

