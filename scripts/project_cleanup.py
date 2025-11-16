#!/usr/bin/env python3
"""
Project Cleanup Script
Removes unnecessary files and organizes project structure
"""

import os
import shutil
from pathlib import Path
from typing import List, Set

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# Files and directories to keep (actionable code)
KEEP_PATTERNS = {
    # Source code
    "src/**/*.py",
    "src/**/*.js",
    "src/**/*.jsx",
    "src/**/*.ts",
    "src/**/*.tsx",
    "src/**/*.rs",
    "src/**/*.toml",
    "src/**/*.json",
    "src/**/*.css",
    "src/**/*.html",
    
    # Tests
    "tests/**/*.py",
    "tests/**/*.js",
    "tests/**/*.spec.js",
    "src/frontend/tests/**/*",
    
    # Configuration
    "*.json",
    "*.toml",
    "*.yaml",
    "*.yml",
    "*.config.js",
    "*.config.ts",
    "requirements.txt",
    "package.json",
    "package-lock.json",
    "Cargo.toml",
    "Cargo.lock",
    ".gitignore",
    ".gitattributes",
    ".editorconfig",
    ".prettierrc",
    ".eslintrc",
    "pyproject.toml",
    "ruff.toml",
    
    # Scripts
    "scripts/**/*.py",
    "scripts/**/*.sh",
    "scripts/**/*.ps1",
    
    # Essential docs
    "README.md",
    "LICENSE",
    "CHANGELOG.md",
    
    # Workspace config
    ".vscode/**/*",
    ".cursor/**/*",
    ".github/**/*",
    
    # Data catalogs (if needed)
    "data/catalogs/**/*",
}

# Documentation files to remove (keep only essential)
DOCS_TO_REMOVE = [
    # Archive docs
    "docs/archive/**/*",
    
    # Redundant summaries
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
    
    # Redundant docs in docs/
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

# Directories to remove
DIRS_TO_REMOVE = [
    "docs/archive",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "*.egg-info",
    ".eggs",
]

# Essential docs to keep
ESSENTIAL_DOCS = [
    "README.md",
    "docs/WORKSPACE_INTERACTION_ARCHITECTURE.md",
    "docs/UNICODE_SERIES_ARCHITECTURE.md",  # Core architecture
]

def find_files(pattern: str) -> List[Path]:
    """Find files matching pattern"""
    import glob
    matches = []
    for path in glob.glob(str(PROJECT_ROOT / pattern), recursive=True):
        p = Path(path)
        if p.is_file():
            matches.append(p)
    return matches

def should_keep(file_path: Path) -> bool:
    """Check if file should be kept"""
    rel_path = file_path.relative_to(PROJECT_ROOT)
    
    # Keep essential docs
    if rel_path.name in ESSENTIAL_DOCS:
        return True
    
    # Keep source code
    if any(rel_path.parts[0] == part for part in ["src", "tests", "scripts"]):
        return True
    
    # Keep config files
    if rel_path.name.startswith(".") and rel_path.suffix in [".json", ".yaml", ".yml", ".toml"]:
        return True
    
    # Keep package files
    if rel_path.name in ["package.json", "package-lock.json", "requirements.txt", "Cargo.toml"]:
        return True
    
    # Keep GitHub workflows
    if ".github" in rel_path.parts:
        return True
    
    return False

def cleanup_project(dry_run: bool = True):
    """Clean up project files"""
    removed_files = []
    removed_dirs = []
    
    print("=" * 70)
    print("Project Cleanup")
    print("=" * 70)
    print(f"\nMode: {'DRY RUN' if dry_run else 'LIVE'}")
    
    # Remove redundant documentation
    print("\n[1] Removing redundant documentation...")
    for doc_pattern in DOCS_TO_REMOVE:
        for file_path in find_files(doc_pattern):
            if not should_keep(file_path):
                removed_files.append(file_path)
                if not dry_run:
                    file_path.unlink()
                print(f"  {'[DRY]' if dry_run else '[DEL]'} {file_path.relative_to(PROJECT_ROOT)}")
    
    # Remove empty directories
    print("\n[2] Removing empty directories...")
    for dir_pattern in DIRS_TO_REMOVE:
        for dir_path in PROJECT_ROOT.rglob(dir_pattern):
            if dir_path.is_dir():
                try:
                    if not any(dir_path.iterdir()):
                        removed_dirs.append(dir_path)
                        if not dry_run:
                            dir_path.rmdir()
                        print(f"  {'[DRY]' if dry_run else '[DEL]'} {dir_path.relative_to(PROJECT_ROOT)}")
                except:
                    pass
    
    # Summary
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"\nFiles to remove: {len(removed_files)}")
    print(f"Directories to remove: {len(removed_dirs)}")
    
    if dry_run:
        print("\n[INFO] This was a dry run. No files were deleted.")
        print("[INFO] Run with --execute to actually delete files.")
    else:
        print("\n[SUCCESS] Cleanup complete!")
    
    return removed_files, removed_dirs

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean up project files")
    parser.add_argument("--execute", action="store_true", help="Actually delete files (default: dry run)")
    
    args = parser.parse_args()
    
    cleanup_project(dry_run=not args.execute)

if __name__ == "__main__":
    main()

