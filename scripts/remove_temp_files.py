#!/usr/bin/env python3
"""
Remove temporary and unnecessary files
"""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# Temporary files to remove
TEMP_PATTERNS = [
    "pasted_content_*.txt",
    "*.png",
    "*.pdf",
    "NEXT_INTEGRATION_PLAN.json",
    "SUMMARY.md",
    "TEST_STATUS.md",
    "AUTOMATED_TESTING_SETUP.md",
    "CI_CD_SETUP.md",
    "DESKTOP_APP_README.md",
    "TESTING_GUIDE.md",
]

def remove_temp_files():
    """Remove temporary files"""
    removed = []
    
    print("=" * 70)
    print("Removing Temporary Files")
    print("=" * 70)
    
    for pattern in TEMP_PATTERNS:
        if "*" in pattern:
            # Use glob
            for file_path in PROJECT_ROOT.glob(pattern):
                if file_path.is_file():
                    try:
                        file_path.unlink()
                        removed.append(file_path)
                        print(f"[DEL] {file_path.relative_to(PROJECT_ROOT)}")
                    except Exception as e:
                        print(f"[ERROR] Failed to remove {file_path}: {e}")
        else:
            # Direct file
            file_path = PROJECT_ROOT / pattern
            if file_path.exists() and file_path.is_file():
                try:
                    file_path.unlink()
                    removed.append(file_path)
                    print(f"[DEL] {file_path.relative_to(PROJECT_ROOT)}")
                except Exception as e:
                    print(f"[ERROR] Failed to remove {file_path}: {e}")
    
    print("\n" + "=" * 70)
    print(f"Removed {len(removed)} temporary files")
    print("=" * 70)
    
    return removed

if __name__ == "__main__":
    remove_temp_files()

