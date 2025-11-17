#!/usr/bin/env python3
"""
Cleanup Context Window
Removes redundant files to focus development context
"""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# Files to remove (redundant documentation, status files, etc.)
FILES_TO_REMOVE = [
    # Lock files
    ".browser_launched.lock",
    ".last_sync.txt",
    
    # Batch files (temporary)
    "start_api.bat",
    "src/frontend/start_frontend.bat",
    
    # Redundant summaries (keep only essential docs)
    "CLEANUP_SUMMARY.md",
    "GPU_WARMING_IMPLEMENTATION_SUMMARY.md",
    "TIER0_RECURSIVE_STRUCTURE_SUMMARY.md",
    "TIER_GENERATION_IMPLEMENTATION_SUMMARY.md",
    "ARCHITECTURE_CORRECTION_SUMMARY.md",
    "IMPLEMENTATION_UPDATES.md",
    "NEXT_STEPS_ANALYSIS.md",
    "docs/GAP_TO_COMPLETION.md",
    "docs/PRIORITIZED_TASK_ROADMAP.md",
    "docs/WORKFLOW_GAP_TO_COMPLETION.md",
    "docs/CURRENT_STATE_SNAPSHOT.md",
    "docs/INTEGRATION_COMPLETION_STATUS.md",
    "docs/WORKFLOW_OPTIMIZATION_SUMMARY.md",
    "docs/DEVELOPMENT_WORKFLOW_OPTIMIZATION.md",
    "docs/CURRENT_ALIGNMENT_STATUS.md",
    "docs/OPTIMIZATION_COMPLETED.md",
    "docs/ATOMIC_CHAINS_ARCHITECTURE.md",
    "docs/ATOMIC_CHAINS_INTEGRATION_PLAN.md",
    "docs/UNIFIED_INTEGRATION_PLAN.md",
    "docs/WORKSPACE_UNIFIED_ENTRY_POINT.md",
    
    # Test result files (should be in .gitignore)
    "src/frontend/playwright-report/index.html",
    "src/frontend/test-results/.last-run.json",
]

# Directories to check for empty/redundant files
DIRS_TO_CLEAN = [
    "test-results",
    "src/frontend/test-results",
    "src/frontend/playwright-report",
]

def remove_file(filepath):
    """Remove a file if it exists"""
    path = PROJECT_ROOT / filepath
    if path.exists():
        try:
            path.unlink()
            print(f"[REMOVED] {filepath}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to remove {filepath}: {e}")
            return False
    return False

def clean_directories():
    """Clean up test result directories"""
    for dir_path in DIRS_TO_CLEAN:
        path = PROJECT_ROOT / dir_path
        if path.exists():
            try:
                # Remove all files in directory
                for file in path.rglob("*"):
                    if file.is_file():
                        file.unlink()
                print(f"[CLEANED] {dir_path}")
            except Exception as e:
                print(f"[ERROR] Failed to clean {dir_path}: {e}")

def main():
    print("=" * 70)
    print("Context Window Cleanup")
    print("=" * 70)
    print("\nRemoving redundant files to focus development context...")
    print()
    
    removed_count = 0
    
    # Remove files
    for filepath in FILES_TO_REMOVE:
        if remove_file(filepath):
            removed_count += 1
    
    # Clean directories
    clean_directories()
    
    print("\n" + "=" * 70)
    print(f"Cleanup complete: {removed_count} files removed")
    print("=" * 70)
    print("\nContext window is now more focused!")
    print("Essential documentation remains in docs/")
    print("Only actionable code and essential docs are kept")
    print("=" * 70)
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())

