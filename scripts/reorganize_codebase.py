#!/usr/bin/env python3
"""Reorganize codebase into professional structure"""
import shutil
from pathlib import Path
import json

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# Files to move to archive
ROOT_LEGACY_FILES = [
    "App.tsx", "BabylonWorkspace.tsx", "Canvas3D.tsx", "Home.tsx",
    "PolygonPalette.tsx", "PolygonSlider.tsx", "SnapGuide.tsx",
    "Workspace.tsx", "Workspace3D.tsx",
    "attachmentMatrix.ts", "attachmentResolver.ts", "autoSnap.ts",
    "edgeSnapping.ts", "edgeSnappingBabylon.ts", "liaisonGraph.ts",
    "polygon3D.ts", "polygonGeometry.ts", "polygonSymbols.ts",
    "polygonSymbolsV2.ts", "polygonSymbolsV2 (2).ts", "precisePolygonGeometry.ts",
    "seriesValidation.test.ts", "index.css", "index.html", "main.tsx",
    "vite.config.js", "tsconfig.json", "package.json", "package-lock.json",
    "launcher.py", "polylog_core.py", "polylog_main.py", "build-sidecar.py",
    "build_installer.bat", "build.ps1", "install_dependencies.bat",
    "launch_api.bat", "launch_desktop.bat", "launch_gui.bat", "start.bat",
    "pytest.ini", "docker-compose.yml", "requirements.txt",
    "stable_polyforms.jsonl", "provenance_log.jsonl", "performance.prof",
    "rustup-init.exe", "test_backend.html", "test_decode.json",
    "src-tauri", "web_portal", "locales", "PolylogCore"
]

# Documentation to consolidate
DOCS_TO_ARCHIVE = [
    "ARCHITECTURE_NOTES.md", "CURSOR_WORKSPACE_SETUP.md", "FILE_MIGRATION_GUIDE.md",
    "GITHUB_SETUP_GUIDE.md", "GITHUB_STATUS.md", "IMPLEMENTATION_COMPLETE.md",
    "INSTALL.md", "MIGRATION_GUIDE.md", "POLYLOG6_ARCHITECTURE.md",
    "QUICK_START.md", "README (2).md", "REORGANIZATION_COMPLETE.md",
    "REORGANIZATION_FINAL_STATUS.md", "REORGANIZATION_PLAN.md",
    "SETUP_COMPLETE.md", "SYNC_WITH_GITHUB.md", "SYSTEM_SPEC_NOTES.md",
    "WINDSURF_MIGRATION_GUIDE.md", "polylog_visualization_notes.md", "todo.md",
    "DESKTOP_IMPLEMENTATION_STATUS.md", "DESKTOP_LAUNCHER_GUIDE.md",
    "FULL_SYSTEM_INTEGRATION_PLAN.md", "CONTINUOUS_DEVELOPMENT_GUIDE.md",
    "CONTINUOUS_TESTING_IMPROVEMENT.md", "ENHANCED_TESTING_GUIDE.md",
    "TEST_SCOPE_EXPANSION_WORKFLOW.md", "TEST_VISUALIZATION_GUIDE.md",
    "CURSOR_DEVELOPMENT_SETUP.md", "DEVELOPMENT_STATUS.md", "DEVELOPMENT_WORKFLOW.md",
    "DEVELOPMENT.md", "POLYFORM_GENERATOR_DEV.md", "QUICK_START_OPTIMIZATION.md"
]

# Pasted content files
PASTED_CONTENT = [f"pasted_content{i}.txt" for i in range(1, 24)] + ["pasted_content.txt"]

def archive_file(path: Path, archive_dir: Path):
    """Move file to archive"""
    if path.exists():
        archive_dir.mkdir(parents=True, exist_ok=True)
        target = archive_dir / path.name
        if target.exists():
            target.unlink()
        path.rename(target)
        print(f"Archived: {path.name}")

def main():
    archive_dir = PROJECT_ROOT / "docs" / "archive" / "legacy_files"
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    # Archive legacy root files
    for filename in ROOT_LEGACY_FILES:
        path = PROJECT_ROOT / filename
        if path.exists():
            archive_file(path, archive_dir)
    
    # Archive documentation
    docs_archive = PROJECT_ROOT / "docs" / "archive" / "legacy_docs"
    for filename in DOCS_TO_ARCHIVE:
        path = PROJECT_ROOT / filename
        if path.exists():
            archive_file(path, docs_archive)
    
    # Archive pasted content
    content_archive = PROJECT_ROOT / "docs" / "archive" / "pasted_content"
    for filename in PASTED_CONTENT:
        path = PROJECT_ROOT / filename
        if path.exists():
            archive_file(path, content_archive)
    
    print("Reorganization complete")

if __name__ == "__main__":
    main()

