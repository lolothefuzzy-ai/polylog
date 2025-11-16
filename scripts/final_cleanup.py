#!/usr/bin/env python3
"""
Final Project Cleanup
Removes all redundant files, keeps only actionable code
"""

import os
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# Files to remove (redundant documentation)
FILES_TO_REMOVE = [
    # Root level redundant docs
    "ARCHITECTURE_CORRECTION_SUMMARY.md",
    "BROWSER_ACCESS.md",
    "BROWSER_COORDINATION_SYSTEM.md",
    "GPU_WARMING_IMPLEMENTATION_SUMMARY.md",
    "IMPLEMENTATION_PLAN.md",
    "IMPLEMENTATION_UPDATES.md",
    "NEXT_STEPS_ANALYSIS.md",
    "STARTUP_ISSUES_AND_FIXES.md",
    "TESTING_SYSTEM_COMPLETE.md",
    "TIER0_RECURSIVE_STRUCTURE_SUMMARY.md",
    "TIER_GENERATION_IMPLEMENTATION_SUMMARY.md",
    "VISIBILITY_FIXES.md",
    "VISUALIZATION_ARCHITECTURE_SUMMARY.md",
    "WORKFLOW_OPTIMIZATION_GUIDE.md",
    
    # Docs directory redundant files
    "docs/ATOMIC_CHAINS_ARCHITECTURE.md",
    "docs/ATOMIC_CHAINS_INTEGRATION_PLAN.md",
    "docs/CHUNK_COMPLETION_SUMMARY.md",
    "docs/CHUNK_PROGRESS_UPDATE.md",
    "docs/CURRENT_ALIGNMENT_STATUS.md",
    "docs/CURRENT_STATE_SNAPSHOT.md",
    "docs/DEVELOPMENT_WORKFLOW_OPTIMIZATION.md",
    "docs/FINAL_INTEGRATION_SUMMARY.md",
    "docs/FOUR_TRACK_SYSTEM_BENEFITS.md",
    "docs/GAP_TO_COMPLETION.md",
    "docs/GAP_TO_COMPLETION_ANALYSIS.md",
    "docs/GEOMETRY_SYSTEM_ANALYSIS.md",
    "docs/GPU_WARMING_ARCHITECTURE.md",
    "docs/INTEGRATION_COMPLETION_STATUS.md",
    "docs/INTEGRATION_STATUS.md",
    "docs/OPTIMIZATION_COMPLETED.md",
    "docs/PRIORITIZED_TASK_ROADMAP.md",
    "docs/STARTUP_ISSUES_RESOLVED.md",
    "docs/TEST_SETUP_COMPLETE.md",
    "docs/TEST_WIRING_SUMMARY.md",
    "docs/TIER_GENERATION_ARCHITECTURE.md",
    "docs/UNICODE_SERIES_ARCHITECTURE.md",
    "docs/UNIFIED_BACKEND_GEOMETRY.md",
    "docs/UNIFIED_INTEGRATION_PLAN.md",
    "docs/VISUALIZATION_UNICODE_INTEGRATION.md",
    "docs/WORKFLOW_GAP_TO_COMPLETION.md",
    "docs/WORKFLOW_OPTIMIZATION_SUMMARY.md",
    "docs/WORKSPACE_UNIFIED_ENTRY_POINT.md",
]

# Essential docs to keep
ESSENTIAL_DOCS = {
    "README.md",
    "docs/ARCHITECTURE.md",
    "docs/DEVELOPMENT.md",
    "docs/WORKSPACE_INTERACTION_ARCHITECTURE.md",
}

def remove_files():
    """Remove redundant files"""
    removed = []
    not_found = []
    
    print("=" * 70)
    print("Final Project Cleanup")
    print("=" * 70)
    
    for file_pattern in FILES_TO_REMOVE:
        file_path = PROJECT_ROOT / file_pattern
        
        if file_path.exists():
            try:
                file_path.unlink()
                removed.append(file_path)
                print(f"[DEL] {file_path.relative_to(PROJECT_ROOT)}")
            except Exception as e:
                print(f"[ERROR] Failed to remove {file_path}: {e}")
        else:
            not_found.append(file_path)
    
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"\nRemoved: {len(removed)} files")
    print(f"Not found: {len(not_found)} files")
    
    if removed:
        print("\nRemoved files:")
        for f in removed[:20]:  # Show first 20
            print(f"  - {f.relative_to(PROJECT_ROOT)}")
        if len(removed) > 20:
            print(f"  ... and {len(removed) - 20} more")
    
    return removed

def cleanup_empty_dirs():
    """Remove empty directories"""
    print("\n[2] Cleaning up empty directories...")
    
    removed_dirs = []
    for root, dirs, files in os.walk(PROJECT_ROOT, topdown=False):
        # Skip .git and node_modules
        if '.git' in root or 'node_modules' in root:
            continue
        
        for dir_name in dirs:
            dir_path = Path(root) / dir_name
            try:
                if not any(dir_path.iterdir()):
                    dir_path.rmdir()
                    removed_dirs.append(dir_path)
                    print(f"  [DEL] {dir_path.relative_to(PROJECT_ROOT)}")
            except:
                pass
    
    print(f"\nRemoved {len(removed_dirs)} empty directories")
    return removed_dirs

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Final project cleanup")
    parser.add_argument("--dry-run", action="store_true", help="Dry run (don't delete)")
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("[DRY RUN] No files will be deleted")
        print("\nFiles that would be removed:")
        for f in FILES_TO_REMOVE:
            file_path = PROJECT_ROOT / f
            if file_path.exists():
                print(f"  - {f}")
        return
    
    removed = remove_files()
    cleanup_empty_dirs()
    
    print("\n" + "=" * 70)
    print("[SUCCESS] Cleanup complete!")
    print("=" * 70)
    print("\nEssential files kept:")
    for doc in ESSENTIAL_DOCS:
        doc_path = PROJECT_ROOT / doc
        if doc_path.exists():
            print(f"  [OK] {doc}")

if __name__ == "__main__":
    main()

