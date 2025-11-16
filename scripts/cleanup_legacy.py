#!/usr/bin/env python3
"""
Cleanup legacy files not related to current development
"""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# Files to remove (legacy, not in src/)
LEGACY_FILES = [
    # Root TypeScript files (should be in src/frontend)
    "App.tsx",
    "BabylonWorkspace.tsx",
    "Canvas3D.tsx",
    "Home.tsx",
    "PolygonPalette.tsx",
    "PolygonSlider.tsx",
    "SnapGuide.tsx",
    "Workspace.tsx",
    "Workspace3D.tsx",
    "attachmentMatrix.ts",
    "attachmentResolver.ts",
    "autoSnap.ts",
    "edgeSnapping.ts",
    "edgeSnappingBabylon.ts",
    "liaisonGraph.ts",
    "polygon3D.ts",
    "polygonGeometry.ts",
    "polygonSymbols.ts",
    "polygonSymbolsV2.ts",
    "polygonSymbolsV2 (2).ts",
    "precisePolygonGeometry.ts",
    "seriesValidation.test.ts",
    "index.css",
    "main.tsx",
    "index.html",
    "vite.config.js",
    "tsconfig.json",
    "package.json",  # Root package.json (duplicate)
    "package-lock.json",
    
    # Legacy Python files
    "launcher.py",
    "polylog_core.py",
    "polylog_main.py",
    "build-sidecar.py",
    
    # Legacy batch files
    "build_installer.bat",
    "build.ps1",
    "install_dependencies.bat",
    "launch_api.bat",
    "launch_desktop.bat",
    "launch_gui.bat",
    "start.bat",
    
    # Legacy configs
    "pytest.ini",
    "docker-compose.yml",
    "requirements.txt",
    
    # Legacy data
    "stable_polyforms.jsonl",
    "provenance_log.jsonl",
    "performance.prof",
    "rustup-init.exe",
    
    # Pasted content files
    "pasted_content.txt",
    "pasted_content_2.txt",
    "pasted_content_3.txt",
    "pasted_content_4.txt",
    "pasted_content_5.txt",
    "pasted_content_6.txt",
    "pasted_content_7.txt",
    "pasted_content_8.txt",
    "pasted_content_9.txt",
    "pasted_content_10.txt",
    "pasted_content_11.txt",
    "pasted_content_12.txt",
    "pasted_content_13.txt",
    "pasted_content_14.txt",
    "pasted_content_15.txt",
    "pasted_content_16.txt",
    "pasted_content_17.txt",
    "pasted_content_18.txt",
    "pasted_content_19.txt",
    "pasted_content_20.txt",
    "pasted_content_21.txt",
    "pasted_content_22.txt",
    "pasted_content_23.txt",
    
    # Legacy directories
    "web_portal",
    "locales",
    "src-tauri",  # Should be in src/desktop/
    "PolylogCore",
]

# Documentation to consolidate (move to docs/archive/)
LEGACY_DOCS = [
    "ARCHITECTURE_NOTES.md",
    "CURSOR_WORKSPACE_SETUP.md",
    "FILE_MIGRATION_GUIDE.md",
    "GITHUB_SETUP_GUIDE.md",
    "GITHUB_STATUS.md",
    "IMPLEMENTATION_COMPLETE.md",
    "INSTALL.md",
    "MIGRATION_GUIDE.md",
    "POLYLOG6_ARCHITECTURE.md",
    "QUICK_START.md",
    "README (2).md",
    "REORGANIZATION_COMPLETE.md",
    "REORGANIZATION_FINAL_STATUS.md",
    "REORGANIZATION_PLAN.md",
    "SETUP_COMPLETE.md",
    "SYNC_WITH_GITHUB.md",
    "SYSTEM_SPEC_NOTES.md",
    "WINDSURF_MIGRATION_GUIDE.md",
    "polylog_visualization_notes.md",
    "todo.md",
    "DESKTOP_IMPLEMENTATION_STATUS.md",
    "DESKTOP_LAUNCHER_GUIDE.md",
    "FULL_SYSTEM_INTEGRATION_PLAN.md",
]

def remove_file(path):
    """Remove a file if it exists"""
    if path.exists() and path.is_file():
        try:
            path.unlink()
            print(f"✓ Removed: {path.name}")
            return True
        except Exception as e:
            print(f"✗ Failed to remove {path.name}: {e}")
            return False
    return False

def remove_dir(path):
    """Remove a directory if it exists"""
    if path.exists() and path.is_dir():
        try:
            import shutil
            shutil.rmtree(path)
            print(f"✓ Removed directory: {path.name}")
            return True
        except Exception as e:
            print(f"✗ Failed to remove {path.name}: {e}")
            return False
    return False

def archive_doc(path):
    """Move documentation to archive"""
    archive_dir = PROJECT_ROOT / "docs" / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    if path.exists() and path.is_file():
        try:
            target = archive_dir / path.name
            if target.exists():
                target.unlink()
            path.rename(target)
            print(f"✓ Archived: {path.name}")
            return True
        except Exception as e:
            print(f"✗ Failed to archive {path.name}: {e}")
            return False
    return False

def main():
    print("Cleaning up legacy files...\n")
    
    removed = 0
    archived = 0
    
    # Remove legacy files
    print("Removing legacy files...")
    for filename in LEGACY_FILES:
        path = PROJECT_ROOT / filename
        if path.is_file():
            if remove_file(path):
                removed += 1
        elif path.is_dir():
            if remove_dir(path):
                removed += 1
    
    # Archive legacy docs
    print("\nArchiving legacy documentation...")
    for filename in LEGACY_DOCS:
        path = PROJECT_ROOT / filename
        if archive_doc(path):
            archived += 1
    
    print(f"\n✓ Cleanup complete: {removed} files removed, {archived} docs archived")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--yes":
        main()
    else:
        print("This will remove legacy files.")
        print("Run with --yes flag to proceed: python scripts/cleanup_legacy.py --yes")
        sys.exit(0)

